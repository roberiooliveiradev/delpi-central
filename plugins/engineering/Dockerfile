# MFE — consome @delpi/plugin-ui via Module Federation (remote runtime).
# Pré-requisito: container delpi-plugin-ui (profile plugins).

FROM node:20-alpine AS builder

WORKDIR /app

COPY engineering/package*.json ./engineering/
RUN --mount=type=cache,target=/root/.npm \
    cd engineering && npm install

COPY engineering ./engineering
COPY vite ./vite
# Line Balance Studio — fonte compilada pelo vite do MFE (path aliases).
COPY delpi-line-balance-studio ./delpi-line-balance-studio
# Fonte do kit consumida via path aliases (workspace-controls + CSS) —
# o vite do MFE resolve somente os módulos importados pelo Studio.
COPY plugin-ui/src ./plugin-ui/src

WORKDIR /app/engineering
RUN npx vite build
RUN node ../vite/verify-federation-react-patch.mjs dist/assets

FROM nginx:alpine AS production

COPY --from=builder /app/engineering/dist /usr/share/nginx/html

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
