import requests
from bs4 import BeautifulSoup
import hashlib
from icalendar import Calendar, Event
from datetime import datetime, timedelta, date
from urllib.parse import urljoin

BASE_URL = "https://everyonetheatres.com/theatres/the-eric-morecambe-centre/whats-on/"
OUTPUT = "events_emc.ics"
HEADERS = {"User-Agent": "EMCCalendarFeed/1.0"}

def get_page_count():
    # Attempt to find how many pages there are. 
    # Based on URL structure /pages/1, /pages/2 etc.
    # We'll just fetch page 1 and look for pagination
    try:
        r = requests.get(f"{BASE_URL}pages/1", headers=HEADERS, timeout=10)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")
        # Logic to find max pages. 
        # This is a placeholder as the specific HTML structure is unknown.
        # Assuming typical pagination links.
        # This will need refinement once we see the page structure.
        return 5 # Assume 5 pages for now or implement logic
    except:
        return 1

def parse_events(html, source_url):
    soup = BeautifulSoup(html, "html.parser")
    events = []
    # Placeholder: logic to extract events from EMC page
    # Look for items and parse title, date, link
    # This structure must be adapted to EMC website
    return events

def event_uid(e):
    raw = f'{e["date"]}|{e["time"]}|{e["title"]}|{e["url"]}'
    return hashlib.sha256(raw.encode()).hexdigest() + "@emc-calendar"

def build_ics(events):
    cal = Calendar()
    cal.add("prodid", "-//Eric Morecambe Centre Events Feed//")
    cal.add("version", "2.0")
    cal.add("x-wr-calname", "Eric Morecambe Centre Events")
    cal.add("x-wr-timezone", "Europe/London")

    for e in events:
        uid = event_uid(e)
        start = datetime.combine(e["date"], datetime.strptime(e["time"], "%H:%M").time())
        ev = Event()
        ev.add("uid", uid)
        ev.add("dtstamp", datetime.utcnow())
        ev.add("dtstart", start)
        ev.add("dtend", start + timedelta(hours=2)) # Placeholder duration
        ev.add("summary", e["title"])
        ev.add("url", e["url"])
        cal.add_component(ev)
    return cal.to_ical()

def main():
    # Implement scraping loop for pages 1 to N
    all_events = []
    # pages = get_page_count()
    # for i in range(1, pages + 1):
    #     url = f"{BASE_URL}pages/{i}"
    #     ...
    
    # Save to events_emc.ics
    with open(OUTPUT, "wb") as f:
        f.write(build_ics(all_events))

if __name__ == "__main__":
    main()
