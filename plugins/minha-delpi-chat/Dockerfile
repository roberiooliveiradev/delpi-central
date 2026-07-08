FROM node:20-alpine AS builder

WORKDIR /app

COPY plugin-ui/package*.json ./plugin-ui/
RUN cd plugin-ui && npm install

COPY minha-delpi-chat/package*.json ./minha-delpi-chat/
RUN cd minha-delpi-chat && npm install

COPY plugin-ui ./plugin-ui
COPY minha-delpi-chat ./minha-delpi-chat

WORKDIR /app/minha-delpi-chat
RUN npm run build

FROM nginx:alpine

COPY --from=builder /app/minha-delpi-chat/dist /usr/share/nginx/html

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
