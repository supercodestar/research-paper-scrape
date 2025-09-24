from pathlib import Path
from docx import Document

def extract_docx_text(path: Path) -> str:
    doc = Document(str(path))
    parts = []
    for p in doc.paragraphs:
        parts.append(p.text)
    return "\n".join(parts)
