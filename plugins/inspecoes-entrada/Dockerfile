FROM node:20-alpine AS builder

WORKDIR /app

COPY plugin-ui/package*.json ./plugin-ui/
RUN cd plugin-ui && npm install

COPY inspecoes-entrada/package*.json ./inspecoes-entrada/
RUN cd inspecoes-entrada && npm install

COPY plugin-ui ./plugin-ui
COPY inspecoes-entrada ./inspecoes-entrada

WORKDIR /app/inspecoes-entrada
RUN npm run build

FROM nginx:alpine

COPY --from=builder /app/inspecoes-entrada/dist /usr/share/nginx/html

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
