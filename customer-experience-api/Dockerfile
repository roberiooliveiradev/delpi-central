FROM python:3.11-slim

WORKDIR /app

COPY customer-experience-api/requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

COPY shared /shared
RUN pip install --no-cache-dir -e /shared[fastapi]

COPY customer-experience-api /app

ENV PYTHONPATH=/app
ENV CX_API_ROOT_PATH=/apps/customer-experience-api

EXPOSE 8000

CMD ["python", "-m", "uvicorn", "cx_app.main:app", "--host", "0.0.0.0", "--port", "8000", "--root-path", "/apps/customer-experience-api"]
