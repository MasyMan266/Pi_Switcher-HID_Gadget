
from pathlib import Path
from PIL import Image, ImageDraw
from typing import Any, cast

import Pi_Gadget.Pi_Gadget_def as pgdef

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:  # pragma: no cover - exercised in non-Pillow environments
    Image = ImageDraw = ImageFont = None


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


def load_fonts():
    """Load the fonts used for the menu text."""
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 11)
        small_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 8)
    except Exception:
        font = ImageFont.load_default()
        small_font = ImageFont.load_default()
    return font, small_font

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
            items = pgdef.get_menu_items(current_menu)
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