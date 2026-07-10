# MFE — @delpi/plugin-ui via Module Federation (remote delpi-plugin-ui).
# Doc: plugins/plugin-ui/docs/module-federation.md

FROM node:20-alpine AS builder

WORKDIR /app

COPY pedidos-venda-abertos/package*.json ./pedidos-venda-abertos/
RUN --mount=type=cache,target=/root/.npm \
    cd pedidos-venda-abertos && npm install

COPY pedidos-venda-abertos ./pedidos-venda-abertos
# Source plugin-ui — tsconfig paths no build; runtime = remote MF.
COPY plugin-ui ./plugin-ui
COPY vite ./vite

WORKDIR /app/pedidos-venda-abertos
RUN npm run build

FROM nginx:alpine AS production

COPY --from=builder /app/pedidos-venda-abertos/dist /usr/share/nginx/html

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
