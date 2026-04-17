from __future__ import annotations

import secrets
import uuid
from datetime import datetime, timezone

from sqlalchemy import create_engine, Column, String, Text, Integer, DateTime, ForeignKey, Index
from sqlalchemy.orm import sessionmaker, DeclarativeBase, relationship

from mindpalace.config import settings


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, default=lambda: uuid.uuid4().hex[:16])
    username = Column(String, unique=True, nullable=False, index=True)
    password_hash = Column(String, nullable=False)
    display_name = Column(String, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    api_keys = relationship("ApiKey", back_populates="user", cascade="all, delete-orphan")
    webauthn_credentials = relationship("WebAuthnCredential", back_populates="user", cascade="all, delete-orphan")
    chat_sessions = relationship("ChatSession", back_populates="user", cascade="all, delete-orphan")


class ApiKey(Base):
    __tablename__ = "api_keys"

    id = Column(String, primary_key=True, default=lambda: uuid.uuid4().hex[:16])
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    key = Column(String, unique=True, nullable=False, index=True, default=lambda: secrets.token_hex(32))
    label = Column(String, default="default")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    user = relationship("User", back_populates="api_keys")


class WebAuthnCredential(Base):
    __tablename__ = "webauthn_credentials"

    id = Column(String, primary_key=True, default=lambda: uuid.uuid4().hex)
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    credential_id = Column(String, unique=True, nullable=False)
    public_key = Column(Text, nullable=False)
    sign_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    user = relationship("User", back_populates="webauthn_credentials")


class ChatSession(Base):
    __tablename__ = "chat_sessions"

    id = Column(String, primary_key=True, default=lambda: uuid.uuid4().hex[:16])
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    title = Column(String, default="New Chat")
    source_filter = Column(String, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    user = relationship("User", back_populates="chat_sessions")
    messages = relationship("ChatMessage", back_populates="session", order_by="ChatMessage.created_at", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_chat_sessions_user_id", "user_id"),
    )


class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id = Column(String, primary_key=True, default=lambda: uuid.uuid4().hex)
    session_id = Column(String, ForeignKey("chat_sessions.id", ondelete="CASCADE"), nullable=False)
    role = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    session = relationship("ChatSession", back_populates="messages")

    __table_args__ = (
        Index("ix_chat_messages_session_id", "session_id"),
    )


# ── Engine & Session ────────────────────────────────

_engine = None
_SessionLocal = None


def get_engine():
    global _engine
    if _engine is None:
        _engine = create_engine(settings.database.url, pool_pre_ping=True)
    return _engine


def get_session_factory():
    global _SessionLocal
    if _SessionLocal is None:
        _SessionLocal = sessionmaker(bind=get_engine())
    return _SessionLocal


def init_db():
    """Create all tables if they don't exist."""
    Base.metadata.create_all(get_engine())


def get_db():
    """Dependency / context manager for DB sessions."""
    Session = get_session_factory()
    db = Session()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
