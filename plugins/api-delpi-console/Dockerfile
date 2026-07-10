# MFE federado — compartilha plugins/vite (federationReactProxyFix, react pin).
# Doc: plugins/plugin-ui/docs/module-federation.md

FROM node:20-alpine AS builder

WORKDIR /app

COPY api-delpi-console/package*.json ./api-delpi-console/
RUN --mount=type=cache,target=/root/.npm \
    cd api-delpi-console && npm install

COPY api-delpi-console ./api-delpi-console
COPY vite ./vite

WORKDIR /app/api-delpi-console
# tsc roda no CI/local; Docker só bundla (vite resolve ../vite).
RUN npx vite build

FROM nginx:alpine AS production

COPY --from=builder /app/api-delpi-console/dist /usr/share/nginx/html

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
