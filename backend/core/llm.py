"""Unified LLM client factory — Anthropic primary, OpenAI fallback."""

from typing import AsyncGenerator
from config import get_settings
from langfuse import observe


class LLMResponse:
    """Standardised response wrapper."""
    def __init__(self, text: str, model: str, usage: dict | None = None):
        self.text = text
        self.model = model
        self.usage = usage or {}


class LLMClient:
    """Manages LLM calls through Anthropic's API.

    Supports both one-shot completions and streaming.
    The Anthropic client is created lazily on first use so that importing
    this module does not crash when ANTHROPIC_API_KEY is absent.
    """

    def __init__(self):
        self._anthropic = None

    def _get_client(self):
        """Return the AsyncAnthropic client, creating it once."""
        if self._anthropic is None:
            import anthropic
            settings = get_settings()
            self._anthropic = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)
        return self._anthropic

    def _route_model(self, model: str, system: str, messages: list[dict], user: str = "") -> str:
        """Lightweight model router to save cost on simple queries."""
        # 1. Normalise invalid PRD constants
        if "sonnet-4" in model or "3-5-sonnet" in model:
            target_model = "claude-3-5-sonnet-20241022"
        elif "haiku-4-5" in model or "3-5-haiku" in model:
            target_model = "claude-3-5-haiku-20241022"
        else:
            target_model = model

        # 2. Only attempt to downgrade if target is Sonnet
        if "claude-3-5-sonnet" not in target_model:
            return target_model
            
        # DocDoubt factual question routing
        if "You are DocDoubt" in system:
            query = user if user else (messages[-1].get("content", "") if messages else "")
            if len(query) < 80:
                keywords = ["explain", "compare", "derive", "prove"]
                if not any(k in query.lower() for k in keywords):
                    return "claude-3-5-haiku-20241022"
                    
        # MemoryTutor start-of-session routing
        if "You are MemoryTutor" in system:
            history_len = len(messages) if messages else (1 if user else 0)
            if history_len <= 1:
                return "claude-3-5-haiku-20241022"
                
        return target_model

    @observe()
    async def complete(
        self,
        model: str,
        system: str,
        user: str,
        max_tokens: int = 4096,
        temperature: float = 0.3,
    ) -> LLMResponse:
        """Single-turn completion. Returns full text."""
        model = self._route_model(model, system, [], user)
        response = await self._get_client().messages.create(
            model=model,
            max_tokens=max_tokens,
            temperature=temperature,
            system=[{"type": "text", "text": system, "cache_control": {"type": "ephemeral"}}],
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

    @observe()
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

        model = self._route_model(model, system, messages, user or "")
        async with self._get_client().messages.stream(
            model=model,
            max_tokens=max_tokens,
            temperature=temperature,
            system=[{"type": "text", "text": system, "cache_control": {"type": "ephemeral"}}],
            messages=messages,
        ) as stream:
            async for text in stream.text_stream:
                yield text

    @observe()
    async def complete_multi_turn(
        self,
        model: str,
        system: str,
        messages: list[dict],
        max_tokens: int = 4096,
        temperature: float = 0.3,
    ) -> LLMResponse:
        """Multi-turn completion with full message history."""
        model = self._route_model(model, system, messages, "")
        response = await self._get_client().messages.create(
            model=model,
            max_tokens=max_tokens,
            temperature=temperature,
            system=[{"type": "text", "text": system, "cache_control": {"type": "ephemeral"}}],
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


# Singleton — Anthropic client created lazily on first call
llm = LLMClient()
