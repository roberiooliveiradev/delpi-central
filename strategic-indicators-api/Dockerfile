# strategic-indicators-api — cópia funcional do pacote ``app`` da api-delpi como ``si_app``.
FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    curl \
    gnupg \
    ca-certificates \
    unixodbc \
    unixodbc-dev \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

RUN curl -fsSL https://packages.microsoft.com/keys/microsoft.asc | \
    gpg --dearmor -o /usr/share/keyrings/microsoft-prod.gpg

RUN echo "deb [signed-by=/usr/share/keyrings/microsoft-prod.gpg] https://packages.microsoft.com/debian/12/prod bookworm main" \
    > /etc/apt/sources.list.d/mssql-release.list

RUN apt-get update && ACCEPT_EULA=Y apt-get install -y msodbcsql18 \
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
