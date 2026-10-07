# TV canonical render worker — bounded Chromium execution host.
# Renders @delpi/tv-dashboard-presentation (shared package) to canonical_stage
# PNG. Internal only — not exposed through the gateway, no public surface.

FROM node:20-bookworm-slim AS builder

WORKDIR /app

# Shared presentation package + its plugin-ui source dependency (same source
# resolution as MFE vite aliases — no registry round-trip). Their own deps are
# installed in-place so node resolution walks up correctly during the build.
COPY plugins/tv-dashboard-presentation/package*.json ./plugins/tv-dashboard-presentation/
RUN --mount=type=cache,target=/root/.npm \
    cd plugins/tv-dashboard-presentation && npm install --omit=peer
COPY plugins/tv-dashboard-presentation ./plugins/tv-dashboard-presentation

COPY plugins/plugin-ui/package*.json ./plugins/plugin-ui/
RUN --mount=type=cache,target=/root/.npm \
    cd plugins/plugin-ui && npm install --omit=peer
COPY plugins/plugin-ui/src ./plugins/plugin-ui/src

COPY tv-dashboard-render-worker/package*.json ./tv-dashboard-render-worker/
RUN --mount=type=cache,target=/root/.npm \
    cd tv-dashboard-render-worker && npm install

COPY tv-dashboard-render-worker ./tv-dashboard-render-worker
WORKDIR /app/tv-dashboard-render-worker
RUN npm run build

# --- runtime ---------------------------------------------------------------
# Pinned Playwright image matching package.json (chromium + deps included).
FROM mcr.microsoft.com/playwright:v1.62.1-noble

WORKDIR /app
ENV NODE_ENV=production

COPY --from=builder /app/tv-dashboard-render-worker/dist ./dist
COPY --from=builder /app/tv-dashboard-render-worker/node_modules ./node_modules
COPY --from=builder /app/tv-dashboard-render-worker/package.json ./package.json

# Render page bundle lives inside dist (vite output) — server serves it on
# loopback only; the browser context never leaves the allowlist.
EXPOSE 8100

HEALTHCHECK --interval=10s --timeout=5s --start-period=20s --retries=5 \
  CMD node -e "fetch('http://127.0.0.1:'+(process.env.RENDER_WORKER_PORT||8100)+'/healthz').then(r=>process.exit(r.ok?0:1)).catch(()=>process.exit(1))"

CMD ["node", "dist/server.js"]
