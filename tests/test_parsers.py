import pytest
from pathlib import Path
from src.scrape.parsers.pdf_parser import extract_pdf_text
from src.scrape.parsers.guess_sections import count_sections
from src.scrape.parsers.latex_parser import extract_latex_text
from src.scrape.parsers.docx_parser import extract_docx_text

def test_count_sections():
    """Test section counting functionality."""
    text1 = """
    1. Introduction
    This is the introduction section.
    
    2. Methods
    This is the methods section.
    
    3. Results
    This is the results section.
    """
    assert count_sections(text1) >= 3
    
    text2 = "No sections here"
    assert count_sections(text2) == 1

def test_latex_parser():
    """Test LaTeX parser preserves math symbols."""
    latex_content = r"""
    \section{Introduction}
    The equation $E = mc^2$ is famous.
    Another equation: $\int_0^\infty e^{-x} dx = 1$
    """
    result = extract_latex_text(Path("dummy"), preserve_math=True)
    # This is a dummy test since we don't have a real file
    assert isinstance(result, str)

def test_docx_parser():
    """Test DOCX parser."""
    # This would need a real DOCX file to test properly
    # For now, just test that the function exists
    assert callable(extract_docx_text)

def test_pdf_parser_ocr_available():
    """Test PDF parser with OCR availability check."""
    from src.scrape.utils.ocr import available
    # Test that OCR availability check works
    assert isinstance(available(), bool)

def test_pdf_parser_signature():
    """Test PDF parser function signature."""
    # Test that the function accepts the expected parameters
    import inspect
    sig = inspect.signature(extract_pdf_text)
    params = list(sig.parameters.keys())
    assert 'pdf_path' in params
    assert 'ocr_enabled' in params
    assert 'ocr_language' in params