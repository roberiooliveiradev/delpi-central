# MFE — @delpi/plugin-ui via Module Federation (remote delpi-plugin-ui).
# Doc: plugins/plugin-ui/docs/module-federation.md

FROM node:20-alpine AS builder

WORKDIR /app

COPY propostas-comerciais/package*.json ./propostas-comerciais/
RUN --mount=type=cache,target=/root/.npm \
    cd propostas-comerciais && npm install

COPY propostas-comerciais ./propostas-comerciais
COPY vite ./vite

WORKDIR /app/propostas-comerciais
# tsc roda no CI/local; Docker só bundla (MF externaliza @delpi/plugin-ui).
RUN npx vite build

FROM nginx:alpine AS production

COPY --from=builder /app/propostas-comerciais/dist /usr/share/nginx/html

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
