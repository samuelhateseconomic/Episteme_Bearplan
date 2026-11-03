"""Google routes: status, sign-in, disconnect, sync, followed calendars and their events.

Tokens and the client secret are never returned; only whether they exist.
Sync calls Google outside any transaction (sync route, worker thread).
"""
from __future__ import annotations

from fastapi import APIRouter, Request
from pydantic import BaseModel, ConfigDict, StrictStr

from backend.domain.google_reading import (
    AddedEvent, SourceCalendar, SourceEvent, add_event_task, list_calendars, list_events, read_calendars,
    refresh_events, set_followed,
)
from backend.domain.google_tasks import SyncStatus, get_status
from backend.platform.google import NOT_CONNECTED, SCOPES

router = APIRouter(prefix="/api/google")


class GoogleState(BaseModel):
    configured: bool
    connected: bool
    sign_in_pending: bool
    sign_in_error: str | None
    missing_permissions: list[str]
    tasks: SyncStatus


class SignIn(BaseModel):
    url: str


def _state(request: Request) -> GoogleState:
    auth = request.app.state.google_auth
    connected = auth.connected()
    granted = auth.granted_scopes() if connected else set()
    return GoogleState(
        configured=auth.configured(), connected=connected,
        sign_in_pending=auth.sign_in_pending(), sign_in_error=auth.last_sign_in_error(),
        missing_permissions=[scope.rsplit("/", 1)[-1] for scope in SCOPES if connected and scope not in granted],
        tasks=get_status(request.app.state.db))


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
    request.app.state.google_auth.disconnect()
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
