# Documento 100 — P6-MIN + P2-READ: evidência de execução do primeiro incremento de runtime

**Data:** 2026-10-24. **Task:** `CF-C3-P6-MIN-P2-READ-RUNTIME-EXECUTION-001`. **GO:** `CF-C3-P6-MIN-P2-READ-RUNTIME-GO-001` ([doc 99](./99-ciclo3-go-runtime-p6-min-p2-read-e-handoff-devin.md)).
**BASE_SHA:** `d2eb2aab268a7ae46e66a87d931938dbdc716d6f` (main). **Branch:** `main`. **Escopo executado:** `P6-MIN + P2-READ` somente.
**Deploy de produção:** **não realizado** (`DEPLOY_PRODUCTION_AUTHORIZED=NO`, doc 99 §2). Imagem Docker local reconstruída apenas para testes.

Este documento registra o que foi efetivamente implementado e provado. Estados: `PROVEN | TO_INVENTORY | PLANNED | TARGET`. Gates: `PASS | FAIL | PENDING | INCONCLUSIVE | TEST_NOT_RUN | STALE_EVIDENCE`.

## 1. Implementação por checkpoint (E0–E5)

### E0 — Pré-flight e contratos — `PASS`

- `git rev-parse HEAD` = `d2eb2aab26`, branch `main`, working tree sem alterações preexistentes de escopo concorrente relevantes.
- Padrão canônico reconfirmado no HEAD: `psycopg` + schema próprio por app no `postgres-plugins` (supplies/commercial), `PLUGINS_DB_*`, migrations `V###__*.sql` com checksum SHA-256, runner no startup gated, `ok()/fail()` envelope, `has_permission`/`map_authz_exception`, `can_administer` (manage efetivo) como admin scope mínimo da plataforma.
- `READY_TO_EXECUTE`: nenhuma premissa material do doc 96 invalidada; `EXECUTION_DRIFT`: não ocorrido.

### E1 / CP02-DB — Persistência — `PASS`

Arquivos criados:

- `controllership-finance-api/migrations/V001__create_closing_checklist_schema.sql` — schema `controllership_finance`, tabelas `checklist_template`, `checklist_template_version`, `checklist_template_item`, `monthly_competence`, `competence_checklist_item`, `closing_audit_event`, `schema_migrations`; constraints de unicidade (`period`, `item_key` por versão), `revision` otimista, `CHECK` de período `YYYY-MM`, `state='EXPECTED'` no snapshot.
- `controllership-finance-api/migrations/V002__seed_monthly_closing_checklist_v1.sql` — seed do template `monthly_closing_checklist` v1 com **53 itens `CK-*`** (contagem verificada), status `DRAFT`; **nenhuma publicação automática**; conteúdo sanitizado (sem dados bancários reais, contas, nomes de pessoas, valores ou arquivos privados; rótulos do checklist oficial do doc 59/95).
- `controllership_finance_app/infrastructure/persistence/plugins_db.py` — conexão `psycopg` via `PLUGINS_DB_*` (padrão supplies: conexão por chamada, autocommit off, `search_path`/schema qualificado).
- `controllership_finance_app/infrastructure/persistence/migrations_runner.py` — discovery de `migrations/`, checksum SHA-256, execução SQL direta + `conn.commit()` (alinhado ao runner irmão; savepoint incompatível com `BEGIN/COMMIT` internos — corrigido em E5), rollback + `MigrationError` em falha, restart no-op.
- `controllership_finance_app/startup/run_migrations_on_startup.py` + flag `PLUGINS_DB_MIGRATIONS_ON_STARTUP` em `config.py` — runner gated; default off fora de ambiente autorizado.
- `config.py` estendido com `PLUGINS_DB_*`; `infra/docker-compose.yml` recebeu as envs no serviço `controllership-finance-api` seguindo convenção dos irmãos (sem defaults divergentes).
- `requirements.txt`: `psycopg[binary]==3.2.4`.

**Prova em PostgreSQL real** (`delpi-postgres-plugins`, `plugins_hub`, rede `infra_delpi-network`): `tests/test_pg_closing_checklist.py` — 10/10 PASS:

