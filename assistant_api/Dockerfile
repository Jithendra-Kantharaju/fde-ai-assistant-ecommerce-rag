FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY assistant_api/requirements.txt /app/assistant_api/requirements.txt
RUN pip install --no-cache-dir -r /app/assistant_api/requirements.txt

COPY assistant_api /app/assistant_api

EXPOSE 8000

CMD ["uvicorn", "assistant_api.main:app", "--host", "0.0.0.0", "--port", "8000"]
