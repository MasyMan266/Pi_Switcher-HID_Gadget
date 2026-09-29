
from pathlib import Path
import os
import subprocess as sup

try:
    import LCD_1in44 as LCD_1in44
except Exception as exc:  
    LCD_1in44 = None
    LCD_IMPORT_ERROR = exc
else:
    LCD_IMPORT_ERROR = None

try:
    import serial
    import serial.tools.list_ports as serial_tools
except ImportError:  
    from typing import Any, cast
    serial = None
    serial_tools = None

ports = serial_tools.comports() if serial_tools is not None else []


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
    #Return the label list for the menu that is currently open.
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
            1: ("main", 0),
            2: ("shutdown", 0),
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



