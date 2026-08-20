FROM python:3.11-slim

WORKDIR /app

COPY production-control-api/requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

COPY shared /shared
RUN pip install --no-cache-dir -e /shared[fastapi]

COPY production-control-api /app

ENV PYTHONPATH=/app
ENV PC_API_ROOT_PATH=/apps/production-control-api

EXPOSE 8000

CMD ["python", "-m", "uvicorn", "production_control_app.main:app", "--host", "0.0.0.0", "--port", "8000", "--root-path", "/apps/production-control-api"]
