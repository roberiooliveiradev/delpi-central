# MFE — @delpi/plugin-ui via Module Federation (remote delpi-plugin-ui).
# Doc: plugins/plugin-ui/docs/module-federation.md

FROM node:20-alpine AS builder

WORKDIR /app

COPY financeiro-centro-custo/package*.json ./financeiro-centro-custo/
RUN --mount=type=cache,target=/root/.npm \
    cd financeiro-centro-custo && npm install

COPY financeiro-centro-custo ./financeiro-centro-custo
# Source plugin-ui — tsconfig paths no build; runtime = remote MF.
COPY plugin-ui ./plugin-ui
COPY vite ./vite

WORKDIR /app/financeiro-centro-custo
RUN npm run build

FROM nginx:alpine AS production

COPY --from=builder /app/financeiro-centro-custo/dist /usr/share/nginx/html

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
