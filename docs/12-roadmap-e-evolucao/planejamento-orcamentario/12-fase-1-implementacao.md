# 12 — Fase 1 — Fundação implementada

**Branch:** `feat/planejamento-orcamentario`  
**Data:** 2026-08-04  
**Escopo:** exercício, escopos, orientações versionadas, documentos, confirmação de leitura, MFE federado.  
**Fora (Fase 1):** Receita, Pessoal, CAPEX, consolidação, exportações.  
**Integração/homologação:** ver [13-fase-1-1-homologacao.md](./13-fase-1-1-homologacao.md).

---

## 1. Arquitetura utilizada

- Domínio na **api-delpi** (`/planejamento-orcamentario/*`)
- Schema Postgres plugins: `planejamento_orcamentario`
- MFE: `plugins/planejamento-orcamentario` (Module Federation + `@delpi/plugin-ui`)
- Clean Architecture: domain services → use cases → repository plugins → HTTP routers
- Envelope `api_delpi_success` + `route_contract_registry`
- Auth: JWT + `@require_any_permission` + usuário via `get_current_user()`

### Decisão de estados do exercício

Brief pediu `draft/published/open/closed/archived`. Doc 04 pediu `draft/open/closing/locked`.

**Implementado (canônico):** `draft | open | closing | locked | archived`

| Brief | Implementação |
|-------|----------------|
| published | ação `publish` → status `open` + `is_active` |
| closed | `closing` / `locked` |
| archived | status `archived` (pós-lock) |

Único exercício `is_active=TRUE` (índice único parcial).

### Catálogo organizacional

Centros de custo **não** vêm do TOTVS nesta fase. Catálogo interno (`org_units`, `org_areas`, `org_cost_centers`) administrável; escopos só referenciam códigos existentes.

---

## 2. Tabelas (V001)

`budget_exercises`, `guidance_versions`, `guidance_premises`, `guidance_schedule_items`, `support_documents`, `reading_acknowledgements`, `user_org_scopes`, `org_*`, `audit_events` (append-only).

Migration: `api-delpi/migrations/plugins/planejamento-orcamentario/V001__create_budget_planning_core.sql`

---

## 3. Endpoints

Prefixo FastAPI: `/planejamento-orcamentario`  
Público via gateway: `/apps/api-delpi/planejamento-orcamentario/...`

| Método | Path | Permissão |
|--------|------|-----------|
| GET | `/context` | access |
| GET | `/guidance/current` | guidance.view |
| POST | `/guidance/current/acknowledge` | access |
| GET | `/guidance/current/documents` | guidance.view |
| GET | `/documents/{id}/download` | guidance.view |
| CRUD admin | `/admin/exercises…`, `/admin/guidance…`, `/admin/documents…`, `/admin/scopes…`, `/admin/org/cost-centers` | admin / guidance.manage / scopes.manage |

Guard reutilizável: `BudgetGuidanceAcknowledgementGuard.assert_modules_unlocked`.

---

## 4. Permissões (constantes + manifesto; **não atribuídas**)

- `planejamento-orcamentario.access`
- `planejamento-orcamentario.guidance.view`
- `planejamento-orcamentario.guidance.manage`
- `planejamento-orcamentario.scopes.manage`
- `planejamento-orcamentario.admin`

---

## 5. Storage

`PLANEJAMENTO_ORCAMENTARIO_UPLOAD_DIR` (default `/app/data/planejamento-orcamentario`).  
Volume Compose + env documentados na Fase 1.1 (`infra/docker-compose*.yml`, `README-ambiente.md`).

---

## 6. Frontend

Rotas: `/`, `/orientacoes`, `/admin`, `/admin/exercicios`, `/admin/orientacoes`, `/admin/escopos`.  
Manifesto criado, **não registrado**.

---

## 7. Testes e validações

Atualizado na Fase 1.1 (execução real):

| Item | Resultado |
|------|-----------|
| Migration V001 no `postgres-plugins` | **APLICADA** + schema inspecionado |
| `pytest` unitário no container `delpi-api-delpi` | **17 passed** |
| Vitest / typecheck / build MFE (`node:20-alpine`) | **11 passed** + `remoteEntry.js` |
| Container MFE + Gateway | Up; `nginx -t` OK; remoteEntry **200** |
| Registro manifesto / RBAC / smoke autenticado | **BLOCKED** (token Keycloak) — ver doc 13 |

```bash
docker exec delpi-api-delpi python scripts/run_plugins_migrations.py status --plugin planejamento-orcamentario
docker exec delpi-api-delpi python -m pytest tests/unit/planejamento_orcamentario -q
docker run --rm -v "$PWD/plugins:/plugins" -w /plugins/planejamento-orcamentario node:20-alpine sh -c 'npm ci && npm test && npm run build'
```

---

## 8. Limitações / próximos passos

1. ~~Volume Compose / picker / upload UI~~ — feitos na 1.1; falta registro manifesto + RBAC + smoke autenticado.
2. ~~Homologar migration~~ — V001 aplicada e revisada.
3. Fase 2: Receita / Pessoal / CAPEX (não iniciar enquanto 1.1 estiver BLOQUEADA por auth).
4. Corrigir `get-dev-token.sh` / credenciais Keycloak de desenvolvimento.
