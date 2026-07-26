from __future__ import annotations

import os

from dotenv import load_dotenv
from fastapi import HTTPException
from openai import OpenAI

from .catalog import ProductRecord, find_relevant_products, render_catalog
from .schemas import AssistantRequest, AssistantResponse, HealthResponse


class ProductAssistantService:
    def __init__(self) -> None:
        load_dotenv()
        self.model = os.getenv("OPENAI_MODEL", "gpt-4.1-mini")
        api_key = os.getenv("OPENAI_API_KEY", "").strip()
        if not api_key or api_key == "your_openai_api_key_here":
            self.client: OpenAI | None = None
        else:
            self.client = OpenAI(api_key=api_key)

    def health(self) -> HealthResponse:
        return HealthResponse(
            status="ok",
            openai_key_configured=self.client is not None,
            model=self.model,
        )

    def list_products(self) -> list[ProductRecord]:
        return list(find_relevant_products("pricing"))

    def answer(self, request: AssistantRequest) -> AssistantResponse:
        if self.client is None:
            raise HTTPException(
                status_code=500,
                detail="OPENAI_API_KEY is not configured. Set it in your .env file before calling the assistant.",
            )

        matched_products = find_relevant_products(request.message)
        catalog_text = render_catalog(matched_products)

        completion = self.client.chat.completions.create(
            model=self.model,
            temperature=0.2,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a product assistant. Answer only with product information from the provided catalog. "
                        "Focus on pricing, plan comparisons, and practical product guidance. "
                        "If the catalog does not contain the answer, say what is missing and ask one clarifying question."
                    ),
                },
                {
                    "role": "user",
                    "content": (
                        f"Customer question: {request.message}\n\n"
                        f"Catalog:\n{catalog_text}\n\n"
                        "When the user asks about pricing, quote the exact product price and billing period."
                    ),
                },
            ],
        )

        answer_text = completion.choices[0].message.content or "I could not generate a response."
        return AssistantResponse(
            answer=answer_text.strip(),
            matched_products=[product.name for product in matched_products],
            model=self.model,
        )
