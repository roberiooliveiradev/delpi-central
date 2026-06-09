# Auditoria 5S — plugin Minha DELPI

MFE federado para auditoria operacional 5S por filial (01/02).

## Dev local (WSL)

```bash
cd plugins/auditoria-5s
npm ci
npm run dev
```

## Build / CI

```bash
./scripts/ci/build-auditoria-5s.sh
```

## Docker (compose)

Serviço `auditoria-5s` → container `delpi-auditoria-5s`.

**Chat/Ollama:** no dev, `ollama`, `minha-delpi-ai-api` e `minha-delpi-chat` usam profile `chat` — não sobem junto com o gateway. Para o chat: `--profile chat`.

```bash
cd infra

# Stack mínima Auditoria 5S (sem Ollama, sem rebuild de todos os dashboards)
docker compose -f docker-compose.dev.yml --env-file .env up -d --build \
  postgres-plugins postgres-core keycloak core-api strategic-indicators-api \
  api-delpi auditoria-5s portal

docker compose -f docker-compose.dev.yml --env-file .env up -d --no-deps gateway

# Só se precisar do chat depois:
docker compose -f docker-compose.dev.yml --env-file .env --profile chat up -d ollama minha-delpi-ai-api minha-delpi-chat
```

Parar Ollama se subiu por engano: `docker stop delpi-ollama`

## Registro no Portal

```bash
export TOKEN="<jwt superadmin>"
./plugins/auditoria-5s/scripts/register-manifest.sh
```

## API (gateway)

Base: `/apps/api-delpi/quality/audit-5s`

Documentação: [docs/12-roadmap-e-evolucao/auditoria-5s/ROADMAP.md](../../docs/12-roadmap-e-evolucao/auditoria-5s/ROADMAP.md)

## Homologação

```bash
# Fase 1 — remoteEntry + critérios
bash ../../scripts/homologacao/check-auditoria-5s.sh

export TOKEN="<jwt>"
bash ../../scripts/homologacao/check-auditoria-5s.sh

# Fase 2 — fluxo API completo
bash ../../scripts/homologacao/check-audit-5s-api.sh
```

## Migrations

As migrations do 5S ficam em `api-delpi/migrations/plugins/quality/` (plugin slug **`quality`**).

**Pré-requisito:** `delpi-postgres-plugins` em execução (`Up`, não `Restarting`). Se o log mostrar `exec format error`, repuxar a imagem AMD64:

```bash
cd infra
docker compose -f docker-compose.dev.yml --env-file .env stop postgres-plugins
docker rm -f delpi-postgres-plugins
docker pull --platform linux/amd64 pgvector/pgvector:pg15
docker compose -f docker-compose.dev.yml --env-file .env up -d postgres-plugins
```

```bash
# Ver pendências (V022, V023 do audit_5s)
docker exec delpi-api-delpi python scripts/run_plugins_migrations.py status --plugin quality

# Aplicar só as do schema quality (recomendado)
docker exec delpi-api-delpi python scripts/run_plugins_migrations.py up --plugin quality
```
