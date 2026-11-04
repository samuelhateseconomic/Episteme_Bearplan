"""Read-only bCourses (Berkeley's Canvas) API client.

Only GET requests, only to https://bcourses.berkeley.edu, with the token in the
Authorization header (never the URL). Redirects are not followed, so the token
cannot be sent elsewhere. Certificates are always verified. Called outside any
database transaction.
"""

from __future__ import annotations

import json
import ssl
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

from backend.platform.secrets import read_secret

BASE = "https://bcourses.berkeley.edu"
TOKEN_KEY = "BCOURSES_TOKEN"
TIMEOUT_SECONDS = 20
MAX_PAGES = 50


class BCoursesUnavailable(RuntimeError):
    """bCourses could not be read; message is safe to show the user (never contains the token)."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *args: Any, **kwargs: Any) -> None:
        return None


def _tls_context() -> ssl.SSLContext:
    """Always verify. python.org macOS builds ship without a CA list; use the system bundle then."""
    context = ssl.create_default_context()
    if not context.get_ca_certs() and Path("/etc/ssl/cert.pem").is_file():
        context = ssl.create_default_context(cafile="/etc/ssl/cert.pem")
    return context


class BCoursesClient:
    def __init__(self, token: str | None = None) -> None:
        self._token = token
        self._opener = urllib.request.build_opener(_NoRedirect, urllib.request.HTTPSHandler(context=_tls_context()))

    def _secret(self) -> str:
        token = self._token or read_secret(TOKEN_KEY)
        if not token:
            raise BCoursesUnavailable(
                "bcourses_not_configured",
                "No bCourses token is set. Paste a token after BCOURSES_TOKEN= in bearplans.secrets.env "
                "in the secrets folder inside the BearPlans data folder (on a Mac, "
                "~/Library/Application Support/BearPlans/secrets/), save it, then choose Refresh.")
        return token

    def _get(self, path: str, pages: int = MAX_PAGES, **params: Any) -> list[dict[str, Any]]:
        token = self._secret()
        url: str | None = f"{BASE}/api/v1/{path}?" + urllib.parse.urlencode({"per_page": 100, **params}, doseq=True)
        results: list[dict[str, Any]] = []
        for _ in range(pages):
            if url is None:
                break
            if not url.startswith(BASE + "/"):
                raise BCoursesUnavailable("bcourses_unexpected", "bCourses sent an unexpected link. Nothing was changed.")
            request = urllib.request.Request(url, headers={
                "Authorization": f"Bearer {token}", "Accept": "application/json+canvas-string-ids"})
            try:
                with self._opener.open(request, timeout=TIMEOUT_SECONDS) as response:
                    body = json.load(response)
                    links = response.headers.get("Link", "")
            except urllib.error.HTTPError as error:
                if error.code == 401:
                    raise BCoursesUnavailable(
                        "bcourses_token_rejected",
                        "bCourses did not accept the token (it may be wrong, expired or deleted). "
                        "Create a new one in bCourses and paste it into bearplans.secrets.env in the BearPlans secrets folder.") from None
                if error.code == 403:
                    raise BCoursesUnavailable("bcourses_forbidden", "bCourses refused access to this information.") from None
                raise BCoursesUnavailable("bcourses_unavailable", f"bCourses replied with an error (HTTP {error.code}). Try again later.") from None
            except (urllib.error.URLError, TimeoutError, OSError, ValueError):
                raise BCoursesUnavailable(
                    "bcourses_unreachable", "Cannot reach bCourses. Check your internet connection, then try again.") from None
            if not isinstance(body, list):
                raise BCoursesUnavailable("bcourses_unexpected", "bCourses sent an unexpected reply. Nothing was changed.")
            results += [item for item in body if isinstance(item, dict)]
            url = next((part.split(";")[0].strip(" <>") for part in links.split(",") if 'rel="next"' in part), None)
        return results

    def check(self) -> None:
        """One small read (a single course) to confirm bCourses accepts the token."""
        self._get("courses", pages=1, per_page=1)

    def courses(self) -> list[dict[str, Any]]:
        return self._get("courses", enrollment_state="active", **{"include[]": ["term"]})

    def assignments(self, course_id: str) -> list[dict[str, Any]]:
        return self._get(f"courses/{urllib.parse.quote(course_id, safe='')}/assignments", order_by="due_at")
