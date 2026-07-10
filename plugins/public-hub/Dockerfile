# Shell público (/p/) — @delpi/plugin-ui via Module Federation; tv-dashboard-presentation bundled.
# Doc: plugins/plugin-ui/docs/module-federation.md

FROM node:20-alpine AS builder

WORKDIR /app

COPY tv-dashboard-presentation/package*.json ./tv-dashboard-presentation/
RUN --mount=type=cache,target=/root/.npm \
    cd tv-dashboard-presentation && npm install

COPY tv-dashboard-presentation ./tv-dashboard-presentation

COPY public-hub/package*.json ./public-hub/
RUN --mount=type=cache,target=/root/.npm \
    cd public-hub && npm install

COPY public-hub ./public-hub
# Source plugin-ui — tsconfig paths no build; runtime = remote MF.
COPY plugin-ui ./plugin-ui
COPY vite ./vite

WORKDIR /app/public-hub
RUN npm run build

FROM nginx:alpine AS production

COPY --from=builder /app/public-hub/dist /usr/share/nginx/html
COPY public-hub/nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
