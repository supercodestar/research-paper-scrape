import re

HEADING_RE = re.compile(r"^\s*(\d+(\.\d+)*)\s+[A-Z][^\n]{0,80}$")

def count_sections(txt: str) -> int:
    # Heuristic: numbered headings and some all-caps/Title-ish lines
    lines = txt.splitlines()
    count = 0
    for line in lines:
        if HEADING_RE.match(line) or line.strip().isupper():
            count += 1
    return max(1, count)
