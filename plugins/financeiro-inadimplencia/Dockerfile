# MFE — @delpi/plugin-ui via Module Federation (remote delpi-plugin-ui).
# Doc: plugins/plugin-ui/docs/module-federation.md

FROM node:20-alpine AS builder

WORKDIR /app

COPY financeiro-inadimplencia/package*.json ./financeiro-inadimplencia/
RUN --mount=type=cache,target=/root/.npm \
    cd financeiro-inadimplencia && npm install

COPY financeiro-inadimplencia ./financeiro-inadimplencia
COPY vite ./vite

WORKDIR /app/financeiro-inadimplencia
# tsc roda no CI/local; Docker só bundla (MF externaliza @delpi/plugin-ui).
RUN npx vite build

FROM nginx:alpine AS production

COPY financeiro-inadimplencia/nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=builder /app/financeiro-inadimplencia/dist /usr/share/nginx/html

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
