FROM python:3.11-slim

WORKDIR /app

COPY bpmn-modeler/requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

COPY shared /shared
RUN pip install --no-cache-dir -e /shared[fastapi]

COPY bpmn-modeler /app

ENV PYTHONPATH=/app
ENV BPMN_MODELER_API_ROOT_PATH=/apps/bpmn-modeler-api

EXPOSE 8000

CMD ["python", "-m", "uvicorn", "bpmn_modeler.main:app", "--host", "0.0.0.0", "--port", "8000", "--root-path", "/apps/bpmn-modeler-api"]
