# MFE — @delpi/plugin-ui via Module Federation (remote delpi-plugin-ui).
# Doc: plugins/plugin-ui/docs/module-federation.md

FROM node:20-alpine AS builder

WORKDIR /app

COPY auditoria-5s/package*.json ./auditoria-5s/
RUN --mount=type=cache,target=/root/.npm \
    cd auditoria-5s && npm install

COPY auditoria-5s ./auditoria-5s
COPY vite ./vite

WORKDIR /app/auditoria-5s
RUN npm run build

FROM nginx:alpine AS production

COPY --from=builder /app/auditoria-5s/dist /usr/share/nginx/html

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