- seed aplica 53 itens em `DRAFT`, zero `PUBLISHED`, zero competências auto-criadas;
- segundo `run_migrations` é no-op (checksum/restart);
- nenhum schema alheio tocado (verificação de `information_schema`);
- snapshot 53 `EXPECTED`; isolamento v1×v2; auditoria append-only.

### E2 / CP02-P6 — API administrativa — `PASS`

`interface/http/routes/admin_checklist_routes.py` (prefixo `/apps/controllership-finance-api/admin/checklist-templates`):

| operationId | Método/Path | Regra |
|---|---|---|
| `list_checklist_templates` | GET `/` | manage+admin scope |
| `list_checklist_template_versions` | GET `/{template_id}/versions` | idem |
| `get_checklist_template_version` | GET `/{template_id}/versions/{version_id}` | idem |
| `create_checklist_template_draft` | POST `/{template_id}/drafts` | idem |
| `update_checklist_template_draft` | PUT `/{template_id}/versions/{version_id}` | idem + `expected_revision` (OCC) |
| `publish_checklist_template_version` | POST `/{template_id}/versions/{version_id}/publish` | idem + vigência `effective_from_period` |
| `inactivate_checklist_template_version` | POST `/{template_id}/versions/{version_id}/inactivate` | idem, prospectivo |

AuthZ: `interface/http/authz.py` — `ACCESS_PERMISSION`/`MANAGE_PERMISSION` via `has_permission` (Core); principal humano obrigatório (`principal_type="user"`); falha Core ⇒ `rbac_unavailable` 503 fail-closed; ACCESS-only e ausência de manage ⇒ 403. Admin scope = `manage` efetivo (padrão `can_administer` dos irmãos; única permission administrativa do produto).

`domain/closing_checklist/errors.py` — erros tipados: `template_not_found`, `version_not_found`, `stale_revision`, `published_version_immutable`, `no_published_template`, `competence_not_opened`, `draft_already_exists`, `version_already_published` etc.

Testes (`tests/test_admin_checklist_routes.py`): publicação autorizada; ACCESS-only negado; MANAGE-sem-escopo negado; double-publish; stale revision/OCC; falha Core; audit append-only com ator.

### E3 / CP03-P2 — Competências e leitura — `PASS`

`interface/http/routes/competences_routes.py` (prefixo `/apps/controllership-finance-api/competences`):

| operationId | Método/Path | Regra |
|---|---|---|
| `list_closing_competences` | GET `/` | access efetivo |
| `open_closing_competence` | POST `/` body `{period}` | access; idempotente por `period`; exige versão `PUBLISHED` vigente |
| `get_closing_competence` | GET `/{period}` | access |
| `list_closing_competence_items` | GET `/{period}/items` | access; filtros `sheet`, `origin_kind`, `recipient_area`, `branch_scope`, `state` |
| `get_closing_competence_item` | GET `/{period}/items/{item_key}` | access; detalhe e proveniência |

Invariantes provados em PG real:

- abertura concorrente/replay da mesma competência ⇒ **uma única** `monthly_competence` (`UNIQUE(period)` + `ON CONFLICT` + retorno do existente); prova com **8 threads reais** na revisão arquitetural: exatamente 1 `created`, 7 replays, snapshot completo;
- abertura com template `DRAFT` ⇒ `no_published_template` (sem fallback);
- snapshot persiste `template_version_id` de origem; publicar v2 **não altera** snapshot v1;
- os 53 itens nascem `EXPECTED` — `EXPECTED != ATTACHED/VALIDATED` (RQ-P2-13);
- itens sem R-ID mantêm `totvs_report_ref` nulo (RQ-P2-14).

### E4 / CP03-UX — MFE — `PASS`

