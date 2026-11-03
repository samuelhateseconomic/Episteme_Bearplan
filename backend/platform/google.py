"""Google sign-in and API client (Google Tasks now; Calendar in a later step).

User decisions (2026-11-02): Desktop-app OAuth client in git-ignored
`.secrets/google_oauth_client.json`; the long-lived sign-in token is saved beside it
in `.secrets/google_token.json` (owner-only). Neither is ever logged, printed or
returned by the API. Requests go only to Google's API hosts over verified TLS,
without following redirects. Called outside any database transaction.
"""

from __future__ import annotations

import base64
import hashlib
import http.server
import json
import os
import secrets
import ssl
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

from backend.platform.secrets import secrets_file

SCOPES = (
    "https://www.googleapis.com/auth/calendar.calendarlist.readonly",
    "https://www.googleapis.com/auth/calendar.events.readonly",
    "https://www.googleapis.com/auth/calendar.app.created",
    "https://www.googleapis.com/auth/tasks",
)
TASKS_API = "https://tasks.googleapis.com/tasks/v1"
CALENDAR_API = "https://www.googleapis.com/calendar/v3"
ALLOWED_HOSTS = ("https://tasks.googleapis.com/", "https://www.googleapis.com/", "https://oauth2.googleapis.com/")
TIMEOUT_SECONDS = 20
MAX_PAGES = 50
SIGN_IN_WAIT_SECONDS = 300


