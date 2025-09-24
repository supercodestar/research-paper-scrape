from pathlib import Path
from typing import Dict, Any, Iterable, List, Optional
from urllib.parse import urljoin
import httpx
from datetime import datetime
from ..models import Record, DiscussionPost, RawPaths
from ..parsers.pdf_parser import extract_pdf_text
from ..normalize import normalize_text
from ..utils.http import get_with_retry, post_with_retry
from loguru import logger

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
        Search OpenReview API for notes in the date range.
        """
        logger.info(f"Searching OpenReview from {date_from} to {date_to}")
        
        api = self.cfg.openreview_api_base.rstrip("/")
        search_url = urljoin(api, self.cfg.openreview_search_path.lstrip("/"))
        
        # Convert dates to proper format
        try:
            from_dt = datetime.fromisoformat(date_from.replace("Z", "+00:00"))
            to_dt = datetime.fromisoformat(date_to.replace("Z", "+00:00"))
        except ValueError:
            # Fallback to string format
            from_dt = f"{date_from}T00:00:00Z"
            to_dt = f"{date_to}T23:59:59Z"
        else:
            from_dt = from_dt.isoformat()
            to_dt = to_dt.isoformat()
        
        # Try different API query formats based on OpenReview API documentation
        query_formats = [
            {
                "query": "*",  # Use wildcard instead of empty string
                "limit": 1000,
                "details": "directReplies",
                "offset": 0,
                "invitation": "all",
                "sort": "cdate:desc"
            },
            {
                "query": "*",
                "limit": 1000,
                "details": "directReplies",
                "offset": 0
            },
            {
                "query": "submission",  # Search for submissions
                "limit": 1000,
                "details": "directReplies",
                "offset": 0
            }
        ]
        
        for i, payload in enumerate(query_formats):
            try:
                logger.debug(f"Trying OpenReview API format {i+1}")
                self.rl.wait()
                
                # Try POST first, then GET as fallback
                try:
                    r = post_with_retry(self.http, search_url, json_data=payload, rate_limiter=self.rl)
                except httpx.HTTPStatusError as e:
                    if e.response.status_code == 400:
                        # Try GET request instead
                        logger.debug(f"POST failed, trying GET for format {i+1}")
                        r = get_with_retry(self.http, search_url, rate_limiter=self.rl)
                    else:
                        raise
                
                data = r.json()
                
                notes = data.get("notes", [])
                if not notes:
                    logger.warning(f"No notes found with API format {i+1}")
                    continue
                    
                logger.info(f"Found {len(notes)} notes with API format {i+1}")
                
                for note in notes:
                    try:
                        # Extract metadata with fallbacks
                        note_id = note.get("id") or note.get("_id", "")
                        content = note.get("content", {})
                        
                        # Get PDF URL from various possible fields
                        pdf_url = None
                        for field in ["pdf", "pdf_url", "content.pdf", "content.pdf_url"]:
                            if "." in field:
                                parts = field.split(".")
                                pdf_url = note.get(parts[0], {}).get(parts[1])
                            else:
                                pdf_url = note.get(field)
                            if pdf_url:
                                # Ensure PDF URL is absolute
                                if pdf_url.startswith("/"):
                                    pdf_url = "https://openreview.net" + pdf_url
                                elif not pdf_url.startswith("http"):
                                    pdf_url = "https://openreview.net/pdf/" + pdf_url
                                break
                        
                        # Get authors
                        authors = content.get("authors", [])
                        if not authors:
                            authors = note.get("signatures", [])
                        
                        # Get date
                        note_date = note.get("cdate") or note.get("date")
                        if note_date and isinstance(note_date, (int, float)):
                            note_date = datetime.fromtimestamp(note_date / 1000).isoformat()
                        
                        yield {
                            "id": note_id,
                            "title": content.get("title", ""),
                            "abstract": content.get("abstract", ""),
                            "authors": authors,
                            "date": note_date,
                            "source_url": f"https://openreview.net/forum?id={note.get('forum', note_id)}",
                            "pdf_url": pdf_url,
                            "forum": note.get("forum", note_id),
                            "venue": note.get("venue", ""),
                            "subject": content.get("subject", ""),
                            "comments": content.get("comments", ""),
                        }
                        
                    except Exception as e:
                        logger.warning(f"Error processing note: {e}")
                        continue
                
                # If we got results, break out of the loop
                if notes:
                    break
                    
            except httpx.HTTPStatusError as e:
                logger.warning(f"HTTP error with API format {i+1}: {e}")
                self.rl.backoff()
                continue
            except Exception as e:
                logger.warning(f"Error with API format {i+1}: {e}")
                continue
        
        logger.info("Finished searching OpenReview")

    def _download_pdf(self, url: Optional[str], rec_id: str) -> Optional[Path]:
        if not url:
            return None
        
        logger.debug(f"Downloading PDF from {url}")
        
        try:
            r = get_with_retry(self.http, url, rate_limiter=self.rl)
            
            content_type = r.headers.get("content-type", "").lower()
            if content_type.startswith("application/pdf") or url.lower().endswith(".pdf"):
                path = self.out_dir / "raw" / "openreview" / f"{rec_id}.pdf"
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

    def _fetch_discussions(self, forum_id: str) -> List[DiscussionPost]:
        """Fetch discussion posts for a forum."""
        if not forum_id:
            return []
            
        logger.debug(f"Fetching discussions for forum {forum_id}")
        
        api = self.cfg.openreview_api_base.rstrip("/")
        discussions_url = urljoin(api, self.cfg.openreview_discussions_path.lstrip("/"))
        
        try:
            r = get_with_retry(self.http, discussions_url, rate_limiter=self.rl)
            
            data = r.json()
            notes = data.get("notes", [])
            posts = []
            
            for n in notes:
                try:
                    content = n.get("content", {})
                    signatures = n.get("signatures", [])
                    author = signatures[0] if signatures else None
                    
                    # Convert timestamp to ISO format
                    cdate = n.get("cdate")
                    if cdate and isinstance(cdate, (int, float)):
                        cdate = datetime.fromtimestamp(cdate / 1000).isoformat()
                    else:
                        cdate = str(cdate) if cdate else None
                    
                    posts.append(DiscussionPost(
                        platform="openreview",
                        thread_url=f"https://openreview.net/forum?id={forum_id}",
                        post_id=n.get("id"),
                        author=author,
                        created=cdate,
                        body=content.get("text", ""),
                        reply_to=n.get("replyto")
                    ))
                except Exception as e:
                    logger.warning(f"Error processing discussion post: {e}")
                    continue
            
            logger.debug(f"Fetched {len(posts)} discussion posts")
            return posts
            
        except httpx.HTTPStatusError as e:
            logger.warning(f"HTTP error fetching discussions for {forum_id}: {e}")
            self.rl.backoff()
            return []
        except Exception as e:
            logger.warning(f"Error fetching discussions for {forum_id}: {e}")
            return []

    def fetch_item(self, item: Dict[str, Any]) -> Record:
        rec = Record(
            source=self.name,
            id=str(item["id"]),
            title=item.get("title"),
            abstract=item.get("abstract"),
            authors=item.get("authors"),
            date=item.get("date"),
            subject=item.get("subject"),
            comments=item.get("comments"),
            source_url=item.get("source_url"),
            raw_paths=RawPaths()
        )
        
        # Download PDF if available
        pdf_path = self._download_pdf(item.get("pdf_url"), rec.id)
        if pdf_path:
            rec.raw_paths.pdf = str(pdf_path)
            rec.file_type = "pdf"
            self.rl.reset_backoff()  # Reset backoff on success
        else:
            logger.warning(f"No PDF available for {rec.id}")
        
        # Fetch discussions
        rec.discussions = self._fetch_discussions(item.get("forum"))
        
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
        # Add other types if present
        clean_dir = Path(self.cfg.output_dir) / "clean"
        return normalize_text(rec, clean_text, clean_dir)
