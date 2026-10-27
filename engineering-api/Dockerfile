FROM python:3.11-slim

WORKDIR /app

COPY engineering-api/requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

COPY engineering-api /app

ENV PYTHONPATH=/app
ENV ENGINEERING_API_ROOT_PATH=/apps/engineering-api

EXPOSE 8000

CMD ["sh", "-c", "find /app -type d -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null || true; exec python -m uvicorn engineering_app.main:app --host 0.0.0.0 --port 8000 --root-path /apps/engineering-api"]
