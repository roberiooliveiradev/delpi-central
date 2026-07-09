# Estágio opcional: empacota dist/ já gerado no host (npm run build && docker build --target static).
FROM nginx:alpine AS static

COPY dist/ /usr/share/nginx/html/

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]


# Padrão do compose dev/prod: build Vite dentro do Docker (contexto ../plugins).
FROM node:20-alpine AS builder

WORKDIR /app

COPY plugin-ui/package*.json ./plugin-ui/
RUN cd plugin-ui && npm install

COPY cultura-delpi/package*.json ./cultura-delpi/
RUN cd cultura-delpi && npm install

COPY plugin-ui ./plugin-ui
COPY cultura-delpi ./cultura-delpi

WORKDIR /app/cultura-delpi
RUN npm run build

FROM nginx:alpine AS production

COPY --from=builder /app/cultura-delpi/dist /usr/share/nginx/html

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
