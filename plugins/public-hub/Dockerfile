FROM node:20-alpine AS builder

WORKDIR /app

# Dependências do pacote compartilhado (tipos TS). Runtime: dedupe no vite.config.ts.
COPY tv-dashboard-presentation/package*.json ./tv-dashboard-presentation/
RUN cd tv-dashboard-presentation && npm install

COPY plugin-ui/package*.json ./plugin-ui/
RUN cd plugin-ui && npm install

COPY public-hub/package*.json ./public-hub/
RUN cd public-hub && npm install

COPY tv-dashboard-presentation ./tv-dashboard-presentation
COPY plugin-ui ./plugin-ui
COPY public-hub ./public-hub

WORKDIR /app/public-hub
RUN npm run build

FROM nginx:alpine AS production

COPY --from=builder /app/public-hub/dist /usr/share/nginx/html
COPY public-hub/nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
