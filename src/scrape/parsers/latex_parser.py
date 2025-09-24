from pathlib import Path

def extract_latex_text(path: Path, preserve_math: bool = True) -> str:
    # As a baseline, return raw with minimal normalization.
    # If preserve_math=True, keep $...$ blocks intact (we are not stripping).
    return Path(path).read_text(encoding="utf-8", errors="ignore")
