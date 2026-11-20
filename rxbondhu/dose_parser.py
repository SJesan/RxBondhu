"""Parse prescription dose notations into a 3-slot schedule.

Examples understood:
    1+0+1, 1 + 0 + 1, BD, TDS, OD, HS, সকাল ১ টি, রাতে ১ টি, ৭ দিন
"""

import re

# Normalise Bangla digits to ASCII digits.
_DIGIT_MAP = {
    ord("০"): "0", ord("১"): "1", ord("২"): "2", ord("৩"): "3", ord("৪"): "4",
    ord("৫"): "5", ord("৬"): "6", ord("৭"): "7", ord("৮"): "8", ord("৯"): "9",
}

_TRIPLET = re.compile(r"(\d)\s*\+\s*(\d)\s*\+\s*(\d)")
_DAYS = re.compile(r"(\d+)\s*(?:দিন|days?|ডোজ)", re.IGNORECASE)


def normalise(text: str) -> str:
    """Return text with Bangla digits replaced and full-width plus fixed."""
    if not text:
        return ""
    return text.translate(_DIGIT_MAP).replace("＋", "+").strip()


def parse(text: str) -> dict:
    """Parse a dose string into morning/noon/night amounts plus metadata.

    Returns a dict with keys: morning, noon, night, times_per_day,
    days (int or None), label (str), warnings (list[str]), raw (str).
    """
    raw = text or ""
    t = normalise(raw)
    upper = t.upper()

    result = {
        "morning": 0,
        "noon": 0,
        "night": 0,
        "times_per_day": 0,
        "days": None,
        "label": "",
        "warnings": [],
        "raw": raw,
    }

    triplet = _TRIPLET.search(t)
    if triplet:
        result["morning"], result["noon"], result["night"] = (int(x) for x in triplet.groups())
        result["label"] = triplet.group(0).replace(" ", "")
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
        else:
            # Latin abbreviations common in Bangladeshi prescriptions.
            if re.search(r"\bTDS\b", upper):
                result.update(morning=1, noon=1, night=1, label="TDS")
            elif re.search(r"\bBD\b", upper):
                result.update(morning=1, night=1, label="BD")
            elif re.search(r"\bQID\b", upper):
                result.update(morning=1, noon=1, night=1, label="QID (4 doses — reduce to 3 slots, confirm)")
            elif re.search(r"\bOD\b", upper):
                result.update(morning=1, label="OD")
            elif re.search(r"\bHS\b", upper):
                result.update(night=1, label="HS")

    total = result["morning"] + result["noon"] + result["night"]
    result["times_per_day"] = total

    days = _DAYS.search(t)
    if days:
        result["days"] = int(days.group(1))
    elif "সপ্তাহ" in t:
        result["days"] = 14 if re.search(r"দু[ইি]", t) else 7

    if total == 0:
        result["warnings"].append("Dose not understood — please confirm with the prescriber/pharmacist.")

    return result


def to_bangla_summary(parsed: dict) -> str:
    """Small helper used later by bangla.py; returns a Bangla sentence."""
    parts = []
    if parsed["morning"]:
        parts.append(f"সকালে {parsed['morning']} টি")
    if parsed["noon"]:
        parts.append(f"দুপুরে {parsed['noon']} টি")
    if parsed["night"]:
        parts.append(f"রাতে {parsed['night']} টি")
    if not parts:
        return "মাত্রা বোঝা যায়নি — দয়া করে নিশ্চিত করুন।"
    text = ", ".join(parts)
    if parsed["days"]:
        text += f", {parsed['days']} দিন"
    return text + "।"
