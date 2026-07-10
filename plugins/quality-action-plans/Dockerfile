# MFE — @delpi/plugin-ui via Module Federation (remote delpi-plugin-ui).
# Doc: plugins/plugin-ui/docs/module-federation.md

FROM node:20-alpine AS builder

WORKDIR /app

COPY quality-action-plans/package*.json ./quality-action-plans/
RUN --mount=type=cache,target=/root/.npm \
    cd quality-action-plans && npm install

COPY quality-action-plans ./quality-action-plans
COPY vite ./vite

WORKDIR /app/quality-action-plans
RUN npm run build

FROM nginx:alpine AS production

COPY --from=builder /app/quality-action-plans/dist /usr/share/nginx/html

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
