# MFE — @delpi/plugin-ui via Module Federation (remote delpi-plugin-ui).
# Doc: plugins/plugin-ui/docs/module-federation.md

FROM node:20-alpine AS builder

WORKDIR /app

COPY bpmn-modeler/package*.json ./bpmn-modeler/
RUN --mount=type=cache,target=/root/.npm \
    cd bpmn-modeler && npm install

COPY bpmn-modeler ./bpmn-modeler
COPY vite ./vite

WORKDIR /app/bpmn-modeler
# tsc roda no CI/local; Docker só bundla (MF externaliza @delpi/plugin-ui).
RUN npx vite build

FROM nginx:alpine AS production

ARG BUILD_SHA=unknown
ARG BUILD_TIME=unknown

LABEL org.opencontainers.image.title="delpi-bpmn-modeler" \
      org.opencontainers.image.source="delpi-central/plugins/bpmn-modeler" \
      org.opencontainers.image.revision="${BUILD_SHA}"

COPY --from=builder /app/bpmn-modeler/dist /usr/share/nginx/html

# Provenance do bundle servido — consultavel via /apps/bpmn-modeler/assets/build-info.json.
RUN printf '{"service":"bpmn-modeler","git_sha":"%s","built_at":"%s"}\n' \
      "$BUILD_SHA" "$BUILD_TIME" \
      > /usr/share/nginx/html/assets/build-info.json

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
