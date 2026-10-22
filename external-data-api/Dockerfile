FROM python:3.12-slim

WORKDIR /app

COPY external-data-api/requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

COPY shared /shared
RUN pip install --no-cache-dir -e "/shared[flask]"

COPY external-data-api /app

ENV PYTHONPATH=/app
ENV FLASK_APP=app.main:app

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --retries=3 --start-period=15s   CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health')"

CMD ["sh", "-c", "find /app -type d -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null || true; exec gunicorn -b 0.0.0.0:8000 --workers 2 --threads 4 --timeout ${GUNICORN_TIMEOUT_SECONDS:-90} app.main:app"]
