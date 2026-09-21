"""Cloud-backed RAG using OpenAI for generation and embeddings."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import chromadb
from openai import OpenAI
from pypdf import PdfReader


BASE_DIR = Path(__file__).resolve().parent.parent
CHROMA_PATH = Path(os.getenv("CHROMA_PATH", str(BASE_DIR / "data" / "chroma")))
COLLECTION_NAME = os.getenv("CHROMA_COLLECTION", "docs")
CHAT_MODEL = os.getenv("OPENAI_CHAT_MODEL", "gpt-4o-mini")
EMBED_MODEL = os.getenv("OPENAI_EMBED_MODEL", "text-embedding-3-small")
CHUNK_SIZE = int(os.getenv("RAG_CHUNK_SIZE", "800"))
CHUNK_OVERLAP = int(os.getenv("RAG_CHUNK_OVERLAP", "100"))


def _openai_client() -> OpenAI:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is not configured.")
    return OpenAI(api_key=api_key)


def _chroma_collection():
    CHROMA_PATH.mkdir(parents=True, exist_ok=True)
    client = chromadb.PersistentClient(path=str(CHROMA_PATH))
    return client.get_or_create_collection(COLLECTION_NAME)


def _load_text(filepath: Path) -> str:
    if filepath.suffix.lower() == ".pdf":
        reader = PdfReader(str(filepath))
        return "\n".join(page.extract_text() or "" for page in reader.pages)
    return filepath.read_text(encoding="utf-8")


def _chunk_text(text: str) -> list[str]:
    if CHUNK_SIZE <= CHUNK_OVERLAP:
        raise ValueError("RAG_CHUNK_SIZE must be greater than RAG_CHUNK_OVERLAP")
    step = CHUNK_SIZE - CHUNK_OVERLAP
    return [text[start : start + CHUNK_SIZE] for start in range(0, len(text), step)]


def _embed(text: str) -> list[float]:
    response = _openai_client().embeddings.create(model=EMBED_MODEL, input=text)
    return response.data[0].embedding


def ingest(folder_path: str | Path) -> int:
    """Embed PDF/text files into ChromaDB; run before serving questions."""
    folder = Path(folder_path)
    if not folder.is_dir():
        raise NotADirectoryError(f"Document folder does not exist: {folder}")

    collection = _chroma_collection()
    added = 0
    for filepath in sorted(folder.iterdir()):
        if filepath.suffix.lower() not in {".txt", ".pdf"}:
            continue
        for index, chunk in enumerate(_chunk_text(_load_text(filepath))):
            if not chunk.strip():
                continue
            collection.upsert(
                ids=[f"{filepath.name}:{index}"],
                embeddings=[_embed(chunk)],
                documents=[chunk],
                metadatas=[{"source": filepath.name}],
            )
            added += 1
    return added


def retrieve(question: str, n_results: int = 4) -> tuple[list[str], list[dict[str, Any]]]:
    collection = _chroma_collection()
    count = collection.count()
    if count == 0:
        raise RuntimeError("The knowledge base is empty. Run ingest_documents first.")

    result = collection.query(
        query_embeddings=[_embed(question)],
        n_results=min(n_results, count),
    )
    return result["documents"][0], result["metadatas"][0]


def answer(question: str) -> dict[str, Any]:
    """Retrieve relevant context and generate an answer grounded in it."""
    chunks, metadatas = retrieve(question)
    context = "\n\n---\n\n".join(chunks)
    prompt = (
        "Answer the question using ONLY the context below. "
        "If the context does not contain the answer, say you do not know; do not guess.\n\n"
        f"Context:\n{context}\n\nQuestion: {question}\n\nAnswer:"
    )
    response = _openai_client().responses.create(
        model=CHAT_MODEL,
        input=prompt,
        store=False,
    )
    return {
        "answer": response.output_text,
        "sources": sorted({metadata["source"] for metadata in metadatas}),
    }
