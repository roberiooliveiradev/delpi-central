FROM node:20-alpine AS builder

WORKDIR /app

COPY plugin-ui/package*.json ./plugin-ui/
RUN cd plugin-ui && npm install

COPY dashboard-production/package*.json ./dashboard-production/
RUN cd dashboard-production && npm install

COPY plugin-ui ./plugin-ui
COPY dashboard-production ./dashboard-production

WORKDIR /app/dashboard-production
RUN npm run build

FROM nginx:alpine

COPY --from=builder /app/dashboard-production/dist /usr/share/nginx/html

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
