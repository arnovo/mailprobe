"""Email pattern generation (from MVP email_patterns)."""
from __future__ import annotations

from app.services.utils import slugify_name

# Patrones estándar (nombre + apellido)
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

# Patrones para cuando solo hay nombre (sin apellido) - emails genéricos o basados en nombre
FIRST_ONLY_PATTERNS = [
    "{first}@{domain}",
    "info@{domain}",
    "contact@{domain}",
    "contacto@{domain}",
    "hello@{domain}",
    "hola@{domain}",
]


def generate_candidates(
    first_name: str,
    last_name: str,
    domain: str,
    max_candidates: int = 15,
    enabled_pattern_indices: list[int] | None = None,
    allow_no_lastname: bool = False,
    custom_patterns: list[str] | None = None,
) -> list[str]:
    """
    Genera candidatos de email basados en patrones.
    enabled_pattern_indices: índices en COMMON_PATTERNS a usar (0..len-1). None = todos.
    allow_no_lastname: si True y no hay apellido, usa FIRST_ONLY_PATTERNS (info@, contact@, etc.).
    custom_patterns: patrones adicionales definidos por el workspace (se añaden a los estándar).
    """
    first = slugify_name(first_name)
    last = slugify_name(last_name)
    if not domain:
        return []
    domain = domain.strip().lower()
    f = first[:1] if first else ""
    li = last[:1] if last else ""  # li = last initial

    # Si no hay apellido y está permitido, usar patrones alternativos
    if not last:
        if not allow_no_lastname:
            return []  # No permitido: devolver vacío
        raw = []
        for pat in FIRST_ONLY_PATTERNS:
            if "{first}" in pat and not first:
                continue
            raw.append(pat.format(first=first, domain=domain))
        seen = set()
        out = []
        for e in raw:
            if e not in seen:
                seen.add(e)
                out.append(e)
            if len(out) >= max_candidates:
                break
        return out

    # Patrones normales con nombre y apellido
    patterns = list(COMMON_PATTERNS)
    if enabled_pattern_indices is not None:
        patterns = [COMMON_PATTERNS[i] for i in enabled_pattern_indices if 0 <= i < len(COMMON_PATTERNS)]

    # Añadir patrones personalizados del workspace (si hay)
    if custom_patterns:
        patterns = patterns + list(custom_patterns)

    raw = []
    for pat in patterns:
        if "{first}" in pat and not first:
            continue
        if "{last}" in pat and not last:
            continue
        if "{f}" in pat and not f:
            continue
        if "{l}" in pat and not li:
            continue
        try:
            raw.append(pat.format(first=first, last=last, f=f, l=li, domain=domain))
        except KeyError:
            # Patrón con placeholder desconocido, ignorar
            continue

    seen = set()
    out = []
    for e in raw:
        if e not in seen:
            seen.add(e)
            out.append(e)
        if len(out) >= max_candidates:
            break
    return out
