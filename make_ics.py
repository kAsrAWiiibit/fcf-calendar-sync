"""Step 2 of the pipeline: build one docs/<slug>.ics per feed in config.FEEDS
from the data/matches-<grup_id>.json files.

Usage:  python make_ics.py
"""
import hashlib
import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

from ics import Calendar, Event
from ics.grammar.parse import ContentLine

import config

# A fixed timestamp for CREATED / DTSTAMP. If we used "now", the file would
# change on every run and the workflow would commit every day for nothing.
FIXED_STAMP = datetime(2026, 1, 1, tzinfo=timezone.utc)


def stable_uid(feed: dict, match_id: str) -> str:
    """Same match -> same UID forever, so calendar apps update instead of duplicate.
    The slug is included so two feeds following teams that play each other don't
    share UIDs (calendar apps can hide one of two events with the same UID)."""
    key = f"{feed['slug']}-{feed['competicio_id']}-{feed['grup_id']}-{match_id}"
    return hashlib.sha1(key.encode()).hexdigest() + "@fcf-calendar-sync"


def build_event(feed: dict, match: dict) -> Event:
    tz = ZoneInfo(config.TIMEZONE)
    start = datetime.fromisoformat(match["kickoff"]).replace(tzinfo=tz)

    event = Event()
    event.uid = stable_uid(feed, match["match_id"])
    event.name = f"{match['home_team']} vs {match['away_team']}"
    event.begin = start
    event.end = start + timedelta(minutes=feed["match_duration_minutes"])
    event.location = match["venue"]
    event.created = FIXED_STAMP
    event.last_modified = FIXED_STAMP

    lines = [
        f"{match['competition']} - {match['group']}",
        f"Matchday {match['matchday']}",
    ]
    if match["home_goals"] is not None and match["away_goals"] is not None:
        lines.append(f"Result: {match['home_goals']}-{match['away_goals']}")
    if match["latitude"] and match["longitude"]:
        lines.append(
            "Map: https://www.google.com/maps?q=" f"{match['latitude']},{match['longitude']}"
        )
    event.description = "\n".join(lines)
    return event


def build_calendar(feed: dict) -> None:
    matches = json.loads(Path(config.matches_json(feed["grup_id"])).read_text(encoding="utf-8"))

    if feed["team_filter"]:
        needle = feed["team_filter"].lower()
        matches = [
            m for m in matches
            if needle in m["home_team"].lower() or needle in m["away_team"].lower()
        ]

    # Matches without a date yet (not scheduled) can't be put on a calendar.
    scheduled = [m for m in matches if m["kickoff"]]
    skipped = len(matches) - len(scheduled)
    if not scheduled:
        sys.exit(f"Feed {feed['slug']!r}: no scheduled matches - check team_filter "
                 f"{feed['team_filter']!r} against the team names in the group.")

    calendar = Calendar(creator="-//fcf-calendar-sync//EN")
    for match in scheduled:
        calendar.events.add(build_event(feed, match))

    # Calendar name shown in Google Calendar (a non-standard but widely
    # supported header) - taken from the data, e.g. "INFANTIL PRIMERA DIVISIÓ S13 - GRUP 6".
    first = scheduled[0]
    calendar.extra.append(
        ContentLine(name="X-WR-CALNAME", value=f"{first['competition']} - {first['group']}")
    )
    calendar.extra.append(ContentLine(name="X-WR-TIMEZONE", value=config.TIMEZONE))

    out = Path(config.calendar_ics(feed["slug"]))
    out.parent.mkdir(parents=True, exist_ok=True)
    # Events are sorted by the library, so output order is deterministic.
    out.write_text(calendar.serialize(), encoding="utf-8", newline="")
    print(f"Wrote {len(scheduled)} events to {out} ({skipped} without a date skipped)")


def main() -> None:
    for feed in config.FEEDS:
        build_calendar(feed)


if __name__ == "__main__":
    main()
