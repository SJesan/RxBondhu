"""Safety checks that do not depend on any AI model."""

import re

STRENGTH_TOKEN = re.compile(r"\b\d+(?:\.\d+)?\s*(?:mg|mcg|gm|g|ml|iu|%)?\b", re.I)


def generic_key(generic: str) -> str:
    """Canonical form for duplicate detection.

    ``Amlodipine + Atenolol`` and ``Atenolol + Amlodipine`` are the same
    combination. Strength is not part of the key: two strengths of one generic
    still need a total-daily-dose check, but this app never states an mg limit.
    """
    parts = [re.sub(r"\s+", " ", STRENGTH_TOKEN.sub(" ", p)).strip().casefold()
             for p in str(generic or "").split("+")]
    parts = [p for p in parts if p]
    return " + ".join(sorted(set(parts)))


def duplicate_warning(medicines: list[dict]) -> list[str]:
    """Warn when confirmed medicines share a generic or the same combination.

    Each item should have a 'generic' key and a 'name'/'brand' key.
    This is a non-blocking reminder — the user still confirms the schedule.
    """
    by_generic: dict[str, list[tuple[str, str]]] = {}
    for item in medicines or []:
        generic = str(item.get("generic") or "").strip()
        if not generic:
            continue
        name = item.get("name") or item.get("brand") or "unknown"
        by_generic.setdefault(generic_key(generic), []).append((str(name), generic))

    warnings = []
    for entries in by_generic.values():
        if len(entries) > 1:
            names = " and ".join(name for name, _ in entries)
            label = entries[0][1]
            warnings.append(
                f"Duplicate generic: {names} have the same generic ({label}) "
                "— check for double dose with your pharmacist."
            )
    return warnings


def has_red(items: list[dict]) -> bool:
    """True when any review item is marked RED."""
    return any(str(item.get("colour", "")).upper() == "RED" for item in items or [])


def has_unconfirmed(items: list[dict]) -> bool:
    """True for RED, YELLOW or UNVERIFIED — all need human review."""
    return any(str(item.get("colour", "")).upper() in {"RED", "YELLOW", "UNVERIFIED"}
               for item in items or [])
