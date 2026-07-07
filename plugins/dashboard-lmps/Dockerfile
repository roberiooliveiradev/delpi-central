FROM node:20-alpine AS builder

WORKDIR /app

COPY plugin-ui/package*.json ./plugin-ui/
RUN cd plugin-ui && npm install

COPY dashboard-lmps/package*.json ./dashboard-lmps/
RUN cd dashboard-lmps && npm install

COPY plugin-ui ./plugin-ui
COPY dashboard-lmps ./dashboard-lmps

WORKDIR /app/dashboard-lmps
RUN npm run build

FROM nginx:alpine

COPY --from=builder /app/dashboard-lmps/dist /usr/share/nginx/html

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
