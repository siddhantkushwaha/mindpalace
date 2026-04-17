from __future__ import annotations

from typing import Any, AsyncIterator

import litellm

from mindpalace.config import settings


def _model_name() -> str:
    return settings.llm.model


def _base_kwargs() -> dict[str, Any]:
    kwargs: dict[str, Any] = {
        "model": _model_name(),
        "temperature": settings.llm.temperature,
        "max_tokens": settings.llm.max_tokens,
    }
    if settings.llm.api_key:
        kwargs["api_key"] = settings.llm.api_key
    if settings.llm.base_url:
        kwargs["api_base"] = settings.llm.base_url
    return kwargs


def complete(messages: list[dict[str, str]], **kwargs: Any) -> str:
    try:
        response = litellm.completion(messages=messages, **{**_base_kwargs(), **kwargs})
        return response.choices[0].message.content
    except Exception:
        if settings.llm.fallback_model:
            fb_kwargs = {**_base_kwargs(), **kwargs, "model": settings.llm.fallback_model}
            response = litellm.completion(messages=messages, **fb_kwargs)
            return response.choices[0].message.content
        raise


async def stream(messages: list[dict[str, str]], **kwargs: Any) -> AsyncIterator[tuple[str, str]]:
    """Yield (token_type, text) tuples where token_type is 'thinking' or 'content'."""
    try:
        response = await litellm.acompletion(messages=messages, stream=True, **{**_base_kwargs(), **kwargs})
        async for chunk in response:
            d = chunk.choices[0].delta
            if d.content:
                yield ("content", d.content)
            else:
                reasoning = getattr(d, "reasoning_content", None)
                if reasoning:
                    yield ("thinking", reasoning)
    except Exception:
        if settings.llm.fallback_model:
            fb_kwargs = {**_base_kwargs(), **kwargs, "model": settings.llm.fallback_model}
            response = await litellm.acompletion(messages=messages, stream=True, **fb_kwargs)
            async for chunk in response:
                d = chunk.choices[0].delta
                if d.content:
                    yield ("content", d.content)
                else:
                    reasoning = getattr(d, "reasoning_content", None)
                    if reasoning:
                        yield ("thinking", reasoning)
        else:
            raise
