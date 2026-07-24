# MFE — @delpi/plugin-ui via Module Federation (remote delpi-plugin-ui).
# Doc: plugins/plugin-ui/docs/module-federation.md

FROM node:20-alpine AS builder

WORKDIR /app

COPY lancamento-notas-fiscais/package*.json ./lancamento-notas-fiscais/
RUN --mount=type=cache,target=/root/.npm \
    cd lancamento-notas-fiscais && npm install

COPY lancamento-notas-fiscais ./lancamento-notas-fiscais
COPY vite ./vite

WORKDIR /app/lancamento-notas-fiscais
# tsc roda no CI/local; Docker só bundla (MF externaliza @delpi/plugin-ui).
RUN npx vite build

FROM nginx:alpine AS production

COPY lancamento-notas-fiscais/nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=builder /app/lancamento-notas-fiscais/dist /usr/share/nginx/html

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
