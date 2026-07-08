FROM node:20-alpine AS builder

WORKDIR /app

COPY plugin-ui/package*.json ./plugin-ui/
RUN cd plugin-ui && npm install

COPY customer-experience/package*.json ./customer-experience/
RUN cd customer-experience && npm install

COPY plugin-ui ./plugin-ui
COPY customer-experience ./customer-experience

WORKDIR /app/customer-experience
RUN npm run build

FROM nginx:alpine AS production

COPY --from=builder /app/customer-experience/dist /usr/share/nginx/html

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
