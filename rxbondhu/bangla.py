"""Bangla formatting for the final schedule and the spoken summary."""

from html import escape

from .dose_parser import to_bangla_summary

_TO_BN = str.maketrans("0123456789", "০১২৩৪৫৬৭৮৯")
MISSING_DAYS = "দিন লেখা নেই — নিশ্চিত করুন"


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
            "days": digits(dose["days"]) if dose.get("days") else MISSING_DAYS,
        })
    return rows


def _slot(value) -> str:
    """Big tick + big Bangla digit for a dose slot; em dash when it is zero."""
    try:
        count = int(value or 0)
    except (TypeError, ValueError):
        count = 0
    if count <= 0:
        return "—"
    return f"<span class='rx-tick'>✓</span> <span class='rx-count'>{digits(count)}</span>"


def schedule_table_html(medicines: list[dict]) -> str:
    """Bangla-first table: Bangla labels with small English, ticks and digits."""
    headers = [
        ("ওষুধ", "Brand"), ("জেনেরিক", "Generic"), ("ডোজ", "Dose"),
        ("সকাল", "Morning"), ("দুপুর", "Noon"), ("রাত", "Night"),
        ("দিন", "Days"),
    ]
    head = "".join(
        f"<th>{escape(bn)}<small>{escape(en)}</small></th>" for bn, en in headers
    )
    body = []
    for med in medicines or []:
        dose = med["dose"]
        days = dose.get("days")
        cells = [
            escape(str(med.get("name") or "—")),
            escape(str(med.get("generic") or "—")),
            escape(to_bangla_summary(dose)),
            _slot(dose.get("morning")), _slot(dose.get("noon")),
            _slot(dose.get("night")),
            f"<span class='rx-count'>{digits(days)}</span>" if days
            else f"<span class='rx-missing'>{MISSING_DAYS}</span>",
        ]
        body.append("<tr>" + "".join(f"<td>{cell}</td>" for cell in cells) + "</tr>")
    return (
        "<table class='rx-schedule-table'><thead><tr>"
        + head + "</tr></thead><tbody>" + "".join(body) + "</tbody></table>"
    )


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
