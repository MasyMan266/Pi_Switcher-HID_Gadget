
from pathlib import Path
from typing_extensions import Self
from PIL import Image, ImageDraw
from typing import Any, cast

if __package__:
    from . import Pi_Gadget_def as pgdef
else:
    import Pi_Gadget_def as pgdef

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:  # pragma: no cover - exercised in non-Pillow environments
    Image = ImageDraw = ImageFont = None


import numpy as np

class _DummyImage:  # type: ignore[no-redef]
    def __init__(self, *args, **kwargs):
        # Create a real, blank 128x128 PIL Image canvas
        self._pil_img = Image.new("RGB", (128, 128), (0, 0, 0))
        # Keep a numpy array version for array indexing operations
        self._array = np.zeros((128, 128, 3), dtype=np.uint8)

    # Mimics PIL Image behavior (.paste, .size, etc.)
    def __getattr__(self, name):
        return getattr(self._pil_img, name)

    # Mimics NumPy Array behavior (bracket indexing like img[..., 0])
    def __getitem__(self, index):
        return self._array[index]

    @property
    def shape(self):
        return self._array.shape

    @property
    def ndim(self):
        return 3

    def convert(self, *_args, **_kwargs):
        return self

    def resize(self, size):
        return self

    def paste(self, *_args, **_kwargs):
        return None

    def new(self, *args, **kwargs):
        return self

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