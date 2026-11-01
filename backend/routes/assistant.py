from __future__ import annotations

import asyncio

from fastapi import APIRouter, Request
from pydantic import BaseModel, ConfigDict, Field

from backend.domain.assistant import AssistantError
from backend.domain.assistant_actions import apply_action, undo_action

router = APIRouter(prefix="/api/assistant")


class Context(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    project_id: str | None = Field(default=None, max_length=100)
    date: str | None = Field(default=None, max_length=10)


class ChatRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    model: str = Field(min_length=1, max_length=200)
    prompt: str = Field(default="", max_length=2000)
    context: Context = Field(default_factory=Context)
    # Clarification state from the previous reply and an optional selected choice.
    pending: dict | None = None
    choice: dict | None = None


@router.get("/status")
async def status(request: Request) -> dict:
    return await request.app.state.assistant.status()


@router.post("/chat")
async def chat(body: ChatRequest, request: Request) -> dict:
    if not body.prompt.strip() and body.choice is None:
        raise AssistantError("assistant_prompt", "Enter a question.", 422)
    work = asyncio.create_task(request.app.state.assistant.ask(
        body.model, body.prompt.strip(), body.context.model_dump(), pending=body.pending, choice=body.choice))
    try:
        while not work.done():
            await asyncio.wait({work}, timeout=0.1)
            if await request.is_disconnected():
                raise AssistantError("assistant_cancelled", "The assistant request was cancelled. Your records were unchanged.", 499)
        return await work
    finally:
        if not work.done():
            work.cancel()
        # Drain cancellation so the service slot and HTTP connection are released.
        await asyncio.gather(work, return_exceptions=True)


class ApplyRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    proposal: dict
    operation_id: str = Field(max_length=36)


class UndoRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    undo_operation_id: str = Field(max_length=36)


# Applying is the user's explicit decision and never waits on the model.
@router.post("/actions/apply")
def apply(body: ApplyRequest, request: Request) -> dict:
    return apply_action(request.app.state.db, request.app.state.timer, body.proposal, body.operation_id)


@router.post("/actions/{operation_id}/undo")
def undo(operation_id: str, body: UndoRequest, request: Request) -> dict:
    return undo_action(request.app.state.db, operation_id, body.undo_operation_id)
