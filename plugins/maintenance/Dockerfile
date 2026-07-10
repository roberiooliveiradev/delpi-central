# MFE — @delpi/plugin-ui via Module Federation (remote delpi-plugin-ui).
# Doc: plugins/plugin-ui/docs/module-federation.md

FROM node:20-alpine AS builder

WORKDIR /app

COPY maintenance/package*.json ./maintenance/
RUN --mount=type=cache,target=/root/.npm \
    cd maintenance && npm install

COPY maintenance ./maintenance
COPY vite ./vite

WORKDIR /app/maintenance

# Invalida cache do vite build quando o código-fonte muda (git rev no deploy).
ARG SOURCE_REVISION=dev
RUN echo "maintenance build ${SOURCE_REVISION}" && npx vite build

FROM nginx:alpine AS production

COPY --from=builder /app/maintenance/dist /usr/share/nginx/html

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
