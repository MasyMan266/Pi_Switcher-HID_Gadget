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
    import LCD_1in44 
except Exception as exc:  # pragma: no cover - depends on hardware
    LCD_1in44 = None
    LCD_IMPORT_ERROR = exc
else:
    LCD_IMPORT_ERROR = None

if __package__:
    from . import Pi_def as pgdef
    from . import Pi_GUI as pggui
    from . import Gadget_Config as pgconfig
else:
    import Pi_Gadget.Pi_def as pgdef
    import Pi_Gadget.Pi_GUI as pggui
    import Pi_Gadget.Gadget_Config as pgconfig

try:
    from gpiozero import DigitalInputDevice, DigitalOutputDevice, PWMOutputDevice  # type: ignore
except ImportError:  # pragma: no cover - exercised in non-gpiozero environments
    DigitalInputDevice = DigitalOutputDevice = PWMOutputDevice = object

def main():
    """Run the menu loop and respond to button presses."""
    pgconfig.apply_default_gadget_mode()
    disp = pgdef.initialize_display()
    current_menu = "main"
    selected_index = 0
    update_thread = None
    update_complete = False
    update_error = None
    update_complete_holder = [False]
    update_error_holder = [None]
    update_thread_holder = [None]
    status_message = "Checking USB..."
    status_thread = None
    status_result = [status_message]
    menu_stack = ["main"]
    last_action_time = time.monotonic()

    font, small_font = pggui.load_fonts()
    print("about to set background_path")
    background_path = Path(__file__).resolve().parent / "mal_I.png"
    print("background_path:", background_path)
    print("path type:", type(background_path))
    print("exists:", background_path.exists())
    base_image = pggui.load_background_image(background_path)

    while True:
        update_complete = update_complete_holder[0]
        update_error = update_error_holder[0]
        if current_menu == "updating":
            current_menu, selected_index = pgdef.transition_after_update(current_menu, update_complete, update_thread)

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

        pggui.draw_menu(
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
        
        key1 = pgdef.read_button_state(disp, "GPIO_KEY1_PIN")
        key2 = pgdef.read_button_state(disp, "GPIO_KEY2_PIN")
        key3 = pgdef.read_button_state(disp, "GPIO_KEY3_PIN")

        if key1 == 1:
            # Select Key
            if current_menu not in {"status", "updating"}:
                menu_items = pgdef.get_menu_items(current_menu)
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
            elif current_menu == "main":
                next_menu, next_index = pgdef.handle_selection(current_menu, selected_index)
                current_menu, selected_index = next_menu, next_index
                if current_menu == "reboot":
                    sup.run("sudo reboot", shell=True, check=False)
                    time.sleep(2)
                    break

            elif current_menu == "settings":
                next_menu, next_index = pgdef.handle_selection(current_menu, selected_index)
                current_menu, selected_index = next_menu, next_index
                if current_menu == "updating":
                    update_complete = False
                    update_error = None
                    update_complete_holder = [False]
                    update_error_holder = [None]
                    update_thread_holder = [None]
                    update_thread = threading.Thread(
                        target=pgdef.run_update,
                        args=(update_complete_holder, update_error_holder, update_thread_holder),
                        daemon=True,
                    )
                    update_thread.start()
                elif current_menu == "shutdown":
                    sup.run("sudo shutdown now", shell=True, check=False)
                    time.sleep(2)
                    break                           
            elif current_menu == "gadget":
                if selected_index == 3 and pgconfig.current_gadget_mode != pgdef.DEFAULT_GADGET_MODE:
                    # Leaving the gadget menu: restore default USB mode and reboot so cmdline/module changes apply.
                    sup.run("sudo reboot", shell=True, check=False)
                    time.sleep(2)
                    break
                else:
                    next_menu, next_index = pgdef.handle_selection(current_menu, selected_index)
                    current_menu, selected_index = next_menu, next_index
                if current_menu == "drive":
                    pgconfig.switch_to_drive_mode()
        
            elif current_menu == "drive":
                pgconfig.restore_default_gadget_mode()
                current_menu = "gadget"
                selected_index = 0

            elif current_menu == "rubber_ducky":
                if 0 <= selected_index < 3:
                    pgdef.launch_rubber_ducky_script(selected_index)
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

