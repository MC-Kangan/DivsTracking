from __future__ import annotations

from typing import Any, Protocol


class LLMAdapter(Protocol):
    """Portable structured-output interface for optional model-backed steps."""

    def generate_structured(
        self,
        prompt: str,
        schema: dict[str, Any],
        context: dict[str, Any],
    ) -> dict[str, Any]:
        """Return schema-shaped JSON-compatible output."""


class DeterministicLLMAdapter:
    """No-op adapter used when the workflow runs without a live LLM."""

    def generate_structured(
        self,
        prompt: str,
        schema: dict[str, Any],
        context: dict[str, Any],
    ) -> dict[str, Any]:
        return {}
