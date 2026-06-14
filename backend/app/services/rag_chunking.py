from __future__ import annotations

import re
from dataclasses import dataclass
from hashlib import sha1

from .document_loader import LoadedDocument


@dataclass(frozen=True)
class RagChunk:
    id: str
    text: str
    source: str
    file_path: str
    chunk_index: int
    # Hash of (file_path + mtime + content) used for stale-index detection
    doc_hash: str
    page: int | None = None
    heading: str | None = None


def _doc_hash(document: LoadedDocument, content_hash: str) -> str:
    """Stable hash that changes when file content changes.

    Uses sha1(file_path + page + content_hash) so that:
    - Moving a file → new hash (different file_path)
    - Editing content → new hash (different content_hash)
    - Same file, same content → same hash (idempotent upsert)
    """
    key = f"{document.file_path}:{document.page}:{content_hash}"
    return sha1(key.encode("utf-8")).hexdigest()[:16]


def chunk_documents(
    documents: list[LoadedDocument],
    target_chars: int = 1500,
    overlap_chars: int = 250,
) -> list[RagChunk]:
    chunks: list[RagChunk] = []

    for document in documents:
        # Content hash for stale detection
        content_hash = sha1(document.text.encode("utf-8")).hexdigest()[:16]
        doc_key = sha1(f"{document.file_path}:{document.page}".encode("utf-8")).hexdigest()[:12]
        d_hash = _doc_hash(document, content_hash)

        sections = _split_sections(document.text)
        chunk_index = 0

        for heading, text in sections:
            for piece in _split_text(text, target_chars=target_chars, overlap_chars=overlap_chars):
                chunks.append(
                    RagChunk(
                        id=f"{doc_key}:{chunk_index}",
                        text=piece,
                        source=document.source,
                        file_path=document.file_path,
                        page=document.page,
                        heading=heading,
                        chunk_index=chunk_index,
                        doc_hash=d_hash,
                    )
                )
                chunk_index += 1

    return chunks


def _split_sections(text: str) -> list[tuple[str | None, str]]:
    """Split text into (heading, content) sections.

    Handles both Markdown headings (# Title) and inferred headings for
    plain-text / PDF documents (ALL-CAPS lines, numbered headings like
    "1. Introduction", "CHAPTER 2").
    """
    normalized = re.sub(r"\r\n?", "\n", text).strip()
    if not normalized:
        return []

    sections: list[tuple[str | None, str]] = []
    current_heading: str | None = None
    buffer: list[str] = []

    for line in normalized.split("\n"):
        # Markdown heading
        if line.startswith("#"):
            if buffer:
                sections.append((current_heading, "\n".join(buffer).strip()))
                buffer = []
            current_heading = re.sub(r"^#+\s*", "", line).strip() or current_heading
        # Inferred heading: ALL-CAPS line (≥4 chars, no lowercase)
        elif _is_inferred_heading(line):
            if buffer:
                sections.append((current_heading, "\n".join(buffer).strip()))
                buffer = []
            current_heading = line.strip()
        else:
            buffer.append(line)

    if buffer:
        sections.append((current_heading, "\n".join(buffer).strip()))

    return sections or [(None, normalized)]


def _is_inferred_heading(line: str) -> bool:
    """Heuristic: detect non-Markdown headings in PDF/TXT documents."""
    stripped = line.strip()
    if len(stripped) < 4 or len(stripped) > 120:
        return False
    # Numbered heading: "1. Title", "1.2 Title", "CHAPTER 1"
    if re.match(r"^(\d+\.)+\s+\S", stripped):
        return True
    # ALL-CAPS heading (no lowercase letters, has at least one alpha)
    if stripped.isupper() and any(c.isalpha() for c in stripped):
        return True
    return False


def _split_text(text: str, target_chars: int, overlap_chars: int) -> list[str]:
    paragraphs = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    chunks: list[str] = []
    current = ""

    for paragraph in paragraphs:
        candidate = f"{current}\n\n{paragraph}".strip() if current else paragraph
        if len(candidate) <= target_chars:
            current = candidate
            continue

        if current:
            chunks.append(current)
            current = ""

        if len(paragraph) > target_chars:
            chunks.extend(_split_long_paragraph(paragraph, target_chars, overlap_chars))
            current = ""
        else:
            current = paragraph

    if current:
        chunks.append(current)

    return chunks


def _split_long_paragraph(text: str, target_chars: int, overlap_chars: int) -> list[str]:
    chunks: list[str] = []
    start = 0

    while start < len(text):
        end = min(start + target_chars, len(text))
        if end < len(text):
            boundary = max(text.rfind(". ", start, end), text.rfind("; ", start, end))
            if boundary > start + target_chars // 2:
                end = boundary + 1

        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)

        if end >= len(text):
            break
        start = max(end - overlap_chars, start + 1)

    return chunks


def _tail(text: str, max_chars: int) -> str:
    if len(text) <= max_chars:
        return text
    tail = text[-max_chars:]
    for separator in (". ", "\n", " "):
        index = tail.find(separator)
        if index >= 0 and index + len(separator) < len(tail):
            return tail[index + len(separator) :].lstrip()
    return tail.lstrip()
