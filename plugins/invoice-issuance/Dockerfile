# MFE — @delpi/plugin-ui via Module Federation (remote delpi-plugin-ui).
# Doc: plugins/plugin-ui/docs/module-federation.md

FROM node:20-alpine AS builder

WORKDIR /app

COPY invoice-issuance/package*.json ./invoice-issuance/
RUN --mount=type=cache,target=/root/.npm \
    cd invoice-issuance && npm install

COPY invoice-issuance ./invoice-issuance
COPY vite ./vite

WORKDIR /app/invoice-issuance
# tsc roda no CI/local; Docker só bundla (MF externaliza @delpi/plugin-ui).
RUN npx vite build

FROM nginx:alpine AS production

COPY invoice-issuance/nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=builder /app/invoice-issuance/dist /usr/share/nginx/html

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