class GoogleUnavailable(RuntimeError):
    """Google could not be used; message is safe to show (never contains a token)."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


NOT_CONNECTED = GoogleUnavailable("google_not_connected", "Google is not connected. Choose Connect Google first.")


def client_file() -> Path:
    return secrets_file().parent / "google_oauth_client.json"


def token_file() -> Path:
    return secrets_file().parent / "google_token.json"


def _tls_context() -> ssl.SSLContext:
    context = ssl.create_default_context()
    if not context.get_ca_certs() and Path("/etc/ssl/cert.pem").is_file():
        context = ssl.create_default_context(cafile="/etc/ssl/cert.pem")
    return context


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *args: Any, **kwargs: Any) -> None:
        return None


_OPENER = urllib.request.build_opener(_NoRedirect, urllib.request.HTTPSHandler(context=_tls_context()))


def _read_json(path: Path) -> dict[str, Any] | None:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    return data if isinstance(data, dict) else None


def _oauth_client() -> dict[str, Any] | None:
    data = _read_json(client_file())
    info = data.get("installed") if data else None
    if not isinstance(info, dict) or not all(isinstance(info.get(k), str) for k in ("client_id", "client_secret", "auth_uri", "token_uri")):
        return None
    return info


def _write_token(stored: dict[str, Any]) -> None:
    path = token_file()
    path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    temporary = path.with_suffix(".tmp")
    descriptor = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
        json.dump(stored, handle)
    os.chmod(temporary, 0o600)
    os.replace(temporary, path)


def _post_form(url: str, fields: dict[str, str]) -> dict[str, Any]:
    if not url.startswith(ALLOWED_HOSTS):
        raise GoogleUnavailable("google_unexpected", "Google sign-in uses an unexpected address. Nothing was changed.")
    request = urllib.request.Request(url, data=urllib.parse.urlencode(fields).encode(), method="POST")
    try:
        with _OPENER.open(request, timeout=TIMEOUT_SECONDS) as response:
            return json.load(response)
    except urllib.error.HTTPError as error:
        try:
            reason = json.load(error).get("error", "")
        except (ValueError, AttributeError):
            reason = ""
        if reason in ("invalid_grant", "unauthorized_client", "invalid_client"):
            raise GoogleUnavailable(
                "google_signin_expired",
                "Google sign-in has expired or was removed. Choose Connect Google to sign in again.") from None
        raise GoogleUnavailable("google_unavailable", f"Google replied with an error (HTTP {error.code}). Try again later.") from None
    except (urllib.error.URLError, TimeoutError, OSError, ValueError):
        raise GoogleUnavailable("google_unreachable", "Cannot reach Google. Check your internet connection, then try again.") from None


class GoogleAuth:
    """Holds the refresh token on disk and a short-lived access token in memory."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._access: str | None = None
        self._expires = 0.0
        self._pending: dict[str, Any] | None = None

    # ---- status

    def configured(self) -> bool:
        return _oauth_client() is not None

    def connected(self) -> bool:
        data = _read_json(token_file())
        return bool(data and isinstance(data.get("refresh_token"), str))

    def granted_scopes(self) -> set[str]:
        data = _read_json(token_file()) or {}
        return set(str(data.get("scope", "")).split())

    def sign_in_pending(self) -> bool:
        with self._lock:
            return self._pending is not None and self._pending["thread"].is_alive()

    def last_sign_in_error(self) -> str | None:
        with self._lock:
            return self._pending.get("error") if self._pending else None

    # ---- sign-in (loopback redirect with PKCE, as Google requires for desktop apps)

    def start_sign_in(self) -> str:
        info = _oauth_client()
        if info is None:
            raise GoogleUnavailable(
                "google_not_configured",
                "No Google sign-in file was found. Save the Desktop app credential as .secrets/google_oauth_client.json.")
        with self._lock:
            if self._pending is not None and self._pending["thread"].is_alive():
                self._pending["server"].shutdown()
        verifier = secrets.token_urlsafe(64)
        challenge = base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest()).rstrip(b"=").decode()
        state = secrets.token_urlsafe(24)
        received: dict[str, str] = {}

        class Handler(http.server.BaseHTTPRequestHandler):
            def do_GET(self) -> None:  # noqa: N802
                query = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
                if "code" not in query and "error" not in query:
                    self.send_response(404)
                    self.end_headers()
                    return
                received.update({key: values[0] for key, values in query.items()})
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.end_headers()
                self.wfile.write(b"<p>BearPlans received the Google sign-in. You can close this tab.</p>")
                threading.Thread(target=self.server.shutdown, daemon=True).start()

            def log_message(self, *args: Any) -> None:  # Keep the code out of logs.
                pass

        server = http.server.HTTPServer(("127.0.0.1", 0), Handler)
        redirect = f"http://127.0.0.1:{server.server_port}"
        url = info["auth_uri"] + "?" + urllib.parse.urlencode({
            "client_id": info["client_id"], "redirect_uri": redirect, "response_type": "code",
            "scope": " ".join(SCOPES), "state": state, "code_challenge": challenge,
            "code_challenge_method": "S256", "access_type": "offline", "prompt": "consent"})
        pending: dict[str, Any] = {"server": server, "error": None}

        def wait() -> None:
            timer = threading.Timer(SIGN_IN_WAIT_SECONDS, server.shutdown)
            timer.daemon = True
            timer.start()
            try:
                server.serve_forever()
            finally:
                timer.cancel()
                server.server_close()
            if not received:
                pending["error"] = "Google sign-in was not finished in time. Choose Connect Google to try again."
            elif received.get("error") or received.get("state") != state or "code" not in received:
                pending["error"] = "Google sign-in was cancelled or did not match. Nothing was changed."
            else:
                try:
                    tokens = _post_form(info["token_uri"], {
                        "code": received["code"], "client_id": info["client_id"],
                        "client_secret": info["client_secret"], "redirect_uri": redirect,
                        "grant_type": "authorization_code", "code_verifier": verifier})
                    if not isinstance(tokens.get("refresh_token"), str):
                        raise GoogleUnavailable("google_unexpected", "Google did not return a sign-in token.")
                    _write_token({"refresh_token": tokens["refresh_token"], "scope": tokens.get("scope", "")})
                    with self._lock:
                        self._access = tokens.get("access_token")
                        self._expires = time.monotonic() + float(tokens.get("expires_in", 0)) - 60
                except GoogleUnavailable as error:
                    pending["error"] = error.message

        thread = threading.Thread(target=wait, daemon=True, name="bearplans-google-signin")
        pending["thread"] = thread
        with self._lock:
            self._pending = pending
        thread.start()
        return url

    def disconnect(self) -> None:
        with self._lock:
            self._access = None
            self._expires = 0.0
        try:
            token_file().unlink()
        except FileNotFoundError:
            pass

    # ---- access tokens

    def access_token(self) -> str:
        with self._lock:
            if self._access and time.monotonic() < self._expires:
                return self._access
        info = _oauth_client()
        data = _read_json(token_file())
        refresh = data.get("refresh_token") if data else None
        if info is None or not isinstance(refresh, str):
            raise NOT_CONNECTED
        tokens = _post_form(info["token_uri"], {
            "client_id": info["client_id"], "client_secret": info["client_secret"],
            "refresh_token": refresh, "grant_type": "refresh_token"})
        access = tokens.get("access_token")
        if not isinstance(access, str):
            raise GoogleUnavailable("google_unexpected", "Google sent an unexpected sign-in reply.")
        with self._lock:
            self._access = access
            self._expires = time.monotonic() + float(tokens.get("expires_in", 0)) - 60
        return access

    def forget_access(self) -> None:
        with self._lock:
            self._access = None


