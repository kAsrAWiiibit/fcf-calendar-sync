"""Settings shared by fetch_matches.py and make_ics.py.

Each feed's IDs come from the competition page URL, e.g.
https://www.fcf.cat/ca/competicio?temporadaId=22&disciplinaId=19308233
    &competicioId=58162474&grupId=58162481
"""

TEMPORADA_ID = "22"          # season 2026-2027
DISCIPLINA_ID = "19308233"   # Futbol 11

API_BASE = "https://www.fcf.cat/api/competition"

# The API gives kickoff times as plain local strings ("2026-09-26 09:00:00"),
# so we interpret them in the Catalan timezone.
TIMEZONE = "Europe/Madrid"

# One calendar per feed, published at https://<user>.github.io/fcf-calendar-sync/<slug>.ics
#   slug                    file name in docs/ (and part of the event UIDs)
#   competicio_id, grup_id  competition and group, from the URL above
#   team_filter             team name (or part of one, case-insensitive) to only
#                           keep that team's matches; None = every match in the group
#   match_duration_minutes  the API has no match length, so every event gets this
FEEDS = [
    {
        # "calendar" keeps the original URL .../calendar.ics working.
        "slug": "calendar",
        "competicio_id": "58162474",   # INFANTIL PRIMERA DIVISIÓ S13
        "grup_id": "58162481",         # GRUP 6
        "team_filter": "SANT CUGAT FUTBOL CLUB B",
        "match_duration_minutes": 70,
    },
]

# Fallback used if a competition name can't be fetched.
COMPETITION_NAME_FALLBACK = "FCF League"

# Files
DATA_DIR = "data"     # matches-<grup_id>.json, one per group
DOCS_DIR = "docs"     # <slug>.ics, served by GitHub Pages


def matches_json(grup_id: str) -> str:
    return f"{DATA_DIR}/matches-{grup_id}.json"


def calendar_ics(slug: str) -> str:
    return f"{DOCS_DIR}/{slug}.ics"
