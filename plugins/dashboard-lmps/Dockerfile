# MFE — @delpi/plugin-ui via Module Federation (remote delpi-plugin-ui).
# Doc: plugins/plugin-ui/docs/module-federation.md

FROM node:20-alpine AS builder

WORKDIR /app

COPY dashboard-lmps/package*.json ./dashboard-lmps/
RUN --mount=type=cache,target=/root/.npm \
    cd dashboard-lmps && npm install

COPY dashboard-lmps ./dashboard-lmps
COPY vite ./vite

WORKDIR /app/dashboard-lmps
# tsc roda no CI/local; Docker só bundla (MF externaliza @delpi/plugin-ui).
RUN npx vite build

FROM nginx:alpine AS production

COPY --from=builder /app/dashboard-lmps/dist /usr/share/nginx/html

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
