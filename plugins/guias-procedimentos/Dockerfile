# MFE — consome @delpi/plugin-ui via Module Federation (remote runtime).
# Pré-requisito: container delpi-plugin-ui (profile plugins).
# Doc: plugins/plugin-ui/docs/module-federation.md

FROM node:20-alpine AS builder

WORKDIR /app

COPY guias-procedimentos/package*.json ./guias-procedimentos/
RUN --mount=type=cache,target=/root/.npm \
    cd guias-procedimentos && npm install

COPY guias-procedimentos ./guias-procedimentos
COPY vite ./vite

WORKDIR /app/guias-procedimentos
# tsc roda no CI/local; Docker só bundla (MF externaliza @delpi/plugin-ui).
RUN npx vite build

FROM nginx:alpine AS production

COPY guias-procedimentos/nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=builder /app/guias-procedimentos/dist /usr/share/nginx/html

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
