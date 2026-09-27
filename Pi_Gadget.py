from __future__ import annotations

"""Simple Raspberry Pi menu UI for a small LCD display.

This version keeps the same behavior as the original script, but it uses
clearer helper functions and comments so beginners can follow the flow more easily.
"""
import os
import subprocess as sup
import threading
import time
from pathlib import Path

try:
    import serial
    import serial.tools.list_ports as serial_tools
except ImportError:  
    from typing import Any, cast
    serial = None
    serial_tools = None

ports = serial_tools.comports() if serial_tools is not None else []

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:  # pragma: no cover - exercised in non-Pillow environments
    class _DummyImage:  # type: ignore[no-redef]
        @staticmethod
        def open(_path):
            return _DummyImage(mode="RGB", size=(128, 128), color=(0, 0, 0))

        @staticmethod
        def new(
            mode: str,
            size: tuple[int, int],
            color: int | str = 0,
        ):
            return _DummyImage(mode=mode, size=size, color=color)
    
        def __init__(self, mode=None, size=None, color=None):
            self.mode = mode
            self.size = size or (128, 128)
            self.color = color
        def convert(self, *_args, **_kwargs):
            return self

        def resize(self, size):
            self.size = size
            return self

        def paste(self, *_args, **_kwargs):
            return None

        def __enter__(self):
            return self
        def __exit__(self, exc_type, exc, tb):
            return False

    class _DummyImageDraw:  # type: ignore[no-redef]
        @staticmethod
        def Draw(_image: Any, mode: str | None = None) -> "_DummyImageDraw":
            return _DummyImageDraw()
        
        def __init__(self, *_args, **_kwargs):
            pass

        def rectangle(self, *_args: Any, **_kwargs: Any) -> None:
            return None

        def text(self, *_args: Any, **_kwargs: Any) -> None:
            return None

    class _DummyImageFont:  # type: ignore[no-redef]
        @staticmethod
        def truetype(*_args, **_kwargs):
            return None

        @staticmethod
        def load_default():
            return None

    Image = _DummyImage
    ImageDraw = _DummyImageDraw
    ImageFont = _DummyImageFont

try:
    import LCD_1in44
except Exception as exc:  # pragma: no cover - depends on hardware
    LCD_1in44 = None
    LCD_IMPORT_ERROR = exc
else:
    LCD_IMPORT_ERROR = None

try:
    from gpiozero import DigitalInputDevice, DigitalOutputDevice, PWMOutputDevice  # type: ignore
except ImportError:  # pragma: no cover - exercised in non-gpiozero environments
    DigitalInputDevice = DigitalOutputDevice = PWMOutputDevice = object

MAIN_MENU_ITEMS = ["View Status", "Settings", "Gadgets", "Reboot"]
GADGET_MENU_ITEMS = ["Rubber Ducky", "drive", "unknown","Back"]
RUBBER_DUCKY_MENU_ITEMS = ["1.", "2.", "3.", "Back"]
SETTINGS_MENU_ITEMS = ["Update","Back", "Shutdown"]
DEFAULT_GADGET_MODE = "libcomposite"
current_gadget_mode = DEFAULT_GADGET_MODE

class FileHandler:
    def __init__(self, base_directory: Path):
        path = self.base_directory = base_directory

    def read(self, filename: str):
        path = self.base_directory / filename
        if not path.exists():
            raise FileNotFoundError(path)
        return path.read_text(encoding="utf-8")

    def write(self, filename: str, content: str):
        path = self.base_directory / filename
        path.write_text(content, encoding="utf-8")

    def swap(self, active_file: str, replacement_file: str) -> None:
        active_path = self.base_directory / active_file
        replacement_path = self.base_directory / replacement_file
        if not replacement_path.exists():
            raise FileNotFoundError(active_path)

        if not active_path.exists():
            raise FileNotFoundError(replacement_path)

        active_contents = active_path.read_text(encoding="utf-8")
        replacement_contents = replacement_path.read_text(encoding="utf-8")

        active_path.write_text(replacement_contents, encoding="utf-8")
        replacement_path.write_text(active_contents, encoding="utf-8")

