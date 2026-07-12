# MFE — @delpi/plugin-ui via Module Federation (remote delpi-plugin-ui).
# Doc: plugins/plugin-ui/docs/module-federation.md

FROM node:20-alpine AS builder

WORKDIR /app
COPY tv-dashboard-presentation/package*.json ./tv-dashboard-presentation/
COPY tv-dashboard-presentation/.npmrc ./tv-dashboard-presentation/
RUN --mount=type=cache,target=/root/.npm \
    cd tv-dashboard-presentation && npm install --omit=peer

COPY tv-dashboard-presentation ./tv-dashboard-presentation


COPY tv-dashboard/package*.json ./tv-dashboard/
RUN --mount=type=cache,target=/root/.npm \
    cd tv-dashboard && npm install

COPY tv-dashboard ./tv-dashboard
COPY vite ./vite

WORKDIR /app/tv-dashboard
# tsc roda no CI/local; Docker só bundla (MF externaliza @delpi/plugin-ui).
RUN npx vite build

FROM nginx:alpine AS production

COPY --from=builder /app/tv-dashboard/dist /usr/share/nginx/html

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
