"""LLM provider abstraction (OpenAI / Anthropic today; Gemini/Azure later)."""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable

from runner.config import Settings
from runner.integrations import llm_simple


@runtime_checkable
class LLMProvider(Protocol):
    def complete(self, system: str, user: str, *, max_tokens: int = 2048) -> tuple[str, str]:
        """Return (provider_label, raw_text)."""
        ...


class ConfiguredMultiLLM:
    """Delegates to Anthropic or OpenAI based on settings (same as `complete_llm`)."""

    def __init__(self, settings: Settings) -> None:
        self._s = settings

    def complete(self, system: str, user: str, *, max_tokens: int = 2048) -> tuple[str, str]:
        return llm_simple.complete_llm(
            anthropic_key=self._s.anthropic_api_key,
            anthropic_model=self._s.anthropic_model,
            openai_key=self._s.openai_api_key,
            openai_model=self._s.openai_model,
            system=system,
            user=user,
            max_tokens=max_tokens,
        )


def get_llm_provider(settings: Settings) -> LLMProvider:
    return ConfiguredMultiLLM(settings)
