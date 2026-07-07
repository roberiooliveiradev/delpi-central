FROM node:20-alpine AS builder

WORKDIR /app

COPY plugin-ui/package*.json ./plugin-ui/
RUN cd plugin-ui && npm install

COPY dashboard-commercial/package*.json ./dashboard-commercial/
RUN cd dashboard-commercial && npm install

COPY plugin-ui ./plugin-ui
COPY dashboard-commercial ./dashboard-commercial

WORKDIR /app/dashboard-commercial
RUN npm run build

FROM nginx:alpine

COPY --from=builder /app/dashboard-commercial/dist /usr/share/nginx/html

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
