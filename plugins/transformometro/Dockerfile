# MFE — @delpi/plugin-ui via Module Federation (remote delpi-plugin-ui).
# Doc: plugins/plugin-ui/docs/module-federation.md

FROM node:20-alpine AS builder

WORKDIR /app

COPY transformometro/package*.json ./transformometro/
RUN --mount=type=cache,target=/root/.npm \
    cd transformometro && npm install

COPY transformometro ./transformometro
# Source plugin-ui — tsconfig paths no build; runtime = remote MF.
COPY plugin-ui ./plugin-ui
COPY vite ./vite

WORKDIR /app/transformometro
RUN npm run build

FROM nginx:alpine AS production

COPY --from=builder /app/transformometro/dist /usr/share/nginx/html

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
