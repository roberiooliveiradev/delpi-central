FROM node:20-alpine AS builder

WORKDIR /app

COPY plugin-ui/package*.json ./plugin-ui/
RUN cd plugin-ui && npm install

COPY dashboard-financial/package*.json ./dashboard-financial/
RUN cd dashboard-financial && npm install

COPY plugin-ui ./plugin-ui
COPY dashboard-financial ./dashboard-financial

WORKDIR /app/dashboard-financial
RUN npm run build

FROM nginx:alpine

COPY --from=builder /app/dashboard-financial/dist /usr/share/nginx/html

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
