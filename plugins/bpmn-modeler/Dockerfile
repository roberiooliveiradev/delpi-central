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

COPY --from=builder /app/bpmn-modeler/dist /usr/share/nginx/html

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
