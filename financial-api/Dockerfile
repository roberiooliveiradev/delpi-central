FROM python:3.11-slim

WORKDIR /app

COPY financial-api/requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

COPY shared /shared
RUN pip install --no-cache-dir -e /shared[fastapi]

COPY financial-api /app

ENV PYTHONPATH=/app
ENV FIN_API_ROOT_PATH=/apps/financial-api

EXPOSE 8000

CMD ["python", "-m", "uvicorn", "financial_app.main:app", "--host", "0.0.0.0", "--port", "8000", "--root-path", "/apps/financial-api"]
