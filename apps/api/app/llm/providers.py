"""LLM provider abstraction. Default 'local' is deterministic and key-free."""
from __future__ import annotations

from functools import lru_cache
from typing import Protocol

from ..config import settings


class LLMProvider(Protocol):
    name: str

    def complete(self, prompt: str, system: str = "") -> str: ...


class LocalProvider:
    """Deterministic, no-API text generation. Good enough to run the platform and
    keep outputs reproducible in tests; swap to a real provider via LLM_PROVIDER."""

    name = "local-deterministic"

    def complete(self, prompt: str, system: str = "") -> str:
        head = system.strip().splitlines()[0] if system.strip() else "FitLens AI"
        body = prompt.strip()
        return f"[{head}]\n{body}"


class OpenAIProvider:  # pragma: no cover - requires API key
    name = "openai"

    def __init__(self) -> None:
        from openai import OpenAI  # type: ignore

        self._client = OpenAI(api_key=settings.openai_api_key)

    def complete(self, prompt: str, system: str = "") -> str:
        resp = self._client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system or "You are FitLens, a staffing AI."},
                {"role": "user", "content": prompt},
            ],
        )
        return resp.choices[0].message.content or ""


class AnthropicProvider:  # pragma: no cover - requires API key
    name = "anthropic"

    def __init__(self) -> None:
        from anthropic import Anthropic  # type: ignore

        self._client = Anthropic(api_key=settings.anthropic_api_key)

    def complete(self, prompt: str, system: str = "") -> str:
        msg = self._client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=1024,
            system=system or "You are FitLens, a staffing AI.",
            messages=[{"role": "user", "content": prompt}],
        )
        return "".join(block.text for block in msg.content if block.type == "text")


class GeminiProvider:  # pragma: no cover - requires API key
    name = "gemini"

    def __init__(self) -> None:
        import google.generativeai as genai  # type: ignore

        genai.configure(api_key=settings.gemini_api_key)
        self._model = genai.GenerativeModel("gemini-1.5-flash")

    def complete(self, prompt: str, system: str = "") -> str:
        resp = self._model.generate_content(f"{system}\n\n{prompt}" if system else prompt)
        return resp.text or ""


@lru_cache(maxsize=1)
def get_llm() -> LLMProvider:
    provider = settings.llm_provider.lower()
    try:
        if provider == "openai" and settings.openai_api_key:
            return OpenAIProvider()
        if provider == "anthropic" and settings.anthropic_api_key:
            return AnthropicProvider()
        if provider == "gemini" and settings.gemini_api_key:
            return GeminiProvider()
    except Exception:  # noqa: BLE001 — any SDK/import failure => local fallback
        return LocalProvider()
    return LocalProvider()
