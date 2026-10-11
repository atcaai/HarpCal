import sys
import subprocess
from icalendar import Calendar

def load_ics_string(raw_text):
    if not raw_text.strip():
        return {}
    cal = Calendar.from_ical(raw_text)
    events = {}
    for component in cal.walk():
        if component.name == "VEVENT":
            uid = str(component.get("uid"))
            summary = str(component.get("summary"))
            dtstart = component.get("dtstart").dt
            events[uid] = {"summary": summary, "start": dtstart}
    return events

def main():
    try:
        with open("events_emc.ics", "rb") as f:
            new_events = load_ics_string(f.read().decode("utf-8"))
    except FileNotFoundError:
        new_events = {}

    try:
        old_raw = subprocess.check_output(
            ["git", "show", "HEAD:events_emc.ics"], stderr=subprocess.DEVNULL
        ).decode("utf-8")
        old_events = load_ics_string(old_raw)
    except Exception:
        old_events = {}

    added = [e for uid, e in new_events.items() if uid not in old_events]
    removed = [e for uid, e in old_events.items() if uid not in new_events]
    
    modified = []
    for uid, e in new_events.items():
        if uid in old_events and old_events[uid] != e:
            modified.append({"old": old_events[uid], "new": e})

    summary_lines = []
    summary_lines.append("### 📅 EMC Daily Update Summary\n")

    if not added and not removed and not modified:
        summary_lines.append("No event changes detected today.")
    else:
        if added:
            summary_lines.append(f"**➕ Added Events ({len(added)}):**")
            for e in added:
                summary_lines.append(f"- **{e['summary']}** on `{e['start']}`")
            summary_lines.append("")

        if removed:
            summary_lines.append(f"**🗑️ Removed Events ({len(removed)}):**")
            for e in removed:
                summary_lines.append(f"- **{e['summary']}** on `{e['start']}`")
            summary_lines.append("")

        if modified:
            summary_lines.append(f"**✏️ Modified Events ({len(modified)}):**")
            for m in modified:
                summary_lines.append(
                    f"- **{m['new']['summary']}**: Changed from `{m['old']['start']}` to `{m['new']['start']}`"
                )
            summary_lines.append("")

    report = "\n".join(summary_lines)
    print(report)

    import os
    if "GITHUB_STEP_SUMMARY" in os.environ:
        with open(os.environ["GITHUB_STEP_SUMMARY"], "a", encoding="utf-8") as f:
            f.write(report)

if __name__ == "__main__":
    main()
