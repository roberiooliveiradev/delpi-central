# MFE — @delpi/plugin-ui via Module Federation (remote delpi-plugin-ui).
# Doc: plugins/plugin-ui/docs/module-federation.md

FROM node:20-alpine AS builder

WORKDIR /app

COPY cultura-delpi/package*.json ./cultura-delpi/
RUN --mount=type=cache,target=/root/.npm \
    cd cultura-delpi && npm install

COPY cultura-delpi ./cultura-delpi
COPY vite ./vite

WORKDIR /app/cultura-delpi
RUN npm run build

FROM nginx:alpine AS production

COPY --from=builder /app/cultura-delpi/dist /usr/share/nginx/html

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
