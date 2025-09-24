# Research Paper Scrape (Trial)
Trial scrape for **chemRxiv** + **OpenReview** (2025‑08‑01 → 2025‑08‑31).  
Deliverables: JSON/JSONL with raw+clean+metadata, CSV stats (incl. errors, timing), and source code with configs, tests, README.  
See `configs/trial.yaml` and CLI `scrape --help`.

> Brief references: deliverables, sources, and date window per client doc. (chemRxiv dashboard & OpenReview API). 

## Quickstart
```bash
python -m venv .venv && source .venv/bin/activate
pip install -e .
python -m playwright install chromium
scrape trial --config configs/trial.yaml --limit 25
