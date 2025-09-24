from pathlib import Path
from typing import Dict, Any, Iterable, Optional
from urllib.parse import urljoin
import httpx
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError
from datetime import datetime, timedelta
from ..models import Record, RawPaths
from ..parsers.pdf_parser import extract_pdf_text
from ..normalize import normalize_text
from ..utils.http import get_with_retry
from loguru import logger

class ChemRxivSource:
    name = "chemrxiv"

    def __init__(self, cfg, http_client: httpx.Client, rate_limiter, out_dir: Path, stats):
        self.cfg = cfg
        self.http = http_client
        self.rl = rate_limiter
        self.out_dir = out_dir
        self.stats = stats
        (self.out_dir / "raw" / "chemrxiv").mkdir(parents=True, exist_ok=True)

    def list_items(self, date_from: str, date_to: str) -> Iterable[Dict[str, Any]]:
        """
        Navigate the public dashboard, collect article links for the date window.
        Selectors are configurable in YAML; you may refine after inspecting DOM.
        """
        logger.info(f"Scraping chemRxiv from {date_from} to {date_to}")
        
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            try:
                page = browser.new_page()
                page.set_default_timeout(30000)
                
                # Set user agent
                page.set_extra_http_headers({"User-Agent": self.cfg.user_agent})
                
                page.goto(self.cfg.chemrxiv_listing_url)
                
                # Wait for page to load completely
                try:
                    page.wait_for_selector(self.cfg.chemrxiv_listing_wait_selector, timeout=30000)
                except PlaywrightTimeoutError:
                    # If the specific selector doesn't exist, wait for any content
                    logger.warning("Primary selector not found, waiting for page content")
                    page.wait_for_load_state("networkidle", timeout=30000)
                
                # Try to find and interact with date filters if they exist
                try:
                    # Look for date filter elements (these selectors may need adjustment)
                    date_from_input = page.query_selector('input[type="date"], input[placeholder*="date"], input[name*="date"]')
                    if date_from_input:
                        page.fill('input[type="date"], input[placeholder*="date"], input[name*="date"]', date_from)
                        logger.info(f"Set date filter to {date_from}")
                except Exception as e:
                    logger.debug(f"Could not set date filter: {e}")
                
                # Wait a bit for any dynamic content to load
                page.wait_for_timeout(2000)
                
                # Get all article links
                links = page.query_selector_all(self.cfg.chemrxiv_item_link_selector)
                logger.info(f"Found {len(links)} potential article links")
                
                # Debug: log some page content to understand the structure
                if len(links) == 0:
                    logger.debug("No links found, checking page content...")
                    # Try to find any links on the page
                    all_links = page.query_selector_all("a")
                    logger.debug(f"Total links on page: {len(all_links)}")
                    
                    # Log first few links for debugging
                    for i, link in enumerate(all_links[:5]):
                        href = link.get_attribute("href")
                        text = link.text_content()
                        logger.debug(f"Link {i}: {href} - {text[:50] if text else 'No text'}")
                    
                    # Try alternative selectors
                    alt_selectors = [
                        "a[href*='article']",
                        "a[href*='preprint']",
                        "a[href*='chemrxiv']",
                        ".article-link",
                        ".preprint-link",
                        "[data-testid*='article']"
                    ]
                    
                    for selector in alt_selectors:
                        alt_links = page.query_selector_all(selector)
                        if alt_links:
                            logger.info(f"Found {len(alt_links)} links with selector: {selector}")
                            break
                
                for i, a in enumerate(links):
                    try:
                        href = a.get_attribute("href")
                        if not href:
                            continue
                        url = href if href.startswith("http") else urljoin(self.cfg.chemrxiv_listing_url, href)
                        
                        # Try to extract additional metadata from the link element
                        title_elem = a.query_selector("span, div, h1, h2, h3")
                        title = title_elem.text_content().strip() if title_elem else None
                        
                        yield {
                            "url": url,
                            "title": title,
                            "index": i
                        }
                    except Exception as e:
                        logger.warning(f"Error processing link {i}: {e}")
                        continue
                        
            except PlaywrightTimeoutError as e:
                logger.error(f"Timeout while loading chemRxiv page: {e}")
            except Exception as e:
                logger.error(f"Error scraping chemRxiv: {e}")
            finally:
                browser.close()

    def _resolve_pdf(self, article_url: str) -> Optional[str]:
        """Try to resolve PDF URL using HTTP requests instead of Playwright to avoid async issues."""
        logger.debug(f"Resolving PDF for {article_url}")
        
        try:
            # Try to get the page content with HTTP request first
            r = get_with_retry(self.http, article_url, rate_limiter=self.rl)
            
            # Parse HTML to find PDF links
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(r.text, 'html.parser')
            
            # Look for PDF links
            pdf_links = soup.find_all('a', href=True)
            for link in pdf_links:
                href = link.get('href')
                if href and '.pdf' in href.lower():
                    full_url = href if href.startswith('http') else urljoin(article_url, href)
                    logger.debug(f"Found PDF link: {full_url}")
                    return full_url
            
            # Look for download buttons
            download_links = soup.find_all(['a', 'button'], string=lambda text: text and ('download' in text.lower() or 'pdf' in text.lower()))
            for link in download_links:
                href = link.get('href')
                if href and '.pdf' in href.lower():
                    full_url = href if href.startswith('http') else urljoin(article_url, href)
                    logger.debug(f"Found PDF via download button: {full_url}")
                    return full_url
            
            logger.warning(f"No PDF found for {article_url}")
            return None
            
        except Exception as e:
            logger.warning(f"Error resolving PDF for {article_url}: {e}")
            return None

    def _download_pdf(self, url: Optional[str], rec_id: str) -> Optional[Path]:
        if not url:
            return None
        
        logger.debug(f"Downloading PDF from {url}")
        self.rl.wait()
        
        try:
            r = get_with_retry(self.http, url, rate_limiter=self.rl)
            
            content_type = r.headers.get("content-type", "").lower()
            if "application/pdf" in content_type or url.lower().endswith(".pdf"):
                path = self.out_dir / "raw" / "chemrxiv" / f"{rec_id}.pdf"
                path.write_bytes(r.content)
                logger.info(f"Downloaded PDF: {path}")
                return path
            else:
                logger.warning(f"Invalid content type for PDF: {content_type}")
                return None
                
        except httpx.HTTPStatusError as e:
            logger.warning(f"HTTP error downloading PDF {url}: {e}")
            self.rl.backoff()
            return None
        except Exception as e:
            logger.warning(f"Error downloading PDF {url}: {e}")
            self.rl.backoff()
            return None

    def fetch_item(self, item: Dict[str, Any]) -> Record:
        url = item["url"]
        rec_id = url.split("/")[-1]
        
        # Extract metadata from the item if available
        title = item.get("title")
        
        rec = Record(
            source=self.name, 
            id=rec_id, 
            source_url=url, 
            title=title,
            raw_paths=RawPaths(), 
            file_type="pdf"
        )
        
        # Try to resolve and download PDF
        pdf_url = self._resolve_pdf(url)
        pdf_path = self._download_pdf(pdf_url, rec_id)
        if pdf_path:
            rec.raw_paths.pdf = str(pdf_path)
            self.rl.reset_backoff()  # Reset backoff on success
        else:
            logger.warning(f"No PDF available for {url}")
            
        return rec

    def parse_and_normalize(self, rec: Record) -> Record:
        clean_text = ""
        if rec.raw_paths.pdf:
            txt, is_scanned = extract_pdf_text(
                Path(rec.raw_paths.pdf), 
                ocr_enabled=self.cfg.ocr_enabled,
                ocr_language=self.cfg.ocr_language
            )
            clean_text = txt
        clean_dir = Path(self.cfg.output_dir) / "clean"
        return normalize_text(rec, clean_text, clean_dir)
