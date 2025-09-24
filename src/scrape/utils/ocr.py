from pathlib import Path
from typing import Optional
import pytesseract
from PIL import Image

def ocr_image(image_path: Path, lang: str = "eng") -> str:
    img = Image.open(image_path)
    return pytesseract.image_to_string(img, lang=lang)

def available() -> bool:
    try:
        _ = pytesseract.get_tesseract_version()
        return True
    except Exception:
        return False
