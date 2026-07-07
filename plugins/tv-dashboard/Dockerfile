FROM node:20-alpine AS builder

WORKDIR /app

# Pacotes compartilhados — aliases Vite (../tv-dashboard-presentation, ../plugin-ui)
COPY tv-dashboard-presentation/package*.json ./tv-dashboard-presentation/
RUN cd tv-dashboard-presentation && npm install

COPY plugin-ui/package*.json ./plugin-ui/
RUN cd plugin-ui && npm install

COPY tv-dashboard/package*.json ./tv-dashboard/
RUN cd tv-dashboard && npm install

COPY tv-dashboard-presentation ./tv-dashboard-presentation
COPY plugin-ui ./plugin-ui
COPY tv-dashboard ./tv-dashboard

WORKDIR /app/tv-dashboard
RUN npm run build

FROM nginx:alpine
COPY --from=builder /app/tv-dashboard/dist /usr/share/nginx/html
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
