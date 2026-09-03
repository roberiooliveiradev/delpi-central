# MFE — consome @delpi/plugin-ui via Module Federation (remote runtime).
# Pré-requisito: container delpi-plugin-ui (profile plugins).

FROM node:20-alpine AS builder

WORKDIR /app

COPY my-requests/package*.json ./my-requests/
RUN --mount=type=cache,target=/root/.npm \
    cd my-requests && npm install

COPY my-requests ./my-requests
COPY vite ./vite

WORKDIR /app/my-requests
RUN npx vite build
RUN node ../vite/verify-federation-react-patch.mjs dist/assets

FROM nginx:alpine AS production

COPY --from=builder /app/my-requests/dist /usr/share/nginx/html

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
