FROM node:20-alpine AS builder

WORKDIR /app

COPY plugin-ui/package*.json ./plugin-ui/
RUN cd plugin-ui && npm install

COPY propostas-comerciais/package*.json ./propostas-comerciais/
RUN cd propostas-comerciais && npm install

COPY plugin-ui ./plugin-ui
COPY propostas-comerciais ./propostas-comerciais

WORKDIR /app/propostas-comerciais
RUN npm run build

FROM nginx:alpine

COPY --from=builder /app/propostas-comerciais/dist /usr/share/nginx/html

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
