FROM node:20-alpine AS builder

WORKDIR /app

COPY delpi-mes/package*.json ./delpi-mes/
RUN --mount=type=cache,target=/root/.npm cd delpi-mes && npm install

COPY delpi-mes ./delpi-mes
COPY vite ./vite

WORKDIR /app/delpi-mes
# test/tsc/lint rodam no CI/local; Docker só bundla (MF externaliza @delpi/plugin-ui).
RUN npx vite build
RUN node ../vite/verify-federation-react-patch.mjs dist/assets

FROM nginx:alpine AS production

COPY --from=builder /app/delpi-mes/dist /usr/share/nginx/html

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
