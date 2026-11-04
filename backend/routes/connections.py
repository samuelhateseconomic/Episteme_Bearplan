"""Connection setup routes: save, check and remove the bCourses token and Google sign-in file.

User request (2026-11-03): set credentials from inside the app instead of editing
files. These routes are write-only: responses say only whether a credential is set,
when it was saved and the last check result; no value or part of one is ever
returned or logged. Each credential is checked before it replaces the old one, so a
bad paste keeps the previous value. The assistant has no tool that reaches them.
"""
from __future__ import annotations

import json
from collections.abc import Callable
from datetime import datetime, timezone
from pathlib import Path

from fastapi import APIRouter, Request
from pydantic import BaseModel, ConfigDict, Field, StrictStr

from backend.domain.errors import InvalidInput
from backend.platform.bcourses import TOKEN_KEY, BCoursesClient, BCoursesUnavailable
from backend.platform.google import client_file, current_client_id, parse_client_file
from backend.platform.secrets import (
    read_secret, read_status, remove_private_file, remove_secret, secrets_dir, update_status, write_private_file,
    write_secret,
)

router = APIRouter(prefix="/api/connections")

BCOURSES = "bcourses_token"
GOOGLE = "google_client"
TOKEN_MAX = 512


class CredentialStatus(BaseModel):
    set: bool
    saved_at: str | None = None
    checked_at: str | None = None
    check_ok: bool | None = None
    check_message: str | None = None


class GoogleClientStatus(CredentialStatus):
    connected: bool


class ConnectionsState(BaseModel):
    folder: str  # Where the credentials live, with the home folder shown as ~.
    bcourses: CredentialStatus
    google: GoogleClientStatus


class TokenRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    token: StrictStr = Field(max_length=TOKEN_MAX)


class ClientFileRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    client_file: StrictStr = Field(max_length=32 * 1024)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _status(name: str, is_set: bool) -> dict[str, object]:
    entry = read_status().get(name, {}) if is_set else {}
    keys = ("saved_at", "checked_at", "check_ok", "check_message")
    return {"set": is_set, **{key: entry.get(key) for key in keys}}


def _folder() -> str:
    folder, home = secrets_dir(), Path.home()
    try:
        return "~/" + str(folder.relative_to(home))
    except ValueError:
        return str(folder)


def _state(request: Request) -> ConnectionsState:
    return ConnectionsState(
        folder=_folder(),
        bcourses=CredentialStatus(**_status(BCOURSES, read_secret(TOKEN_KEY) is not None)),
        google=GoogleClientStatus(**_status(GOOGLE, current_client_id() is not None),
                                  connected=request.app.state.google_auth.connected()))


def _token_checker(request: Request) -> Callable[[str], None]:
    """Tests replace this; the real check is one read-only bCourses request."""
    return getattr(request.app.state, "bcourses_token_checker", None) or (lambda token: BCoursesClient(token).check())


def _check_token(request: Request, token: str) -> tuple[bool, str]:
    """(accepted, message). Only an answer from bCourses counts as a rejection."""
    try:
        _token_checker(request)(token)
    except BCoursesUnavailable as error:
        if error.code in ("bcourses_token_rejected", "bcourses_forbidden"):
            return False, "bCourses did not accept this token (it may be mistyped, expired or deleted)."
        raise BCoursesUnavailable(
            error.code, f"{error.message} The token was not checked, so nothing was changed.") from None
    return True, "bCourses accepted the token."


@router.get("")
def connections_state(request: Request) -> ConnectionsState:
    return _state(request)


@router.put("/bcourses")
def save_bcourses_token(body: TokenRequest, request: Request) -> ConnectionsState:
    token = body.token.strip()
    if not token or any(ch.isspace() or not ch.isprintable() for ch in token):
        raise InvalidInput("token", "Paste the token as one piece, without spaces or line breaks.")
    accepted, message = _check_token(request, token)
    if not accepted:
        raise InvalidInput("token", f"{message} The previous token was kept.")
    write_secret(TOKEN_KEY, token)
    now = _now()
    update_status(BCOURSES, {"saved_at": now, "checked_at": now, "check_ok": True, "check_message": message})
    return _state(request)


@router.post("/bcourses/check")
def check_bcourses_token(request: Request) -> ConnectionsState:
    token = read_secret(TOKEN_KEY)
    if token is None:
        raise InvalidInput("token", "No bCourses token is saved yet.")
    accepted, message = _check_token(request, token)
    update_status(BCOURSES, {"checked_at": _now(), "check_ok": accepted, "check_message": message})
    return _state(request)


@router.delete("/bcourses")
def remove_bcourses_token(request: Request) -> ConnectionsState:
    remove_secret(TOKEN_KEY)
    update_status(BCOURSES, None)
    return _state(request)


@router.put("/google")
def save_google_client(body: ClientFileRequest, request: Request) -> ConnectionsState:
    try:
        stored = parse_client_file(body.client_file)
    except ValueError as error:
        raise InvalidInput("client_file", f"{error} The previous sign-in file was kept.") from None
    if current_client_id() not in (None, stored["installed"]["client_id"]):
        # The old sign-in belongs to the old client and cannot be used with the new one.
        request.app.state.google_auth.disconnect()
    write_private_file(client_file(), json.dumps(stored, indent=2).encode("utf-8"))
    now = _now()
    update_status(GOOGLE, {"saved_at": now, "checked_at": now, "check_ok": True,
                           "check_message": "The file is a Google Desktop app sign-in file. Choose Connect Google next."})
    return _state(request)


@router.delete("/google")
def remove_google_client(request: Request) -> ConnectionsState:
    request.app.state.google_auth.disconnect()
    remove_private_file(client_file())
    update_status(GOOGLE, None)
    return _state(request)
