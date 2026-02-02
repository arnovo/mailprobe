\
from __future__ import annotations
import re
import unicodedata
from datetime import datetime, timezone

def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()

def slugify_name(s: str) -> str:
    """
    Normaliza nombres para emails:
    - lowercase
    - quita acentos
    - ñ -> n
    - elimina caracteres no alfanuméricos
    """
    if s is None:
        return ""
    s = s.strip().lower()
    s = unicodedata.normalize("NFKD", s)
    s = "".join(ch for ch in s if not unicodedata.combining(ch))
    s = s.replace("ñ", "n")
    # mantener solo [a-z0-9]
    s = re.sub(r"[^a-z0-9]+", "", s)
    return s

def safe_json_dumps(obj) -> str:
    import json
    return json.dumps(obj, ensure_ascii=False, separators=(",", ":"))

def log(msg: str) -> None:
    print(msg, flush=True)
