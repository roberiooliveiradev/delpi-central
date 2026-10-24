# Documento 98 — Revisão transversal final de prontidão: `P6-MIN + P2-READ`

**Rodada:** `CF-C3-P6-MIN-P2-READ-TRANSVERSAL-GO-REVIEW-001` (2026-10-24)
**BASE_SHA:** `9d3c1bb309` (main, worktree limpa, sem alterações concorrentes
no escopo). **Referência anterior revalidada:** `9791fabc28` (superseded).
**Modo:** READ → VERIFY → REVIEW → CLASSIFY → DOCUMENT → REPORT.
**`IMPLEMENTATION_AUTHORIZED=NO`.**
**Authorities:** instruções oficiais, `.cursor` aplicáveis (boundaries,
segurança, contratos, dados, frontend, qualidade, delivery), docs 09, 13, 14,
21, 23, 30, 37, 45, 59, 90–97. **Doc 97 é a autoridade das decisões do PO.**

---

## 1. Revisão de persistência — `PERSISTENCE_READY_FOR_IMPLEMENTATION = YES`

Verificação do doc 96 §1 contra o código real no HEAD `9d3c1bb309`:

| Requisito | Evidência verificada | Estado |
|---|---|---|
| `psycopg` + `dict_row`, autocommit off | `supplies-api/.../migrations_runner.py`; `commercial-api/.../plugins_postgres_connection.py` | PROVEN |
| `postgres-plugins` + `PLUGINS_DB_*` | compose `delpi-postgres-plugins` (linha ~1378); envs padrão nos irmãos | PROVEN |
| Schema isolado por contexto | `SCHEMA_NAME` por app; `controllership_finance` livre (não colide com nenhum schema existente) | PROVEN |
| Runner + checksum SHA-256 + ordem `V###` | `migrations_runner.py` (supplies/travel_expenses idênticos); divergência de checksum aborta | PROVEN |
| Startup gated | `run_migrations_on_startup` → flag + `plugins_db_configured()` | PROVEN |
| Seed por migration | `travel-expenses-api/V001`, `commercial-api/V010`, `maintenance-api/V004` | PROVEN |
| Audit append-only | `V003__supplier_enrichment_decision_operations` | PROVEN |
| Concorrência otimista | `revision` + `ReviewRevisionConflictError` | PROVEN |
| Idempotência física | `UNIQUE(…, idempotency_key)` + conflito tipado | PROVEN |
| Testes PG reais | `test_supplier_enrichment_repository_pg.py` (`skipif` por `*_TEST_PG_*`; mocks não aceitos para atomicidade) | PROVEN |
| Rollback/preservação | migrations imutáveis; nunca reset em prod (`plugins-migrations-no-reset-prod`); rollback de release = deploy anterior + migration aditiva | PROVEN |

**Diferenças encontradas e avaliação:**
- `commercial-api` usa **pool de conexões próprio**
  (`plugins_postgres_connection.py`, `PLUGINS_DB_APPLICATION_NAME`); supplies
  usa conexão por chamada. Ambos convergem no mesmo banco/schema-padrão —
  escolha de pooling é detalhe de implementação, não divergência material.
  Recomendação: começar com o padrão supplies (simples) e avaliar pool só se
  carga exigir.
- A BFF `controllership-finance-api` hoje **não tem** `psycopg`,
  `PLUGINS_DB_*`, `depends_on: postgres-plugins` nem migrations — são o diff
  já mapeado (doc 96 §1.1), não desvios novos.
- Nenhum risco de: schema em contexto errado (nome único), dependência
  circular (BFF não lê tabelas de terceiros), reset de dados (imutabilidade
  por checksum + política no-reset-prod), mutação de dados de outros plugins
  (schema próprio + user compartilhado não concede privilégio extra).

## 2. Revisão do modelo de domínio — invariantes fechadas

As seis entidades do doc 96 §2 foram revalidadas contra os invariantes
exigidos:

