"""FastAPI application: JSON API under /api and the built interface at /."""

from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path
import sqlite3

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.types import ASGIApp, Receive, Scope, Send

from backend import __version__
from backend.domain.errors import InvalidInput
from backend.domain.planning import PlacementConflict, WeekConflict
from backend.domain.timer import Clock, TimerConflict, TimerService
from backend.routes import planning, projects, tasks, timer, weeks
from backend.storage.db import Database, StorageError

LOCAL_HOSTNAMES = frozenset({"127.0.0.1", "localhost", "[::1]"})
SAFE_METHODS = frozenset({"GET", "HEAD", "OPTIONS"})

NOT_BUILT_PAGE = """<!doctype html><title>BearPlans</title>
<p>The BearPlans interface has not been built. Start the app with <code>python3 launch.py</code>,
or run <code>npm run build</code> in <code>frontend/</code>.</p>"""


def _hostname(host_header: str) -> str:
    host = host_header.strip().lower()
    if host.startswith("["):
        return host[: host.find("]") + 1]
    return host.split(":", 1)[0]


class LocalOnlyMiddleware:
    """Reject requests that did not come from this machine's own BearPlans page.

    - Host must be a loopback name, which blocks DNS-rebinding pages.
    - Mutating requests that carry an Origin must come from the same origin they
      address, so an unrelated website (or another local web app) cannot call them.
    """

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        headers = {k.decode("latin-1").lower(): v.decode("latin-1") for k, v in scope["headers"]}
        host = headers.get("host", "")
        if _hostname(host) not in LOCAL_HOSTNAMES:
            await _reject(scope, receive, send, 400, "invalid_host", "Requests must address this computer.")
            return
        if scope["method"] not in SAFE_METHODS:
            origin = headers.get("origin")
            cross_site = headers.get("sec-fetch-site") == "cross-site"
            if cross_site or (origin is not None and origin.lower() != f"http://{host.lower()}"):
                await _reject(scope, receive, send, 403, "cross_origin", "Cross-origin changes are not allowed.")
                return
        await self.app(scope, receive, send)


async def _reject(scope: Scope, receive: Receive, send: Send, status: int, code: str, message: str) -> None:
    response = JSONResponse({"error": {"code": code, "message": message}}, status_code=status)
    await response(scope, receive, send)


def create_app(db: Database, static_dir: Path | None = None, *, timer_clock: Clock | None = None) -> FastAPI:
    countdown = TimerService(db, timer_clock)

    @asynccontextmanager
    async def lifespan(_: FastAPI):
        countdown.start_monitor()
        try:
            yield
        finally:
            countdown.stop_monitor()

    app = FastAPI(
        title="BearPlans",
        version=__version__,
        docs_url="/api/docs",
        redoc_url=None,
        openapi_url="/api/openapi.json",
        lifespan=lifespan,
    )
    app.state.db = db
    app.state.timer = countdown
    app.add_middleware(LocalOnlyMiddleware)

    @app.exception_handler(TimerConflict)
    async def timer_conflict(_: Request, exc: TimerConflict) -> JSONResponse:
        return JSONResponse(
            {"error": {"code": "timer_conflict", "field": exc.field, "message": exc.message}},
            status_code=409,
        )

    @app.exception_handler(WeekConflict)
    async def week_conflict(_: Request, exc: WeekConflict) -> JSONResponse:
        return JSONResponse(
            {"error": {"code": "week_conflict", "field": exc.field, "message": exc.message}},
            status_code=409,
        )

    @app.exception_handler(PlacementConflict)
    async def placement_conflict(_: Request, exc: PlacementConflict) -> JSONResponse:
        return JSONResponse(
            {"error": {"code": "placement_conflict", "field": exc.field, "message": exc.message}},
            status_code=409,
        )

    @app.exception_handler(sqlite3.Error)
    @app.exception_handler(StorageError)
    async def storage_error(_: Request, exc: Exception) -> JSONResponse:
        return JSONResponse(
            {"error": {
                "code": "storage_unavailable",
                "message": "BearPlans could not access its saved data. Check disk space and "
                "folder permissions, close other database tools, then try again.",
            }},
            status_code=503,
        )

    @app.exception_handler(InvalidInput)
    async def invalid_input(_: Request, exc: InvalidInput) -> JSONResponse:
        return JSONResponse(
            {"error": {"code": "invalid_input", "field": exc.field, "message": exc.message}},
            status_code=422,
        )

    @app.exception_handler(RequestValidationError)
    async def malformed_request(_: Request, exc: RequestValidationError) -> JSONResponse:
        first = exc.errors()[0] if exc.errors() else {}
        location = [str(part) for part in first.get("loc", ()) if part != "body"]
        error = {"code": "invalid_input", "message": "The request was not in the expected format."}
        if location:
            error["field"] = ".".join(location)
            field = location[-1].replace("_", " ").capitalize()
            message = first.get("msg", "Check this value.")
            error["message"] = f"{field}: {message}"
        return JSONResponse({"error": error}, status_code=422)

    @app.exception_handler(StarletteHTTPException)
    async def http_error(_: Request, exc: StarletteHTTPException) -> JSONResponse:
        code = "not_found" if exc.status_code == 404 else "http_error"
        return JSONResponse(
            {"error": {"code": code, "message": str(exc.detail)}},
            status_code=exc.status_code,
            headers=exc.headers,
        )

    app.include_router(projects.router)
    app.include_router(planning.router)
    app.include_router(weeks.router)
    app.include_router(tasks.router)
    app.include_router(timer.router)

    if static_dir is not None and (static_dir / "index.html").is_file():
        app.mount("/", StaticFiles(directory=static_dir, html=True), name="interface")
    else:

        @app.get("/", include_in_schema=False)
        def interface_not_built() -> HTMLResponse:
            return HTMLResponse(NOT_BUILT_PAGE, status_code=503)

    return app
