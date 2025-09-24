from pathlib import Path
from typing import Dict, Any, Iterable, Optional
from urllib.parse import urljoin
import httpx
from playwright.sync_api import sync_playwright
from ..models import Record, RawPaths
from ..parsers.pdf_parser import extract_pdf_text
from ..normalize import normalize_text

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
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            try:
                page = browser.new_page()
                page.set_default_timeout(30000)
                page.goto(self.cfg.chemrxiv_listing_url)
                page.wait_for_selector(self.cfg.chemrxiv_listing_wait_selector)
                # TODO: add date filtering via UI or use an API call if exposed.
                links = page.query_selector_all(self.cfg.chemrxiv_item_link_selector)
                for a in links:
                    href = a.get_attribute("href")
                    if not href:
                        continue
                    url = href if href.startswith("http") else urljoin(self.cfg.chemrxiv_listing_url, href)
                    yield {"url": url}
            finally:
                browser.close()

    def _resolve_pdf(self, article_url: str) -> Optional[str]:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            try:
                page = browser.new_page()
                page.goto(article_url)
                # Try a direct PDF link
                el = page.query_selector(self.cfg.chemrxiv_pdf_link_selector)
                if el:
                    href = el.get_attribute("href")
                    if href:
                        return href if href.startswith("http") else urljoin(article_url, href)
                return None
            finally:
                browser.close()

    def _download_pdf(self, url: Optional[str], rec_id: str) -> Optional[Path]:
        if not url:
            return None
        self.rl.wait()
        r = self.http.get(url)
        if r.status_code == 200 and "application/pdf" in r.headers.get("content-type","").lower():
            path = self.out_dir / "raw" / "chemrxiv" / f"{rec_id}.pdf"
            path.write_bytes(r.content)
            return path
        return None

    def fetch_item(self, item: Dict[str, Any]) -> Record:
        url = item["url"]
        rec_id = url.split("/")[-1]
        rec = Record(source=self.name, id=rec_id, source_url=url, raw_paths=RawPaths(), file_type="pdf")
        pdf_url = self._resolve_pdf(url)
        pdf_path = self._download_pdf(pdf_url, rec_id)
        if pdf_path:
            rec.raw_paths.pdf = str(pdf_path)
        return rec

    def parse_and_normalize(self, rec: Record) -> Record:
        clean_text = ""
        if rec.raw_paths.pdf:
            txt, is_scanned = extract_pdf_text(Path(rec.raw_paths.pdf))
            clean_text = txt
        clean_dir = Path(self.cfg.output_dir) / "clean"
        return normalize_text(rec, clean_text, clean_dir)
