# MFE — consome @delpi/plugin-ui via Module Federation (remote runtime).
# Pré-requisito: container delpi-plugin-ui (profile plugins).
# Doc: plugins/plugin-ui/docs/module-federation.md

FROM node:20-alpine AS builder

WORKDIR /app

COPY codigo-etica/package*.json ./codigo-etica/
RUN --mount=type=cache,target=/root/.npm \
    cd codigo-etica && npm install

COPY codigo-etica ./codigo-etica
COPY vite ./vite

WORKDIR /app/codigo-etica
# tsc roda no CI/local; Docker só bundla (MF externaliza @delpi/plugin-ui).
RUN npx vite build
RUN node ../vite/verify-federation-react-patch.mjs dist/assets

FROM nginx:alpine AS production

COPY --from=builder /app/codigo-etica/dist /usr/share/nginx/html
COPY codigo-etica/nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
