from pathlib import Path
import time
import typer
from .config import load_config
from .logging import setup_logging
from .utils.http import make_client
from .utils.rate import RateLimiter
from .exporters.jsonl_writer import JSONLWriter
from .exporters.stats import Stats
from .sources.openreview import OpenReviewSource
from .sources.chemrxiv import ChemRxivSource
from .models import Record

app = typer.Typer(help="ChemRxiv + OpenReview trial scraper")

def _load_sources(cfg, http, rl, out_dir, stats):
    sx = []
    if "chemrxiv" in cfg.sources:
        sx.append(ChemRxivSource(cfg, http, rl, out_dir, stats))
    if "openreview" in cfg.sources:
        sx.append(OpenReviewSource(cfg, http, rl, out_dir, stats))
    return sx

def _run(cfg_path: str, limit: int | None, dry_run: bool = False):
    logger = setup_logging()
    cfg = load_config(cfg_path)
    out_dir = Path(cfg.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    
    if dry_run:
        logger.info("DRY RUN MODE: No files will be downloaded or written")
    
    jsonl_path = out_dir / "jsonl" / "records.jsonl"
    writer = JSONLWriter(jsonl_path) if not dry_run else None
    stats = Stats()

    http = make_client(cfg.user_agent)
    rl = RateLimiter(
        cfg.rl_max_rpm, 
        cfg.rl_burst, 
        cfg.rl_backoff_initial_s, 
        cfg.rl_backoff_max_s
    )

    sources = _load_sources(cfg, http, rl, out_dir, stats)

    start = time.time()
    total = 0
    would_download = []
    
    for src in sources:
        logger.info(f"[{src.name}] listing items {cfg.date_from} → {cfg.date_to}")
        try:
            items = src.list_items(cfg.date_from, cfg.date_to)
            for i, it in enumerate(items, start=1):
                if limit and total >= limit:
                    break
                try:
                    if dry_run:
                        # In dry run mode, just collect what would be downloaded
                        item_info = {
                            "source": src.name,
                            "id": it.get("id", "unknown"),
                            "url": it.get("url", "unknown"),
                            "title": it.get("title", "No title")
                        }
                        would_download.append(item_info)
                        logger.info(f"Would process {src.name}:{item_info['id']} - {item_info['title']}")
                        total += 1
                    else:
                        rec: Record = src.fetch_item(it)
                        rec = src.parse_and_normalize(rec)
                        writer.append(rec)
                        stats.add_record({
                            "source": rec.source,
                            "id": rec.id,
                            "title": rec.title,
                            "length_chars": rec.length_chars,
                            "sections": rec.sections,
                            "file_type": rec.file_type,
                            "has_pdf": bool(rec.raw_paths.pdf),
                            "discussions_count": len(rec.discussions) if rec.discussions else 0
                        })
                        total += 1
                        logger.info(f"Processed {rec.source}:{rec.id} - {rec.title or 'No title'}")
                except Exception as e:
                    error_id = str(it.get("id") or it.get("url") or "unknown")
                    stats.add_error(src.name, error_id, "fetch/parse", str(e))
                    logger.error(f"Error processing {src.name}:{error_id}: {e}")
                    continue
        except Exception as e:
            stats.add_error(src.name, "-", "list_items", str(e))
    
    elapsed = time.time() - start
    stats.add_metric("elapsed_seconds", elapsed)
    stats.add_metric("records", total)
    
    if dry_run:
        logger.info(f"DRY RUN COMPLETE. Would process {total} records in {elapsed:.1f}s")
        logger.info("Items that would be processed:")
        for item in would_download:
            logger.info(f"  - {item['source']}:{item['id']} - {item['title']}")
    else:
        stats.write(out_dir / "reports")
        logger.info(f"Done. Records={total} Elapsed={elapsed:.1f}s")

@app.command()
def run(config: str = typer.Option(..., "--config", "-c", help="Path to YAML config"),
        dry_run: bool = typer.Option(False, "--dry-run", help="List what would be downloaded without fetching files")):
    _run(config, limit=None, dry_run=dry_run)

@app.command()
def trial(config: str = typer.Option(..., "--config", "-c"), 
          limit: int = 25,
          dry_run: bool = typer.Option(False, "--dry-run", help="List what would be downloaded without fetching files")):
    _run(config, limit=limit, dry_run=dry_run)
