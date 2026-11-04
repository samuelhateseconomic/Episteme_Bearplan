"""Google routes: status, sign-in, disconnect, sync, followed calendars and their events.

Tokens and the client secret are never returned; only whether they exist.
Sync calls Google outside any transaction (sync route, worker thread).
"""
from __future__ import annotations

from typing import Literal

from fastapi import APIRouter, FastAPI, Request
from pydantic import BaseModel, ConfigDict, StrictStr

from backend.domain.google_reading import (
    AddedEvent, SourceCalendar, SourceEvent, add_event_task, list_calendars, list_events, read_calendars,
    refresh_events, set_followed,
)
from backend.domain.google_tasks import SyncStatus, set_paused
from backend.platform.google import NOT_CONNECTED, SCOPES

router = APIRouter(prefix="/api/google")


ConnectionStatus = Literal["not_set_up", "signed_out", "signing_in", "needs_attention", "paused", "syncing", "working"]


class GoogleState(BaseModel):
    configured: bool
    connected: bool
    sign_in_pending: bool
    sign_in_error: str | None
    missing_permissions: list[str]
    tasks: SyncStatus
    # One summary for the Settings screen, most urgent first: not_set_up (no sign-in
    # file), signed_out, signing_in, needs_attention (last sync failed or permissions
    # missing), paused, syncing, working (last sync succeeded, or none yet).
    status: ConnectionStatus
    # Only on a Disconnect reply: True Google confirmed, False Google could not be
    # asked (remove access in the Google Account), None there was no sign-in.
    revoked: bool | None = None


class SignIn(BaseModel):
    url: str


def _state(request: Request, revoked: bool | None = None) -> GoogleState:
    auth = request.app.state.google_auth
    configured, connected, pending = auth.configured(), auth.connected(), auth.sign_in_pending()
    granted = auth.granted_scopes() if connected else set()
    missing = [scope.rsplit("/", 1)[-1] for scope in SCOPES if connected and scope not in granted]
    tasks = request.app.state.google_sync.status()
    status: ConnectionStatus
    if not configured:
        status = "not_set_up"
    elif pending:
        status = "signing_in"
    elif not connected:
        status = "signed_out"
    elif tasks.last_error or missing:
        status = "needs_attention"
    elif tasks.paused_at:
        status = "paused"
    elif tasks.syncing:
        status = "syncing"
    else:
        status = "working"
    return GoogleState(
        configured=configured, connected=connected, sign_in_pending=pending, sign_in_error=auth.last_sign_in_error(),
        missing_permissions=missing, tasks=tasks, status=status, revoked=revoked)


def disconnect_google(app: FastAPI) -> bool | None:
    """Sign out of Google once no sync is running; see GoogleAuth.disconnect."""
    return app.state.google_sync.while_idle(app.state.google_auth.disconnect)


@router.get("")
def google_state(request: Request) -> GoogleState:
    return _state(request)


class Changes(BaseModel):
    version: int


@router.get("/changes")
def google_changes(request: Request) -> Changes:
    """Cheap check for the open page: refresh when this number changes."""
    return Changes(version=request.app.state.google_sync.version)


@router.post("/connect")
def google_connect(request: Request) -> SignIn:
    return SignIn(url=request.app.state.google_auth.start_sign_in())


@router.post("/disconnect")
def google_disconnect(request: Request) -> GoogleState:
    return _state(request, revoked=disconnect_google(request.app))


@router.post("/pause")
def google_pause(request: Request) -> GoogleState:
    """Stop automatic sync (kept across restarts). Waits for a sync already running, so
    once this returns no automatic sync runs until Resume; Sync now still works."""
    set_paused(request.app.state.db, True)
    request.app.state.google_sync.while_idle(lambda: None)
    return _state(request)


@router.post("/resume")
def google_resume(request: Request) -> GoogleState:
    set_paused(request.app.state.db, False)
    request.app.state.google_sync.nudge()
    return _state(request)


@router.post("/tasks/sync")
def google_tasks_sync(request: Request) -> GoogleState:
    request.app.state.google_sync.sync_now()
    return _state(request)


class FollowCalendars(BaseModel):
    model_config = ConfigDict(extra="forbid")
    calendar_ids: list[StrictStr]


class EventRef(BaseModel):
    model_config = ConfigDict(extra="forbid")
    calendar_id: StrictStr
    event_id: StrictStr


def _reader(request: Request):
    client = request.app.state.google_calendar_factory()
    if client is None:
        raise NOT_CONNECTED
    return client


@router.get("/calendars")
def google_calendars(request: Request) -> list[SourceCalendar]:
    return list_calendars(request.app.state.db)


@router.post("/calendars/refresh")
def google_calendars_refresh(request: Request) -> list[SourceCalendar]:
    read_calendars(request.app.state.db, _reader(request))
    return list_calendars(request.app.state.db)


@router.put("/calendars")
def google_calendars_follow(body: FollowCalendars, request: Request) -> list[SourceCalendar]:
    set_followed(request.app.state.db, body.calendar_ids)
    refresh_events(request.app.state.db, _reader(request))
    return list_calendars(request.app.state.db)


@router.get("/events")
def google_events(request: Request, start: str, end: str) -> list[SourceEvent]:
    return list_events(request.app.state.db, start, end)


@router.post("/events/add")
def google_event_add(body: EventRef, request: Request) -> AddedEvent:
    return add_event_task(request.app.state.db, body.calendar_id, body.event_id)