- `plugins/controllership-finance/src/features/closing/ClosingChecklistPage.tsx` — página de checklist: sem período lista competências abertas; com período renderiza snapshot com estados truthful (loading/empty/not-opened/error/403); ação governada "Abrir competência" (`open_competence`) com retry; detalhe por item com proveniência; nenhuma representação de item esperado como entregue/validado.
- `src/api/competencesApi.ts` + `httpPost` em `httpClient.ts` — client tipado, envelope `ok/fail`, erros tipados (`competence_not_opened` ⇒ estado dedicado).
- `pluginRoutes.ts` + `App.tsx` — rota `/closing/checklist` e `/closing/checklist/:period` (deep link/F5).
- `controllership-finance.manifest.json` — **apenas** a rota do checklist, `permission: controllership-finance.access`, `showInMenu: false`, ordem 33; nenhuma permission nova.
- `pluginRouteCatalog.ts` — `closing_checklist` adicionado como `CODE_PRESENT`; Home ganha entrada honesta para a rota.
- `helpTooltips.ts` — Help contextual do checklist (competência, snapshot, estado esperado, origem, destinatário) no mesmo diff.
- Dados pendentes (responsável/validador/destinatário — CP-D02/CP-D03) exibidos como pendência, nunca inventados.

Testes MFE: `ClosingChecklistPage.test.tsx` (6 testes: loading, snapshot 53 EXPECTED, not-opened+opening, erro tipado, detalhe, período inválido) + estruturais atualizados (`pluginRouteCatalog`, `manifestContract`, `homeHonesty`, `pluginRoutes`).

### E5 — Integração e regressão — `PASS` (com `TEST_NOT_RUN` explícito)

| Suíte | Resultado |
|---|---|
| BFF pytest (domínio+rotas+authz+runner) | **131 passed**, 2 warnings — inclui 10 testes PG reais contra `delpi-postgres-plugins` |
| MFE vitest | **100 passed** / 13 arquivos |
| MFE `tsc -b` | `TSC_OK` |
| MFE eslint (arquivos novos) | 0 erros / 0 warnings |
| MFE structural (`*.test.mjs`) | 25 pass / 0 fail |
| MFE `npm run build` | PASS (chunks >500 kB = warning preexistente do bundle) |
| Regressão FinancialSettlements/StockInventory | 16 + 19 testes verdes |
| Smoke autenticado em ambiente de homologação | `TEST_NOT_RUN` — sem ambiente autorizado neste GO |

## 2. Residual search — `PASS`

- **Imports cross-domain:** zero — novos módulos só importam `controllership_finance_app`, `delpi_auth`, stdlib, `psycopg`, FastAPI/Pydantic.
- **Permissions novas:** zero — somente `controllership-finance.access` e `.manage`.
- **Escrita ERP/TOTVS:** zero — `totvs_report_ref`/`origin_kind=TOTVS` são metadados de proveniência declarativos (R-ID do checklist), não escrita.
- **SQL destrutivo:** zero — nenhum `DROP`/`TRUNCATE`/reset; migrations só `up`.
- **Fases futuras:** nenhum upload/anexo, R01–R15 oficial, conciliação, classificação, pacote, CLARA, página/permission DRE.
- **Seed privado:** ausente — rótulos do checklist oficial apenas.
- **Rotas no catálogo:** somente viewIds implementados (`home`, `financial_settlements`, `stock_inventory`, `closing_checklist`).

## 3. Pendências e riscos

| Item | Owner | Estado |
|---|---|---|
| CP-D02 — responsáveis/validadores/regras não informados no checklist | Controladoria | PENDING — representados como dados pendentes, não bloqueantes |
| CP-D03 — `CK-E-27` sem produtor identificado | Controladoria | PENDING — idem |
| Smoke autenticado E2E (Keycloak real) | PO/Plataforma | TEST_NOT_RUN — requer ambiente autorizado |
| Deploy/restart de produção + migrations no banco real | PO | NÃO AUTORIZADO — gate separado |
| P2-Upload, P3, P4, P5, CLARA | — | FORA DO GO — novo gate necessário |

## 4. Veredito

`ACCEPT_WITH_RESIDUAL` — o incremento `P6-MIN + P2-READ` está implementado e provado (persistência isolada, seed 53 DRAFT, publicação governada por API, abertura idempotente de competência, snapshot imutável 53 `EXPECTED`, página MFE com Help, auditoria append-only, AuthZ fail-closed). Residuais: smoke autenticado não executado (`TEST_NOT_RUN`), CP-D02/CP-D03 pendentes na Controladoria, deploy de produção não autorizado nem realizado.
