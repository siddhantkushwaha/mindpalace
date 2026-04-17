from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any


class ContentType(str, Enum):
    EMAIL = "email"
    NOTE = "note"
    CHECKLIST = "checklist"
    BOOKMARK = "bookmark"
    DOCUMENT = "document"
    PHOTO = "photo"


def _make_id(*parts: str) -> str:
    return hashlib.sha256(":".join(parts).encode()).hexdigest()[:16]


@dataclass
class Document:
    source: str
    source_id: str
    title: str
    content: str
    content_type: ContentType
    created_at: datetime
    user_id: str = ""
    url: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    updated_at: datetime | None = None
    ingested_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    expires_at: datetime | None = None

    @property
    def id(self) -> str:
        return _make_id(self.source, self.source_id)


@dataclass
class Chunk:
    document_id: str
    content: str
    chunk_index: int
    total_chunks: int
    # Denormalized from parent Document
    source: str
    source_id: str
    content_type: str
    title: str
    url: str | None
    created_at: datetime
    ingested_at: datetime
    user_id: str = ""
    expires_at: datetime | None = None
    embedding: list[float] | None = None

    @property
    def id(self) -> str:
        return _make_id(self.document_id, str(self.chunk_index))

    def to_chroma_metadata(self) -> dict[str, Any]:
        return {
            "document_id": self.document_id,
            "source": self.source,
            "source_id": self.source_id,
            "content_type": self.content_type,
            "title": self.title,
            "url": self.url or "",
            "chunk_index": self.chunk_index,
            "total_chunks": self.total_chunks,
            "created_at": self.created_at.timestamp(),
            "ingested_at": self.ingested_at.timestamp(),
            "expires_at": self.expires_at.timestamp() if self.expires_at else -1,
            "user_id": self.user_id,
        }

    @classmethod
    def from_document(cls, doc: Document, content: str, chunk_index: int, total_chunks: int) -> Chunk:
        return cls(
            document_id=doc.id,
            content=content,
            chunk_index=chunk_index,
            total_chunks=total_chunks,
            source=doc.source,
            source_id=doc.source_id,
            content_type=doc.content_type.value,
            title=doc.title,
            url=doc.url,
            created_at=doc.created_at,
            ingested_at=doc.ingested_at,
            user_id=doc.user_id,
            expires_at=doc.expires_at,
        )
