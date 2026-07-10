# MFE — @delpi/plugin-ui via Module Federation (remote delpi-plugin-ui).
# Doc: plugins/plugin-ui/docs/module-federation.md

FROM node:20-alpine AS builder

WORKDIR /app

COPY quality-labels/package*.json ./quality-labels/
RUN --mount=type=cache,target=/root/.npm \
    cd quality-labels && npm install

COPY quality-labels ./quality-labels
# Source plugin-ui — tsconfig paths no build; runtime = remote MF.
COPY plugin-ui ./plugin-ui
COPY vite ./vite

WORKDIR /app/quality-labels
RUN npm run build

FROM nginx:alpine AS production

COPY --from=builder /app/quality-labels/dist /usr/share/nginx/html

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
