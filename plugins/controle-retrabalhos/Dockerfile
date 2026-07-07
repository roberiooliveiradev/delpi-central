FROM node:20-alpine AS builder

WORKDIR /app

COPY plugin-ui/package*.json ./plugin-ui/
RUN cd plugin-ui && npm install

COPY controle-retrabalhos/package*.json ./controle-retrabalhos/
RUN cd controle-retrabalhos && npm install

COPY plugin-ui ./plugin-ui
COPY controle-retrabalhos ./controle-retrabalhos

WORKDIR /app/controle-retrabalhos
RUN npm run build

FROM nginx:alpine

COPY --from=builder /app/controle-retrabalhos/dist /usr/share/nginx/html

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
