from scrape.parsers.latex_parser import extract_latex_text
from pathlib import Path

def test_latex_roundtrip(tmp_path):
    f = tmp_path / "x.tex"
    f.write_text("Intro $E=mc^2$ end.", encoding="utf-8")
    txt = extract_latex_text(f)
    assert "$E=mc^2$" in txt
