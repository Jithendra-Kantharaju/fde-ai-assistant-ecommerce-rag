from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .rag import RagAssistantService
from .schemas import AssistantRequest, AssistantResponse, HealthResponse, ReindexResponse, SourceResponse

app = FastAPI(title="Product AI Assistant", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:4200",
        "http://127.0.0.1:4200",
        "http://localhost:8001",
        "http://127.0.0.1:8001",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
service = RagAssistantService()


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return service.health()


@app.get("/assistant/sources", response_model=SourceResponse)
def sources() -> SourceResponse:
    return service.source_summary()


@app.post("/assistant/reindex", response_model=ReindexResponse)
def reindex() -> ReindexResponse:
    return service.reindex()


@app.post("/assistant/chat", response_model=AssistantResponse)
def chat(request: AssistantRequest) -> AssistantResponse:
    return service.answer(request)

