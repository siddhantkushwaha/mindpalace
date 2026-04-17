from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel

from mindpalace.models import Document, ContentType
from mindpalace.pipeline.chunker import chunk_document
from mindpalace.pipeline.embedder import embed_chunks
from mindpalace.store.vectordb import upsert_chunks, delete_by_document_id
from mindpalace.db import get_db, ApiKey

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/ingest")


def _resolve_api_key(x_api_key: str) -> str:
    """Look up API key in DB and return the owning user_id."""
    db = next(get_db())
    api_key = db.query(ApiKey).filter(ApiKey.key == x_api_key).first()
    if not api_key:
        raise HTTPException(status_code=401, detail="Invalid API key")
    return api_key.user_id


class DocumentPayload(BaseModel):
    source: str
    source_id: str
    title: str
    content: str
    content_type: str
    created_at: float
    url: str | None = None
    metadata: dict[str, Any] = {}
    expires_at: float | None = None


class IngestRequest(BaseModel):
    documents: list[DocumentPayload]


class DeleteRequest(BaseModel):
    source: str
    source_id: str


@router.post("/documents")
def ingest_documents(req: IngestRequest, x_api_key: str = Header(...)):
    user_id = _resolve_api_key(x_api_key)

    ingested = []
    for payload in req.documents:
        doc = Document(
            source=payload.source,
            source_id=payload.source_id,
            title=payload.title,
            content=payload.content,
            content_type=ContentType(payload.content_type),
            created_at=datetime.fromtimestamp(payload.created_at, tz=timezone.utc),
            url=payload.url,
            metadata=payload.metadata,
            user_id=user_id,
            expires_at=(
                datetime.fromtimestamp(payload.expires_at, tz=timezone.utc)
                if payload.expires_at
                else None
            ),
        )
        delete_by_document_id(doc.id)
        chunks = chunk_document(doc)
        embed_chunks(chunks)
        upsert_chunks(chunks)
        ingested.append({"document_id": doc.id, "chunks": len(chunks)})
        logger.info("Ingested document %s (%s chunks) for user %s", doc.id, len(chunks), user_id)

    return {"ingested": len(ingested), "documents": ingested}


@router.delete("/documents")
def delete_document(req: DeleteRequest, x_api_key: str = Header(...)):
    _resolve_api_key(x_api_key)

    from mindpalace.models import _make_id

    doc_id = _make_id(req.source, req.source_id)
    delete_by_document_id(doc_id)
    logger.info("Deleted document %s", doc_id)
    return {"deleted": doc_id}
