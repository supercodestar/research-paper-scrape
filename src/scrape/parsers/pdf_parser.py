from pathlib import Path
import fitz  # PyMuPDF
from typing import Tuple, Optional
import io
from PIL import Image
from ..utils.ocr import ocr_image, available as ocr_available
from loguru import logger

def extract_pdf_text(pdf_path: Path, ocr_enabled: bool = True, ocr_language: str = "eng") -> Tuple[str, bool]:
    """
    Extract text from PDF, using OCR if needed for scanned documents.
    Preserves LaTeX math symbols ($...$) in the text.
    Returns (text, is_scanned_guess).
    """
    text_chunks = []
    is_scanned_guess = True
    ocr_used = False
    
    try:
        with fitz.open(pdf_path) as doc:
            for page_num, page in enumerate(doc):
                # Try to extract text normally first
                text = page.get_text("text")
                
                if text.strip():
                    # Text extraction worked, likely not scanned
                    is_scanned_guess = False
                    text_chunks.append(text)
                elif ocr_enabled and ocr_available():
                    # Try OCR for this page
                    try:
                        # Convert page to image
                        mat = fitz.Matrix(2.0, 2.0)  # 2x zoom for better OCR
                        pix = page.get_pixmap(matrix=mat)
                        img_data = pix.tobytes("png")
                        
                        # Use PIL to open the image
                        img = Image.open(io.BytesIO(img_data))
                        
                        # OCR the image
                        ocr_text = ocr_image(img, ocr_language)
                        if ocr_text.strip():
                            text_chunks.append(ocr_text)
                            ocr_used = True
                            logger.debug(f"Used OCR for page {page_num + 1}")
                    except Exception as e:
                        logger.warning(f"OCR failed for page {page_num + 1}: {e}")
                        text_chunks.append("")  # Empty string for failed page
                else:
                    text_chunks.append("")  # Empty string for page with no text
                    
    except Exception as e:
        logger.error(f"Error processing PDF {pdf_path}: {e}")
        return "", True
    
    full_text = "\n".join(text_chunks)
    
    # Preserve LaTeX math symbols - they should already be in the text
    # This function just ensures we don't accidentally strip them
    if ocr_used:
        logger.info(f"Used OCR for PDF: {pdf_path.name}")
    
    return full_text, is_scanned_guess
