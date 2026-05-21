# Status atual — Transformômetro

Atualizado: 2026-05-21 (Fase 4 — alertas, export CSV, comparativo, rateio/família).

## Entregue

| Área | Status |
|------|--------|
| API + migrations V001–V004 | ✅ Repo (V004 no próximo deploy) |
| CRUD + UI cadastro + datas de vigência | ✅ |
| Dashboard + recálculo materializado | ✅ |
| Import planilha (CLI + UI + merge por código) | ✅ |
| Dados migrados da planilha Transforma+ | ✅ (~43 processos) |
| Rotas integração engenharia (`/transformometro/integrations/...`) | ✅ |
| api-delpi + SI via `transformometro_client` (HTTP) | ✅ |
| Auth S2S `API_DELPI_INTERNAL_SERVICE_TOKEN` + JWT em threads (SI) | ✅ |
| Fase 4 — alertas, export CSV, comparativo revisões, diagnóstico rateio | ✅ |
| Fase 4 — campos família/agrupador no cadastro de processos | ✅ |

## Pendente (operacional)

| Item | Responsável |
|------|-------------|
| Registrar/atualizar manifesto na Core API + RBAC | Ops — `register-manifest.sh` |
| Deploy Fase 4 (V004 + MFE alertas/export/comparativo) | Ops — rebuild + migrations |
| `TRANSFORMOMETRO_API_BASE_URL=http://transformometro-api:8000` no `.env` | ✅ Produção |
| Planilha somente leitura | Google Workspace |

## Variáveis de produção (checklist)

```bash
API_DELPI_INTERNAL_SERVICE_TOKEN=<mesmo valor em api-delpi, SI, transformometro-api>
TRANSFORMOMETRO_API_BASE_URL=http://transformometro-api:8000
```

## Comandos úteis (srv-api)

```bash
cd ~/projetos/delpi-central
git pull
docker compose build transformometro-api transformometro strategic-indicators-api api-delpi
docker compose up -d --force-recreate transformometro-api transformometro strategic-indicators-api api-delpi

# Testes locais (venv)
./scripts/ci-transformometro-api.sh

# Health + integração (token interno)
curl -s -H "X-Delpi-Service-Token: $API_DELPI_INTERNAL_SERVICE_TOKEN" \
  "http://transformometro-api:8000/transformometro/integrations/engineering/transforma-mais/processes/summary?start_date=2026-05-01&end_date=2026-05-31"
```

## Referências

- [ROADMAP.md](./ROADMAP.md)
- [OPERATIONS.md](./OPERATIONS.md)
- [ARCHITECTURE.md](./ARCHITECTURE.md)
- [DEPLOYMENT.md](../../../transformometro-api/docs/DEPLOYMENT.md)
