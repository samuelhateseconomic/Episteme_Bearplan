"""Google access spike: can BearPlans sign in and reach Calendar and Tasks?

Opens Google's sign-in page in your browser. After you approve, Google sends you
back to a one-time page served by this script on 127.0.0.1. The sign-in tokens are
saved to the git-ignored file .secrets/google_token.json (owner-only) and never
printed. After sign-in this script only reads (GET); it creates nothing.

Output is granted permissions and counts only: no calendar names, event titles or
task titles.

Run:
    .venv/bin/python tools/google_spike.py
"""
import base64
import hashlib
import http.server
import json
import os
import secrets
import ssl
import sys
import threading
import urllib.error
import urllib.parse
import urllib.request
import webbrowser
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CLIENT_FILE = ROOT / ".secrets" / "google_oauth_client.json"
TOKEN_FILE = ROOT / ".secrets" / "google_token.json"
SCOPES = [
    "https://www.googleapis.com/auth/calendar.calendarlist.readonly",
    "https://www.googleapis.com/auth/calendar.events.readonly",
    "https://www.googleapis.com/auth/calendar.app.created",
    "https://www.googleapis.com/auth/tasks",
]


def tls_context() -> ssl.SSLContext:
    """Always verify certificates; python.org macOS builds lack a CA list, so use the system bundle."""
    context = ssl.create_default_context()
    if not context.get_ca_certs() and Path("/etc/ssl/cert.pem").is_file():
        context = ssl.create_default_context(cafile="/etc/ssl/cert.pem")
    return context


TLS = tls_context()


def client() -> dict:
    if not CLIENT_FILE.is_file():
        sys.exit(f"Missing {CLIENT_FILE}.")
    data = json.loads(CLIENT_FILE.read_text())
    if "installed" not in data:
        sys.exit("The client file is not a Desktop app client. Create one with Application type: Desktop app.")
    return data["installed"]


def post_form(url: str, fields: dict) -> dict:
    request = urllib.request.Request(url, data=urllib.parse.urlencode(fields).encode(), method="POST")
    try:
        with urllib.request.urlopen(request, context=TLS, timeout=20) as response:
            return json.load(response)
    except urllib.error.HTTPError as error:
        try:
            detail = json.load(error).get("error", "")
        except ValueError:
            detail = ""
        sys.exit(f"Google refused the sign-in exchange (HTTP {error.code} {detail}).")


def sign_in(info: dict) -> dict:
    verifier = secrets.token_urlsafe(64)
    challenge = base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest()).rstrip(b"=").decode()
    state = secrets.token_urlsafe(24)
    result: dict = {}

    class Handler(http.server.BaseHTTPRequestHandler):
        def do_GET(self):  # noqa: N802
            query = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
            if "code" not in query and "error" not in query:
                self.send_response(404); self.end_headers(); return
            result.update({key: values[0] for key, values in query.items()})
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(b"<p>BearPlans: sign-in received. You can close this tab and return to Terminal.</p>")
            threading.Thread(target=server.shutdown, daemon=True).start()

        def log_message(self, *args):  # Keep the code out of the terminal.
            pass

    server = http.server.HTTPServer(("127.0.0.1", 0), Handler)
    redirect = f"http://127.0.0.1:{server.server_port}"
    url = info["auth_uri"] + "?" + urllib.parse.urlencode({
        "client_id": info["client_id"], "redirect_uri": redirect, "response_type": "code",
        "scope": " ".join(SCOPES), "state": state, "code_challenge": challenge,
        "code_challenge_method": "S256", "access_type": "offline", "prompt": "consent"})
    print("Opening Google sign-in in your browser. If it doesn't open, paste this link into it:\n")
    print(url, "\n")
    webbrowser.open(url)
    server.serve_forever()
    server.server_close()
    if result.get("error"):
        sys.exit(f"Sign-in was not completed ({result['error']}).")
    if result.get("state") != state:
        sys.exit("Sign-in reply did not match this request; nothing was saved.")
    return post_form(info["token_uri"], {
        "code": result["code"], "client_id": info["client_id"], "client_secret": info["client_secret"],
        "redirect_uri": redirect, "grant_type": "authorization_code", "code_verifier": verifier})


def save(tokens: dict) -> None:
    TOKEN_FILE.parent.mkdir(mode=0o700, exist_ok=True)
    stored = {key: tokens[key] for key in ("refresh_token", "scope") if key in tokens}
    descriptor = os.open(TOKEN_FILE, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(descriptor, "w") as handle:
        json.dump(stored, handle)
    os.chmod(TOKEN_FILE, 0o600)


def get(access: str, url: str, **params) -> dict:
    full = url + ("?" + urllib.parse.urlencode(params) if params else "")
    request = urllib.request.Request(full, headers={"Authorization": f"Bearer {access}"})
    try:
        with urllib.request.urlopen(request, context=TLS, timeout=20) as response:
            return json.load(response)
    except urllib.error.HTTPError as error:
        try:
            reason = json.load(error)["error"]["errors"][0].get("reason", "")
        except (ValueError, KeyError, IndexError, TypeError):
            reason = ""
        return {"_error": f"HTTP {error.code} {reason}".strip()}


def main() -> None:
    info = client()
    tokens = sign_in(info)
    if "refresh_token" not in tokens:
        sys.exit("Google did not return a refresh token; nothing was saved.")
    save(tokens)
    granted = set(tokens.get("scope", "").split())
    print("Signed in. Tokens saved to .secrets/google_token.json (owner-only, git-ignored).\n")
    for scope in SCOPES:
        print(f"  {'granted' if scope in granted else 'MISSING'}  {scope.rsplit('/', 1)[-1]}")
    access = tokens["access_token"]

    calendars = get(access, "https://www.googleapis.com/calendar/v3/users/me/calendarList", maxResults=250)
    if "_error" in calendars:
        print(f"\nCalendar list: failed ({calendars['_error']}). Is the Google Calendar API enabled?")
    else:
        items = calendars.get("items", [])
        print(f"\nCalendars: {len(items)} ({sum(1 for c in items if c.get('primary'))} primary)")
        now = datetime.now(timezone.utc)
        events = get(access, "https://www.googleapis.com/calendar/v3/calendars/primary/events",
                     timeMin=now.isoformat(), timeMax=(now + timedelta(days=7)).isoformat(),
                     singleEvents="true", maxResults=250)
        print("Primary calendar, next 7 days:",
              f"failed ({events['_error']})" if "_error" in events else f"{len(events.get('items', []))} events")

    lists = get(access, "https://tasks.googleapis.com/tasks/v1/users/@me/lists", maxResults=100)
    if "_error" in lists:
        print(f"Task lists: failed ({lists['_error']}). Is the Google Tasks API enabled?")
    else:
        print(f"Task lists: {len(lists.get('items', []))}")
    print("\nNothing was created or changed in your Google account.")


if __name__ == "__main__":
    main()
