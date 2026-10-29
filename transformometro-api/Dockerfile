# ---- layout bundle stage: canonical Organizar pipeline (elkjs +
# plugins/bpmn-editor/src/layout) compiled once at image build — runtime
# executes the SAME implementation the Portal editor uses, no port. ----
FROM node:20-slim AS bpmn_layout_bundle
WORKDIR /build
COPY transformometro-api/vendor/bpmn-layout/package.json \
     transformometro-api/vendor/bpmn-layout/package-lock.json \
     transformometro-api/vendor/bpmn-layout/build.mjs vendor/
RUN cd vendor && npm ci
COPY plugins/bpmn-editor/src/layout src_layout
RUN cd vendor && LAYOUT_SRC=/build/src_layout node build.mjs

FROM node:20-slim AS node_runtime

FROM python:3.11-slim

WORKDIR /app

# Node runtime (glibc) + canonical layout bundle — server-side Organizar.
COPY --from=node_runtime /usr/local/bin/node /usr/local/bin/node
COPY --from=bpmn_layout_bundle /build/vendor/out/organize.cjs \
    /app/vendor/bpmn-layout/organize.cjs

COPY transformometro-api/requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

COPY shared /shared
RUN pip install --no-cache-dir -e /shared[fastapi]

COPY transformometro-api /app

ENV PYTHONPATH=/app
ENV TM_API_ROOT_PATH=/apps/transformometro-api

EXPOSE 8000

CMD ["python", "-m", "uvicorn", "tm_app.main:app", "--host", "0.0.0.0", "--port", "8000", "--root-path", "/apps/transformometro-api"]
