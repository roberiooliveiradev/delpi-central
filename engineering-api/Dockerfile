FROM python:3.11-slim

WORKDIR /app

COPY engineering-api/requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

# EVA drawing R7 — extras visuais (OpenCV/PaddleOCR) são OPT-IN:
# docker build --build-arg INSTALL_VISION_EXTRAS=true. Ausentes, os
# adapters respondem provider_unavailable/model_not_provisioned
# (fail-closed) e o perfil approved_local_visual_ocr fica gated.
ARG INSTALL_VISION_EXTRAS=false
COPY engineering-api/requirements-vision.txt /tmp/requirements-vision.txt
RUN if [ "$INSTALL_VISION_EXTRAS" = "true" ]; then \
      apt-get update && apt-get install -y --no-install-recommends libgomp1 libglib2.0-0 \
        && rm -rf /var/lib/apt/lists/*; \
      pip install --no-cache-dir -r /tmp/requirements-vision.txt; \
      # R7.2 — deps do paddle arrastam opencv-python (precisa libGL);
      # reimpor a variante headless por último, sem re-baixar deps.
      pip install --no-cache-dir --force-reinstall --no-deps opencv-python-headless==4.10.0.84; \
    fi

COPY shared /shared
RUN pip install --no-cache-dir -e "/shared[fastapi]"

COPY engineering-api /app

ENV PYTHONPATH=/app
ENV ENGINEERING_API_ROOT_PATH=/apps/engineering-api

EXPOSE 8000

# R9.9 — SLANet persistente via volume /opt/ocr-models/paddlex (provisioning
# governado, sem docker cp; symlink baked → modelo disponível pós-build/recreate).
RUN mkdir -p /root/.paddlex \
    && ln -sfn /opt/ocr-models/paddlex /root/.paddlex/official_models

CMD ["sh", "-c", "find /app -type d -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null || true; exec python -m uvicorn engineering_app.main:app --host 0.0.0.0 --port 8000 --root-path /apps/engineering-api"]
