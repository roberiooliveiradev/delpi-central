FROM node:20-alpine AS builder

WORKDIR /app

COPY plugin-ui/package*.json ./plugin-ui/
RUN cd plugin-ui && npm install

COPY dashboard-quality/package*.json ./dashboard-quality/
RUN cd dashboard-quality && npm install

COPY plugin-ui ./plugin-ui
COPY dashboard-quality ./dashboard-quality

WORKDIR /app/dashboard-quality
RUN npm run build

FROM nginx:alpine

COPY --from=builder /app/dashboard-quality/dist /usr/share/nginx/html

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
