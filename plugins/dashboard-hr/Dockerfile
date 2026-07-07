FROM node:20-alpine AS builder

WORKDIR /app

COPY plugin-ui/package*.json ./plugin-ui/
RUN cd plugin-ui && npm install

COPY dashboard-hr/package*.json ./dashboard-hr/
RUN cd dashboard-hr && npm install

COPY plugin-ui ./plugin-ui
COPY dashboard-hr ./dashboard-hr

WORKDIR /app/dashboard-hr
RUN npm run build

FROM nginx:alpine

COPY --from=builder /app/dashboard-hr/dist /usr/share/nginx/html

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
