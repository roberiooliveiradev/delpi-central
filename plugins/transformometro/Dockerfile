# MFE — @delpi/plugin-ui via Module Federation (remote delpi-plugin-ui).
# Doc: plugins/plugin-ui/docs/module-federation.md

FROM node:20-alpine AS builder

WORKDIR /app

COPY transformometro-meeting-minutes-presentation/package*.json ./transformometro-meeting-minutes-presentation/
COPY transformometro-meeting-minutes-presentation/.npmrc ./transformometro-meeting-minutes-presentation/
RUN --mount=type=cache,target=/root/.npm \
    cd transformometro-meeting-minutes-presentation && npm install --omit=peer

COPY transformometro-meeting-minutes-presentation ./transformometro-meeting-minutes-presentation

COPY transformometro/package*.json ./transformometro/
RUN --mount=type=cache,target=/root/.npm \
    cd transformometro && npm install

COPY transformometro ./transformometro
COPY vite ./vite

WORKDIR /app/transformometro
# tsc roda no CI/local; Docker só bundla (MF externaliza @delpi/plugin-ui).
RUN npx vite build

FROM nginx:alpine AS production

COPY --from=builder /app/transformometro/dist /usr/share/nginx/html

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
