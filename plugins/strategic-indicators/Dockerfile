FROM node:20-alpine AS builder

WORKDIR /app

COPY plugin-ui/package*.json ./plugin-ui/
RUN cd plugin-ui && npm install

COPY strategic-indicators/package*.json ./strategic-indicators/
RUN cd strategic-indicators && npm install

COPY plugin-ui ./plugin-ui
COPY strategic-indicators ./strategic-indicators

WORKDIR /app/strategic-indicators
RUN npm run build

FROM nginx:alpine

COPY --from=builder /app/strategic-indicators/dist /usr/share/nginx/html

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
