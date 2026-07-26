# Product AI Assistant API

This FastAPI service exposes a RAG-based AI assistant focused on product information and pricing.

It scans application files, embeds the content with OpenAI embeddings, stores the vectors in Chroma DB, and retrieves the most relevant chunks before generating an answer.

## Endpoints

- `GET /health` returns service status, OpenAI status, and Chroma indexing status.
- `GET /assistant/sources` summarizes the active source root and indexed chunk count.
- `POST /assistant/reindex` scans the app and stores fresh embeddings in Chroma DB.
- `POST /assistant/chat` retrieves relevant app context from Chroma and sends it to OpenAI.

## Setup

1. Install dependencies with `pip install -r assistant_api/requirements.txt`.
2. Set `OPENAI_API_KEY` in the repository root `.env` file.
3. Start Chroma DB and the assistant with `docker compose -f docker-compose.rag.yml up --build`.
4. Trigger indexing with `POST /assistant/reindex` after the app starts.

## Example request

```bash
curl -X POST http://127.0.0.1:8000/assistant/chat \
  -H "Content-Type: application/json" \
  -d '{"message":"What is the price of the Growth plan?"}'
```

