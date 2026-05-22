# Status atual — Transformômetro

Atualizado: 2026-05-21 (Fase 4 + notificações workflow + envs `infra/.env`).

## Entregue

| Área | Status |
|------|--------|
| API + migrations V001–V005 | ✅ Repo |
| CRUD processos, revisões, medições, investimentos, recursos, vínculos | ✅ |
| UI navegação | Início, Dashboard, Processos, **Recursos**, Importar |
| Cadastro revisão (abas) | Vigência/identificação, Medição, Investimentos, Recursos (vínculos + edição inline) |
| Workflow revisão (V005) | Rascunho → análise → aprovada/rejeitada; ativar só se aprovada |
| Catálogo global recursos | Página `/recursos` + `PUT`/`DELETE` na API |
| Dashboard materializado + recálculo | ✅ |
| Fase 4 | Alertas, CSV/Excel, por-família, comparativo, diagnóstico rateio |
| Import planilha (CLI + UI) | ✅ |
| Integração SI / api-delpi (`transformometro_client`) | ✅ |
| Testes API | `scripts/ci-transformometro-api.sh` |
| URLs processo/revisão no MFE | `/processos/{id}` e `/processos/{id}/revisoes/{revisaoId}` |
| Recálculo incremental | `POST /dashboard/recalcular?processo_id=` ou `revisao_id=` |
| Notificações workflow | Core API + MFE (`DELPI_NAVIGATE`) — doc [NOTIFICACOES-WORKFLOW.md](./NOTIFICACOES-WORKFLOW.md) |

## Pendente (operacional)

| Item | Responsável |
|------|-------------|
| Registrar/atualizar manifesto na Core API + RBAC (rota `/recursos`) | Ops — `register-manifest.sh` |
| Deploy com V004–V005 + MFE recente | Ops — rebuild + migrations |
| Planilha somente leitura | Google Workspace |
| Export PDF dashboard | ✅ Impressão/PDF via navegador (`PDF / Imprimir` no dashboard) |

## Variáveis de produção (checklist)

```bash
API_DELPI_INTERNAL_SERVICE_TOKEN=<mesmo valor em api-delpi, SI, transformometro-api>
TRANSFORMOMETRO_API_BASE_URL=http://transformometro-api:8000
TM_RUN_MIGRATIONS_ON_STARTUP=true
TM_NOTIFICATIONS_ENABLED=true
TM_CORE_API_URL=http://core-api:8000
CORE_API_INTEGRATIONS_SERVICE_TOKEN=<mesmo valor do infra/.env da Core API>
TM_WORKFLOW_APPROVER_EMAILS=gestor1@delpi.com.br,gestor2@delpi.com.br
# opcional: TM_WORKFLOW_APPROVER_ROLE_IDS=<uuid-papel-rbac>
```

## Comandos úteis (servidor)

```bash
cd ~/projetos/delpi-central
git pull
docker compose build transformometro-api transformometro
docker compose up -d --force-recreate transformometro-api transformometro

# Migrations (se TM_RUN_MIGRATIONS_ON_STARTUP=false)
docker exec delpi-transformometro-api python -m tm_app.infrastructure.persistence.plugins.migrations_runner status
docker exec delpi-transformometro-api python -m tm_app.infrastructure.persistence.plugins.migrations_runner up

# Manifesto (JWT apps.manage)
export TOKEN="..." BASE_URL="https://www.minhadelpi.com.br"
./plugins/transformometro/scripts/register-manifest.sh

# Testes locais
./scripts/ci-transformometro-api.sh
```

## Referências

- [NOTIFICACOES-WORKFLOW.md](./NOTIFICACOES-WORKFLOW.md) — alertas de submeter/aprovar/rejeitar revisão

- [ROADMAP.md](./ROADMAP.md)
- [OPERATIONS.md](./OPERATIONS.md)
- [OVERVIEW.md](./OVERVIEW.md)
- [ARCHITECTURE.md](./ARCHITECTURE.md)
- [DEPLOYMENT.md](../../../transformometro-api/docs/DEPLOYMENT.md)
