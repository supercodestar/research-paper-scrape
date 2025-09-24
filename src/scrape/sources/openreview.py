from pathlib import Path
from typing import Dict, Any, Iterable, List, Optional
from urllib.parse import urljoin
import httpx
from ..models import Record, DiscussionPost, RawPaths
from ..parsers.pdf_parser import extract_pdf_text
from ..normalize import normalize_text

class OpenReviewSource:
    name = "openreview"

    def __init__(self, cfg, http_client: httpx.Client, rate_limiter, out_dir: Path, stats):
        self.cfg = cfg
        self.http = http_client
        self.rl = rate_limiter
        self.out_dir = out_dir
        self.stats = stats
        (self.out_dir / "raw" / "openreview").mkdir(parents=True, exist_ok=True)

    def list_items(self, date_from: str, date_to: str) -> Iterable[Dict[str, Any]]:
        """
        Generic date-range search.
        NOTE: API query shape can vary; adjust 'payload' to match current spec.
        """
        api = self.cfg.openreview_api_base.rstrip("/")
        search_url = urljoin(api, self.cfg.openreview_search_path.lstrip("/"))
        payload = {
            "term": "",  # empty term, rely on date filter
            "source": "all",
            "limit": 1000,
            "date": {"from": f"{date_from}T00:00:00Z", "to": f"{date_to}T23:59:59Z"}
        }
        self.rl.wait()
        r = self.http.post(search_url, json=payload)
        r.raise_for_status()
        data = r.json()
        for note in data.get("notes", []):
            yield {
                "id": note.get("id") or note.get("_id"),
                "title": note.get("content", {}).get("title"),
                "abstract": note.get("content", {}).get("abstract"),
                "authors": note.get("content", {}).get("authors"),
                "date": note.get("cdate"),
                "source_url": f"https://openreview.net/forum?id={note.get('forum', note.get('id'))}",
                "pdf_url": note.get("content", {}).get("pdf") or note.get("pdf"),
                "forum": note.get("forum", note.get("id")),
            }

    def _download_pdf(self, url: Optional[str], rec_id: str) -> Optional[Path]:
        if not url:
            return None
        self.rl.wait()
        r = self.http.get(url)
        if r.status_code == 200 and r.headers.get("content-type","").lower().startswith("application/pdf"):
            path = self.out_dir / "raw" / "openreview" / f"{rec_id}.pdf"
            path.write_bytes(r.content)
            return path
        return None

    def _fetch_discussions(self, forum_id: str) -> List[DiscussionPost]:
        api = self.cfg.openreview_api_base.rstrip("/")
        discussions_url = urljoin(api, self.cfg.openreview_discussions_path.lstrip("/"))
        params = {"forum": forum_id}
        self.rl.wait()
        r = self.http.get(discussions_url, params=params)
        r.raise_for_status()
        posts = []
        for n in r.json().get("notes", []):
            posts.append(DiscussionPost(
                platform="openreview",
                thread_url=f"https://openreview.net/forum?id={forum_id}",
                post_id=n.get("id"),
                author=(n.get("signatures") or [None])[0],
                created=str(n.get("cdate")),
                body=(n.get("content") or {}).get("text"),
                reply_to=n.get("replyto")
            ))
        return posts

    def fetch_item(self, item: Dict[str, Any]) -> Record:
        rec = Record(
            source=self.name,
            id=str(item["id"]),
            title=item.get("title"),
            abstract=item.get("abstract"),
            authors=item.get("authors"),
            date=None,
            source_url=item.get("source_url"),
            raw_paths=RawPaths()
        )
        pdf_path = self._download_pdf(item.get("pdf_url"), rec.id)
        if pdf_path:
            rec.raw_paths.pdf = str(pdf_path)
            rec.file_type = "pdf"
        rec.discussions = self._fetch_discussions(item.get("forum"))
        return rec

    def parse_and_normalize(self, rec: Record) -> Record:
        clean_text = ""
        if rec.raw_paths.pdf:
            txt, is_scanned = extract_pdf_text(Path(rec.raw_paths.pdf))
            clean_text = txt
        # Add other types if present
        clean_dir = Path(self.cfg.output_dir) / "clean"
        return normalize_text(rec, clean_text, clean_dir)
