from __future__ import annotations

import json
from datetime import datetime, timezone

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from mindpalace.agent.engine import ask_stream
from mindpalace.api.routes.auth import verify_token
from mindpalace.db import get_db, ChatSession, ChatMessage

router = APIRouter()


@router.websocket("/ws/chat")
async def ws_chat(websocket: WebSocket):
    # Auth: token passed as query param ?token=xxx
    token = websocket.query_params.get("token", "")
    user_id = verify_token(token)
    if not user_id:
        await websocket.close(code=4001, reason="Unauthorized")
        return

    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_text()
            msg = json.loads(data)
            query = msg.get("message", "")
            history = msg.get("chat_history", [])
            source_filter = msg.get("source_filter")
            session_id = msg.get("session_id")
            where = {"source": source_filter} if source_filter else None

            # Persist: create or load session (scoped to user)
            db = next(get_db())
            if session_id:
                session = db.query(ChatSession).filter(
                    ChatSession.id == session_id,
                    ChatSession.user_id == user_id,
                ).first()
            else:
                session = None

            if not session:
                session = ChatSession(
                    user_id=user_id,
                    title=query[:80] if query else "New Chat",
                    source_filter=source_filter,
                )
                db.add(session)
                db.commit()
                db.refresh(session)

            # Save user message
            user_msg = ChatMessage(session_id=session.id, role="user", content=query)
            db.add(user_msg)
            session.updated_at = datetime.now(timezone.utc)
            db.commit()

            # Send session_id back to client so it can track the session
            await websocket.send_text(json.dumps({"type": "session_id", "session_id": session.id}))

            # Stream response (user-scoped retrieval)
            full_response = ""
            async for token_type, tok in ask_stream(query, chat_history=history, where=where, user_id=user_id):
                if token_type == "thinking":
                    await websocket.send_text(json.dumps({"type": "thinking", "content": tok}))
                else:
                    full_response += tok
                    await websocket.send_text(json.dumps({"type": "token", "content": tok}))

            if not full_response:
                await websocket.send_text(json.dumps({"type": "error", "content": "Model failed to generate a response. Please try again."}))
            else:
                # Save assistant message (only actual content, not thinking)
                assistant_msg = ChatMessage(session_id=session.id, role="assistant", content=full_response)
                db.add(assistant_msg)
                session.updated_at = datetime.now(timezone.utc)
                db.commit()

                await websocket.send_text(json.dumps({"type": "done"}))
    except WebSocketDisconnect:
        pass
