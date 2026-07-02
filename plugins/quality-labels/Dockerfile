# Estágio opcional: empacota dist/ já gerado no host (npm run build && docker build --target static).
FROM nginx:alpine AS static

COPY dist/ /usr/share/nginx/html/

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]


# Padrão do compose dev/prod: build Vite dentro do Docker (não exige dist/ no host).
FROM node:20-alpine AS builder

WORKDIR /app

COPY package*.json ./
RUN npm install

COPY . .
RUN npm run build

FROM nginx:alpine AS production

COPY --from=builder /app/dist /usr/share/nginx/html

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
