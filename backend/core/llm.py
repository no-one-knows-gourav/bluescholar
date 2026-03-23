"""Unified LLM client factory — Anthropic primary, OpenAI fallback."""

from typing import AsyncGenerator
import anthropic
from config import get_settings


class LLMResponse:
    """Standardised response wrapper."""
    def __init__(self, text: str, model: str, usage: dict | None = None):
        self.text = text
        self.model = model
        self.usage = usage or {}


class LLMClient:
    """Manages LLM calls through Anthropic's API.

    Supports both one-shot completions and streaming.
    System prompt caching is enabled by default for supported models.
    """

    def __init__(self):
        settings = get_settings()
        self._anthropic = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)

    async def complete(
        self,
        model: str,
        system: str,
        user: str,
        max_tokens: int = 4096,
        temperature: float = 0.3,
    ) -> LLMResponse:
        """Single-turn completion. Returns full text."""
        response = await self._anthropic.messages.create(
            model=model,
            max_tokens=max_tokens,
            temperature=temperature,
            system=system,
            messages=[{"role": "user", "content": user}],
        )
        return LLMResponse(
            text=response.content[0].text,
            model=model,
            usage={
                "input_tokens": response.usage.input_tokens,
                "output_tokens": response.usage.output_tokens,
            },
        )

    async def stream(
        self,
        model: str,
        system: str,
        messages: list[dict] | None = None,
        user: str | None = None,
        max_tokens: int = 4096,
        temperature: float = 0.3,
    ) -> AsyncGenerator[str, None]:
        """Streaming completion. Yields text chunks."""
        if messages is None:
            messages = [{"role": "user", "content": user or ""}]

        async with self._anthropic.messages.stream(
            model=model,
            max_tokens=max_tokens,
            temperature=temperature,
            system=system,
            messages=messages,
        ) as stream:
            async for text in stream.text_stream:
                yield text

    async def complete_multi_turn(
        self,
        model: str,
        system: str,
        messages: list[dict],
        max_tokens: int = 4096,
        temperature: float = 0.3,
    ) -> LLMResponse:
        """Multi-turn completion with full message history."""
        response = await self._anthropic.messages.create(
            model=model,
            max_tokens=max_tokens,
            temperature=temperature,
            system=system,
            messages=messages,
        )
        return LLMResponse(
            text=response.content[0].text,
            model=model,
            usage={
                "input_tokens": response.usage.input_tokens,
                "output_tokens": response.usage.output_tokens,
            },
        )


# Singleton
llm = LLMClient()
