# Minimal, unprivileged, read-only Linux Operations MCP image.
# The image contains only shared auth/MCP packages and this adapter, no host tools.
FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app
WORKDIR /app
COPY linux-ops-mcp/requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt
COPY shared /opt/delpi-shared
RUN pip install --no-cache-dir /opt/delpi-shared
COPY linux-ops-mcp/linux_ops_mcp /app/linux_ops_mcp
RUN groupadd --system --gid 10001 mcpuser \
    && useradd --system --uid 10001 --gid 10001 --no-create-home mcpuser \
    && chown -R root:root /app /opt/delpi-shared
USER 10001:10001
EXPOSE 8000
CMD ["uvicorn", "linux_ops_mcp.asgi:app", "--host", "0.0.0.0", "--port", "8000", "--no-server-header"]
