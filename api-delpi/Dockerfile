# -----------------
# api-delpi - DOCKERFILE
# -----------------
FROM python:3.11-slim

WORKDIR /app

# 🔧 Dependências do sistema
RUN apt-get update && apt-get install -y \
    curl \
    gnupg \
    ca-certificates \
    unixodbc \
    unixodbc-dev \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# 🔐 Chave Microsoft
RUN curl -fsSL https://packages.microsoft.com/keys/microsoft.asc | \
    gpg --dearmor -o /usr/share/keyrings/microsoft-prod.gpg

# 🔐 Repo Microsoft
RUN echo "deb [signed-by=/usr/share/keyrings/microsoft-prod.gpg] https://packages.microsoft.com/debian/12/prod bookworm main" \
    > /etc/apt/sources.list.d/mssql-release.list

# 🔧 Driver SQL Server
RUN apt-get update && ACCEPT_EULA=Y apt-get install -y msodbcsql18 \
    && rm -rf /var/lib/apt/lists/*

# 🔧 Copiar requirements da api-delpi (não do core!)
COPY api-delpi/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 🔥 Copiar shared (sem barra inicial!)
COPY shared /shared
RUN pip install -e /shared

# 🔧 Copiar código da api-delpi
COPY api-delpi /app

EXPOSE 8000

# 🔥 Melhor forma de executar
CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--root-path", "/apps/api-delpi"]