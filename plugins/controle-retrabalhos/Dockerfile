# MFE — consome @delpi/plugin-ui via Module Federation (remote runtime).
# Pré-requisito: container delpi-plugin-ui (profile plugins).
# Doc: plugins/plugin-ui/docs/module-federation.md

FROM node:20-alpine AS builder

WORKDIR /app

COPY controle-retrabalhos/package*.json ./controle-retrabalhos/
RUN --mount=type=cache,target=/root/.npm \
    cd controle-retrabalhos && npm install

COPY controle-retrabalhos ./controle-retrabalhos
# Source plugin-ui — tsconfig paths no build; runtime = remote MF.
COPY plugin-ui ./plugin-ui
COPY vite ./vite

WORKDIR /app/controle-retrabalhos
RUN npm run build

FROM nginx:alpine AS production

COPY --from=builder /app/controle-retrabalhos/dist /usr/share/nginx/html

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
