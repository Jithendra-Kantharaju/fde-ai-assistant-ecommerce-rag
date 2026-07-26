from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

SUPPORTED_SUFFIXES = {
    ".md",
    ".txt",
    ".json",
    ".yaml",
    ".yml",
    ".ts",
    ".js",
    ".py",
    ".html",
    ".hbs",
    ".css",
    ".scss",
    ".xml",
}

SKIP_DIRS = {
    ".git",
    ".pytest_cache",
    ".venv",
    "__pycache__",
    "build",
    "coverage",
    "dist",
    "logs",
    "node_modules",
    "screenshots",
    "tmp",
    "uploads",
}

MAX_FILE_SIZE_BYTES = 250_000
CHUNK_SIZE = 1_600
CHUNK_OVERLAP = 200


@dataclass(frozen=True)
class DocumentChunk:
    source_path: str
    chunk_index: int
    content: str
    language: str


def discover_source_files(root: Path) -> list[Path]:
    source_files: list[Path] = []

    for path in root.rglob("*"):
        if not path.is_file() or path.suffix.lower() not in SUPPORTED_SUFFIXES:
            continue

        if any(part in SKIP_DIRS for part in path.parts):
            continue

        if path.stat().st_size > MAX_FILE_SIZE_BYTES:
            continue

        source_files.append(path)

    return sorted(source_files)


def chunk_text(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> list[str]:
    normalized_text = "\n".join(line.rstrip() for line in text.splitlines()).strip()
    if not normalized_text:
        return []

    if len(normalized_text) <= chunk_size:
        return [normalized_text]

    chunks: list[str] = []
    start = 0
    step = max(chunk_size - overlap, 1)

    while start < len(normalized_text):
        end = min(start + chunk_size, len(normalized_text))
        chunk = normalized_text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        if end >= len(normalized_text):
            break
        start += step

    return chunks


def collect_document_chunks(root: Path) -> list[DocumentChunk]:
    chunks: list[DocumentChunk] = []

    for source_file in discover_source_files(root):
        try:
            text = source_file.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue

        relative_path = source_file.relative_to(root).as_posix()
        language = source_file.suffix.lstrip(".") or "text"

        for chunk_index, chunk in enumerate(chunk_text(text)):
            chunks.append(
                DocumentChunk(
                    source_path=relative_path,
                    chunk_index=chunk_index,
                    content=chunk,
                    language=language,
                )
            )

    return chunks
