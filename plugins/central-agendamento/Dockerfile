# MFE — @delpi/plugin-ui via Module Federation (remote delpi-plugin-ui).
# Doc: plugins/plugin-ui/docs/module-federation.md

FROM node:20-alpine AS builder

WORKDIR /app

COPY central-agendamento/package*.json ./central-agendamento/
RUN --mount=type=cache,target=/root/.npm \
    cd central-agendamento && npm install

COPY central-agendamento ./central-agendamento
# Source plugin-ui — tsconfig paths no build; runtime = remote MF.
COPY plugin-ui ./plugin-ui
COPY vite ./vite

WORKDIR /app/central-agendamento
RUN npm run build

FROM nginx:alpine AS production

COPY --from=builder /app/central-agendamento/dist /usr/share/nginx/html

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
