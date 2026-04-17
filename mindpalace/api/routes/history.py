from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from mindpalace.api.routes.auth import _get_user_id_from_request
from mindpalace.db import get_db, ChatSession, ChatMessage

router = APIRouter(prefix="/api/chats")


class SessionOut(BaseModel):
    id: str
    title: str
    source_filter: str | None
    created_at: str
    updated_at: str
    message_count: int


class MessageOut(BaseModel):
    id: str
    role: str
    content: str
    created_at: str


class SessionDetail(BaseModel):
    id: str
    title: str
    source_filter: str | None
    created_at: str
    updated_at: str
    messages: list[MessageOut]


class CreateSessionRequest(BaseModel):
    title: str = "New Chat"
    source_filter: str | None = None


class AddMessageRequest(BaseModel):
    role: str
    content: str


class UpdateTitleRequest(BaseModel):
    title: str


@router.get("", response_model=list[SessionOut])
def list_sessions(request: Request):
    user_id = _get_user_id_from_request(request)
    db = next(get_db())
    sessions = db.query(ChatSession).filter(ChatSession.user_id == user_id).order_by(ChatSession.updated_at.desc()).all()
    return [
        SessionOut(
            id=s.id,
            title=s.title,
            source_filter=s.source_filter,
            created_at=s.created_at.isoformat(),
            updated_at=s.updated_at.isoformat(),
            message_count=len(s.messages),
        )
        for s in sessions
    ]


@router.post("", response_model=SessionDetail)
def create_session(req: CreateSessionRequest, request: Request):
    user_id = _get_user_id_from_request(request)
    db = next(get_db())
    session = ChatSession(user_id=user_id, title=req.title, source_filter=req.source_filter)
    db.add(session)
    db.commit()
    db.refresh(session)
    return SessionDetail(
        id=session.id,
        title=session.title,
        source_filter=session.source_filter,
        created_at=session.created_at.isoformat(),
        updated_at=session.updated_at.isoformat(),
        messages=[],
    )


@router.get("/{session_id}", response_model=SessionDetail)
def get_session(session_id: str, request: Request):
    user_id = _get_user_id_from_request(request)
    db = next(get_db())
    session = db.query(ChatSession).filter(ChatSession.id == session_id, ChatSession.user_id == user_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return SessionDetail(
        id=session.id,
        title=session.title,
        source_filter=session.source_filter,
        created_at=session.created_at.isoformat(),
        updated_at=session.updated_at.isoformat(),
        messages=[
            MessageOut(id=m.id, role=m.role, content=m.content, created_at=m.created_at.isoformat())
            for m in session.messages
        ],
    )


@router.post("/{session_id}/messages", response_model=MessageOut)
def add_message(session_id: str, req: AddMessageRequest, request: Request):
    user_id = _get_user_id_from_request(request)
    db = next(get_db())
    session = db.query(ChatSession).filter(ChatSession.id == session_id, ChatSession.user_id == user_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    msg = ChatMessage(session_id=session_id, role=req.role, content=req.content)
    db.add(msg)
    session.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(msg)
    return MessageOut(id=msg.id, role=msg.role, content=msg.content, created_at=msg.created_at.isoformat())


@router.patch("/{session_id}", response_model=SessionOut)
def update_session_title(session_id: str, req: UpdateTitleRequest, request: Request):
    user_id = _get_user_id_from_request(request)
    db = next(get_db())
    session = db.query(ChatSession).filter(ChatSession.id == session_id, ChatSession.user_id == user_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    session.title = req.title
    session.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(session)
    return SessionOut(
        id=session.id,
        title=session.title,
        source_filter=session.source_filter,
        created_at=session.created_at.isoformat(),
        updated_at=session.updated_at.isoformat(),
        message_count=len(session.messages),
    )


@router.delete("/{session_id}")
def delete_session(session_id: str, request: Request):
    user_id = _get_user_id_from_request(request)
    db = next(get_db())
    session = db.query(ChatSession).filter(ChatSession.id == session_id, ChatSession.user_id == user_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    db.delete(session)
    db.commit()
    return {"deleted": session_id}
