# strategic-indicators-api — serviço dedicado ao painel de indicadores estratégicos.
FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY strategic-indicators-api/requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

COPY shared /shared
RUN pip install --no-cache-dir -e /shared[fastapi]

COPY strategic-indicators-api /app

ENV PYTHONPATH=/app
ENV SI_API_ROOT_PATH=/apps/strategic-indicators-api

EXPOSE 8000

CMD ["python", "-m", "uvicorn", "si_app.main:app", "--host", "0.0.0.0", "--port", "8000", "--root-path", "/apps/strategic-indicators-api"]
