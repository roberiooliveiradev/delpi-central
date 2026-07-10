# MFE — @delpi/plugin-ui via Module Federation (remote delpi-plugin-ui).
# Doc: plugins/plugin-ui/docs/module-federation.md

FROM node:20-alpine AS builder

WORKDIR /app

COPY dashboard-hr/package*.json ./dashboard-hr/
RUN --mount=type=cache,target=/root/.npm \
    cd dashboard-hr && npm install

COPY dashboard-hr ./dashboard-hr
COPY vite ./vite

WORKDIR /app/dashboard-hr
# tsc roda no CI/local; Docker só bundla (MF externaliza @delpi/plugin-ui).
RUN npx vite build

FROM nginx:alpine AS production

COPY --from=builder /app/dashboard-hr/dist /usr/share/nginx/html

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