def get_menu_items(current_menu: str):
    """Return the label list for the menu that is currently open."""
    menu_items = {
        "main": MAIN_MENU_ITEMS,
        "gadget": GADGET_MENU_ITEMS,
        "rubber_ducky": RUBBER_DUCKY_MENU_ITEMS,
        "settings": SETTINGS_MENU_ITEMS,
    }
    return list(menu_items.get(current_menu, []))


def advance_selection(selected_index: int, item_count: int) -> int:
    """Move to the next menu item and wrap around to the start when needed."""
    if item_count <= 0:
        return 0
    if selected_index >= item_count - 1:
        return 0
    return selected_index + 1


def handle_selection(current_menu: str, selected_index: int):
    """Return the next menu screen after the user confirms a selection."""
    if current_menu == "main":
        menu_map = {
            0: ("status", 0),
            1: ("settings", 0),
            2: ("gadget", 0),
            3: ("reboot", 0),
        }
        return menu_map.get(selected_index, (current_menu, selected_index))

    if current_menu == "settings":
        menu_map = {
            0: ("updating", 0),
            1: ("settings", 1),
            2: ("main", 0),
            3: ("shutdown", 0),
        }
        return menu_map.get(selected_index, (current_menu, selected_index))

    if current_menu == "gadget":
        menu_map = {
            0: ("rubber_ducky", 0),
            1: ("drive", 1),
            2: ("serial", 2),
            3: ("main", 0),
        }
        return menu_map.get(selected_index, (current_menu, selected_index))

    if current_menu == "rubber_ducky":
        menu_map = {
            0: ("rubber_ducky", 0),
            1: ("rubber_ducky", 1),
            2: ("rubber_ducky", 2),
            3: ("gadget", 0),
        }
        return menu_map.get(selected_index, (current_menu, selected_index))

    return current_menu, selected_index


def transition_after_update(current_menu: str, update_complete: bool, update_thread) -> tuple[str, int]:
    if current_menu != "updating":
        return current_menu, 0
    if update_complete:
        return "settings", 0
    if update_thread is None:
        return current_menu, 0
    if hasattr(update_thread, "is_alive") and not update_thread.is_alive():
        return "settings", 0
    return current_menu, 0

def pi_config(cmdline=None, modules=None):
    config_dir = Path(__file__).resolve().parent / "config_swap_files"

    if cmdline is not None:
        old_cmdline_path = Path("/boot/firmware/cmdline.txt")
        new_cmdline_path = config_dir / cmdline

        if not new_cmdline_path.exists():
            raise FileNotFoundError(f"Missing cmdline swap file: {new_cmdline_path}")

        if not old_cmdline_path.exists():
            # Not running on real Pi hardware (e.g. local dev/debugging); nothing to swap.
            print(f"Skipping cmdline swap, not found: {old_cmdline_path}")
        else:
            temp = old_cmdline_path.read_text()
            old_cmdline_path.write_text(new_cmdline_path.read_text())
            new_cmdline_path.write_text(temp)

    if modules is not None:
        old_modules_path = Path("/etc/modules")
        new_modules_path = config_dir / modules

        if not new_modules_path.exists():
            raise FileNotFoundError(f"Missing modules swap file: {new_modules_path}")

        if not old_modules_path.exists():
            print(f"Skipping modules swap, not found: {old_modules_path}")
        else:
            temp = old_modules_path.read_text()
            old_modules_path.write_text(new_modules_path.read_text())
            new_modules_path.write_text(temp)


def load_background_image(path: Path):
    try:
        with Image.open(path) as image:
            image = image.convert("RGB")
            if image.size != (128, 128):
                image = image.resize((128, 128))
            return image
    except Exception as exc:
        print(f"Background image unavailable: {exc}")
        return Image.new("RGB", (128, 128), "Black")
