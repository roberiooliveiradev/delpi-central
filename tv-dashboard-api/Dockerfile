FROM python:3.11-slim

WORKDIR /app

COPY tv-dashboard-api/requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

COPY shared /shared
RUN pip install --no-cache-dir -e /shared[fastapi]

COPY tv-dashboard-api /app

ENV PYTHONPATH=/app
ENV TV_DASHBOARD_API_ROOT_PATH=/apps/tv-dashboard-api

EXPOSE 8000

CMD ["python", "-m", "uvicorn", "tv_app.main:app", "--host", "0.0.0.0", "--port", "8000", "--root-path", "/apps/tv-dashboard-api"]
