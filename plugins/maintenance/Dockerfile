FROM node:20-alpine AS builder

WORKDIR /app

COPY plugin-ui/package*.json ./plugin-ui/
RUN cd plugin-ui && npm install

COPY maintenance/package*.json ./maintenance/
RUN cd maintenance && npm install

COPY plugin-ui ./plugin-ui
COPY maintenance ./maintenance

WORKDIR /app/maintenance
RUN npm run build

FROM nginx:alpine

COPY --from=builder /app/maintenance/dist /usr/share/nginx/html

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
