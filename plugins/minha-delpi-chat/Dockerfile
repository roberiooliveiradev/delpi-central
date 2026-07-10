# MFE — @delpi/plugin-ui via Module Federation (remote delpi-plugin-ui).
# Doc: plugins/plugin-ui/docs/module-federation.md

FROM node:20-alpine AS builder

WORKDIR /app

COPY minha-delpi-chat/package*.json ./minha-delpi-chat/
RUN --mount=type=cache,target=/root/.npm \
    cd minha-delpi-chat && npm install

COPY minha-delpi-chat ./minha-delpi-chat
# Source plugin-ui — tsconfig paths no build; runtime = remote MF.
COPY plugin-ui ./plugin-ui
COPY vite ./vite

WORKDIR /app/minha-delpi-chat
RUN npm run build

FROM nginx:alpine AS production

COPY --from=builder /app/minha-delpi-chat/dist /usr/share/nginx/html

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
