import calendar
import hashlib
import re
from datetime import date, datetime, timedelta
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup
from icalendar import Calendar, Event

BASE = "https://www.harpenden.gov.uk/events-and-markets/calendar" 
#"https://www.harpenden.gov.uk/events-and-markets/calendar"
OUTPUT = "events_htc.ics"
MONTHS_AHEAD = 14
EXCLUDE = ("citizens advice", "planning committee")

HEADERS = {"User-Agent": "HarpendenCalendarFeed/1.0"}

def month_urls():
    today = date.today()
    y, m = today.year, today.month
    for i in range(MONTHS_AHEAD):
        mm = m + i
        yy = y + (mm - 1) // 12
        mm = (mm - 1) % 12 + 1
        yield f"{BASE}?date={yy:04d}-{mm:02d}-01"

def excluded(title):
    t = re.sub(r"\s+", " ", title).strip().lower()
    return any(x in t for x in EXCLUDE)

def parse_month(html, source_url):
    soup = BeautifulSoup(html, "html.parser")
    events = []

    # The page has a calendar, with modals for each day's events.
    # Looking at sample_page.html, events are inside div.modal-body
    for modal in soup.find_all("div", class_="modal-body"):
        # Find the title in the modal-header to get the date
        header = modal.find_previous("div", class_="modal-header")
        if not header:
            continue
        
        date_text = header.find("h5", class_="modal-title").get_text(strip=True)
        # Parse date from "Events for 27th September 2026"
        m = re.search(r"(\d{1,2})(?:st|nd|rd|th)\s+([A-Za-z]+)\s+(\d{4})", date_text)
        if not m:
            continue
        day, month_name, year = m.groups()
        event_date = datetime.strptime(f"{day} {month_name} {year}", "%d %B %Y").date()

        for a in modal.find_all("a", class_="eventLink", href=True):
            # The event div within the link has the time and title
            event_div = a.find("div", class_="calendarEvent")
            if not event_div:
                continue
            
            title_text = event_div.get_text(strip=True)
            # e.g., "10:00: Farmers' Market"
            tm = re.match(r"^(\d{1,2}:\d{2}):\s*(.*)$", title_text)
            if not tm:
                continue
            
            time_str, event_title = tm.groups()
            if excluded(event_title):
                continue
                
            events.append({
                "date": event_date,
                "time": time_str,
                "title": event_title.strip(),
                "url": urljoin(source_url, a["href"]),
            })

    return events

def event_uid(e):
    raw = f'{e["date"]}|{e["time"]}|{e["title"]}|{e["url"]}'
    return hashlib.sha256(raw.encode()).hexdigest() + "@harpenden-calendar"

def build_ics(events):
    cal = Calendar()
    cal.add("prodid", "-//Harpenden Town Council Events Feed//")
    cal.add("version", "2.0")
    cal.add("calscale", "GREGORIAN")
    cal.add("x-wr-calname", "Harpenden Town Council Events")
    cal.add("x-wr-timezone", "Europe/London")

    seen = set()
    for e in events:
        uid = event_uid(e)
        if uid in seen:
            continue
        seen.add(uid)

        start = datetime.fromisoformat(
            f'{e["date"].isoformat()}T{e["time"]}:00'
        )
        ev = Event()
        ev.add("uid", uid)
        ev.add("dtstamp", datetime.utcnow())
        ev.add("dtstart", start)
        ev.add("dtend", start + timedelta(hours=1))
        ev.add("summary", e["title"])
        ev.add("url", e["url"])
        ev.add("description", f"Source: {e['url']}")
        cal.add_component(ev)

    return cal.to_ical()

def main():
    session = requests.Session()
    session.headers.update(HEADERS)
    all_events = []

    for url in month_urls():
        print("Fetching", url)
        r = session.get(url, timeout=30)
        r.raise_for_status()
        all_events.extend(parse_month(r.text, url))

    all_events.sort(key=lambda x: (x["date"], x["time"], x["title"].lower()))

    with open(OUTPUT, "wb") as f:
        f.write(build_ics(all_events))

    print(f"Wrote {len(all_events)} events to {OUTPUT}")

if __name__ == "__main__":
    main()
