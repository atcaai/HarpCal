# Harpenden Related calendar feeds

This repository creates an automatically updated `.ics` feed from various calendar websites.


### Harpenden Town Calendar
(scraper_htc.py)
Excluded:
- Citizens Advice
- Planning Committee

### Eric Morecambe Centre
(scraper_emc.py)
No exclusions

## Setup

1. Create a public GitHub repository.
2. Copy these files into it.
3. Run the GitHub Action once with **Actions -> Update Harpenden calendar -> Run workflow**.
4. Enable GitHub Pages for the repository, using the `main` branch and `/ (root)`.
5. The feed will be:

   `https://YOUR-USERNAME.github.io/YOUR-REPOSITORY/events_[XXX].ics`

6. In Google Calendar, use **Other calendars -> From URL** and paste that URL.

The GitHub Action refreshes the feed as defined in /.github/workflows/update_[XXX].yml

## Notes

Harpenden Town Council
The council page is server-rendered. The scraper reads the dated event sections
and follows the individual event links. The feed deliberately gives each event
a stable UID so repeated runs do not create duplicates in subscribing clients.