# Raspberry Pi File Swap

def draw_menu(disp, current_menu, selected_index, base_image, font, small_font, update_error,
              status_message="Checking USB..."):
    if disp is None:
        print("Display unavalible - running in debug mode")
        return

    try:
        im = Image.new("RGB", (128, 128), "Black")
        if base_image is not None:
            im.paste(base_image, (0, 0))
        draw = ImageDraw.Draw(cast(Any, im))
        

        if current_menu == "updating":
            draw.rectangle((8, 20, 120, 84), fill="Black")
            draw.text((64, 36), "Updating System...", fill="White", font=font, anchor="mm")
            if update_error:
                draw.text((64, 64), "Update failed", fill="Red", font=small_font, anchor="mm")
            else:
                draw.text((64, 64), "Please wait", fill="White", font=small_font, anchor="mm")
            draw.text((64, 92), "Menu will return shortly", fill="Grey", font=small_font, anchor="mm")

        elif current_menu == "status":
            draw.rectangle((8, 8, 120, 120), fill="Black")
            draw.text((64, 60), status_message, fill="White", font=small_font, anchor="mm")
        elif current_menu == "drive":
            try:
                draw.rectangle((8, 8, 120, 120), fill="Blue")
                with Image.open("/home/masyman266/RaspberryPiCode/usb_image.png") as drive_image:
                    drive_image = drive_image.convert("RGB")
                    if drive_image.size != (60, 60):
                        drive_image = drive_image.resize((60, 60))
                    im.paste(cast(Any, drive_image), (32, 32))

            except Exception as exc:
                print(f"Failed to load drive image: {exc}")
                draw.rectangle((8, 8, 120, 120), fill="Black")
                draw.text((64, 60), f"{exc}", fill="Red", font=small_font, anchor="mm")
        else:
            items = get_menu_items(current_menu)
            y_offset = 8
            for i, item in enumerate(items):
                box_top = y_offset + (i * 20)
                box_bottom = box_top + 24
                if i == selected_index:
                    draw.rectangle((10, box_top, 118, box_bottom), fill="Grey")
                    text_color = "White"
                else:
                    draw.rectangle((10, box_top, 118, box_bottom), fill="Black")
                    text_color = "Red"
                draw.text((64, box_top + 12), item, fill=text_color, font=font, anchor="mm")

        disp.LCD_ShowImage(im, 0, 0)
    except Exception as exc:
        print(f"Display render failed: {exc}")

def apply_default_gadget_mode():
    if current_gadget_mode == "libcomposite":
        pi_config("cmdline_Drive.txt", "modules_libcomposite.txt")
    elif current_gadget_mode == "drive":
        pi_config("cmdline_Drive.txt", "modules_Drive.txt")
    elif current_gadget_mode == "serial":
        pi_config("cmdline_USBSerial.txt", "modules_USBSerial.txt")

def start_serial():
    try:
        sup.run("sudo /home/masyman266/RaspberryPiCode/usbmode_swap_files/start_serial.sh", shell=True, check=False)
    except Exception as exc:
        print(f"Failed to start serial gadget: {exc}")

def stop_current_gadget():
    try:
        sup.run("sudo /home/masyman266/RaspberryPiCode/usbmode_swap_files/stop_gadget.sh", shell=True, check=False)
    except Exception as exc:
        print(f"Failed to stop current gadget: {exc}")


def unmount_drive():
    try:
        sup.run("sudo /home/masyman266/RaspberryPiCode/usbmode_swap_files/unmount_drive.sh", shell=True, check=False)
    except Exception as exc:
        print(f"Failed to unmount drive: {exc}")

def mount_drive(path, folder):
    try:
        sup.run(f"sudo /home/masyman266/RaspberryPiCode/usbmode_swap_files/mount_drive.sh {path} {folder}", shell=True, check=False)
        
    except Exception as exc:
        print(f"Failed to mount drive: {exc}")

