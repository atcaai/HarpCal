import hashlib
import re
from datetime import date, datetime, timedelta
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup
from icalendar import Calendar, Event

BASE = "https://everyonetheatres.com/whats-on/?search=&theatre%5B%5D=the-eric-morecambe-centre&d=&ppp=-1"
OUTPUT = "events_emc.ics"
PAGES_TO_SCRAPE = 1
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"}

def get_events_from_page(page_num):
    url = f"{BASE}"
    print(f"Fetching {url}")
    try:
        r = requests.get(url, headers=HEADERS, timeout=30)
        if r.status_code == 404:
            return []
        r.raise_for_status()
    except Exception as e:
        print(f"Error fetching {url}: {e}")
        return []
    
    soup = BeautifulSoup(r.text, "html.parser")
    events = []
    
    # Each event is in a div with class "col event-card-container"
    for container in soup.find_all("div", class_="event-card-container"):
        # Date
        time_tag = container.find("time")
        if not time_tag:
            continue
        date_str = time_tag.get("datetime") # YYYY-MM-DD
        event_date = datetime.strptime(date_str, "%Y-%m-%d").date()
        
        # Title and URL
        title_a = container.find("a", href=re.compile(r"/whats-on/"))
        if not title_a:
            continue
            
        title = title_a.get("title")
        if title and title.startswith("Find out more about "):
            title = title[len("Find out more about "):]
        event_url = title_a.get("href")
        
        # Time - sometimes hidden in title or location or just not there
        # Defaulting to 19:30
        time_str = "19:30" 
        
        events.append({
            "date": event_date,
            "time": time_str,
            "title": title.strip(),
            "url": event_url,
        })
    return events

def event_uid(e):
    raw = f'{e["date"]}|{e["time"]}|{e["title"]}|{e["url"]}'
    return hashlib.sha256(raw.encode()).hexdigest() + "@emc-calendar"

def build_ics(events):
    cal = Calendar()
    cal.add("prodid", "-//Eric Morecambe Centre Events//")
    cal.add("version", "2.0")
    cal.add("calscale", "GREGORIAN")
    cal.add("x-wr-calname", "Harps - Eric Morecambe Centre Events")
    cal.add("x-wr-timezone", "Europe/London")

    seen = set()
    for e in events:
        uid = event_uid(e)
        if uid in seen:
            continue
        seen.add(uid)

        start = datetime.combine(e["date"], datetime.strptime(e["time"], "%H:%M").time())
        ev = Event()
        ev.add("uid", uid)
        ev.add("dtstamp", datetime.utcnow())
        ev.add("dtstart", start)
        ev.add("dtend", start + timedelta(hours=2))
        ev.add("summary", e["title"])
        ev.add("url", e["url"])
        ev.add("description", f"Source: {e['url']}")
        cal.add_component(ev)

    return cal.to_ical()

def load_existing_events(filepath):
    try:
        with open(filepath, "rb") as f:
            cal = Calendar.from_ical(f.read())
            events = {}
            for component in cal.walk("VEVENT"):
                uid = str(component.get("uid"))
                start_dt = component.get("dtstart").dt
                event_date = start_dt.date() if isinstance(start_dt, datetime) else start_dt
                
                events[uid] = {
                    "date": event_date,
                    "time": start_dt.strftime("%H:%M") if isinstance(start_dt, datetime) else "00:00",
                    "title": str(component.get("summary")),
                    "url": str(component.get("url")),
                }
            return events
    except FileNotFoundError:
        return {}

def main():
    scraped_events = []
    for i in range(1, PAGES_TO_SCRAPE + 1):
        page_events = get_events_from_page(i)
        if not page_events:
            break
        scraped_events.extend(page_events)

    existing_events = load_existing_events(OUTPUT)
    today = date.today()
    
    new_future_events = {event_uid(e): e for e in scraped_events if e["date"] >= today}

    final_events_list = [e for uid, e in existing_events.items() if e["date"] < today]
    final_events_list.extend(new_future_events.values())
    final_events_list.sort(key=lambda x: (x["date"], x["time"], x["title"].lower()))

    with open(OUTPUT, "wb") as f:
        f.write(build_ics(final_events_list))

    print(f"Wrote {len(final_events_list)} total events to {OUTPUT}")

if __name__ == "__main__":
    main()
