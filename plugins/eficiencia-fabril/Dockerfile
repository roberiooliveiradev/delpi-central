# MFE — @delpi/plugin-ui via Module Federation (remote delpi-plugin-ui).
# Doc: plugins/plugin-ui/docs/module-federation.md

FROM node:20-alpine AS builder

WORKDIR /app

COPY eficiencia-fabril/package*.json ./eficiencia-fabril/
RUN --mount=type=cache,target=/root/.npm \
    cd eficiencia-fabril && npm install

COPY eficiencia-fabril ./eficiencia-fabril
# Source plugin-ui — tsconfig paths no build; runtime = remote MF.
COPY plugin-ui ./plugin-ui
COPY vite ./vite

WORKDIR /app/eficiencia-fabril
RUN npm run build

FROM nginx:alpine AS production

COPY --from=builder /app/eficiencia-fabril/dist /usr/share/nginx/html

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
