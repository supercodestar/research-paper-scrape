from pydantic_settings import BaseSettings
from pydantic import Field
from typing import List, Optional
import os
from ruamel.yaml import YAML

yaml = YAML(typ="safe")

class Settings(BaseSettings):
    run_name: str = "trial-aug-2025"
    output_dir: str = "data"
    date_from: str = "2025-08-01"
    date_to: str = "2025-08-31"
    user_agent: str = "ResearchScrapeBot/0.1 (+contact: team@example.com)"
    sources: List[str] = ["chemrxiv", "openreview"]

    # Rate limits
    rl_max_rpm: int = 12
    rl_burst: int = 6
    rl_backoff_initial_s: float = 1.0
    rl_backoff_max_s: float = 30.0

    # Concurrency
    conc_downloads: int = 4
    conc_parsing: int = 4

    # OCR / Math
    ocr_enabled: bool = True
    ocr_language: str = "eng"
    math_preserve_latex: bool = True
    mathpix_enabled: bool = False
    mathpix_app_id: Optional[str] = None
    mathpix_app_key: Optional[str] = None

    # Source-specific
    chemrxiv_listing_url: str = "https://chemrxiv.org/engage/chemrxiv/public-dashboard"
    chemrxiv_listing_wait_selector: str = "div[role='grid']"
    chemrxiv_item_link_selector: str = "a[href*='/engage/chemrxiv/article/']"
    chemrxiv_pdf_link_selector: str = "a[href$='.pdf']"

    openreview_api_base: str = "https://api.openreview.net"
    openreview_search_path: str = "/notes/search"
    openreview_discussions_path: str = "/notes"

    class Config:
        env_file = ".env"
        extra = "ignore"

def load_config(path: str) -> Settings:
    with open(path, "r", encoding="utf-8") as f:
        data = yaml.load(f)
    # Map YAML keys to Settings fields
    s = Settings(
        run_name=data.get("run_name", "trial-aug-2025"),
        output_dir=data.get("output_dir", "data"),
        date_from=data.get("date_from", "2025-08-01"),
        date_to=data.get("date_to", "2025-08-31"),
        user_agent=data.get("user_agent", "ResearchScrapeBot/0.1 (+contact: team@example.com)"),
        sources=data.get("sources", ["chemrxiv","openreview"]),
        rl_max_rpm=data.get("rate_limit", {}).get("max_requests_per_minute", 12),
        rl_burst=data.get("rate_limit", {}).get("burst", 6),
        rl_backoff_initial_s=data.get("rate_limit", {}).get("backoff_initial_s", 1.0),
        rl_backoff_max_s=data.get("rate_limit", {}).get("backoff_max_s", 30.0),
        conc_downloads=data.get("concurrency", {}).get("downloads", 4),
        conc_parsing=data.get("concurrency", {}).get("parsing", 4),
        ocr_enabled=data.get("OCR", {}).get("enabled", True),
        ocr_language=data.get("OCR", {}).get("language", "eng"),
        math_preserve_latex=data.get("math", {}).get("preserve_latex", True),
        mathpix_enabled=data.get("math", {}).get("mathpix", {}).get("enabled", False),
        mathpix_app_id=os.getenv("MATHPIX_APP_ID"),
        mathpix_app_key=os.getenv("MATHPIX_APP_KEY"),
        chemrxiv_listing_url=data.get("chemrxiv", {}).get("listing_url", "https://chemrxiv.org/engage/chemrxiv/public-dashboard"),
        chemrxiv_listing_wait_selector=data.get("chemrxiv", {}).get("listing_wait_selector", "div[role='grid']"),
        chemrxiv_item_link_selector=data.get("chemrxiv", {}).get("item_link_selector", "a[href*='/engage/chemrxiv/article/']"),
        chemrxiv_pdf_link_selector=data.get("chemrxiv", {}).get("pdf_link_selector", "a[href$='.pdf']"),
        openreview_api_base=data.get("openreview", {}).get("api_base", "https://api.openreview.net"),
        openreview_search_path=data.get("openreview", {}).get("search_path", "/notes/search"),
        openreview_discussions_path=data.get("openreview", {}).get("discussions_path", "/notes"),
    )
    return s
