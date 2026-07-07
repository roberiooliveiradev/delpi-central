FROM node:20-alpine AS builder

WORKDIR /app

COPY plugin-ui/package*.json ./plugin-ui/
RUN cd plugin-ui && npm install

COPY auditoria-5s/package*.json ./auditoria-5s/
RUN cd auditoria-5s && npm install

COPY plugin-ui ./plugin-ui
COPY auditoria-5s ./auditoria-5s

WORKDIR /app/auditoria-5s
RUN npm run build

FROM nginx:alpine AS production

COPY --from=builder /app/auditoria-5s/dist /usr/share/nginx/html

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
