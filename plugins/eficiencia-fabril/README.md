# Eficiência Fabril — plugin Minha DELPI

Microfrontend (Module Federation) para dashboard de eficiência operacional e resultado MOD dos apontamentos de produção.

## API

```http
GET /apps/api-delpi/production/eficiencia-fabril/dashboard
```

## Desenvolvimento local

```bash
cd plugins/eficiencia-fabril
npm install
npm run build
```

Rebuild do container (gateway serve `delpi-eficiencia-fabril`):

```bash
cd infra
docker compose -f docker-compose.dev.yml build eficiencia-fabril
docker compose -f docker-compose.dev.yml up -d eficiencia-fabril gateway
```

## Registro no Portal

```bash
export TOKEN="<jwt_superadmin>"
./scripts/register-manifest.sh
```

## Smoke

```bash
curl -sI http://localhost/apps/eficiencia-fabril/assets/remoteEntry.js
```

Documentação: [docs/12-roadmap-e-evolucao/eficiencia-fabril/](../../docs/12-roadmap-e-evolucao/eficiencia-fabril/)
