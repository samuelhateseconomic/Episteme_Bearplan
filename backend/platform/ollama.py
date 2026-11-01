"""Async Ollama transport, pinned to loopback; no proxy, redirects or downloads."""
from __future__ import annotations

import json

import httpx2 as httpx

from backend.domain.assistant import AssistantError

BASE_URL = "http://127.0.0.1:11434"
MAX_RESPONSE = 262144


class OllamaProvider:
    def __init__(self):
        self._thinking: dict[str, bool] = {}

    async def _json(self, method: str, path: str, payload: dict | None = None, *, timeout: float = 5) -> dict:
        try:
            async with httpx.AsyncClient(base_url=BASE_URL, trust_env=False, follow_redirects=False, timeout=timeout) as client:
                async with client.stream(method, path, json=payload) as response:
                    if response.status_code != 200:
                        raise AssistantError("ollama_request", "Ollama could not use that model. Check that it is installed locally and supports tools.")
                    chunks = bytearray()
                    async for chunk in response.aiter_bytes():
                        chunks.extend(chunk)
                        if len(chunks) > MAX_RESPONSE:
                            raise AssistantError("ollama_response", "Ollama returned too much data. Ask a smaller question.")
            result = json.loads(chunks)
            if not isinstance(result, dict):
                raise ValueError
            return result
        except httpx.TimeoutException:
            raise AssistantError("assistant_timeout", "Ollama took too long. Try another local model; your records were unchanged.", 504) from None
        except httpx.HTTPError:
            raise AssistantError("ollama_unavailable", "Ollama is unavailable. Open Ollama, then refresh models. Plan, Track and Stats remain available.") from None
        except (ValueError, UnicodeError):
            raise AssistantError("ollama_response", "Ollama returned an unreadable response. Refresh models or try another model.") from None

    async def models(self) -> list[dict]:
        response = await self._json("GET", "/api/tags")
        models = response.get("models")
        if not isinstance(models, list):
            raise AssistantError("ollama_response", "Ollama returned an invalid model list.")
        return [{"name": m["name"], "digest": m.get("digest", ""), "details": m.get("details", {})}
                for m in models[:50] if isinstance(m, dict) and isinstance(m.get("name"), str) and len(m["name"]) <= 200]

    async def check_model(self, model: str) -> None:
        models = await self.models()
        if model not in {m["name"] for m in models}:
            raise AssistantError("model_missing", "Choose an installed local model. BearPlans never downloads a model automatically.", 422)
        info = await self._json("POST", "/api/show", {"model": model})
        if info.get("remote_host") or info.get("remote_model") or "cloud" in model.casefold():
            raise AssistantError("model_remote", "Choose a model whose weights are stored locally. Cloud models are outside this app's scope.", 422)
        capabilities = info.get("capabilities")
        if not isinstance(capabilities, list) or "tools" not in capabilities:
            raise AssistantError("model_tools", "This model does not support tool calling. Choose a local tools-capable model such as Qwen3.", 422)
        self._thinking[model] = "thinking" in capabilities

    async def chat(self, model: str, messages: list[dict], tools: list[dict]) -> dict:
        payload = {"model": model, "messages": messages, "tools": tools,
                   "stream": False, "keep_alive": "2m", "options": {"temperature": 0, "num_ctx": 8192, "num_predict": 1536}}
        if self._thinking.get(model):
            payload["think"] = True
        result = await self._json("POST", "/api/chat", payload, timeout=60)
        message = result.get("message")
        if result.get("done") is not True or result.get("done_reason") == "length" or not isinstance(message, dict):
            raise AssistantError("ollama_response", "Ollama returned an incomplete answer. Try a shorter question.")
        # Ollama separates model reasoning into `thinking`; never return it to the
        # coordinator/browser. A token-limited partial response is not an answer.
        return {"content": message.get("content", ""), "tool_calls": message.get("tool_calls", [])}
