FROM python:3.11-slim

WORKDIR /app

COPY maintenance-api/requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

COPY shared /shared
RUN pip install --no-cache-dir -e /shared[fastapi]

COPY maintenance-api /app

ENV PYTHONPATH=/app
ENV MAINT_API_ROOT_PATH=/apps/maintenance-api

EXPOSE 8000

CMD ["python", "-m", "uvicorn", "maint_app.main:app", "--host", "0.0.0.0", "--port", "8000", "--root-path", "/apps/maintenance-api"]
