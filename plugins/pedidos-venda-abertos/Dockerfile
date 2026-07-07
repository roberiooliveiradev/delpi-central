FROM node:20-alpine AS builder

WORKDIR /app

COPY plugin-ui/package*.json ./plugin-ui/
RUN cd plugin-ui && npm install

COPY pedidos-venda-abertos/package*.json ./pedidos-venda-abertos/
RUN cd pedidos-venda-abertos && npm install

COPY plugin-ui ./plugin-ui
COPY pedidos-venda-abertos ./pedidos-venda-abertos

WORKDIR /app/pedidos-venda-abertos
RUN npm run build

FROM nginx:alpine

COPY --from=builder /app/pedidos-venda-abertos/dist /usr/share/nginx/html

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
