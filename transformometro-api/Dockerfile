FROM python:3.11-slim

WORKDIR /app

COPY transformometro-api/requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

COPY shared /shared
RUN pip install --no-cache-dir -e /shared[fastapi]

COPY transformometro-api /app

ENV PYTHONPATH=/app
ENV TM_API_ROOT_PATH=/apps/transformometro-api

EXPOSE 8000

CMD ["python", "-m", "uvicorn", "tm_app.main:app", "--host", "0.0.0.0", "--port", "8000", "--root-path", "/apps/transformometro-api"]
