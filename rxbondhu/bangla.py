"""Bangla formatting for the final schedule and the spoken summary."""

from .dose_parser import to_bangla_summary

_TO_BN = str.maketrans("0123456789", "০১২৩৪৫৬৭৮৯")


def digits(text) -> str:
    """ASCII digits -> Bangla digits."""
    return str(text).translate(_TO_BN)


def schedule_rows(medicines: list[dict]) -> list[dict]:
    """Rows for a Bangla table: Real name, Generic, Morning, Noon, Night, Days."""
    rows = []
    for med in medicines or []:
        dose = med["dose"]
        rows.append({
            "medicine": med["name"],
            "generic": med.get("generic") or "—",
            "morning": digits(dose["morning"]) if dose["morning"] else "—",
            "noon": digits(dose["noon"]) if dose["noon"] else "—",
            "night": digits(dose["night"]) if dose["night"] else "—",
            "days": digits(dose["days"]) if dose.get("days") else "—",
        })
    return rows


def summary_text(schedule: dict) -> str:
    """One short Bangla paragraph for speech and the confirmation screen."""
    lines = ["আপনার ওষুধের সময়সূচি:"]
    for med in schedule.get("medicines", []):
        line = f"{med['name']} — {to_bangla_summary(med['dose'])}"
        lines.append(line)
    warnings = schedule.get("warnings") or []
    if warnings:
        lines.append("সতর্কতা:")
        for warning in warnings:
            lines.append(str(warning))
    lines.append("এটি কেবল একটি পড়ার সহায়তা। দয়া করে ডাক্তার বা ফার্মাসিস্টের সাথে নিশ্চিত করুন।")
    return "\n".join(lines)
