"""Parse prescription dose notations into a 3-slot schedule.

Examples understood:
    1+0+1, 1 + 0 + 1, 10+0+10, BD, TDS, OD, HS, সকাল ১ টি, রাতে ১ টি, ৭ দিন
"""

import re

# Normalise Bangla digits to ASCII digits.
_DIGIT_MAP = {
    ord("০"): "0", ord("১"): "1", ord("২"): "2", ord("৩"): "3", ord("৪"): "4",
    ord("৫"): "5", ord("৬"): "6", ord("৭"): "7", ord("৮"): "8", ord("৯"): "9",
}

_TRIPLET = re.compile(r"(?<!\d)(\d+)\s*\+\s*(\d+)\s*\+\s*(\d+)(?!\s*\+\s*\d)")
_FOUR_PLUS = re.compile(r"(?<!\d)\d+\s*(?:\+\s*\d+){3,}")
_DAYS = re.compile(r"(\d+)\s*(?:দিন|days?|ডোজ)", re.IGNORECASE)
_HIGH_SLOT = 3
UNREADABLE_DOSE = "Dose not understood — dose পড়া যায়নি; please confirm with the prescriber/pharmacist."
HIGH_DOSE = "Dose looks unusually high — please confirm this dose with the prescriber/pharmacist."


def normalise(text: str) -> str:
    """Return text with Bangla digits replaced and full-width plus fixed."""
    if not text:
        return ""
    return text.translate(_DIGIT_MAP).replace("＋", "+").strip()


def _parse_result(raw: str) -> dict:
    return {
        "morning": 0,
        "noon": 0,
        "night": 0,
        "times_per_day": 0,
        "days": None,
        "label": "",
        "warnings": [],
        "raw": raw,
        "ok": False,
        "needs_confirm": False,
    }


def parse(text: str) -> dict:
    """Parse a dose string into a 3-slot schedule.

    Returns a dict with keys: morning, noon, night, times_per_day,
    days (int or None), label (str), warnings (list[str]), raw (str),
    ok (bool), needs_confirm (bool).
    """
    raw = text or ""
    t = normalise(raw)
    upper = t.upper()
    result = _parse_result(raw)

    if not t.strip():
        result["warnings"].append(UNREADABLE_DOSE)
        return result

    # Reject ambiguous 4+ slot patterns (e.g. 1+1+1+1) instead of misparsing.
    if _FOUR_PLUS.search(t):
        result["label"] = _FOUR_PLUS.search(t).group(0).replace(" ", "")
        result["warnings"].append("Unusual dose format — please confirm this dose with the prescriber/pharmacist.")
        result["needs_confirm"] = True
        return result

    triplet = _TRIPLET.search(t)
    if triplet:
        result["morning"], result["noon"], result["night"] = (int(x) for x in triplet.groups())
        result["label"] = triplet.group(0).replace(" ", "")
        result["ok"] = True
    else:
        # Explicit Bangla slot words.
        slot_patterns = (
            ("morning", r"সকালে?\s*(\d+)|(\d+)\s*টি?\s*সকালে?"),
            ("noon", r"দুপুরে?\s*(\d+)|(\d+)\s*টি?\s*দুপুরে?"),
            ("night", r"রাতে?\s*(\d+)|(\d+)\s*টি?\s*রাতে?"),
        )
        found = {}
        for slot, pattern in slot_patterns:
            m = re.search(pattern, t)
            if m:
                found[slot] = int(m.group(1) or m.group(2))
        if found:
            for slot, value in found.items():
                result[slot] = value
            result["label"] = ", ".join(f"{k}={v}" for k, v in found.items())
            result["ok"] = True
        else:
            # Latin abbreviations common in Bangladeshi prescriptions.
            if re.search(r"\bQID\b", upper):
                result.update(morning=1, noon=1, night=1, label="QID (4 doses — reduce to 3 slots, confirm)", ok=True, needs_confirm=True)
                result["warnings"].append("QID written — shown as 3 slots; please confirm the real dose.")
            elif re.search(r"\bTDS\b", upper):
                result.update(morning=1, noon=1, night=1, label="TDS", ok=True)
            elif re.search(r"\bBD\b|BID\b", upper):
                result.update(morning=1, night=1, label="BD", ok=True)
            elif re.search(r"\bOD\b|\bQD\b", upper):
                result.update(morning=1, label="OD", ok=True)
            elif re.search(r"\bHS\b", upper):
                result.update(night=1, label="HS", ok=True)

    total = result["morning"] + result["noon"] + result["night"]
    result["times_per_day"] = total

    days = _DAYS.search(t)
    if days:
        result["days"] = int(days.group(1))
    elif "সপ্তাহ" in t:
        result["days"] = 14 if re.search(r"দু[ইি]", t) else 7

    high_slots = [s for s in ("morning", "noon", "night") if int(result.get(s) or 0) > _HIGH_SLOT]
    if high_slots:
        result["needs_confirm"] = True
        result["warnings"].append(HIGH_DOSE)

    if not result["ok"] or total == 0:
        result["ok"] = False
        result["needs_confirm"] = True
        result["morning"] = result["noon"] = result["night"] = 0
        result["times_per_day"] = 0
        if UNREADABLE_DOSE not in result["warnings"]:
            result["warnings"].append(UNREADABLE_DOSE)

    return result


def to_bangla_summary(parsed: dict) -> str:
    """Small helper used later by bangla.py; returns a Bangla sentence."""
    if not parsed.get("ok") or parsed.get("times_per_day", 0) == 0:
        return "মাত্রা পড়া যায়নি — দয়া করে নিশ্চিত করুন।"
    parts = []
    if parsed["morning"]:
        parts.append(f"সকালে {parsed['morning']} টি")
    if parsed["noon"]:
        parts.append(f"দুপুরে {parsed['noon']} টি")
    if parsed["night"]:
        parts.append(f"রাতে {parsed['night']} টি")
    if not parts:
        return "মাত্রা পড়া যায়নি — দয়া করে নিশ্চিত করুন।"
    text = ", ".join(parts)
    if parsed.get("needs_confirm"):
        text += " (মাত্রা নিশ্চিত করুন)"
    if parsed["days"]:
        text += f", {parsed['days']} দিন"
    return text + "।"
