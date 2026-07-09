# Remote Module Federation — @delpi/plugin-ui (runtime nginx)
# Doc: plugins/plugin-ui/docs/module-federation.md

FROM node:20-alpine AS builder

WORKDIR /app

COPY plugin-ui/package*.json ./plugin-ui/
RUN --mount=type=cache,target=/root/.npm \
    cd plugin-ui && npm install

COPY plugin-ui ./plugin-ui
COPY vite ./vite

WORKDIR /app/plugin-ui
RUN npm run build

FROM nginx:alpine AS production

COPY --from=builder /app/plugin-ui/dist /usr/share/nginx/html

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
