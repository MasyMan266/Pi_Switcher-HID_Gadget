import sys
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import Pi_Gadget.Pi_main as gadget


class PiGadgetTests(unittest.TestCase):
    def test_main_menu_items(self):
        self.assertEqual(gadget.get_menu_items("main"), gadget.MAIN_MENU_ITEMS)

    def test_gadget_menu_items(self):
        self.assertEqual(gadget.get_menu_items("gadget"), gadget.GADGET_MENU_ITEMS)

    def test_selection_wraps_around(self):
        self.assertEqual(gadget.advance_selection(3, 3), 0)

    def test_main_selection_routes_to_gadget(self):
        current_menu, selected_index = gadget.handle_selection("main", 2)
        self.assertEqual(current_menu, "gadget")
        self.assertEqual(selected_index, 0)

    def test_gadget_selection_routes_to_rubber_ducky(self):
        current_menu, selected_index = gadget.handle_selection("gadget", 0)
        self.assertEqual(current_menu, "rubber_ducky")
        self.assertEqual(selected_index, 0)

    def test_gadget_menu_allows_back_navigation(self):
        current_menu, selected_index = gadget.handle_selection("gadget", 3)
        self.assertEqual(current_menu, "main")
        self.assertEqual(selected_index, 0)

    def test_update_completion_returns_to_settings(self):
        current_menu, selected_index = gadget.transition_after_update("updating", True, object())
        self.assertEqual(current_menu, "settings")
        self.assertEqual(selected_index, 0)

    @patch("Pi_Gadget.serial_tools")
    def test_usb_status_reports_connected_gadget(self, mock_serial_tools):
        mock_serial_tools.comports.return_value = [
            type("Port", (), {
                "device": "/dev/ttyACM0",
                "description": "USB Serial Device",
                "manufacturer": "Rubber Ducky",
                "hwid": r"USB\VID_1209&PID_2302",
                "vid": 0x1209,
                "pid": 0x2302,
                "serial_number": "ABC123",
            })()
        ]
        self.assertEqual(gadget.usb_status_info(), "Rubber Ducky connected")

    @patch("Pi_Gadget.serial_tools")
    def test_draw_status_screen_does_not_crash(self, mock_serial_tools):
        mock_serial_tools.comports.return_value = [
            type("Port", (), {
                "device": "/dev/ttyACM0",
                "description": "USB Serial Device",
                "manufacturer": "Rubber Ducky",
                "hwid": r"USB\VID_1209&PID_2302",
                "vid": 0x1209,
                "pid": 0x2302,
                "serial_number": "ABC123",
            })()
        ]

        class DummyDisplay:
            def LCD_ShowImage(self, *args, **kwargs):
                return None

        gadget.draw_menu(
            DummyDisplay(),
            "status",
            0,
            None,
            gadget.ImageFont.load_default(),
            gadget.ImageFont.load_default(),
            None,
        )

    def test_read_button_state_reads_display_pin_value(self):
        class DummyDisplay:
            GPIO_KEY1_PIN = type("Pin", (), {"value": 1})()

        self.assertEqual(gadget.read_button_state(DummyDisplay(), "GPIO_KEY1_PIN"), 1)


if __name__ == "__main__":
    unittest.main()
