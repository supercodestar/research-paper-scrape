import pytest
from pathlib import Path
from unittest.mock import Mock, patch
from src.scrape.sources.chemrxiv import ChemRxivSource
from src.scrape.sources.openreview import OpenReviewSource
from src.scrape.models import Record

def test_chemrxiv_source_init():
    """Test ChemRxiv source initialization."""
    cfg = Mock()
    cfg.chemrxiv_listing_url = "https://chemrxiv.org/engage/chemrxiv/public-dashboard"
    cfg.chemrxiv_listing_wait_selector = "div[role='grid']"
    cfg.chemrxiv_item_link_selector = "a[href*='/engage/chemrxiv/article/']"
    cfg.chemrxiv_pdf_link_selector = "a[href$='.pdf']"
    cfg.user_agent = "TestBot/1.0"
    cfg.ocr_enabled = True
    cfg.ocr_language = "eng"
    cfg.output_dir = "data"
    
    http_client = Mock()
    rate_limiter = Mock()
    out_dir = Path("test_output")
    stats = Mock()
    
    source = ChemRxivSource(cfg, http_client, rate_limiter, out_dir, stats)
    assert source.name == "chemrxiv"
    assert source.cfg == cfg

def test_openreview_source_init():
    """Test OpenReview source initialization."""
    cfg = Mock()
    cfg.openreview_api_base = "https://api.openreview.net"
    cfg.openreview_search_path = "/notes/search"
    cfg.openreview_discussions_path = "/notes"
    cfg.user_agent = "TestBot/1.0"
    cfg.ocr_enabled = True
    cfg.ocr_language = "eng"
    cfg.output_dir = "data"
    
    http_client = Mock()
    rate_limiter = Mock()
    out_dir = Path("test_output")
    stats = Mock()
    
    source = OpenReviewSource(cfg, http_client, rate_limiter, out_dir, stats)
    assert source.name == "openreview"
    assert source.cfg == cfg

@patch('src.scrape.sources.chemrxiv.sync_playwright')
def test_chemrxiv_list_items_mock(mock_playwright):
    """Test chemRxiv list_items with mocked Playwright."""
    # Mock Playwright objects
    mock_browser = Mock()
    mock_page = Mock()
    mock_playwright.return_value.__enter__.return_value.chromium.launch.return_value = mock_browser
    mock_browser.new_page.return_value = mock_page
    
    # Mock page elements
    mock_link = Mock()
    mock_link.get_attribute.return_value = "https://chemrxiv.org/engage/chemrxiv/article/12345"
    mock_link.query_selector.return_value = Mock()
    mock_link.query_selector.return_value.text_content.return_value = "Test Article"
    mock_page.query_selector_all.return_value = [mock_link]
    
    cfg = Mock()
    cfg.chemrxiv_listing_url = "https://chemrxiv.org/engage/chemrxiv/public-dashboard"
    cfg.chemrxiv_listing_wait_selector = "div[role='grid']"
    cfg.chemrxiv_item_link_selector = "a[href*='/engage/chemrxiv/article/']"
    cfg.user_agent = "TestBot/1.0"
    
    source = ChemRxivSource(cfg, Mock(), Mock(), Path("test"), Mock())
    
    items = list(source.list_items("2025-08-01", "2025-08-31"))
    assert len(items) == 1
    assert items[0]["url"] == "https://chemrxiv.org/engage/chemrxiv/article/12345"
    assert items[0]["title"] == "Test Article"

def test_record_model():
    """Test Record model creation."""
    record = Record(
        source="test",
        id="12345",
        title="Test Title",
        abstract="Test abstract",
        authors=["Author 1", "Author 2"]
    )
    
    assert record.source == "test"
    assert record.id == "12345"
    assert record.title == "Test Title"
    assert record.abstract == "Test abstract"
    assert record.authors == ["Author 1", "Author 2"]
    assert record.raw_paths is not None
