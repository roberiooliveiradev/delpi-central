FROM node:20-alpine AS builder

WORKDIR /app

COPY plugin-ui/package*.json ./plugin-ui/
RUN cd plugin-ui && npm install

COPY financeiro-centro-custo/package*.json ./financeiro-centro-custo/
RUN cd financeiro-centro-custo && npm install

COPY plugin-ui ./plugin-ui
COPY financeiro-centro-custo ./financeiro-centro-custo

WORKDIR /app/financeiro-centro-custo
RUN npm run build

FROM nginx:alpine

COPY --from=builder /app/financeiro-centro-custo/dist /usr/share/nginx/html

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
