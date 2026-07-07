FROM node:20-alpine AS builder

WORKDIR /app

COPY plugin-ui/package*.json ./plugin-ui/
RUN cd plugin-ui && npm install

COPY dashboard-engineering/package*.json ./dashboard-engineering/
RUN cd dashboard-engineering && npm install

COPY plugin-ui ./plugin-ui
COPY dashboard-engineering ./dashboard-engineering

WORKDIR /app/dashboard-engineering
RUN npm run build

FROM nginx:alpine

COPY --from=builder /app/dashboard-engineering/dist /usr/share/nginx/html

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
