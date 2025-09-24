from typing import Iterable, Dict

def dedupe_latest(items: Iterable[Dict], key="id") -> Dict[str, Dict]:
    seen = {}
    for it in items:
        seen[it[key]] = it
    return seen
