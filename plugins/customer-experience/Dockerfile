# MFE — @delpi/plugin-ui via Module Federation (remote delpi-plugin-ui).
# Doc: plugins/plugin-ui/docs/module-federation.md

FROM node:20-alpine AS builder

WORKDIR /app

COPY customer-experience/package*.json ./customer-experience/
RUN --mount=type=cache,target=/root/.npm \
    cd customer-experience && npm install

COPY customer-experience ./customer-experience
COPY vite ./vite

WORKDIR /app/customer-experience
# tsc roda no CI/local; Docker só bundla (MF externaliza @delpi/plugin-ui).
RUN npx vite build

FROM nginx:alpine AS production

COPY --from=builder /app/customer-experience/dist /usr/share/nginx/html

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
