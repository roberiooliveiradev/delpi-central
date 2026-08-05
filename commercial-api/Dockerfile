FROM python:3.11-slim

WORKDIR /app

COPY commercial-api/requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

COPY shared /shared
RUN pip install --no-cache-dir -e /shared[fastapi]

COPY commercial-api /app

ENV PYTHONPATH=/app
ENV COMMERCIAL_API_ROOT_PATH=/apps/commercial-api

EXPOSE 8000

CMD ["sh", "-c", "find /app -type d -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null || true; exec python -m uvicorn commercial_app.main:app --host 0.0.0.0 --port 8000 --root-path /apps/commercial-api"]
