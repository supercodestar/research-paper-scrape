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

def _run(cfg_path: str, limit: int | None):
    logger = setup_logging()
    cfg = load_config(cfg_path)
    out_dir = Path(cfg.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    jsonl_path = out_dir / "jsonl" / "records.jsonl"
    writer = JSONLWriter(jsonl_path)
    stats = Stats()

    http = make_client(cfg.user_agent)
    rl = RateLimiter(cfg.rl_max_rpm, cfg.rl_burst)

    sources = _load_sources(cfg, http, rl, out_dir, stats)

    start = time.time()
    total = 0
    for src in sources:
        logger.info(f"[{src.name}] listing items {cfg.date_from} → {cfg.date_to}")
        try:
            items = src.list_items(cfg.date_from, cfg.date_to)
            for i, it in enumerate(items, start=1):
                if limit and total >= limit:
                    break
                try:
                    rec: Record = src.fetch_item(it)
                    rec = src.parse_and_normalize(rec)
                    writer.append(rec)
                    stats.add_record({
                        "source": rec.source,
                        "id": rec.id,
                        "length_chars": rec.length_chars,
                        "sections": rec.sections,
                        "file_type": rec.file_type
                    })
                    total += 1
                except Exception as e:
                    stats.add_error(src.name, str(it.get("id") or it.get("url") or ""), "fetch/parse", str(e))
                    continue
        except Exception as e:
            stats.add_error(src.name, "-", "list_items", str(e))
    elapsed = time.time() - start
    stats.add_metric("elapsed_seconds", elapsed)
    stats.add_metric("records", total)
    stats.write(out_dir / "reports")
    logger.info(f"Done. Records={total} Elapsed={elapsed:.1f}s")

@app.command()
def run(config: str = typer.Option(..., "--config", "-c", help="Path to YAML config")):
    _run(config, limit=None)

@app.command()
def trial(config: str = typer.Option(..., "--config", "-c"), limit: int = 25):
    _run(config, limit=limit)
