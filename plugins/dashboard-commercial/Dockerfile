# MFE — @delpi/plugin-ui via Module Federation (remote delpi-plugin-ui).
# Doc: plugins/plugin-ui/docs/module-federation.md

FROM node:20-alpine AS builder

WORKDIR /app

COPY dashboard-commercial/package*.json ./dashboard-commercial/
RUN --mount=type=cache,target=/root/.npm \
    cd dashboard-commercial && npm install

COPY dashboard-commercial ./dashboard-commercial
COPY vite ./vite

WORKDIR /app/dashboard-commercial
RUN npm run build

FROM nginx:alpine AS production

COPY --from=builder /app/dashboard-commercial/dist /usr/share/nginx/html

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
