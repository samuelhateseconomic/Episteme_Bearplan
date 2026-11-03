"""Google connection routes: status, sign-in, disconnect and Google Tasks sync.

Tokens and the client secret are never returned; only whether they exist.
Sync calls Google outside any transaction (sync route, worker thread).
"""
from __future__ import annotations

from fastapi import APIRouter, Request
from pydantic import BaseModel

from backend.domain.google_tasks import SyncStatus, get_status
from backend.platform.google import SCOPES

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
