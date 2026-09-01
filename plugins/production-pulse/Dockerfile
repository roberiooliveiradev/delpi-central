# MFE — consome @delpi/plugin-ui via Module Federation (remote runtime).
# Pré-requisito: container delpi-plugin-ui (profile plugins).

FROM node:20-alpine AS builder

WORKDIR /app

COPY production-pulse/package*.json ./production-pulse/
RUN --mount=type=cache,target=/root/.npm \
    cd production-pulse && npm install

COPY production-pulse ./production-pulse
COPY vite ./vite

WORKDIR /app/production-pulse
RUN npx vite build
RUN node ../vite/verify-federation-react-patch.mjs dist/assets

FROM nginx:alpine AS production

COPY --from=builder /app/production-pulse/dist /usr/share/nginx/html

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
