FROM node:20-alpine AS builder

WORKDIR /app

COPY plugin-ui/package*.json ./plugin-ui/
RUN cd plugin-ui && npm install

COPY quality-action-plans/package*.json ./quality-action-plans/
RUN cd quality-action-plans && npm install

COPY plugin-ui ./plugin-ui
COPY quality-action-plans ./quality-action-plans

WORKDIR /app/quality-action-plans
RUN npm run build

FROM nginx:alpine AS production

COPY --from=builder /app/quality-action-plans/dist /usr/share/nginx/html

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
