from pathlib import Path
import fitz  # PyMuPDF
from typing import Tuple

def extract_pdf_text(pdf_path: Path) -> Tuple[str, bool]:
    """Return (text, is_scanned_guess)."""
    text_chunks = []
    is_scanned_guess = True
    with fitz.open(pdf_path) as doc:
        for page in doc:
            t = page.get_text("text")
            if t.strip():
                is_scanned_guess = False
            text_chunks.append(t)
    return ("\n".join(text_chunks), is_scanned_guess)
