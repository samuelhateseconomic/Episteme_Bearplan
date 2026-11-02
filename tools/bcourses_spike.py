"""bCourses access spike: can this student's token read courses and assignments?

Read-only: sends GET requests to bcourses.berkeley.edu only. The token is read from
the git-ignored file .secrets/bearplans.secrets.env (BCOURSES_TOKEN=...) and never
printed or written anywhere. Output is counts and field availability only, no
course names, titles or descriptions.

Run:
    .venv/bin/python tools/bcourses_spike.py
"""
import json
import os
import ssl
import stat
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path

BASE = "https://bcourses.berkeley.edu"
SECRETS = Path(__file__).resolve().parent.parent / ".secrets" / "bearplans.secrets.env"


def token() -> str:
    if not SECRETS.is_file():
        sys.exit(f"Missing {SECRETS}.")
    if SECRETS.stat().st_mode & (stat.S_IRWXG | stat.S_IRWXO):
        os.chmod(SECRETS, 0o600)  # Keep it readable by the owner only.
    for line in SECRETS.read_text().splitlines():
        key, _, value = line.partition("=")
        if key.strip() == "BCOURSES_TOKEN" and value.strip():
            return value.strip()
    sys.exit(f"BCOURSES_TOKEN is empty in {SECRETS}. Paste your token after the = sign.")


class NoRedirect(urllib.request.HTTPRedirectHandler):
    """Never follow a redirect, so the token is only ever sent to bCourses."""
    def redirect_request(self, *args, **kwargs):
        return None


def tls_context() -> ssl.SSLContext:
    """Always verify certificates. python.org builds for macOS ship without a CA list,
    so fall back to the macOS system bundle instead of turning verification off."""
    context = ssl.create_default_context()
    if not context.get_ca_certs() and Path("/etc/ssl/cert.pem").is_file():
        context = ssl.create_default_context(cafile="/etc/ssl/cert.pem")
    return context


OPENER = urllib.request.build_opener(NoRedirect, urllib.request.HTTPSHandler(context=tls_context()))


def get(secret: str, path: str, **params) -> list | dict:
    """GET every page of a bCourses API list (or one object)."""
    url = f"{BASE}/api/v1/{path}?" + urllib.parse.urlencode({"per_page": 100, **params}, doseq=True)
    results: list = []
    while url:
        if not url.startswith(BASE + "/"):
            raise RuntimeError("Refusing to send the token outside bcourses.berkeley.edu")
        # Header token only (never ?access_token=, which lands in logs); string IDs avoid
        # 64-bit integer loss in the browser.
        request = urllib.request.Request(url, headers={"Authorization": f"Bearer {secret}",
                                                       "Accept": "application/json+canvas-string-ids"})
        with OPENER.open(request, timeout=20) as response:
            body = json.load(response)
            links = response.headers.get("Link", "")
        if not isinstance(body, list):
            return body
        results += body
        url = next((part.split(";")[0].strip(" <>") for part in links.split(",") if 'rel="next"' in part), None)
    return results


def main() -> None:
    secret = token()
    try:
        me = get(secret, "users/self")
    except urllib.error.HTTPError as error:
        sys.exit(f"bCourses refused the token: HTTP {error.code}. "
                 "401 = invalid/expired/revoked token; 403 = access disabled for students.")
    print("Token accepted: yes (user id present)" if me.get("id") else "Token accepted: unexpected reply")

    courses = get(secret, "courses", enrollment_state="active", **{"include[]": ["term"]})
    print(f"Active courses: {len(courses)}")
    now = datetime.now(timezone.utc)
    window_end = now + timedelta(days=60)
    total = upcoming = undated = 0
    blocked = 0
    fields: set[str] = set()
    for course in courses:
        try:
            assignments = get(secret, f"courses/{course['id']}/assignments", order_by="due_at")
        except urllib.error.HTTPError:
            blocked += 1
            continue
        total += len(assignments)
        for item in assignments:
            fields |= {k for k in ("due_at", "html_url", "updated_at", "lock_at", "points_possible") if item.get(k)}
            if not item.get("due_at"):
                undated += 1
            elif now <= datetime.fromisoformat(item["due_at"].replace("Z", "+00:00")) <= window_end:
                upcoming += 1
    print(f"Assignments readable: {total} (courses refused: {blocked})")
    print(f"Due in the next 60 days: {upcoming}; without a due date: {undated}")
    print(f"Fields seen: {', '.join(sorted(fields)) or 'none'}")
    planner = get(secret, "planner/items", start_date=now.date().isoformat(),
                  end_date=window_end.date().isoformat())
    print(f"Planner items (next 60 days, all courses): {len(planner)}")


if __name__ == "__main__":
    main()
