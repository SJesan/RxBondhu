"""Share prepared schedule text and calendar links — never auto-send.

Google Calendar links open Google's own confirmation page. WhatsApp opens a
pre-filled message the user must press "send" on. Nothing is sent by this app.
"""

from datetime import date, datetime, timedelta
from urllib.parse import quote

from . import bangla, reminders

CALENDAR_URL = "https://calendar.google.com/calendar/render"
WHATSAPP_URL = "https://wa.me/?text="


def calendar_links(schedule: dict, start_date: date | None = None) -> list[dict]:
    """One Google Calendar link per generated event (medicine x dose slot)."""
    made = reminders.make_ics(schedule, start_date=start_date)
    links = []
    for event in made["events"]:
        start = event["start"]
        start_dt = datetime.strptime(start, "%Y%m%dT%H%M%S")
        end_dt = start_dt + timedelta(minutes=15)
        text = f"{event['medicine']} — {reminders.SLOT_BN[event['slot']]}"
        details = (
            f"RxBondhu reading aid. {bangla.digits(event['count'])} টি, "
            f"{reminders.SLOT_BN[event['slot']]}. Confirm with your pharmacist. "
            f"The .ics file repeats for {int(event['days'])} days."
        )
        query = (
            f"action=TEMPLATE&text={quote(text)}"
            f"&dates={start_dt:%Y%m%dT%H%M%S}/{end_dt:%Y%m%dT%H%M%S}"
            f"&ctz={reminders.TZID}&details={quote(details)}"
        )
        links.append({
            "medicine": event["medicine"],
            "slot": reminders.SLOT_BN[event["slot"]],
            "url": f"{CALENDAR_URL}?{query}",
        })
    return links


def calendar_all_link(schedule: dict, start_date: date | None = None) -> str:
    """One Google Calendar event containing every confirmed medicine.

    This is an overview, not separate medicine reminders: the .ics download is
    the all-at-once file with actual per-dose events. Nothing is written to any
    calendar until the user confirms on Google's own page.
    """
    start_date = start_date or date.today() + timedelta(days=1)
    start_dt = datetime.combine(start_date, datetime.min.time()) + timedelta(hours=8)
    end_dt = start_dt + timedelta(minutes=15)
    details = bangla.summary_text(schedule)[:1900]
    query = (
        "action=TEMPLATE"
        "&text=RxBondhu%20schedule%20%28confirm%20with%20prescriber%29"
        f"&dates={start_dt:%Y%m%dT%H%M%S}/{end_dt:%Y%m%dT%H%M%S}"
        f"&ctz={reminders.TZID}&details={quote(details)}"
    )
    return f"{CALENDAR_URL}?{query}"


def whatsapp_link(schedule: dict) -> str:
    """A wa.me link containing the Bangla summary as prepared text."""
    text = bangla.summary_text(schedule)[:1400]
    return WHATSAPP_URL + quote(text)