class _GoogleApi:
    """Authorized JSON calls to Google's API hosts. Every method may raise GoogleUnavailable."""

    def __init__(self, auth: GoogleAuth) -> None:
        self._auth = auth

    def _call(self, method: str, url: str, params: dict[str, Any] | None = None,
              body: dict[str, Any] | None = None, *, retry: bool = True) -> Any:
        if not url.startswith(ALLOWED_HOSTS):
            raise GoogleUnavailable("google_unexpected", "Google sent an unexpected link. Nothing was changed.")
        full = url + ("?" + urllib.parse.urlencode(params) if params else "")
        headers = {"Authorization": f"Bearer {self._auth.access_token()}"}
        data = None
        if body is not None:
            data = json.dumps(body).encode()
            headers["Content-Type"] = "application/json"
        request = urllib.request.Request(full, data=data, method=method, headers=headers)
        try:
            with _OPENER.open(request, timeout=TIMEOUT_SECONDS) as response:
                raw = response.read()
                return json.loads(raw) if raw else None
        except urllib.error.HTTPError as error:
            if error.code == 401 and retry:
                self._auth.forget_access()
                return self._call(method, url, params, body, retry=False)
            if error.code == 410:
                raise GoogleUnavailable("google_gone", "That item was already removed from Google.") from None
            if error.code == 404:
                raise GoogleUnavailable("google_not_found", "That item no longer exists in Google.") from None
            if error.code == 403:
                raise GoogleUnavailable(
                    "google_forbidden",
                    "Google refused the request. Check that the Google Calendar and Google Tasks APIs are enabled and that "
                    "BearPlans was given permission, then Connect Google again.") from None
            if error.code == 429:
                raise GoogleUnavailable("google_busy", "Google asked BearPlans to slow down. It will try again shortly.") from None
            raise GoogleUnavailable("google_unavailable", f"Google replied with an error (HTTP {error.code}). Try again later.") from None
        except (urllib.error.URLError, TimeoutError, OSError, ValueError):
            raise GoogleUnavailable("google_unreachable", "Cannot reach Google. Check your internet connection, then try again.") from None

    def _pages(self, url: str, params: dict[str, Any]) -> list[dict[str, Any]]:
        items: list[dict[str, Any]] = []
        token: str | None = None
        for _ in range(MAX_PAGES):
            page = self._call("GET", url, {**params, **({"pageToken": token} if token else {})}) or {}
            items += [item for item in page.get("items", []) if isinstance(item, dict)]
            token = page.get("nextPageToken")
            if not token:
                break
        return items



class GoogleTasksClient(_GoogleApi):
    """The Google Tasks calls BearPlans uses."""

    def lists(self) -> list[dict[str, Any]]:
        return self._pages(f"{TASKS_API}/users/@me/lists", {"maxResults": 100})

    def insert_list(self, title: str) -> dict[str, Any]:
        return self._call("POST", f"{TASKS_API}/users/@me/lists", body={"title": title})

    def rename_list(self, list_id: str, title: str) -> dict[str, Any]:
        return self._call("PATCH", f"{TASKS_API}/users/@me/lists/{_q(list_id)}", body={"title": title})

    def tasks(self, list_id: str) -> list[dict[str, Any]]:
        return self._pages(f"{TASKS_API}/lists/{_q(list_id)}/tasks", {
            "maxResults": 100, "showCompleted": "true", "showHidden": "true", "showDeleted": "true"})

    def insert_task(self, list_id: str, body: dict[str, Any], parent: str | None) -> dict[str, Any]:
        return self._call("POST", f"{TASKS_API}/lists/{_q(list_id)}/tasks", {"parent": parent} if parent else None, body)

    def patch_task(self, list_id: str, task_id: str, body: dict[str, Any]) -> dict[str, Any]:
        return self._call("PATCH", f"{TASKS_API}/lists/{_q(list_id)}/tasks/{_q(task_id)}", body=body)

    def move_task(self, list_id: str, task_id: str, parent: str | None) -> dict[str, Any]:
        return self._call("POST", f"{TASKS_API}/lists/{_q(list_id)}/tasks/{_q(task_id)}/move", {"parent": parent} if parent else None)

    def delete_task(self, list_id: str, task_id: str) -> None:
        try:
            self._call("DELETE", f"{TASKS_API}/lists/{_q(list_id)}/tasks/{_q(task_id)}")
        except GoogleUnavailable as error:
            if error.code != "google_not_found":
                raise


class GoogleCalendarClient(_GoogleApi):
    """The Google Calendar calls BearPlans uses. Writes go only to the calendar it created."""

    def calendar_exists(self, calendar_id: str) -> bool:
        try:
            self._call("GET", f"{CALENDAR_API}/calendars/{_q(calendar_id)}")
        except GoogleUnavailable as error:
            if error.code == "google_not_found":
                return False
            raise
        return True

    def insert_calendar(self, summary: str) -> dict[str, Any]:
        return self._call("POST", f"{CALENDAR_API}/calendars", body={"summary": summary})

    def events(self, calendar_id: str) -> list[dict[str, Any]]:
        return self._pages(f"{CALENDAR_API}/calendars/{_q(calendar_id)}/events", {"maxResults": 2500, "showDeleted": "true"})

    def insert_event(self, calendar_id: str, body: dict[str, Any]) -> dict[str, Any]:
        return self._call("POST", f"{CALENDAR_API}/calendars/{_q(calendar_id)}/events", body=body)

    def patch_event(self, calendar_id: str, event_id: str, body: dict[str, Any]) -> dict[str, Any]:
        return self._call("PATCH", f"{CALENDAR_API}/calendars/{_q(calendar_id)}/events/{_q(event_id)}", body=body)

    def delete_event(self, calendar_id: str, event_id: str) -> None:
        try:
            self._call("DELETE", f"{CALENDAR_API}/calendars/{_q(calendar_id)}/events/{_q(event_id)}")
        except GoogleUnavailable as error:
            if error.code not in ("google_not_found", "google_gone"):
                raise


def _q(value: str) -> str:
    return urllib.parse.quote(value, safe="")
