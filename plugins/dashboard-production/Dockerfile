# MFE — @delpi/plugin-ui via Module Federation (remote delpi-plugin-ui).
# Doc: plugins/plugin-ui/docs/module-federation.md

FROM node:20-alpine AS builder

WORKDIR /app

COPY dashboard-production/package*.json ./dashboard-production/
RUN --mount=type=cache,target=/root/.npm \
    cd dashboard-production && npm install

COPY dashboard-production ./dashboard-production
# Source plugin-ui — tsconfig paths no build; runtime = remote MF.
COPY plugin-ui ./plugin-ui
COPY vite ./vite

WORKDIR /app/dashboard-production
RUN npm run build

FROM nginx:alpine AS production

COPY --from=builder /app/dashboard-production/dist /usr/share/nginx/html

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