| Invariante | Garantia no modelo |
|---|---|
| DRAFT não gera competência | open exige `status=PUBLISHED` → 409 `no_published_template` |
| Só versão publicada e vigente gera snapshot | `effective_from_period <= period` na resolução |
| Publicada não editável retroativamente | imutável; edição só em DRAFT via `revision` |
| Versão nova não altera competência | `template_version_id` congelado + cópia no snapshot |
| Abertura concorrente idempotente | `UNIQUE(period)` → perdedor re-lê; replay = 200 mesmo recurso |
| Snapshot preserva origem/versão | `source_template_item_id` + `source_version_id` |
| Item externo sem R-ID válido | `totvs_report_ref NULL`, `origin_kind=EXTERNAL` |
| `EXPECTED` ≠ entregue | estado inicial único; sem transição neste slice |
| Inativação sem delete | `status=INACTIVE`, histórico RESTRICT |
| Filial não é permission | `branch_scope` = dimensão do item |
| Falha do Core = fail-closed | `rbac_unavailable`→503, padrão já existente |
| Admin exige manage+escopo | matriz §4 abaixo |

**Evolução:** P2-Upload adiciona `attachment`/versioning sobre
`competence_checklist_item`; P3/P5 adicionam entidades próprias sem alterar
o núcleo; CLARA consome os mesmos contratos READ. Nenhuma entidade futura
foi antecipada.

## 3. Revisão dos contratos HTTP — `CONTRACT_FREEZE=PASS` (candidatos fechados)

Os 12 operationIds do doc 96 §3 foram revistos um a um contra:
envelope `ok()/fail()` existente (`core/responses.py`), convenção de erros
tipados do `closing_routes.py`, padrão `has_permission`/`delpi_auth` e
requirements da doc 23. Sem divergência material. Refinamentos documentais:

- `openCompetence`: replay → **200 + recurso existente** (não 409); período
  malformado → 422 `invalid_period`.
- `publishTemplateVersion`: body aceita `effective_from_period` (default =
  próxima competência); DRAFT já publicado → 409 `already_published`.
- `updateTemplateDraft`: `revision` obrigatório; stale → 409
  `stale_revision`; nova edição em versão PUBLISHED → 409 `not_a_draft`.
- Toda operação administrativa emite `closing_audit_event` com ator real.
- Sem paginação em `items` (máximo 53 + extras futuros — slice pequeno);
  paginação somente se ultrapassar o teto, avaliar no primeiro slice real.

## 4. Revisão de segurança — `SECURITY_GATE = PASS`

| Operação | `access` efetivo | `manage` efetivo | admin scope | Regra extra |
|---|---|---|---|---|
| list/open/get competences + items | ✔ | — | — | principal `user`; `rbac_unavailable`→503; S2S→403 |
| admin list/get/draft/publish/inactivate | — | ✔ | ✔ | +revision/audit |
| publicar com `access` only | — | — | — | 403 |
| `manage` sem escopo admin | — | ✔ | ✗ | 403 |
| Core down | — | — | — | 503 fail-closed |
| filtro filial arbitrário | filtro só | — | — | não amplia escopo |

JWT identifica/contextualiza; Core resolve effective permissions; nenhum
permission code criado; doc 91 (DRE) fora; nenhum segredo em log.

## 5. Revisão UI/Help — `UI_GATE = PASS` (especificação)

- Nova rota candidata `/closing/checklist/{period}` usa permission
  `access` existente; manifest hoje tem 3 rotas — evolução trivial, mas
  **somente após GO**.
- `@delpi/plugin-ui` cobre filtros, DataTable, feedback, help; estados
  LOADING/EMPTY/PARTIAL/ERROR/FORBIDDEN já existem no padrão das páginas
  vigentes.
- Requisitos de honestidade: estado `EXPECTED` exibido como "Esperado" —
  sem badges de entrega/aprovação, sem % conclusão; campos
  `responsible`/`validator`/`recipient` ausentes exibidos como pendência
  de configuração (`TO_INVENTORY`), não como falha.
- F5/deep link, tema claro/escuro, mobile, teclado/foco, Help sincronizada
  no mesmo diff (RQ-P2-12 / helpCoverage estrutural).

## 6. Revisão RQ/AC e plano de testes — `TEST_PLAN_SUFFICIENT`

- Ledger doc 23: RQ-P6-01/02/03/09 e RQ-P2-01/02/12 já registrados;
  **RQ-P2-13/14 não constam no doc 23** (verificado: 0 ocorrências) —
  propostas formalizadas no doc 95/96 e registradas no ledger no GO.
- Cobertura planejada: positivos (seed 53 → publish → open → snapshot
  `EXPECTED`), siblings (v1×v2 por competência), negativos
  (403/404/409/422/503), concorrência (open/publish simultâneos, stale
  revision), idempotência (replay), falhas (Core/DB), UI (F5/tema/
  teclado/mobile/help), integração PG real.
