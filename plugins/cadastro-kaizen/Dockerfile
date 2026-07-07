FROM node:20-alpine AS builder

WORKDIR /app

COPY plugin-ui/package*.json ./plugin-ui/
RUN cd plugin-ui && npm install

COPY cadastro-kaizen/package*.json ./cadastro-kaizen/
RUN cd cadastro-kaizen && npm install

COPY plugin-ui ./plugin-ui
COPY cadastro-kaizen ./cadastro-kaizen

WORKDIR /app/cadastro-kaizen
RUN npm run build

FROM nginx:alpine AS production

COPY --from=builder /app/cadastro-kaizen/dist /usr/share/nginx/html

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
