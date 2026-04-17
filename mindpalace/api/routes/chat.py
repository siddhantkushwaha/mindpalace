from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Request
from pydantic import BaseModel

from mindpalace.agent.engine import ask, retrieve
from mindpalace.api.routes.auth import _get_user_id_from_request
from mindpalace.store.vectordb import get_stats

router = APIRouter(prefix="/api")


class ChatRequest(BaseModel):
    message: str
    chat_history: list[dict[str, str]] = []
    source_filter: str | None = None


class ChatResponse(BaseModel):
    reply: str
    sources: list[dict[str, Any]] = []


class SearchRequest(BaseModel):
    query: str
    top_k: int = 10
    source_filter: str | None = None


@router.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest, request: Request):
    user_id = _get_user_id_from_request(request)
    where = {"source": req.source_filter} if req.source_filter else None
    reply = ask(req.message, chat_history=req.chat_history, where=where, user_id=user_id)
    return ChatResponse(reply=reply)


@router.post("/search")
def search(req: SearchRequest, request: Request):
    user_id = _get_user_id_from_request(request)
    where = {"source": req.source_filter} if req.source_filter else None
    results = retrieve(req.query, top_k=req.top_k, where=where, user_id=user_id)
    return {"results": results}


@router.get("/stats")
def stats():
    return get_stats()


@router.get("/health")
def health():
    return {"status": "ok"}
