from __future__ import annotations

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace

from fastapi.testclient import TestClient

from assistant_api.main import app
from assistant_api.rag import RagAssistantService


class FakeEmbeddings:
    def create(self, model: str, input: list[str]) -> SimpleNamespace:
        return SimpleNamespace(
            data=[SimpleNamespace(embedding=[float(len(text)), 0.0, 1.0]) for text in input]
        )


class FakeChatCompletions:
    def create(self, model: str, temperature: float, messages: list[dict[str, str]]) -> SimpleNamespace:
        user_message = messages[-1]["content"]
        return SimpleNamespace(
            choices=[SimpleNamespace(message=SimpleNamespace(content=f"Grounded answer: {user_message}"))]
        )


class FakeChat:
    def __init__(self) -> None:
        self.completions = FakeChatCompletions()


class FakeOpenAIClient:
    def __init__(self) -> None:
        self.embeddings = FakeEmbeddings()
        self.chat = FakeChat()


class FakeCollection:
    def __init__(self) -> None:
        self.rows: list[dict[str, object]] = []

    def count(self) -> int:
        return len(self.rows)

    def upsert(self, ids, documents, embeddings, metadatas) -> None:
        for row_id, document, embedding, metadata in zip(ids, documents, embeddings, metadatas, strict=False):
            self.rows.append(
                {
                    "id": row_id,
                    "document": document,
                    "embedding": embedding,
                    "metadata": metadata,
                }
            )

    def query(self, query_embeddings, n_results, include):
        top_rows = self.rows[:n_results]
        return {
            "documents": [[row["document"] for row in top_rows]],
            "metadatas": [[row["metadata"] for row in top_rows]],
        }


class RagServiceTests(unittest.TestCase):
    def test_reindex_scans_app_files_and_populates_collection(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "README.md").write_text("This app has a pricing page and a checkout flow.")
            (root / "app.ts").write_text("export const price = '49';")

            collection = FakeCollection()
            service = RagAssistantService(
                source_root=root,
                openai_client=FakeOpenAIClient(),
                chroma_collection=collection,
            )

            result = service.reindex()

            self.assertEqual(result.indexed_chunks, 2)
            self.assertEqual(result.source_files, 2)
            self.assertEqual(collection.count(), 2)


class AssistantApiTests(unittest.TestCase):
    def setUp(self) -> None:
        self._original_service = app.dependency_overrides.copy()
        self.fake_collection = FakeCollection()
        self.fake_service = RagAssistantService(
            source_root=Path(__file__).resolve().parents[2],
            openai_client=FakeOpenAIClient(),
            chroma_collection=self.fake_collection,
        )
        self.fake_service.reindex = lambda: SimpleNamespace(
            indexed_chunks=0,
            source_files=0,
            collection_name="product_assistant",
        )
        self.fake_service.health = lambda: SimpleNamespace(
            status="ok",
            openai_key_configured=True,
            chroma_connected=True,
            indexed_chunks=0,
            model="gpt-4.1-mini",
            collection_name="product_assistant",
        )
        self.fake_service.source_summary = lambda: SimpleNamespace(
            source_root=".",
            collection_name="product_assistant",
            indexed_chunks=0,
        )

        import assistant_api.main as main_module

        self._main_module = main_module
        self._previous_service = main_module.service
        main_module.service = self.fake_service
        self.client = TestClient(app)

    def tearDown(self) -> None:
        import assistant_api.main as main_module

        main_module.service = self._previous_service
        app.dependency_overrides = self._original_service

    def test_health_route_reports_configuration(self) -> None:
        response = self.client.get("/health")

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["status"], "ok")
        self.assertTrue(body["chroma_connected"])
        self.assertIn("indexed_chunks", body)

    def test_reindex_route_populates_collection(self) -> None:
        response = self.client.post("/assistant/reindex")

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertIn("indexed_chunks", body)

    def test_chat_route_uses_retrieved_context(self) -> None:
        self.fake_collection.rows.append(
            {
                "id": "README.md:0",
                "document": "The app includes a pricing page for the Pro plan.",
                "embedding": [1.0, 0.0, 0.0],
                "metadata": {"source_path": "README.md", "chunk_index": 0},
            }
        )

        response = self.client.post("/assistant/chat", json={"message": "What pricing info exists?"})

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertIn("Grounded answer", body["answer"])
        self.assertEqual(body["retrieved_chunks"], 1)
        self.assertIn("README.md", body["sources"])


if __name__ == "__main__":
    unittest.main()
