from typing import Iterable, Dict, Any, List
from pathlib import Path
from ..models import Record

class BaseSource:
    name = "base"

    def __init__(self, cfg, http_client, rate_limiter, out_dir: Path, stats):
        self.cfg = cfg
        self.http = http_client
        self.rl = rate_limiter
        self.out_dir = out_dir
        self.stats = stats
        (self.out_dir / "raw").mkdir(parents=True, exist_ok=True)

    def list_items(self, date_from: str, date_to: str) -> Iterable[Dict[str, Any]]:
        """Yield lightweight dicts with ids and URLs."""
        raise NotImplementedError

    def fetch_item(self, item: Dict[str, Any]) -> Record:
        """Download files & assemble core metadata->Record(raw_paths filled)."""
        raise NotImplementedError

    def parse_and_normalize(self, rec: Record) -> Record:
        """Open raw files, extract clean text (preserve LaTeX), run section count/length, etc."""
        raise NotImplementedError