def start_mass_storage(path):
    try:
        sup.run(f"sudo /home/masyman266/RaspberryPiCode/usbmode_swap_files/start_mass_storage.sh {path}", shell=True, check=False)
    except Exception as exc:
        print(f"Failed to start mass storage: {exc}")

def switch_to_drive_mode():
    try:
        stop_current_gadget()
        pi_config("cmdline_Drive.txt", "modules_Drive.txt")
        mount_drive("/piusb.bin", "/mnt/usbdrive")
        start_mass_storage("/piusb.bin")

    except Exception as exc:
        print(f"Failed to switch to drive mode: {exc}")


def restore_default_gadget_mode():
    try:
        stop_current_gadget()
        unmount_drive()
        apply_default_gadget_mode()
    except Exception as exc:
        print(f"Failed to restore default gadget mode: {exc}")

def switch_to_serial_mode():
    try:
        stop_current_gadget()
        pi_config("cmdline_USBSerial.txt", "modules_USBSerial.txt")
        if os.path.ismount("/mnt/usbdrive"):
            unmount_drive()
        start_serial()
    except Exception as exc:
        print(f"Failed to switch to serial mode: {exc}")

def run_update(update_complete_holder, update_error_holder, update_thread_holder):
    try:
        cmd = "sudo apt-get update && sudo apt-get upgrade -y"
        result = sup.run(cmd, shell=True, check=False, capture_output=True, text=True)
        if result.returncode != 0:
            raise RuntimeError(result.stderr.strip() or result.stdout.strip() or "Update failed")
    except Exception as exc:
        update_error_holder[0] = str(exc)
    finally:
        update_complete_holder[0] = True
        if update_thread_holder:
            update_thread_holder[0] = None

def read_button_state(display, pin_name):
    """Read a button pin from the display object and return its current state."""
    try:
        return int(getattr(display, pin_name).value)
    except Exception:
        return 0

def script_cmd(script_path):
    try:
        sup.run(["sudo", "hid_parser", str(script_path)])
    except Exception as exc:
        print(f"Error: {exc}")


def launch_rubber_ducky_script(selected_index):
    script_paths = [
        "Hi this is a test script 1",
        "Hi this is a test script 2",
        "Hi this is a test script 3",
    ]
    if 0 <= selected_index < len(script_paths):
        script_cmd(script_paths[selected_index])

def initialize_display():
    """Create the LCD display object and prepare it for drawing."""
    disp = None
    try:
        if LCD_1in44 is not None:
            disp = LCD_1in44.LCD()
            lcd_scan = getattr(LCD_1in44, "SCAN_DIR_DFT", None)
            disp.LCD_Init(lcd_scan)
            disp.LCD_Clear()
        else:
            print(f"LCD module unavailable: {LCD_IMPORT_ERROR}")
    except Exception as exc:
        print(f"Display init failed: {exc}")
        disp = None
    return disp


def load_fonts():
    """Load the fonts used for the menu text."""
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 11)
        small_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 8)
    except Exception:
        font = ImageFont.load_default()
        small_font = ImageFont.load_default()
    return font, small_font


