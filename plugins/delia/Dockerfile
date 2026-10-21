# MFE — consome @delpi/plugin-ui via Module Federation (remote runtime).
# Pré-requisito: container delpi-plugin-ui (profile plugins).
# Doc: plugins/plugin-ui/docs/module-federation.md

FROM node:20-alpine AS builder

WORKDIR /app

COPY delia/package*.json ./delia/
RUN --mount=type=cache,target=/root/.npm \
    cd delia && npm install

COPY delia ./delia
COPY vite ./vite

WORKDIR /app/delia
# QA-only audio capture admission — default off; production builds never
# admit `?delia-audio-qa=1`. Set only for authorized QA/preview images:
#   docker build --build-arg VITE_DELIA_AUDIO_QA=1 ...
ARG VITE_DELIA_AUDIO_QA=""
ENV VITE_DELIA_AUDIO_QA=$VITE_DELIA_AUDIO_QA
# QA-only demo/fixture admission — default off; production builds never
# admit `?delia-demo=` scenarios nor starter-suggestion fixtures.
# Set only for authorized QA/preview images:
#   docker build --build-arg VITE_DELIA_DEMO=1 ...
ARG VITE_DELIA_DEMO=""
ENV VITE_DELIA_DEMO=$VITE_DELIA_DEMO
# tsc roda no CI/local; Docker só bundla (MF externaliza @delpi/plugin-ui).
RUN npx vite build
RUN node ../vite/verify-federation-react-patch.mjs dist/assets

FROM nginx:alpine AS production

COPY --from=builder /app/delia/dist /usr/share/nginx/html

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
