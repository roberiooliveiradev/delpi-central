ARG SHARED_LIBS_BUILDER=delpi-plugins-shared-builder:local
FROM ${SHARED_LIBS_BUILDER} AS builder

WORKDIR /app

COPY tv-dashboard/package*.json ./tv-dashboard/
RUN --mount=type=cache,target=/root/.npm \
    cd tv-dashboard && npm install

COPY tv-dashboard ./tv-dashboard

WORKDIR /app/tv-dashboard
RUN npm run build

FROM nginx:alpine
COPY --from=builder /app/tv-dashboard/dist /usr/share/nginx/html
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
