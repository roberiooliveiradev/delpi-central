FROM python:3.11-slim

WORKDIR /app

COPY tv-dashboard-api/requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

COPY shared /shared
RUN pip install --no-cache-dir -e /shared[fastapi]

COPY tv-dashboard-api /app

# Gerador do catálogo TV (OpenAPI → tv_data_routes.json) — sync no startup / POST /data/openapi/sync
COPY scripts/generate_tv_data_routes_from_openapi.py /app/tools/generate_tv_data_routes_from_openapi.py

ENV PYTHONPATH=/app
ENV TV_DASHBOARD_API_ROOT_PATH=/apps/tv-dashboard-api
ENV TV_OPENAPI_GENERATOR_SCRIPT=/app/tools/generate_tv_data_routes_from_openapi.py
ENV TV_DATA_ROUTES_PATH=/app/data/tv-dashboard/catalog/tv_data_routes.json
ENV TV_OPENAPI_SYNC_ON_STARTUP=true

EXPOSE 8000

CMD ["python", "-m", "uvicorn", "tv_app.main:app", "--host", "0.0.0.0", "--port", "8000", "--root-path", "/apps/tv-dashboard-api"]
