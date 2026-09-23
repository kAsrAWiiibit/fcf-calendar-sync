"""Settings shared by fetch_matches.py and make_ics.py.

The IDs come from the competition page URL:
https://www.fcf.cat/ca/competicio?temporadaId=22&disciplinaId=19308233
    &competicioId=58162474&grupId=58162481
"""

TEMPORADA_ID = "22"          # season 2026-2027
DISCIPLINA_ID = "19308233"   # Futbol 11
COMPETICIO_ID = "58162474"   # competition (e.g. INFANTIL PRIMERA DIVISIÓ S13)
GRUP_ID = "58162481"         # group ("GRUP 6")

API_BASE = "https://www.fcf.cat/api/competition"

# The API gives kickoff times as plain local strings ("2026-09-26 09:00:00"),
# so we interpret them in the Catalan timezone.
TIMEZONE = "Europe/Madrid"

# The API has no match length, so every event gets this duration (minutes).
MATCH_DURATION_MINUTES = 120

# Set this to a team name (or part of one, case-insensitive) to only put that
# team's matches in the calendar, e.g. "MANRESA". None = every match in the group.
TEAM_FILTER = None

# Fallback used if the competition name can't be fetched.
COMPETITION_NAME_FALLBACK = "FCF League"

# Files
MATCHES_JSON = "data/matches.json"
CALENDAR_ICS = "docs/calendar.ics"
