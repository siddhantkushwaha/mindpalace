from __future__ import annotations

from sentence_transformers import SentenceTransformer

from mindpalace.config import settings
from mindpalace.models import Chunk


_model: SentenceTransformer | None = None


def _get_model() -> SentenceTransformer:
    global _model
    if _model is None:
        _model = SentenceTransformer(settings.embedding.model, device=settings.embedding.device)
    return _model


def embed_chunks(chunks: list[Chunk]) -> list[Chunk]:
    if not chunks:
        return chunks
    model = _get_model()
    texts = [c.content for c in chunks]
    embeddings = model.encode(texts, batch_size=settings.embedding.batch_size, show_progress_bar=False)
    for chunk, emb in zip(chunks, embeddings):
        chunk.embedding = emb.tolist()
    return chunks


def embed_query(query: str) -> list[float]:
    model = _get_model()
    return model.encode(query).tolist()
