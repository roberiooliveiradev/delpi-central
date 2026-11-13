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
# Default = BFF (F6).
ARG VITE_LNF_API_BASE=/apps/controllership-finance-api/lancamento-notas-fiscais
ENV VITE_LNF_API_BASE=$VITE_LNF_API_BASE
# Default desligado. DEV liga só pelo .env local.
ARG VITE_LNF_REALTIME_ENABLED=false
ENV VITE_LNF_REALTIME_ENABLED=$VITE_LNF_REALTIME_ENABLED
# tsc roda no CI/local; Docker só bundla (MF externaliza @delpi/plugin-ui).
RUN npx vite build

FROM nginx:alpine AS production

COPY lancamento-notas-fiscais/nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=builder /app/lancamento-notas-fiscais/dist /usr/share/nginx/html

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
