from __future__ import annotations

import asyncio

from fastapi import APIRouter, Request
from pydantic import BaseModel, ConfigDict, Field

from backend.domain.assistant import AssistantError

router = APIRouter(prefix="/api/assistant")


class Context(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    project_id: str | None = Field(default=None, max_length=100)
    date: str | None = Field(default=None, max_length=10)


class ChatRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    model: str = Field(min_length=1, max_length=200)
    prompt: str = Field(min_length=1, max_length=2000)
    context: Context = Field(default_factory=Context)


@router.get("/status")
async def status(request: Request) -> dict:
    return await request.app.state.assistant.status()


@router.post("/chat")
async def chat(body: ChatRequest, request: Request) -> dict:
    if not body.prompt.strip():
        raise AssistantError("assistant_prompt", "Enter a question.", 422)
    work = asyncio.create_task(request.app.state.assistant.ask(body.model, body.prompt.strip(), body.context.model_dump()))
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
