FROM python:3.12-slim

WORKDIR /app

COPY supplies-api/requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

COPY shared /shared
RUN pip install --no-cache-dir -e "/shared[flask]"

COPY supplies-api /app

ENV PYTHONPATH=/app
ENV SUPPLIES_API_ROOT_PATH=/apps/supplies-api
ENV FLASK_APP=app.main:app

EXPOSE 8000

CMD ["sh", "-c", "find /app -type d -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null || true; exec gunicorn -b 0.0.0.0:8000 --workers 2 --threads 4 --timeout 60 app.main:app"]
