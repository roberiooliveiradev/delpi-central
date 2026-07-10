# MFE — @delpi/plugin-ui via Module Federation (remote delpi-plugin-ui).
# Doc: plugins/plugin-ui/docs/module-federation.md

FROM node:20-alpine AS builder

WORKDIR /app

COPY dashboard-engineering/package*.json ./dashboard-engineering/
RUN --mount=type=cache,target=/root/.npm \
    cd dashboard-engineering && npm install

COPY dashboard-engineering ./dashboard-engineering
COPY vite ./vite

WORKDIR /app/dashboard-engineering
RUN npm run build

FROM nginx:alpine AS production

COPY --from=builder /app/dashboard-engineering/dist /usr/share/nginx/html

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
