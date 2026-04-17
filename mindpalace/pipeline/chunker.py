from __future__ import annotations

import tiktoken

from mindpalace.models import Chunk, Document


_SEPARATORS = ["\n\n", "\n", ". ", " "]


def _count_tokens(text: str, encoding: tiktoken.Encoding) -> int:
    return len(encoding.encode(text))


def _split_text(text: str, max_tokens: int, overlap_tokens: int, encoding: tiktoken.Encoding) -> list[str]:
    if _count_tokens(text, encoding) <= max_tokens:
        return [text]

    # Try each separator level
    for sep in _SEPARATORS:
        parts = text.split(sep)
        if len(parts) > 1:
            break
    else:
        # Last resort: split by characters (approximate token boundaries)
        parts = [text[i : i + max_tokens * 3] for i in range(0, len(text), max_tokens * 3)]

    chunks: list[str] = []
    current = ""

    for part in parts:
        candidate = (current + sep + part).strip() if current else part.strip()
        if _count_tokens(candidate, encoding) > max_tokens and current:
            chunks.append(current.strip())
            # Overlap: take end of current chunk
            if overlap_tokens > 0:
                tokens = encoding.encode(current)
                overlap_text = encoding.decode(tokens[-overlap_tokens:])
                current = overlap_text + sep + part
            else:
                current = part
        else:
            current = candidate

    if current.strip():
        chunks.append(current.strip())

    return chunks


def chunk_document(doc: Document, chunk_size: int = 512, chunk_overlap: int = 64) -> list[Chunk]:
    encoding = tiktoken.get_encoding("cl100k_base")
    texts = _split_text(doc.content, chunk_size, chunk_overlap, encoding)
    total = len(texts)
    return [Chunk.from_document(doc, text, i, total) for i, text in enumerate(texts)]
