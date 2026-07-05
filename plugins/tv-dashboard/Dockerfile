FROM node:20-alpine AS builder

WORKDIR /app

# Pacote compartilhado — alias Vite ../tv-dashboard-presentation
COPY tv-dashboard-presentation/package*.json ./tv-dashboard-presentation/
RUN cd tv-dashboard-presentation && npm install

COPY tv-dashboard/package*.json ./tv-dashboard/
RUN cd tv-dashboard && npm install

COPY tv-dashboard-presentation ./tv-dashboard-presentation
COPY tv-dashboard ./tv-dashboard

WORKDIR /app/tv-dashboard
RUN npm run build

FROM nginx:alpine
COPY --from=builder /app/tv-dashboard/dist /usr/share/nginx/html
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
