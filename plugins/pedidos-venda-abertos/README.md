# Pedidos de Venda em Aberto — plugin Minha DELPI

Microfrontend (Module Federation) para consulta de pedidos de venda em aberto via **api-delpi**.

Documentação: [docs/12-roadmap-e-evolucao/pedidos-venda-abertos/](../../docs/12-roadmap-e-evolucao/pedidos-venda-abertos/)

## API

```http
GET /apps/api-delpi/pedidos-venda-abertos/
```

Permissão: `pedidos-venda-abertos.access` ou `api-delpi.access`.

## Desenvolvimento

```bash
cd plugins/pedidos-venda-abertos
npm install
npm run dev
```

Build:

```bash
npm run ci
```

Docker (a partir de `infra/`):

```bash
docker compose -f docker-compose.dev.yml up -d --build pedidos-venda-abertos
```

## Registro no Portal

```bash
export TOKEN="<jwt_superadmin>"
./scripts/register-manifest.sh
```

## Smoke

```bash
curl -sI http://localhost/apps/pedidos-venda-abertos/assets/remoteEntry.js
```
