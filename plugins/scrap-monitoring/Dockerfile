# MFE — consome @delpi/plugin-ui via Module Federation (remote runtime).
# Pré-requisito: container delpi-plugin-ui (profile plugins).
# Doc: plugins/plugin-ui/docs/module-federation.md

FROM node:20-alpine AS builder

WORKDIR /app

COPY scrap-monitoring/package*.json ./scrap-monitoring/
RUN --mount=type=cache,target=/root/.npm \
    cd scrap-monitoring && npm install

COPY scrap-monitoring ./scrap-monitoring
COPY vite ./vite

WORKDIR /app/scrap-monitoring
# tsc roda no CI/local; Docker só bundla (MF externaliza @delpi/plugin-ui).
RUN npx vite build
RUN node ../vite/verify-federation-react-patch.mjs dist/assets

FROM nginx:alpine AS production

COPY --from=builder /app/scrap-monitoring/dist /usr/share/nginx/html

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
