FROM nginx:alpine AS static

COPY central-agendamento/dist/ /usr/share/nginx/html/

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]

FROM node:20-alpine AS builder

WORKDIR /app

COPY plugin-ui/package*.json ./plugin-ui/
RUN cd plugin-ui && npm install

COPY central-agendamento/package*.json ./central-agendamento/
RUN cd central-agendamento && npm install

COPY plugin-ui ./plugin-ui
COPY central-agendamento ./central-agendamento

WORKDIR /app/central-agendamento
RUN npm run build

FROM nginx:alpine AS production

COPY --from=builder /app/central-agendamento/dist /usr/share/nginx/html

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
