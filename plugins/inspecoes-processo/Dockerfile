# MFE — @delpi/plugin-ui via Module Federation (remote delpi-plugin-ui).
# Doc: plugins/plugin-ui/docs/module-federation.md

FROM node:20-alpine AS builder

WORKDIR /app

COPY inspecoes-processo/package*.json ./inspecoes-processo/
RUN --mount=type=cache,target=/root/.npm \
    cd inspecoes-processo && npm install

COPY inspecoes-processo ./inspecoes-processo
COPY vite ./vite

WORKDIR /app/inspecoes-processo
# tsc roda no CI/local; Docker só bundla (MF externaliza @delpi/plugin-ui).
RUN npx vite build

FROM nginx:alpine AS production

COPY --from=builder /app/inspecoes-processo/dist /usr/share/nginx/html

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
