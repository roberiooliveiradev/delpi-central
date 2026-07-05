FROM node:20-alpine AS builder

WORKDIR /app

# Só o source do pacote compartilhado — react vem do public-hub (evita duplicata).
COPY tv-dashboard-presentation ./tv-dashboard-presentation

COPY public-hub/package*.json ./public-hub/
RUN cd public-hub && npm install

COPY public-hub ./public-hub

WORKDIR /app/public-hub
RUN npm run build

FROM nginx:alpine AS production

COPY --from=builder /app/public-hub/dist /usr/share/nginx/html
COPY public-hub/nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
