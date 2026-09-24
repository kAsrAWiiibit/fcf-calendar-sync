# FCF Calendar Sync

Turns a football league's fixture list from the Catalan Football Federation
([fcf.cat](https://www.fcf.cat)) into an `.ics` calendar feed that Google
Calendar can subscribe to. Everything runs for free:

```
fcf.cat API ──▶ fetch_matches.py ──▶ data/matches-<grup>.json ──▶ make_ics.py ──▶ docs/<slug>.ics
   (GitHub Actions, once a day)                                              │
                                                       GitHub Pages serves it ▼
                                             https://<username>.github.io/fcf-calendar-sync/<slug>.ics
                                                                             │
                                                                Google Calendar subscribes
```

Each entry in `FEEDS` in `config.py` becomes its own calendar with its own
subscription URL. Currently configured (season 2026-2027):

| Feed URL | Team | Competition |
|---|---|---|
| `…/calendar.ics` | SANT CUGAT FUTBOL CLUB B | INFANTIL PRIMERA DIVISIÓ S13 – GRUP 6 (70 min) |

## Files

| File | Purpose |
|---|---|
| `config.py` | Season, timezone and the list of feeds (IDs, team filter, match duration) |
| `fetch_matches.py` | Calls the FCF API, writes `data/matches-<grup_id>.json` per group |
| `make_ics.py` | Writes one `docs/<slug>.ics` per feed |
| `discover_api.py` | One-off helper (Playwright) used to find the API; only needed if FCF changes it |
| `docs/api-notes.md` | Documentation of the API endpoint |
| `.github/workflows/update-calendar.yml` | Daily automation |

## Run it locally

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

python fetch_matches.py   # -> data/matches-<grup_id>.json
python make_ics.py        # -> docs/<slug>.ics
```

## Add a team (another calendar)

Add an entry to `FEEDS` in `config.py`:

```python
{
    "slug": "cadet-a",              # -> https://<username>.github.io/fcf-calendar-sync/cadet-a.ics
    "competicio_id": "58161888",    # from the competition page URL on fcf.cat
    "grup_id": "58161907",
    "team_filter": "SANT CUGAT FUTBOL CLUB A",   # part of the name, case-insensitive; None = whole group
    "match_duration_minutes": 80,
},
```

Copy `competicioId` and `grupId` from the URL of the team's competition /
standings page on fcf.cat (see `docs/api-notes.md`). Push, and the next workflow
run publishes the new `.ics`. If `team_filter` matches no team, `make_ics.py`
stops with an error instead of publishing an empty calendar.

Each match is one event: `Home vs Away`, location = venue, as long as the feed's
`match_duration_minutes` (the API has no match length). Event UIDs are
derived from the feed slug, competition, group and match ID, so a rescheduled match is
*updated* in your calendar rather than duplicated. Scores are added to the
event description once played.

## One-time GitHub setup

1. Create a **public** repo named `fcf-calendar-sync` on GitHub (public repos
   get free Actions minutes and free Pages) and push this folder:
   ```bash
   git remote add origin https://github.com/<username>/fcf-calendar-sync.git
   git push -u origin main
   ```
2. **Enable Pages:** repo → *Settings* → *Pages* → *Build and deployment* →
   Source: *Deploy from a branch* → Branch: `main`, folder: `/docs` → *Save*.
3. **Check Actions can push:** repo → *Settings* → *Actions* → *General* →
   *Workflow permissions* → *Read and write permissions* → *Save*. (The workflow
   also requests this itself, but org/repo defaults can override it.)
4. **Run the workflow once:** *Actions* tab → *Update calendar* → *Run workflow*.
   It then runs by itself every day at 05:17 UTC and commits only when the
   fixtures actually changed.
5. After a minute or two the feed is live at
   `https://<username>.github.io/fcf-calendar-sync/calendar.ics`.
   Open that URL in a browser to check it downloads/shows calendar text.

## Subscribe in Google Calendar

Do this on a computer (the Google Calendar mobile app can't add calendars by
URL, but a calendar added on the web shows up in the app automatically):

1. Open [calendar.google.com](https://calendar.google.com).
2. In the left sidebar next to **Other calendars**, click **+**.
3. Choose **From URL**.
4. Paste `https://<username>.github.io/fcf-calendar-sync/calendar.ics`.
5. Click **Add calendar**.

### Refresh delay — please read

Google decides when to re-download subscribed calendars, and you can't force
it. It is typically **every 12–24 hours, sometimes longer**. So a change on
fcf.cat takes up to a day to reach GitHub (daily job) **plus** up to a day to
reach Google Calendar. Don't expect instant updates.

## Troubleshooting

- **Workflow fails at "Fetch matches":** FCF probably changed its API. Run
  `pip install playwright && playwright install chromium && python discover_api.py`
  and compare with `docs/api-notes.md`. The fetcher deliberately fails rather
  than overwrite the calendar with empty data.
- **"Permission denied" when pushing:** see setup step 3.
- **Scheduled runs stopped:** GitHub disables scheduled workflows after 60
  days without repo activity. The last workflow step re-enables the workflow
  on each run to prevent this (best effort); if it still happens, click
  *Enable workflow* in the Actions tab.
- **A match has no date yet:** it is left out of the calendar until FCF
  publishes a date.
