FROM node:20-alpine AS builder

WORKDIR /app

COPY plugin-ui/package*.json ./plugin-ui/
RUN cd plugin-ui && npm install

COPY transformometro/package*.json ./transformometro/
RUN cd transformometro && npm install

COPY plugin-ui ./plugin-ui
COPY transformometro ./transformometro

WORKDIR /app/transformometro
RUN npm run build

FROM nginx:alpine

COPY --from=builder /app/transformometro/dist /usr/share/nginx/html

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