- **Não declarado PASS**: funcionalidades não existem; resultados virão do
  próximo slice com `CF_TEST_PG_*` + suítes atuais.

## 7. Verificação de dependências — sem antecipação

O slice não depende de: P3/P4/P5, extração oficial R01–R15, upload,
CLARA MCP, permissão/página DRE, ou escrita ERP. CP-D02/CP-D03 ficam
`TO_INVENTORY` visíveis no domínio (`recipient_area NULL` permitido;
`totvs_report_ref NULL`) — não bloqueiam leitura.

## 8. Matriz transversal de GO

| Gate | Estado | Evidência |
|---|---|---|
| Authority/ownership | PASS | docs 21/96/97; owner BFF |
| Persistência | PASS | §1 — padrão irmão comprovado |
| Domínio | PASS | §2 — invariantes fechados |
| Contratos HTTP | PASS | §3 — operationIds + erros tipados |
| Segurança | PASS | §4 — matriz + fail-closed |
| UI/Help | PASS | §5 — plugin-ui + rota/manifest delimitada |
| Testes | PASS(plano) | §6 — casos suficientes; execução no slice |
| Escopo | PASS | §7 — nada além de P6-MIN+P2-READ |
| Decisões PO | PASS | CP-D01/04/05 respeitadas |
| Deploy | FORA | gate operacional separado (`local-first-deploy`) |

**Execução de testes:** `TEST_NOT_RUN` — deliberadamente fora do escopo
(não existe runtime para testar).

## 9. Parecer — `GO_RECOMMENDED`

Não há bloqueio material. O menor diff correto está delimitado:
`requirements`+`psycopg`, `migrations/V001`+`V002`, runner/startup/settings,
`compose` env+depends_on, camadas domain/application/interface para 12
operationIds, rota MFE `/closing/checklist/{period}`, Help, testes.

**`GO_RECOMMENDED` não é autorização.** A decisão cabe ao PO.

### 9.1 Texto pronto para solicitação de autorização ao PO

```text
GO proposto: CF-C3-P6-MIN-P2-READ-RUNTIME-GO-001
BASE_SHA:   9d3c1bb309 (2026-10-24)

Escopo autorizado (se aprovado):
 - Persistência isolada: schema controllership_finance no postgres-plugins
   com migrations V001 (schema+tabelas) e V002 (seed 53 itens, status DRAFT),
   runner SHA-256, startup gated, psycopg e PLUGINS_DB_* na BFF.
 - P6-MIN por API: listar/criar/editar DRAFT (revision), publish com
   vigência, inativar prospectivo; manage efetivo + escopo administrativo;
   audit append-only.
 - P2-READ: POST /closing/competences (idempotente por period),
   GET lista/itens/detalhe; estado inicial EXPECTED; snapshot imutável;
   erros tipados honestos.
 - MFE: rota /closing/checklist/{period} com permission .access existente,
   plugin-ui, estados honestos, Help no mesmo diff.
 - Testes: PG real (CF_TEST_PG_*), contratos BFF, MFE, manifest, positive/
   sibling/negative/concorrência/idempotência.

NÃO autorizado: upload/validação de anexos, P3/P4/P5, relatórios oficiais,
CLARA MCP, permission/página Contabilidade, escrita ERP, deploy de produção.

Stop conditions: divergência de contrato comprova EXECUTION_DRIFT; qualquer
necessidade de permission extra, persistência fora do schema próprio ou
runtime fora do slice → retornar DECISION_REQUIRED.

Deploy: gate operacional separado, independente deste GO.
```

## 10. Pendências e owners fora do GO

| Item | Owner | Estado |
|---|---|---|
| CP-D02 — responsáveis/validadores/regras por item | Controladoria | TO_INVENTORY |
| CP-D03 — produtor de CK-E-27 (faturamento filial) | Controladoria+TI/ERP | TO_INVENTORY |
| RQ-P2-13/14 → ledger doc 23 | executor no slice GO | PLANNED |
| E1–E12 do Ciclo 2 | owners conforme doc 82 | PENDING |
| G6×15 | Controladoria (aceite humano) | PENDING |

**Veredito da rodada:** `ACCEPT_WITH_RESIDUAL` — gates materiais fechados,
pendências de dados e deploy fora do GO por decisão expressa do PO.
