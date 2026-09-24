"""Step 2 of the pipeline: build one docs/<slug>.ics per feed in config.FEEDS
from the data/matches-<grup_id>.json files.

Usage:  python make_ics.py
"""
import hashlib
import json
import re
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


class FeedError(Exception):
    """A feed that can't be built; the other feeds are still written."""


def normalize_name(name: str) -> str:
    """Upper-case, drop quote marks, collapse spaces, so the filter
    'Sant Cugat Futbol Club "B"' also matches 'SANT CUGAT FUTBOL CLUB B'."""
    return " ".join(re.sub(r"[\"'“”‘’«»]", " ", name).upper().split())


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
        needle = normalize_name(feed["team_filter"])
        teams = sorted({m["home_team"] for m in matches} | {m["away_team"] for m in matches})
        matches = [
            m for m in matches
            if needle in normalize_name(m["home_team"]) or needle in normalize_name(m["away_team"])
        ]
        if not matches:
            raise FeedError(
                f"Feed {feed['slug']!r}: team_filter {feed['team_filter']!r} matches no team. "
                "Teams in this group:\n  " + "\n  ".join(teams)
            )

    # Matches without a date yet (not scheduled) can't be put on a calendar.
    scheduled = [m for m in matches if m["kickoff"]]
    skipped = len(matches) - len(scheduled)
    if not scheduled:
        raise FeedError(f"Feed {feed['slug']!r}: none of its {len(matches)} matches has a date yet.")

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
    failed = []
    for feed in config.FEEDS:
        try:
            build_calendar(feed)
        except FeedError as err:
            print(f"ERROR: {err}", file=sys.stderr)
            failed.append(feed["slug"])
    # Exit non-zero so the workflow run is marked failed (and GitHub emails you),
    # but only after writing every feed that did work.
    if failed:
        sys.exit(f"Failed feeds: {', '.join(failed)} (the other feeds were written)")


if __name__ == "__main__":
    main()
