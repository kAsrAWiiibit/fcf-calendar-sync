"""Step 1 of the pipeline: download the fixture list from the FCF API and
save it as a clean, normalized JSON file (data/matches.json).

No browser needed - the API is public and requires no cookies or auth.
See docs/api-notes.md for how the endpoint was found.

Usage:  python fetch_matches.py
"""
import json
import sys
import time
from pathlib import Path

import requests

import config

HEADERS = {"User-Agent": "fcf-calendar-sync (personal calendar feed)"}


def get_json(path: str, params: dict, retries: int = 3):
    """GET <API_BASE>/<path> and return parsed JSON, retrying on failures."""
    url = f"{config.API_BASE}/{path}"
    for attempt in range(1, retries + 1):
        try:
            resp = requests.get(url, params=params, headers=HEADERS, timeout=30)
            resp.raise_for_status()
            return resp.json()
        except (requests.RequestException, ValueError) as err:
            print(f"Attempt {attempt}/{retries} failed for {url}: {err}", file=sys.stderr)
            if attempt == retries:
                raise
            time.sleep(5 * attempt)


def fetch_competition_name() -> str:
    """Look up the competition's display name; fall back to a default on error."""
    try:
        competitions = get_json(
            "competicions",
            {"disciplinaId": config.DISCIPLINA_ID, "temporada": config.TEMPORADA_ID},
        )
        for comp in competitions:
            if comp["value"] == config.COMPETICIO_ID:
                return comp["label"]
    except Exception as err:  # the name is cosmetic, don't fail the whole run
        print(f"Could not fetch competition name: {err}", file=sys.stderr)
    return config.COMPETITION_NAME_FALLBACK


def normalize(raw_match: dict, competition: str) -> dict:
    """Turn one raw API record (Spanish field names) into a simple dict."""

    def score(value):
        return int(value) if value not in (None, "") else None

    return {
        "match_id": raw_match["CODACTA"],
        "competition": competition,
        "group": raw_match["GRUPO"],
        "matchday": int(raw_match["JORNADA"]),
        # Local kickoff time, e.g. "2026-09-26T09:00:00" (None if not scheduled yet)
        "kickoff": (raw_match["COMIENZO1"] or "").replace(" ", "T") or None,
        "home_team": raw_match["NOMBRE_CASA"],
        "away_team": raw_match["NOMBRE_FUERA"],
        "venue": raw_match["CAMPO"],
        "latitude": raw_match["LATITUD"],
        "longitude": raw_match["LONGITUD"],
        "home_goals": score(raw_match["GOLES_CASA"]),
        "away_goals": score(raw_match["GOLES_FUERA"]),
    }


def main() -> None:
    # The response is a dict keyed by matchday: {"1": [match, ...], "2": [...]}.
    # It contains the whole season in one go, so there is no pagination.
    raw = get_json("partidos", {"grupId": config.GRUP_ID})
    competition = fetch_competition_name()

    matches = [normalize(m, competition) for day in raw.values() for m in day]
    matches.sort(key=lambda m: (m["matchday"], m["kickoff"] or "", m["match_id"]))

    # Safety net: never overwrite good data with an empty result. Exiting with
    # an error also makes the GitHub Action fail instead of committing garbage.
    if not matches:
        sys.exit("API returned no matches - refusing to overwrite existing data.")

    out = Path(config.MATCHES_JSON)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(matches, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Saved {len(matches)} matches ({competition}) to {out}")


if __name__ == "__main__":
    main()