def main():
    """Run the menu loop and respond to button presses."""
    apply_default_gadget_mode()
    disp = initialize_display()
    current_menu = "main"
    selected_index = 0
    update_thread = None
    update_complete = False
    update_error = None
    status_message = "Checking USB..."
    status_thread = None
    status_result = [status_message]
    menu_stack = ["main"]
    last_action_time = time.monotonic()

    font, small_font = load_fonts()
    print("about to set background_path")
    background_path = Path(__file__).resolve().parent / "mal_I.png"
    print("background_path:", background_path)
    print("path type:", type(background_path))
    print("exists:", background_path.exists())
    base_image = load_background_image(background_path)

    while True:
        if current_menu == "updating":
            current_menu, selected_index = transition_after_update(current_menu, update_complete, update_thread)

        if current_menu == "status" and status_thread is None:
            status_result[0] = "Checking USB..."
            status_thread = threading.Thread(
                target=lambda: status_result.__setitem__(0, "USB check complete"),
                daemon=True,
            )
            status_thread.start()
        if current_menu == "status" and status_thread is not None and not status_thread.is_alive():
            status_message = status_result[0]
            status_thread = None

        draw_menu(
            disp, current_menu, selected_index, base_image, font, small_font, update_error,
            status_message,
        )

        if disp is None:
            time.sleep(0.2)
            break

        now = time.monotonic()
        if now - last_action_time < 0.25:
            time.sleep(0.01)
            continue
        
        key1 = read_button_state(disp, "GPIO_KEY1_PIN")
        key2 = read_button_state(disp, "GPIO_KEY2_PIN")
        key3 = read_button_state(disp, "GPIO_KEY3_PIN")

        if key1 == 1:
            # Select Key
            if current_menu not in {"status", "updating"}:
                menu_items = get_menu_items(current_menu)
                selectable_indices = [
                    index for index, item in enumerate(menu_items)
                    if item and str(item).strip()
                ]

                if selectable_indices:
                    if selected_index not in selectable_indices:
                        selected_index = selectable_indices[0]
                    else:
                        current_pos = selectable_indices.index(selected_index)
                        selected_index = selectable_indices[(current_pos + 1) % len(selectable_indices)]

                last_action_time = now
                time.sleep(0.05)
        if key2 == 1:
            last_action_time = now
            time.sleep(0.05)

            if current_menu in {"status", "updating"}:
                current_menu = "main"
                selected_index = 0
            elif current_menu == "settings":
                if len(menu_stack) > 1:
                    menu_stack.pop()
                    current_menu = menu_stack[-1]
                    selected_index = 0
                else:
                    current_menu = "main"
                    selected_index = 0

            elif current_menu == "main":
                next_menu, next_index = handle_selection(current_menu, selected_index)
                current_menu, selected_index = next_menu, next_index
                if current_menu == "reboot":
                    sup.run("sudo reboot", shell=True, check=False)
                    time.sleep(2)
                    break

            elif current_menu == "settings":
                next_menu, next_index = handle_selection(current_menu, selected_index)
                current_menu, selected_index = next_menu, next_index
                if current_menu == "updating":
                    update_complete = False
                    update_error = None
                    update_complete_holder = [False]
                    update_error_holder = [None]
                    update_thread_holder = [None]
                    update_thread = threading.Thread(
                        target=run_update,
                        args=(update_complete_holder, update_error_holder, update_thread_holder),
                        daemon=True,
                    )
                    update_thread.start()
                elif current_menu == "shutdown":
                    sup.run("sudo shutdown now", shell=True, check=False)
                    time.sleep(2)
                    break                           
            elif current_menu == "gadget":
                if selected_index == 3 and current_gadget_mode != DEFAULT_GADGET_MODE:
                    # Leaving the gadget menu: restore default USB mode and reboot so cmdline/module changes apply.
                    sup.run("sudo reboot", shell=True, check=False)
                    time.sleep(2)
                    break
                else:
                    next_menu, next_index = handle_selection(current_menu, selected_index)
                    current_menu, selected_index = next_menu, next_index
                if current_menu == "drive":
                    switch_to_drive_mode()
        
            elif current_menu == "drive":
                restore_default_gadget_mode()
                current_menu = "gadget"
                selected_index = 0

            elif current_menu == "rubber_ducky":
                if 0 <= selected_index < 3:
                    launch_rubber_ducky_script(selected_index)
                else:
                    current_menu = "gadget"
                    selected_index = 0


                    

                    
                    
        time.sleep(0.01)

    if disp is not None:
        try:
            disp.LCD_Clear()
        except Exception:
            pass
    print("exit")


if __name__ == "__main__":
    main()

