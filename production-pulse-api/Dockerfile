FROM python:3.11-slim

WORKDIR /app

COPY production-pulse-api/requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

COPY shared /shared
RUN pip install --no-cache-dir -e /shared[fastapi]

COPY production-pulse-api /app

ENV PYTHONPATH=/app
ENV PRODUCTION_PULSE_API_ROOT_PATH=/apps/production-pulse-api

EXPOSE 8000

CMD ["sh", "-c", "find /app -type d -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null || true; exec python -m uvicorn production_pulse_app.main:app --host 0.0.0.0 --port ${PORT:-8000} --root-path /apps/production-pulse-api"]
