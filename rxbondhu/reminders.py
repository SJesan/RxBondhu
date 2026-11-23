"""Calendar reminders (.ics) for a confirmed Bangla medicine schedule.

No new provider or API: this writes a standard iCalendar file that the user can
import into Google Calendar or any phone calendar. Times are examples and must
be confirmed by the user; the app never decides a clinical schedule.
"""

from datetime import date, datetime

from . import bangla

TIMES = {"morning": "080000", "noon": "130000", "night": "210000"}
SLOT_BN = {"morning": "সকাল", "noon": "দুপুর", "night": "রাত"}
TZID = "Asia/Dhaka"


def _esc(text) -> str:
    """Escape iCalendar TEXT values."""
    return (str(text).replace("\\", "\\\\").replace(";", "\\;")
            .replace(",", "\\,").replace("\n", "\\n"))


def _vtimezone() -> list[str]:
    # Bangladesh has no DST, so a single fixed-offset STANDARD block is enough.
    return [
        "BEGIN:VTIMEZONE", "TZID:Asia/Dhaka",
        "BEGIN:STANDARD", "DTSTART:19700101T000000",
        "TZOFFSETFROM:+0600", "TZOFFSETTO:+0600", "TZNAME:BST",
        "END:STANDARD", "END:VTIMEZONE",
    ]


def make_ics(schedule: dict, start_date: date | None = None,
             days_default: int = 7, times: dict | None = None,
             alarm_minutes: int = 5) -> dict:
    """Build an .ics file from a schedule made by pipeline.build_schedule().

    Returns {"ics": str, "events": list[dict], "warnings": list[str]}.
    """
    start = start_date or date.today()
    times = dict(TIMES if times is None else times)
    stamp = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    lines = [
        "BEGIN:VCALENDAR", "VERSION:2.0",
        "PRODID:-//RxBondhu//Medicine reminders//EN",
        "CALSCALE:GREGORIAN", "METHOD:PUBLISH",
        "X-WR-CALNAME:RxBondhu reminders",
    ] + _vtimezone()

    events, warnings = [], []
    day_prefix = start.strftime("%Y%m%d")
    for med_index, med in enumerate(schedule.get("medicines", [])):
        dose = med.get("dose") or {}
        if not dose.get("ok", True) or dose.get("needs_confirm"):
            warnings.append(
                f"{med.get('name', 'Medicine')}: dose is unreadable/unusual — calendar reminder skipped until confirmed."
            )
            continue
        days = dose.get("days") or days_default
        if not dose.get("days"):
            warnings.append(
                f"{med.get('name', 'Medicine')}: number of days missing — defaulting to {days_default} days. Please confirm with prescriber/pharmacist."
            )
        name = str(med.get("name") or "Medicine").strip()
        for slot_index, slot in enumerate(("morning", "noon", "night")):
            count = int(dose.get(slot) or 0)
            if count <= 0:
                continue  # 0 in a slot means no event; never create a fake dose.
            dtstart = f"{day_prefix}T{times[slot]}"
            summary = f"{name}: {bangla.digits(count)} টি, {SLOT_BN[slot]}"
            description = f"RxBondhu reading aid. {summary} Confirm with your pharmacist."
            uid = f"rxbondhu-{stamp}-{med_index}-{slot_index}@rxbondhu.local"
            lines += [
                "BEGIN:VEVENT",
                f"UID:{uid}",
                f"DTSTAMP:{stamp}",
                f"DTSTART;TZID={TZID}:{dtstart}",
                f"RRULE:FREQ=DAILY;COUNT={int(days)}",
                f"SUMMARY:{_esc(summary)}",
                f"DESCRIPTION:{_esc(description)}",
                "BEGIN:VALARM",
                f"TRIGGER:-PT{int(alarm_minutes)}M",
                "ACTION:DISPLAY",
                f"DESCRIPTION:{_esc(summary)}",
                "END:VALARM",
                "END:VEVENT",
            ]
            events.append({
                "medicine": name, "slot": slot, "count": count,
                "days": int(days), "start": dtstart, "uid": uid,
            })
    lines.append("END:VCALENDAR")
    return {"ics": "\r\n".join(lines) + "\r\n", "events": events, "warnings": warnings}
