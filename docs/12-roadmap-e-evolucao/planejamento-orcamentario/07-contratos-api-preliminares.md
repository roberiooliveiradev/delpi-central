# 07 — Contratos API preliminares

**Base path (gateway):** `/apps/api-delpi/planejamento-orcamentario`  
**Envelope:** `{ success, message, data, meta }` via `api_delpi_success` / `error_response`  
**meta:** `operationId`, `entity`, `shape` registrados em `route_contract_registry`.

Paginação padrão (listagens): `page`, `page_size`, `total_items`, `is_complete` (Playbook 10).

Idempotência: `Idempotency-Key` em submits/approvals/exports; PATCH de autosave usa `expected_revision`.

---

## Exercícios

| Método | Path | Finalidade | Permissão | Escopo | Request | Response | Audit |
|--------|------|------------|-----------|--------|---------|----------|-------|
| GET | `/exercises` | Listar | `.access` | — | query year? | lista | não |
| POST | `/exercises` | Criar | `.admin` | — | year, title, dates | exercise | sim |
| GET | `/exercises/{id}` | Detalhe | `.access` | — | — | exercise+status | não |
| PATCH | `/exercises/{id}` | Config/prazos | `.admin` | — | patch | exercise | sim |
| POST | `/exercises/{id}/transitions` | open/closing/lock/reopen | `.admin` | — | `{action, comment?}` | exercise | **sim** |

Erros: 404, 409 transição inválida, 403.

## Orientações e documentos

| Método | Path | Permissão | Notas |
|--------|------|-----------|-------|
| GET | `/exercises/{id}/orientations/current` | `.orientations.read` | versão publicada |
| PUT | `/exercises/{id}/orientations` | `.orientations.manage` | publica nova versão; invalida confirmações antigas |
| GET/POST | `/exercises/{id}/documents` | read / manage | upload multipart → volume |
| GET | `/exercises/{id}/documents/{docId}/download` | read | stream; auth+escopo app |

## Confirmações de leitura

| Método | Path | Permissão | Idempotência |
|--------|------|-----------|--------------|
| GET | `/exercises/{id}/reading-status` | `.access` | — |
| POST | `/exercises/{id}/reading-confirmations` | `.access` | sim (unique user+version) |

Erro 409 se versão desatualizada.

## Escopos do usuário

| Método | Path | Permissão |
|--------|------|-----------|
| GET | `/me/scopes?exercise_id=` | `.access` | retorna units/areas/CCs |
| GET/PUT | `/admin/scopes` | `.admin` | CRUD vínculos |

## Receita

| Método | Path | Permissão | Escopo |
|--------|------|-----------|--------|
| GET | `/exercises/{id}/revenue` | `.revenue.read` | filtra unit |
| PUT/PATCH | `/exercises/{id}/revenue/{projectionId}` | `.revenue.write` | unit no escopo; `expected_revision` |
| POST | `/…/revenue/{id}/import-baseline` | `.revenue.write` | puxa ROL/clientes (se habilitado) |
| POST | `/…/revenue/{id}/transitions` | write/approve | submit/approve… |

## Pessoal

Análogo a receita: `/headcount`, linhas em `/headcount/{id}/lines`, transitions.

## CAPEX

| Método | Path | Notas |
|--------|------|-------|
| GET | `/exercises/{id}/capex` | filtros CC, prioridade, status; paginado |
| POST | `/exercises/{id}/capex` | cria item; valida CC escopo |
| PATCH | `/exercises/{id}/capex/{itemId}` | autosave; expected_revision |
| DELETE | `/…/capex/{itemId}` | soft; só draft |
| POST | `/…/capex/bundles/{bundleId}/transitions` | workflow do pacote |

Erros: 422 validação (prioridade, conta, valor≥0), 403 CC, 409 revision.

## Workflows / aprovações

| Método | Path | Permissão |
|--------|------|-----------|
| GET | `/exercises/{id}/workflows` | `.approve` ou consolidate |
| POST | `/workflows/{id}/actions` | `.approve` / `.approve.all` | body `{action, comment?}` |

## Consolidação

| Método | Path | Permissão | Shape |
|--------|------|-----------|-------|
| GET | `/exercises/{id}/consolidation/summary` | `.consolidate` | scalar/KPIs |
| GET | `/exercises/{id}/consolidation/capex` | `.consolidate` | playbook_report / list |
| GET | `/exercises/{id}/consolidation/headcount` | `.consolidate` | list |

Respeita `.approve.all` / admin para cross-unit; demais só escopo amplo declarado.

## Exportações

| Método | Path | Permissão | Sync |
|--------|------|-----------|------|
| POST | `/exercises/{id}/exports` | `.export` | cria job; body format+filters |
| GET | `/exercises/{id}/exports/{jobId}` | `.export` | status |
| GET | `/…/exports/{jobId}/download` | `.export` | auth; escopo do job ≤ escopo user |

MVP: xlsx síncrono se linhas < limiar; senão 202 + poll.

## Administração

| Método | Path |
|--------|------|
| GET/PUT | `/exercises/{id}/config` |
| GET | `/exercises/{id}/audit` | `.admin` ou consolidate | paginado |
| GET/POST | `/masters/cost-centers` | admin sync/list |

## Erros previsíveis (padrão)

| HTTP | code exemplo |
|------|----------------|
| 401 | JWT |
| 403 | FORBIDDEN_SCOPE / FORBIDDEN_PERMISSION |
| 404 | NOT_FOUND |
| 409 | INVALID_STATE / REVISION_CONFLICT / READING_REQUIRED |
| 422 | VALIDATION_ERROR |

Nenhum endpoint confia em flags só do client.
