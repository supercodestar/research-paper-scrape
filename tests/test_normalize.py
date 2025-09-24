from scrape.models import Record
from scrape.normalize import normalize_text
from pathlib import Path

def test_normalize_text(tmp_path):
    rec = Record(source="x", id="1")
    out = normalize_text(rec, "Hello\nWorld", tmp_path)
    assert out.length_chars == 11
    assert out.sections >= 1
