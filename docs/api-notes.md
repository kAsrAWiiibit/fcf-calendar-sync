# FCF API notes

How the fixture data was found and how to request it. Verified 2026-09-24.

## How it was discovered

`discover_api.py` opens the competition page in headless Chromium (Playwright),
logs every XHR/fetch call and saves them to `data/network_log.json`. Most of the
traffic is noise (Next.js `?_rsc=` link prefetches, Google Analytics, the cookie
consent banner). The real data calls all go to `https://www.fcf.cat/api/competition/...`
— the site's own Next.js API, **not** `api.fcf.cat`.

## The fixtures endpoint

```
GET https://www.fcf.cat/api/competition/partidos?grupId=58162481
```

- **Only `grupId` is needed.** No other query params, no auth, no cookies, no
  special headers. Plain `curl` / `requests` works.
- **No pagination.** One response holds the whole season (30 matchdays, 240
  matches for this group, ~160 KB).
- Response is an object keyed by matchday number (as a string), each value a
  list of matches:

```json
{ "1": [ { "CODGRUPO": "58162481", "JORNADA": "1", "CODACTA": "4210735",
           "NOMBRE_CASA": "MANRESA, C.E. B", "NOMBRE_FUERA": "NATACIO TERRASSA, C B",
           "CAMPO": "ESTADI ZEM DEL CONGOST",
           "COMIENZO1": "2026-09-26 09:00:00",
           "GOLES_CASA": null, "GOLES_FUERA": null,
           "GRUPO": "GRUP 6", "LATITUD": "41.722848", "LONGITUD": "1.812936",
           "...": "..." } ],
  "2": [ ... ] }
```

### Fields we use

| API field | Meaning | Notes |
|---|---|---|
| `CODACTA` | match id | unique per match; basis of the calendar UID |
| `JORNADA` | matchday | string |
| `COMIENZO1` | kickoff | local time, no timezone (`YYYY-MM-DD HH:MM:SS`), treated as Europe/Madrid |
| `NOMBRE_CASA` / `NOMBRE_FUERA` | home / away team | |
| `CAMPO` | venue name | |
| `LATITUD` / `LONGITUD` | venue coordinates | strings |
| `GOLES_CASA` / `GOLES_FUERA` | score | `null` until played |
| `GRUPO` | group name, e.g. `GRUP 6` | |

Other fields exist (`ESTADO`, `CERRADA`, crests, club ids, ...) but weren't
needed. There is **no match length**, so the calendar uses a fixed duration
(`match_duration_minutes` per feed in `config.py`).

`ESTADO` was `0` for every match at the time of writing, so I don't know what
values it takes for postponed/suspended matches. If a match ever gets a null
`COMIENZO1`, `make_ics.py` skips it rather than failing.

## Supporting endpoints (used by the page's selectors)

All are `GET https://www.fcf.cat/api/competition/...` returning
`[{"value": "<id>", "label": "<name>"}, ...]`:

| Endpoint | Params | Returns |
|---|---|---|
| `temporadas` | – | seasons (`22` = 2026-2027) |
| `disciplines` | – | disciplines (`19308233` = Futbol 11) |
| `competicions` | `disciplinaId`, `temporada` | competitions (`58162474` = INFANTIL PRIMERA DIVISIÓ S13) |
| `grupos` | `competicioId` | groups (`58162481` = GRUP 6) |
| `equipos` | `grupId` | teams (contains duplicate entries) |

`fetch_matches.py` uses `competicions` only to look up the competition's name.

## Finding IDs for another group

Change the dropdowns on https://www.fcf.cat/ca/competicio and copy the IDs from
the URL, or walk the endpoints above: `temporadas` → `disciplines` →
`competicions` → `grupos`. Then add a feed to `FEEDS` in `config.py`.

## Risks

This is an undocumented API. FCF can change it at any time; if the daily
GitHub Action starts failing, re-run `discover_api.py` to see what changed.
