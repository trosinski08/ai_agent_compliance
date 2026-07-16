"""
Article-aware chunking for Polish legal documents.

The natural unit of Polish law is the artykuł (Art. N.).
We split on article boundaries first; oversized articles are split
further by paragraph (ust.) boundaries.
"""
from __future__ import annotations

import re
from dataclasses import dataclass

from .parser import ParsedDocument

# Matches the start of an article: "Art. 1.", "Art. 14a.", case-insensitive
_ART_BOUNDARY = re.compile(r"(?=\bArt\.\s*\d+[a-z]?\.)", re.IGNORECASE)

MAX_CHARS = 1500
OVERLAP_CHARS = 150


@dataclass
class Chunk:
    text: str
    source: str
    law_name: str
    article_ref: str
    chunk_index: int


def chunk_document(doc: ParsedDocument, law_name: str = "") -> list[Chunk]:
    name = law_name or doc.title
    parts = _ART_BOUNDARY.split(doc.full_text)

    chunks: list[Chunk] = []
    idx = 0

    for part in parts:
        part = part.strip()
        if not part:
            continue

        article_ref = _article_ref(part)

        sub_parts = _split_if_long(part) if len(part) > MAX_CHARS else [part]

        for sub in sub_parts:
            sub = sub.strip()
            if len(sub) < 50:
                continue
            chunks.append(Chunk(
                text=sub,
                source=doc.source,
                law_name=name,
                article_ref=article_ref,
                chunk_index=idx,
            ))
            idx += 1

    # Fallback when the document has no recognisable article structure
    if not chunks:
        chunks = _char_split(doc.full_text, doc.source, name)

    return chunks


def _article_ref(text: str) -> str:
    m = re.match(r"^(Art\.\s*\d+[a-z]?\.?)", text, re.IGNORECASE)
    return m.group(1).strip() if m else ""


def _split_if_long(text: str) -> list[str]:
    """Split by paragraph (ust.) boundaries; last resort: hard character split."""
    # "1." at line start or "ust. N"
    para_re = re.compile(r"(?=\bust\.\s*\d+|^\d+\.\s)", re.IGNORECASE | re.MULTILINE)
    parts = para_re.split(text)

    result: list[str] = []
    buf = ""
    for p in parts:
        if len(buf) + len(p) <= MAX_CHARS:
            buf += p
        else:
            if buf:
                result.append(buf)
            buf = p
    if buf:
        result.append(buf)

    return result if result else [text[:MAX_CHARS]]


def _char_split(text: str, source: str, law_name: str) -> list[Chunk]:
    chunks = []
    start = 0
    idx = 0
    while start < len(text):
        end = min(start + MAX_CHARS, len(text))
        chunks.append(Chunk(
            text=text[start:end].strip(),
            source=source,
            law_name=law_name,
            article_ref="",
            chunk_index=idx,
        ))
        start += MAX_CHARS - OVERLAP_CHARS
        idx += 1
    return chunks
