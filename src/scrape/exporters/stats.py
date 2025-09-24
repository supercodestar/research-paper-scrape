from pathlib import Path
import pandas as pd

class Stats:
    def __init__(self):
        self.rows = []
        self.errors = []
        self.run_metrics = []

    def add_record(self, rec: dict):
        self.rows.append(rec)

    def add_error(self, source: str, id_: str, stage: str, err: str):
        self.errors.append({"source": source, "id": id_, "stage": stage, "error": err})

    def add_metric(self, k: str, v):
        self.run_metrics.append({"key": k, "value": v})

    def write(self, reports_dir: Path):
        reports_dir.mkdir(parents=True, exist_ok=True)
        if self.rows:
            df = pd.DataFrame(self.rows)
            df.to_csv(reports_dir / "stats.csv", index=False)
        if self.errors:
            pd.DataFrame(self.errors).to_csv(reports_dir / "errors.csv", index=False)
        if self.run_metrics:
            pd.DataFrame(self.run_metrics).to_csv(reports_dir / "run_metrics.csv", index=False)
