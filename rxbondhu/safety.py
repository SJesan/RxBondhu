"""Safety checks that do not depend on any AI model."""


def duplicate_warning(medicines: list[dict]) -> list[str]:
    """Warn when confirmed medicines contain the same generic drug.

    Each item should have a 'generic' key and a 'name'/'brand' key.
    """
    by_generic: dict[str, list[str]] = {}
    for item in medicines or []:
        generic = str(item.get("generic") or "").strip()
        if not generic:
            continue
        name = item.get("name") or item.get("brand") or "unknown"
        by_generic.setdefault(generic.casefold(), []).append(f"{name} ({generic})")

    warnings = []
    for names in by_generic.values():
        if len(names) > 1:
            warnings.append(
                "Duplicate generic: " + " and ".join(names) + " — confirm with your pharmacist."
            )
    return warnings


def has_red(items: list[dict]) -> bool:
    """True when any review item is marked RED."""
    return any(str(item.get("colour", "")).upper() == "RED" for item in items or [])
