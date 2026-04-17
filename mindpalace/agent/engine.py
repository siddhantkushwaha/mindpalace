from __future__ import annotations

from typing import Any, AsyncIterator

from mindpalace.config import settings
from mindpalace.pipeline.embedder import embed_query
from mindpalace.store.vectordb import query as vector_query
from mindpalace.llm.provider import complete, stream


_SYSTEM_PROMPT = """You are MindPalace, a personal AI assistant with access to the user's personal data (emails, notes, bookmarks, documents, photos).

When answering questions:
- Use the retrieved context to ground your answers
- Cite sources by mentioning the source type, title, and date
- If the context doesn't contain relevant information, say so honestly
- Be concise and helpful

Retrieved context will be provided in <context> tags."""


def _build_context(results: list[dict[str, Any]]) -> str:
    if not results:
        return "<context>\nNo relevant documents found.\n</context>"
    parts = []
    for r in results:
        meta = r["metadata"]
        header = f"[{meta['source']}/{meta['content_type']}] {meta['title']}"
        if meta.get("url"):
            header += f" ({meta['url']})"
        parts.append(f"--- {header} ---\n{r['content']}")
    return "<context>\n" + "\n\n".join(parts) + "\n</context>"


def retrieve(
    query_text: str,
    top_k: int | None = None,
    where: dict[str, Any] | None = None,
    user_id: str | None = None,
) -> list[dict[str, Any]]:
    embedding = embed_query(query_text)
    # Build user-scoped filter
    effective_where = _build_user_where(where, user_id)
    return vector_query(embedding, top_k=top_k or settings.rag.top_k, where=effective_where)


def _build_user_where(where: dict[str, Any] | None, user_id: str | None) -> dict[str, Any] | None:
    if not user_id:
        return where
    user_filter = {"user_id": user_id}
    if where:
        return {"$and": [user_filter, where]}
    return user_filter


def ask(query_text: str, chat_history: list[dict[str, str]] | None = None, where: dict[str, Any] | None = None, user_id: str | None = None) -> str:
    results = retrieve(query_text, where=where, user_id=user_id)
    context = _build_context(results)

    messages = [{"role": "system", "content": _SYSTEM_PROMPT}]
    if chat_history:
        messages.extend(chat_history)
    messages.append({"role": "user", "content": f"{context}\n\n{query_text}"})

    return complete(messages)


async def ask_stream(
    query_text: str,
    chat_history: list[dict[str, str]] | None = None,
    where: dict[str, Any] | None = None,
    user_id: str | None = None,
) -> AsyncIterator[tuple[str, str]]:
    results = retrieve(query_text, where=where, user_id=user_id)
    context = _build_context(results)

    messages = [{"role": "system", "content": _SYSTEM_PROMPT}]
    if chat_history:
        messages.extend(chat_history)
    messages.append({"role": "user", "content": f"{context}\n\n{query_text}"})

    async for token in stream(messages):
        yield token
