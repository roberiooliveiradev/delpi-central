FROM node:20-alpine AS builder

WORKDIR /app

COPY plugin-ui/package*.json ./plugin-ui/
RUN cd plugin-ui && npm install

COPY eficiencia-fabril/package*.json ./eficiencia-fabril/
RUN cd eficiencia-fabril && npm install

COPY plugin-ui ./plugin-ui
COPY eficiencia-fabril ./eficiencia-fabril

WORKDIR /app/eficiencia-fabril
RUN npm run build

FROM nginx:alpine

COPY --from=builder /app/eficiencia-fabril/dist /usr/share/nginx/html

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
