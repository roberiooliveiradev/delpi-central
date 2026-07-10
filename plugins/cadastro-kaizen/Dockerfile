# MFE — @delpi/plugin-ui via Module Federation (remote delpi-plugin-ui).
# Doc: plugins/plugin-ui/docs/module-federation.md

FROM node:20-alpine AS builder

WORKDIR /app

COPY cadastro-kaizen/package*.json ./cadastro-kaizen/
RUN --mount=type=cache,target=/root/.npm \
    cd cadastro-kaizen && npm install

COPY cadastro-kaizen ./cadastro-kaizen
COPY vite ./vite

WORKDIR /app/cadastro-kaizen
RUN npm run build

FROM nginx:alpine AS production

COPY --from=builder /app/cadastro-kaizen/dist /usr/share/nginx/html

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
