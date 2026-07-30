# MFE — consome @delpi/plugin-ui via Module Federation (remote runtime).
# Pré-requisito: container delpi-plugin-ui (profile plugins).
# Doc: plugins/plugin-ui/docs/module-federation.md

FROM node:20-alpine AS builder

WORKDIR /app

COPY comite-etica-conduta/package*.json ./comite-etica-conduta/
RUN --mount=type=cache,target=/root/.npm \
    cd comite-etica-conduta && npm install

COPY comite-etica-conduta ./comite-etica-conduta
COPY vite ./vite

WORKDIR /app/comite-etica-conduta
# tsc roda no CI/local; Docker só bundla (MF externaliza @delpi/plugin-ui).
RUN npx vite build
RUN node ../vite/verify-federation-react-patch.mjs dist/assets

FROM nginx:alpine AS production

COPY --from=builder /app/comite-etica-conduta/dist /usr/share/nginx/html

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
