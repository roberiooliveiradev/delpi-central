# Estágio opcional: empacota dist/ já gerado no host.
FROM nginx:alpine AS static

COPY quality-labels/dist/ /usr/share/nginx/html/

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]

FROM node:20-alpine AS builder

WORKDIR /app

COPY plugin-ui/package*.json ./plugin-ui/
RUN cd plugin-ui && npm install

COPY quality-labels/package*.json ./quality-labels/
RUN cd quality-labels && npm install

COPY plugin-ui ./plugin-ui
COPY quality-labels ./quality-labels

WORKDIR /app/quality-labels
RUN npm run build

FROM nginx:alpine AS production

COPY --from=builder /app/quality-labels/dist /usr/share/nginx/html

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
