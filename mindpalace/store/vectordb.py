from __future__ import annotations

from typing import Any

import chromadb

from mindpalace.config import settings
from mindpalace.models import Chunk


_client: chromadb.ClientAPI | None = None


def _get_client() -> chromadb.ClientAPI:
    global _client
    if _client is None:
        _client = chromadb.HttpClient(
            host=settings.vector_store.host,
            port=settings.vector_store.port,
        )
    return _client


def _get_collection() -> chromadb.Collection:
    client = _get_client()
    return client.get_or_create_collection(
        name=settings.vector_store.collection,
        metadata={"hnsw:space": "cosine"},
    )


def upsert_chunks(chunks: list[Chunk]) -> None:
    if not chunks:
        return
    collection = _get_collection()
    collection.upsert(
        ids=[c.id for c in chunks],
        documents=[c.content for c in chunks],
        embeddings=[c.embedding for c in chunks if c.embedding],
        metadatas=[c.to_chroma_metadata() for c in chunks],
    )


def delete_by_document_id(document_id: str) -> None:
    collection = _get_collection()
    collection.delete(where={"document_id": document_id})


def query(
    query_embedding: list[float],
    top_k: int | None = None,
    where: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    collection = _get_collection()
    k = top_k or settings.rag.top_k
    kwargs: dict[str, Any] = {
        "query_embeddings": [query_embedding],
        "n_results": k,
        "include": ["documents", "metadatas", "distances"],
    }
    if where:
        kwargs["where"] = where

    results = collection.query(**kwargs)

    items = []
    for i in range(len(results["ids"][0])):
        items.append({
            "id": results["ids"][0][i],
            "content": results["documents"][0][i],
            "metadata": results["metadatas"][0][i],
            "distance": results["distances"][0][i],
        })
    return items


def get_document_chunks(document_id: str) -> list[dict[str, Any]]:
    collection = _get_collection()
    results = collection.get(
        where={"document_id": document_id},
        include=["documents", "metadatas"],
    )
    items = []
    for i in range(len(results["ids"])):
        items.append({
            "id": results["ids"][i],
            "content": results["documents"][i],
            "metadata": results["metadatas"][i],
        })
    items.sort(key=lambda x: x["metadata"]["chunk_index"])
    return items


def get_stats() -> dict[str, Any]:
    collection = _get_collection()
    count = collection.count()
    return {"collection": settings.vector_store.collection, "total_chunks": count}
