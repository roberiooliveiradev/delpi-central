# MFE — consome @delpi/plugin-ui via Module Federation (remote runtime).
# Pré-requisito: container delpi-plugin-ui (profile plugins).

FROM node:20-alpine AS builder

WORKDIR /app

COPY travel-expenses/package*.json ./travel-expenses/
RUN --mount=type=cache,target=/root/.npm \
    cd travel-expenses && npm install

COPY travel-expenses ./travel-expenses
COPY vite ./vite

WORKDIR /app/travel-expenses
RUN npx vite build
RUN node ../vite/verify-federation-react-patch.mjs dist/assets

FROM nginx:alpine AS production

COPY --from=builder /app/travel-expenses/dist /usr/share/nginx/html

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
