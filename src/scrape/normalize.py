from pathlib import Path
from .models import Record
from .parsers.guess_sections import count_sections

def normalize_text(record: Record, clean_text: str, clean_dir: Path) -> Record:
    clean_path = clean_dir / f"{record.source}_{record.id}.txt"
    clean_path.parent.mkdir(parents=True, exist_ok=True)
    clean_path.write_text(clean_text, encoding="utf-8")
    record.clean_text_path = str(clean_path)
    record.length_chars = len(clean_text)
    record.sections = count_sections(clean_text)
    return record
