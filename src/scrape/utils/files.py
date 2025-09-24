from pathlib import Path
import shutil

def ensure_dir(p: Path):
    p.mkdir(parents=True, exist_ok=True)

def save_bytes(path: Path, content: bytes):
    ensure_dir(path.parent)
    with open(path, "wb") as f:
        f.write(content)

def copy_file(src: Path, dst: Path):
    ensure_dir(dst.parent)
    shutil.copy2(src, dst)
