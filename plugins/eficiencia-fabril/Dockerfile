# Imagem nginx só com dist/ (dev local após npm run build) — evita npm dentro do Docker.
# Uso: npm run build && docker build --target static -t ...
FROM nginx:alpine AS static

COPY dist/ /usr/share/nginx/html/

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]


# Build completo (CI/VM com Docker estável)
FROM node:20-alpine AS builder

WORKDIR /app

COPY package*.json ./
RUN npm ci

COPY . .
RUN npm run build

FROM nginx:alpine AS production

COPY --from=builder /app/dist /usr/share/nginx/html

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
