# MFE — consome @delpi/plugin-ui via Module Federation (remote runtime).
# Pré-requisito: container delpi-plugin-ui (profile plugins).

FROM node:20-alpine AS builder

WORKDIR /app

COPY purchase-requests/package*.json ./purchase-requests/
RUN --mount=type=cache,target=/root/.npm \
    cd purchase-requests && npm install

COPY purchase-requests ./purchase-requests
COPY vite ./vite

WORKDIR /app/purchase-requests
RUN npx vite build
RUN node ../vite/verify-federation-react-patch.mjs dist/assets

FROM nginx:alpine AS production

COPY --from=builder /app/purchase-requests/dist /usr/share/nginx/html

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
