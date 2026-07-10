# MFE — @delpi/plugin-ui via Module Federation (remote delpi-plugin-ui).
# Doc: plugins/plugin-ui/docs/module-federation.md

FROM node:20-alpine AS builder

WORKDIR /app

COPY dashboard-quality/package*.json ./dashboard-quality/
RUN --mount=type=cache,target=/root/.npm \
    cd dashboard-quality && npm install

COPY dashboard-quality ./dashboard-quality
COPY vite ./vite

WORKDIR /app/dashboard-quality
RUN npm run build

FROM nginx:alpine AS production

COPY --from=builder /app/dashboard-quality/dist /usr/share/nginx/html

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
