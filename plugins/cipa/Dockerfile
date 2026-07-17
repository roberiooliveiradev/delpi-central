# MFE — consome @delpi/plugin-ui via Module Federation (remote runtime).
# Pré-requisito: container delpi-plugin-ui (profile plugins).
# Doc: plugins/plugin-ui/docs/module-federation.md

FROM node:20-alpine AS builder

WORKDIR /app

COPY cipa/package*.json ./cipa/
RUN --mount=type=cache,target=/root/.npm \
    cd cipa && npm install

COPY cipa ./cipa
COPY vite ./vite

WORKDIR /app/cipa
# tsc roda no CI/local; Docker só bundla (MF externaliza @delpi/plugin-ui).
RUN npx vite build
RUN node ../vite/verify-federation-react-patch.mjs dist/assets

FROM nginx:alpine AS production

COPY --from=builder /app/cipa/dist /usr/share/nginx/html

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
