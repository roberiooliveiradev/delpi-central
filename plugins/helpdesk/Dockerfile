# MFE — consome @delpi/plugin-ui via Module Federation.

FROM node:20-alpine AS builder

WORKDIR /app

COPY helpdesk/package.json ./helpdesk/
RUN --mount=type=cache,target=/root/.npm \
    cd helpdesk && npm install

COPY helpdesk ./helpdesk
COPY vite ./vite

WORKDIR /app/helpdesk
RUN npx vite build
RUN node ../vite/verify-federation-react-patch.mjs dist/assets

FROM nginx:alpine AS production

COPY --from=builder /app/helpdesk/dist /usr/share/nginx/html

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
