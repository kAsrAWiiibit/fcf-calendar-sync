# FCF Calendar Sync

Turns a football league's fixture list from the Catalan Football Federation
([fcf.cat](https://www.fcf.cat)) into an `.ics` calendar feed that Google
Calendar can subscribe to. Everything runs for free:

```
fcf.cat API ──▶ fetch_matches.py ──▶ data/matches.json ──▶ make_ics.py ──▶ docs/calendar.ics
   (GitHub Actions, once a day)                                              │
                                                       GitHub Pages serves it ▼
                                             https://<username>.github.io/fcf-calendar-sync/calendar.ics
                                                                             │
                                                                Google Calendar subscribes
```

Currently configured for **INFANTIL PRIMERA DIVISIÓ S13 – GRUP 6**, season
2026-2027, filtered to the matches of **SANT CUGAT FUTBOL CLUB B** (30 matches,
70 minutes each). See `config.py`.

## Files

| File | Purpose |
|---|---|
| `config.py` | League IDs, timezone, match duration, optional team filter |
| `fetch_matches.py` | Calls the FCF API, writes `data/matches.json` |
| `make_ics.py` | Converts `data/matches.json` into `docs/calendar.ics` |
| `discover_api.py` | One-off helper (Playwright) used to find the API; only needed if FCF changes it |
| `docs/api-notes.md` | Documentation of the API endpoint |
| `.github/workflows/update-calendar.yml` | Daily automation |

## Run it locally

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

python fetch_matches.py   # -> data/matches.json
python make_ics.py        # -> docs/calendar.ics
```

## Change the league or only follow one team

Edit `config.py`:

- **Another group/competition:** update `COMPETICIO_ID` and `GRUP_ID` (and
  `DISCIPLINA_ID`/`TEMPORADA_ID` if needed). Copy them from the URL on
  fcf.cat's competition page — see `docs/api-notes.md`.
- **Only one team:** set `TEAM_FILTER = "MANRESA"` (case-insensitive, matches
  part of the name). With `None` the calendar contains all matches in the group.

Each match is one event: `Home vs Away`, location = venue, 2 hours long (the
API has no match length; change `MATCH_DURATION_MINUTES`). Event UIDs are
derived from the competition, group and match ID, so a rescheduled match is
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
