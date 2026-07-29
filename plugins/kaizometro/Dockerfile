# MFE — @delpi/plugin-ui via Module Federation (remote delpi-plugin-ui).
# Doc: plugins/plugin-ui/docs/module-federation.md

FROM node:20-alpine AS builder

WORKDIR /app

COPY kaizometro/package*.json ./kaizometro/
RUN --mount=type=cache,target=/root/.npm \
    cd kaizometro && npm install

COPY kaizometro ./kaizometro
COPY vite ./vite

WORKDIR /app/kaizometro
# tsc roda no CI/local; Docker só bundla (MF externaliza @delpi/plugin-ui).
RUN npx vite build

FROM nginx:alpine AS production

COPY --from=builder /app/kaizometro/dist /usr/share/nginx/html

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
