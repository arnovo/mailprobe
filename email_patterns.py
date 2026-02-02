\
from __future__ import annotations
from dataclasses import dataclass
from typing import List
from utils import slugify_name

COMMON_PATTERNS = [
    "{first}@{domain}",
    "{last}@{domain}",
    "{first}.{last}@{domain}",
    "{f}.{last}@{domain}",
    "{f}{last}@{domain}",
    "{first}{last}@{domain}",
    "{last}.{first}@{domain}",
    "{last}{f}@{domain}",
    "{first}_{last}@{domain}",
    "{last}_{first}@{domain}",
]

@dataclass(frozen=True)
class Lead:
    first_name: str
    last_name: str
    company: str
    domain: str
    linkedin_url: str
    title: str = ""

def generate_candidates(first_name: str, last_name: str, domain: str, max_candidates: int = 15) -> List[str]:
    first = slugify_name(first_name)
    last = slugify_name(last_name)
    if not domain:
        return []
    domain = domain.strip().lower()
    f = first[:1] if first else ""
    l = last[:1] if last else ""

    raw = []
    for pat in COMMON_PATTERNS:
        if "{first}" in pat and not first:
            continue
        if "{last}" in pat and not last:
            continue
        if "{f}" in pat and not f:
            continue
        if "{l}" in pat and not l:
            continue
        raw.append(pat.format(first=first, last=last, f=f, l=l, domain=domain))

    # De-dup manteniendo orden
    seen = set()
    out = []
    for e in raw:
        if e not in seen:
            seen.add(e)
            out.append(e)
        if len(out) >= max_candidates:
            break
    return out
