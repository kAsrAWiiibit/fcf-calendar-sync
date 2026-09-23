"""Discovery helper: load the FCF competition page in headless Chromium and
log every XHR/fetch request, so we can find the JSON API behind the page.

Usage:  python discover_api.py
Output: data/network_log.json (request + response preview for each call)
"""
import json
from pathlib import Path

from playwright.sync_api import sync_playwright

URL = (
    "https://www.fcf.cat/ca/competicio?temporadaId=22&disciplinaId=19308233"
    "&competicioId=58162474&grupId=58162481"
)
OUT = Path(__file__).resolve().parent / "data" / "network_log.json"


def main() -> None:
    log = []
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()

        def on_response(resp):
            req = resp.request
            if req.resource_type not in ("xhr", "fetch"):
                return
            try:
                body = resp.text()[:1500]
            except Exception:
                body = "<unreadable>"
            log.append(
                {
                    "method": req.method,
                    "url": req.url,
                    "status": resp.status,
                    "post_data": req.post_data,
                    "request_headers": req.headers,
                    "body_preview": body,
                }
            )

        page.on("response", on_response)
        page.goto(URL, wait_until="networkidle")
        page.wait_for_timeout(3000)
        page.screenshot(path=str(OUT.parent / "page.png"), full_page=True)
        browser.close()

    OUT.write_text(json.dumps(log, indent=2, ensure_ascii=False))
    for entry in log:
        print(entry["status"], entry["method"], entry["url"])


if __name__ == "__main__":
    main()
