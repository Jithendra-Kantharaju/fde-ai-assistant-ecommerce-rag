from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

import chromadb
from dotenv import load_dotenv
from fastapi import HTTPException
from openai import OpenAI

from .ingestion import DocumentChunk, collect_document_chunks
from .schemas import AssistantRequest, AssistantResponse, HealthResponse, ReindexResponse, SourceResponse


@dataclass(frozen=True)
class RetrievedChunk:
    source_path: str
    chunk_index: int
    content: str


class RagAssistantService:
    def __init__(
        self,
        *,
        source_root: Path | None = None,
        openai_client: OpenAI | None = None,
        chroma_collection=None,
    ) -> None:
        load_dotenv()
        self.chat_model = os.getenv("OPENAI_MODEL", "gpt-4.1-mini")
        self.embedding_model = os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")
        self.source_root = source_root or Path(os.getenv("APP_SOURCE_ROOT", Path(__file__).resolve().parents[1]))
        self.chroma_host = os.getenv("CHROMA_HOST", "localhost")
        self.chroma_port = int(os.getenv("CHROMA_PORT", "8000"))
        self.collection_name = os.getenv("CHROMA_COLLECTION", "product_assistant")
        api_key = os.getenv("OPENAI_API_KEY", "").strip()
        self.openai_client = openai_client or (
            OpenAI(api_key=api_key) if api_key and api_key != "your_openai_api_key_here" else None
        )
        self.chroma_client = None
        self.collection = chroma_collection

    def health(self) -> HealthResponse:
        chroma_ready = False
        indexed_chunks = 0
        try:
            indexed_chunks = self._get_collection().count()
            chroma_ready = True
        except Exception:
            chroma_ready = False

        return HealthResponse(
            status="ok",
            openai_key_configured=self.openai_client is not None,
            chroma_connected=chroma_ready,
            indexed_chunks=indexed_chunks,
            model=self.chat_model,
            collection_name=self.collection_name,
        )

    def source_summary(self) -> SourceResponse:
        chunks = 0
        try:
            chunks = self._get_collection().count()
        except Exception:
            chunks = 0

        return SourceResponse(
            source_root=str(self.source_root),
            collection_name=self.collection_name,
            indexed_chunks=chunks,
        )

    def reindex(self) -> ReindexResponse:
        if self.openai_client is None:
            raise HTTPException(
                status_code=500,
                detail="OPENAI_API_KEY is not configured. Set it in your .env file before reindexing.",
            )

        document_chunks = collect_document_chunks(self.source_root)
        if not document_chunks:
            return ReindexResponse(indexed_chunks=0, source_files=0, collection_name=self.collection_name)

        embeddings = self._embed_texts([chunk.content for chunk in document_chunks])
        collection = self._get_collection()
        collection.upsert(
            ids=[self._chunk_id(chunk) for chunk in document_chunks],
            documents=[chunk.content for chunk in document_chunks],
            embeddings=embeddings,
            metadatas=[
                {
                    "source_path": chunk.source_path,
                    "chunk_index": chunk.chunk_index,
                    "language": chunk.language,
                }
                for chunk in document_chunks
            ],
        )
        return ReindexResponse(
            indexed_chunks=len(document_chunks),
            source_files=len({chunk.source_path for chunk in document_chunks}),
            collection_name=self.collection_name,
        )

    def answer(self, request: AssistantRequest) -> AssistantResponse:
        if self.openai_client is None:
            raise HTTPException(
                status_code=500,
                detail="OPENAI_API_KEY is not configured. Set it in your .env file before calling the assistant.",
            )

        collection = self._get_collection()

        if collection.count() == 0:
            self.reindex()

        retrieved_chunks = self.retrieve_context(request.message)
        if not retrieved_chunks:
            raise HTTPException(status_code=503, detail="No indexed application content is available in Chroma DB.")

        context = self._format_context(retrieved_chunks)
        completion = self.openai_client.chat.completions.create(
            model=self.chat_model,
            temperature=0.2,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are an internal product assistant. Answer only from the retrieved application context. "
                        "Use the source snippets to explain product behavior, features, and pricing details when present. "
                        "If the context does not contain the answer, say what is missing and ask one focused follow-up question."
                    ),
                },
                {
                    "role": "user",
                    "content": f"Question: {request.message}\n\nRetrieved context:\n{context}",
                },
            ],
        )

        answer_text = completion.choices[0].message.content or "I could not generate a response."
        return AssistantResponse(
            answer=answer_text.strip(),
            sources=self._unique_sources(retrieved_chunks),
            retrieved_chunks=len(retrieved_chunks),
            model=self.chat_model,
        )

    def retrieve_context(self, question: str, top_k: int = 5) -> list[RetrievedChunk]:
        query_embedding = self._embed_texts([question])[0]
        results = self._get_collection().query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            include=["documents", "metadatas"],
        )

        documents = results.get("documents", [[]])[0]
        metadatas = results.get("metadatas", [[]])[0]
        retrieved_chunks: list[RetrievedChunk] = []

        for document, metadata in zip(documents, metadatas, strict=False):
            if not document or not metadata:
                continue
            retrieved_chunks.append(
                RetrievedChunk(
                    source_path=str(metadata.get("source_path", "unknown")),
                    chunk_index=int(metadata.get("chunk_index", 0)),
                    content=document,
                )
            )

        return retrieved_chunks

    def _embed_texts(self, texts: list[str]) -> list[list[float]]:
        response = self.openai_client.embeddings.create(model=self.embedding_model, input=texts)
        return [item.embedding for item in response.data]

    def _chunk_id(self, chunk: DocumentChunk) -> str:
        return f"{chunk.source_path}:{chunk.chunk_index}"

    def _unique_sources(self, chunks: list[RetrievedChunk]) -> list[str]:
        sources = sorted({chunk.source_path for chunk in chunks})
        return sources

    def _format_context(self, chunks: list[RetrievedChunk]) -> str:
        sections: list[str] = []
        for chunk in chunks:
            sections.append(f"Source: {chunk.source_path}#{chunk.chunk_index}\n{chunk.content}")
        return "\n\n---\n\n".join(sections)

    def _get_collection(self):
        if self.collection is not None:
            return self.collection

        if self.chroma_client is None:
            self.chroma_client = chromadb.HttpClient(host=self.chroma_host, port=self.chroma_port)

        self.collection = self.chroma_client.get_or_create_collection(
            name=self.collection_name,
            metadata={"hnsw:space": "cosine"},
        )
        return self.collection
