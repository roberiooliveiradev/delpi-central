# MFE — @delpi/plugin-ui via Module Federation (remote delpi-plugin-ui).
# Doc: plugins/plugin-ui/docs/module-federation.md

FROM node:20-alpine AS builder

WORKDIR /app

COPY inspecoes-entrada/package*.json ./inspecoes-entrada/
RUN --mount=type=cache,target=/root/.npm \
    cd inspecoes-entrada && npm install

COPY inspecoes-entrada ./inspecoes-entrada
COPY vite ./vite

WORKDIR /app/inspecoes-entrada
RUN npm run build

FROM nginx:alpine AS production

COPY --from=builder /app/inspecoes-entrada/dist /usr/share/nginx/html

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
