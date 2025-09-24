from pathlib import Path
from typing import Optional
import pytesseract
from PIL import Image
import io

def ocr_image(image: Image.Image, lang: str = "eng") -> str:
    """OCR an image object directly."""
    try:
        return pytesseract.image_to_string(image, lang=lang)
    except Exception as e:
        print(f"OCR error: {e}")
        return ""

def ocr_image_file(image_path: Path, lang: str = "eng") -> str:
    """OCR an image file from disk."""
    try:
        img = Image.open(image_path)
        return ocr_image(img, lang)
    except Exception as e:
        print(f"OCR file error: {e}")
        return ""

def available() -> bool:
    try:
        _ = pytesseract.get_tesseract_version()
        return True
    except Exception:
        return False
