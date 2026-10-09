import requests
from scraper import parse_month

# 1. Save HTML to local disk once
URL = "https://www.harpenden.gov.uk/events-and-markets/calendar"
file_path = "sample_page.html"

try:
    with open(file_path, "r", encoding="utf-8") as f:
        html = f.read()
except FileNotFoundError:
    print("Fetching page live for local cache...")
    r = requests.get(URL, headers={"User-Agent": "HarpendenCalendarFeed/1.0"})
    html = r.text
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(html)

# 2. Run parser against cached HTML
events = parse_month(html, URL)
print(f"Extracted {len(events)} events:")
for e in events[:5]:  # Preview first 5
    print(e)