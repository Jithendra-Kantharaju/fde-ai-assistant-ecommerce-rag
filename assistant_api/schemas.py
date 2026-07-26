from __future__ import annotations

from pydantic import BaseModel, Field


class AssistantRequest(BaseModel):
    message: str = Field(min_length=1, description="Customer question about products or pricing")


class ProductItem(BaseModel):
    name: str
    description: str
    price: str
    billing_period: str
    features: list[str]
    keywords: list[str]


class AssistantResponse(BaseModel):
    answer: str
    sources: list[str]
    retrieved_chunks: int
    model: str


class ReindexResponse(BaseModel):
    indexed_chunks: int
    source_files: int
    collection_name: str


class SourceResponse(BaseModel):
    source_root: str
    collection_name: str
    indexed_chunks: int


class HealthResponse(BaseModel):
    status: str
    openai_key_configured: bool
    chroma_connected: bool
    indexed_chunks: int
    model: str
    collection_name: str

