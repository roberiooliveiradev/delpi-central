# MFE — @delpi/plugin-ui via Module Federation (remote delpi-plugin-ui).
# Doc: plugins/plugin-ui/docs/module-federation.md

FROM node:20-alpine AS builder

WORKDIR /app

COPY dashboard-financial/package*.json ./dashboard-financial/
RUN --mount=type=cache,target=/root/.npm \
    cd dashboard-financial && npm install

COPY dashboard-financial ./dashboard-financial
COPY vite ./vite

WORKDIR /app/dashboard-financial
RUN npm run build

FROM nginx:alpine AS production

COPY --from=builder /app/dashboard-financial/dist /usr/share/nginx/html

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
