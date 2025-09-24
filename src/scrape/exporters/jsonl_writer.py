import json
from pathlib import Path
from typing import Iterable
from ..models import Record

class JSONLWriter:
    def __init__(self, path: Path):
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def append(self, rec: Record):
        with open(self.path, "a", encoding="utf-8") as f:
            f.write(json.dumps(rec.model_dump(), ensure_ascii=False) + "\n")
