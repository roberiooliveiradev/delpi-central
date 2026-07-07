FROM node:20-alpine AS builder

WORKDIR /app

COPY plugin-ui/package*.json ./plugin-ui/
RUN cd plugin-ui && npm install

COPY dashboard-supplies/package*.json ./dashboard-supplies/
RUN cd dashboard-supplies && npm install

COPY plugin-ui ./plugin-ui
COPY dashboard-supplies ./dashboard-supplies

WORKDIR /app/dashboard-supplies
RUN npm run build

FROM nginx:alpine

COPY --from=builder /app/dashboard-supplies/dist /usr/share/nginx/html

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
