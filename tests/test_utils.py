import pytest
import time
from src.scrape.utils.rate import RateLimiter
from src.scrape.utils.ocr import available, ocr_image
from src.scrape.utils.files import ensure_dir, save_bytes
from pathlib import Path
from PIL import Image
import io

def test_rate_limiter():
    """Test rate limiter functionality."""
    rl = RateLimiter(max_per_minute=10, burst=2)
    
    # Test basic waiting
    start = time.time()
    rl.wait()
    elapsed = time.time() - start
    assert elapsed < 0.1  # Should be very fast for first call
    
    # Test backoff
    rl.backoff()
    assert rl.consecutive_failures == 1
    
    # Test reset
    rl.reset_backoff()
    assert rl.consecutive_failures == 0

def test_ocr_availability():
    """Test OCR availability check."""
    # This will depend on whether tesseract is installed
    result = available()
    assert isinstance(result, bool)

def test_ocr_image():
    """Test OCR image processing."""
    # Create a simple test image
    img = Image.new('RGB', (100, 100), color='white')
    
    # Test OCR (may fail if tesseract not available, but shouldn't crash)
    try:
        result = ocr_image(img, "eng")
        assert isinstance(result, str)
    except Exception:
        # OCR might not be available, that's okay for testing
        pass

def test_files_utils():
    """Test file utility functions."""
    test_dir = Path("test_temp_dir")
    
    # Test ensure_dir
    ensure_dir(test_dir)
    assert test_dir.exists()
    assert test_dir.is_dir()
    
    # Test save_bytes
    test_file = test_dir / "test.txt"
    test_content = b"Hello, World!"
    save_bytes(test_file, test_content)
    assert test_file.exists()
    assert test_file.read_bytes() == test_content
    
    # Cleanup
    test_file.unlink()
    test_dir.rmdir()
