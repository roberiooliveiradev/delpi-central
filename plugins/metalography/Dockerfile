# MFE — @delpi/plugin-ui via Module Federation (remote delpi-plugin-ui).

FROM node:20-alpine AS builder

WORKDIR /app

COPY metalography/package*.json ./metalography/
RUN --mount=type=cache,target=/root/.npm \
    cd metalography && npm install

COPY metalography ./metalography
COPY vite ./vite

WORKDIR /app/metalography
RUN npx vite build

FROM nginx:alpine AS production

COPY --from=builder /app/metalography/dist /usr/share/nginx/html

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
