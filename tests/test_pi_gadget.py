import sys
import unittest
from pathlib import Path
from unittest.mock import Mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from Pi_Gadget import Pi_def as pgdef
from Pi_Gadget import Pi_GUI as pggui
from Pi_Gadget import Pi_main as app


class PiGadgetTests(unittest.TestCase):
    def test_main_menu_items(self):
        self.assertEqual(pgdef.get_menu_items("main"), pgdef.MAIN_MENU_ITEMS)

    def test_gadget_menu_items(self):
        self.assertEqual(pgdef.get_menu_items("gadget"), pgdef.GADGET_MENU_ITEMS)

    def test_selection_wraps_around(self):
        self.assertEqual(pgdef.advance_selection(2, 3), 0)

    def test_main_selection_routes_to_gadget(self):
        current_menu, selected_index = pgdef.handle_selection("main", 2)
        self.assertEqual(current_menu, "gadget")
        self.assertEqual(selected_index, 0)

    def test_settings_selections_match_menu_items(self):
        self.assertEqual(pgdef.handle_selection("settings", 0), ("updating", 0))
        self.assertEqual(pgdef.handle_selection("settings", 1), ("main", 0))
        self.assertEqual(pgdef.handle_selection("settings", 2), ("shutdown", 0))

    def test_gadget_selection_routes_to_rubber_ducky(self):
        current_menu, selected_index = pgdef.handle_selection("gadget", 0)
        self.assertEqual(current_menu, "rubber_ducky")
        self.assertEqual(selected_index, 0)

    def test_gadget_menu_allows_back_navigation(self):
        current_menu, selected_index = pgdef.handle_selection("gadget", 3)
        self.assertEqual(current_menu, "main")
        self.assertEqual(selected_index, 0)

    def test_update_completion_returns_to_settings(self):
        current_menu, selected_index = pgdef.transition_after_update("updating", True, object())
        self.assertEqual(current_menu, "settings")
        self.assertEqual(selected_index, 0)

    def test_entry_point_uses_split_modules(self):
        self.assertIs(app.pgdef, pgdef)
        self.assertIs(app.pggui, pggui)

    def test_draw_status_screen_sends_image_to_display(self):
        display = Mock()
        font, small_font = pggui.load_fonts()
        pggui.draw_menu(
            display,
            "status",
            0,
            None,
            font,
            small_font,
            None,
        )
        display.LCD_ShowImage.assert_called_once()
        image = display.LCD_ShowImage.call_args.args[0]
        self.assertEqual(image.size, (128, 128))

    def test_read_button_state_reads_display_pin_value(self):
        class DummyDisplay:
            GPIO_KEY1_PIN = type("Pin", (), {"value": 1})()

        self.assertEqual(pgdef.read_button_state(DummyDisplay(), "GPIO_KEY1_PIN"), 1)


if __name__ == "__main__":
    unittest.main()
