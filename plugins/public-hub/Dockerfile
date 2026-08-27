# Shell público (/p/) — splash/styles via MF; assinatura bundled do kit (fatia signature).
# Doc: plugins/plugin-ui/docs/module-federation.md · public-hub/README.md

FROM node:20-alpine AS builder

WORKDIR /app

COPY tv-dashboard-presentation/package*.json ./tv-dashboard-presentation/
COPY tv-dashboard-presentation/.npmrc ./tv-dashboard-presentation/
RUN --mount=type=cache,target=/root/.npm \
    cd tv-dashboard-presentation && npm install --omit=peer

COPY tv-dashboard-presentation ./tv-dashboard-presentation

COPY transformometro-meeting-minutes-presentation/package*.json ./transformometro-meeting-minutes-presentation/
COPY transformometro-meeting-minutes-presentation/.npmrc ./transformometro-meeting-minutes-presentation/
RUN --mount=type=cache,target=/root/.npm \
    cd transformometro-meeting-minutes-presentation && npm install --omit=peer

COPY transformometro-meeting-minutes-presentation ./transformometro-meeting-minutes-presentation

COPY cipa-meeting-minutes-presentation/package*.json ./cipa-meeting-minutes-presentation/
COPY cipa-meeting-minutes-presentation/.npmrc ./cipa-meeting-minutes-presentation/
RUN --mount=type=cache,target=/root/.npm \
    cd cipa-meeting-minutes-presentation && npm install --omit=peer

COPY cipa-meeting-minutes-presentation ./cipa-meeting-minutes-presentation

COPY public-hub/package*.json ./public-hub/
RUN --mount=type=cache,target=/root/.npm \
    cd public-hub && npm install

COPY public-hub ./public-hub
COPY vite ./vite
# @delpi/signature-kit → plugin-ui/src/components/signature (+ overlayLayers).
# Não COPY do plugin-ui inteiro — só a fatia usada no /sign (evita HelpTooltip/MF).
COPY plugin-ui/src/components/signature ./plugin-ui/src/components/signature
COPY plugin-ui/src/overlayLayers.ts ./plugin-ui/src/overlayLayers.ts

WORKDIR /app/public-hub
# tsc roda no CI/local; Docker bundla signature-kit + MF styles/splash.
RUN npx vite build

FROM nginx:alpine AS production

COPY --from=builder /app/public-hub/dist /usr/share/nginx/html
COPY public-hub/nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
