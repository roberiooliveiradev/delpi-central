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

---

## Adendo — Hardening pós-revisão R1/R2/R4 (`CF-C3-P6-P2-POST-REVIEW-HARDENING-R1-R2-R4-001`)

Correções internas dos resíduos menores do Documento 102, sobre BASE_SHA `73a02393dc`. Sem mudança material de contrato, permission, boundary ou persistência.

| Resíduo | Correção | Evidência | Estado |
|---|---|---|---|
| R1 `item_key` duplicado → 500 | `DuplicateItemKey` (`duplicate_item_key`, 409) traduz `UniqueViolation` dentro da transação; rollback integral | teste PG real de atomicidade + matriz de erros HTTP | CORRIGIDO |
| R2 fallback de ator para e-mail | `actor_subject` canônico: somente `user.id` UUID validado; ausente/malformado ⇒ 401 fail-closed | testes de rota (UUID válido, não-UUID, `sub` ausente, service principal) + auditoria UUID-only em PG real | CORRIGIDO |
| R4 fixture `DROP SCHEMA` destrutiva | banco dedicado recriável + `assert_safe_test_database` + opt-in `CF_TEST_PG_ALLOW_DESTRUCTIVE=1` | 16 testes de guarda + probes reais (destino compartilhado bloqueado, opt-in ausente ⇒ skip, banco dedicado executa e é limpo) | CORRIGIDO |

Testes: BFF `143 passed` · PG dedicado `27 passed` · MFE closing `41 passed`. Deploy de produção: NÃO REALIZADO. Detalhes e provas no adendo do Documento 102.

---

## Adendo — Rework de segurança R4 (`CF-C3-HARDENING-R4-SAFETY-REWORK-001`)

Revisão arquitetural independente do hardening `1ad43e04` classificou R4 como REWORK: `assert_safe_test_database` + opt-in provavam *permissão* para destruir, mas não *ownership* do recurso — um banco preexistente chamado `plugins_hub_test` poderia ser dropado por `DROP DATABASE IF EXISTS` se credenciais bastassem. R1/R2 preservados sem alteração.

**Correção:** isolamento por banco efêmero com prova de ownership (`tests/pg_test_isolation.py`):

- nome único por execução `cf_test_<prefixo>_<uuid12>`; `CREATE DATABASE` sem `IF NOT EXISTS` — colisão gera outro identificador, nunca destrói o existente;
- token de ownership gravado dentro do banco criado (`cf_test_run_ownership`);
- teardown executa `DROP DATABASE` **somente** se o token lido no alvo conferir com o desta execução — incerteza (sem marcador, token divergente, falha de conexão) ⇒ nenhum DROP;
- teardown usa o objeto `owned` capturado na criação — nunca releitura de env;
- cluster declarado de teste (`CF_TEST_PG_CLUSTER=test`) + opt-in (`CF_TEST_PG_ALLOW_DESTRUCTIVE=1`) exigidos antes de qualquer DDL.

**Evidências:**

- 24 testes de guarda sem banco real (prefixos protegidos/ambíguos/injeção, opt-ins, colisão, ownership divergente/ausente, falha de conexão, mutação de env pós-setup, identificador malicioso);
- prova adversarial em PostgreSQL real (cluster local descartável): isco `plugins_hub_test` preexistente apontado como `CF_TEST_PG_NAME` — **preservado** com sentinela intacta; órfão `cf_test_orphan_*` sem ownership — **preservado**; `plugins_hub` canônico — **intacto** (159 itens); banco efêmero criado, usado e dropado pela execução;
- suíte PG real no banco efêmero: `11 passed` (migrations V001/V002, seed 53 DRAFT, publish, concorrência, idempotência, atomicidade R1, auditoria UUID);
- BFF: `161 passed` + 11 skips sem env PG; MFE inalterado (`41 passed` closing).

**Resposta à pergunta central:** o fixture só pode destruir um banco cuja prova de ownership (token gravado pela própria execução) confere — bancos preexistentes não podem ser alvo por nome ou por opt-in. Fato observado em código e em probes adversariais; aceite formal cabe à revisão independente.

Risco remanescente: execuções abortadas entre CREATE e teardown deixam resíduos `cf_test_*` no cluster de teste — seguro (nunca são presumidos próprios); limpeza manual eventual. Smoke autenticado: `TEST_NOT_RUN`. Deploy de produção: NÃO REALIZADO.

## Adendo — Evidência de execução P2-Upload SLICE-1 (`CF-C3-P2-UPLOAD-IMPL-GO-001`)

`GO_STATUS=PO_AUTHORIZED` · `SCOPE=SLICE-1_ONLY` · `PRODUCTION_DEPLOY=NO` · `PRODUCTION_MIGRATIONS=NO`. Evidência por etapa; `TEST_NOT_RUN` explícito.

### E1 — Persistência e storage

- `V003__create_closing_documents.sql`: `document_file` (storage_key UNIQUE, sha256, size ≤ 25 MB), `closing_document` (`UNIQUE(competence_id, idempotency_key)`, `request_hash`, FK composta item↔competência — D-U6, CHECK link_kind↔item, `attachment_role='generic'` — D-U5), `document_version` (`UNIQUE(document_id, version_no)`). Auditoria na mesma transação em `closing_audit_event`.
- Sequência C2: `.part` em chunks (cap 25 MB mid-stream) → sha256 durante o write → validação de conteúdo → `os.replace` atômico no mesmo filesystem → transação Postgres → compensação `unlink` com log em falha de compensação. Sem atomicidade distribuída declarada.
- Testes: `test_closing_document_storage.py` (cap mid-stream, rename, traversal guard, compensação, discard) · `test_closing_document_service.py` (replay, conflito, corrida, compensação, `file_missing`).

### E2 — BFF U1–U4

- `documents_routes.py`: `POST|GET /closing/competences/{period}/documents[/{id}[/versions/{v}/content]]` — envelope `ok/fail` canônico, `operation_id` EN, erros tipados (`file_too_large` 422, `unsupported_media_type` 415, `empty_file`/`invalid_file_content`/`content_type_mismatch`/`invalid_upload` 422, `item_not_found`/`document_not_found`/`competence_not_opened` 404, `idempotency_conflict` 409, `persistence_unavailable`/`file_missing`/`rbac_unavailable` 503).
- D-U7=A implementada: `idempotency_key` multipart obrigatória, `UNIQUE(competence_id, key)`, `request_hash`, replay `deduplicated:true` (200), divergente 409, sem TTL.
- Download: `FileResponse` autenticado; `DOCUMENT_DOWNLOADED result=AUTHORIZED` somente após authz + integridade — sem URL pública nem `storage_key` exposta.
- Suíte: `test_closing_documents_routes.py` (upload/list/get/download, authz, service principal 403, ator não-UUID 401, rbac_unavailable 503, replay, conflito) + `test_closing_file_validation.py`.

### E3 — MFE P2

- `ClosingDocumentsPanel` integrado à `ClosingChecklistPage` — evidências da competência + evidências por item no detalhe; `FileDropzone`/`AttachmentFileList` do `@delpi/plugin-ui`; `documentsApi.ts` consome só a BFF; retry preserva a mesma `idempotency_key`; download via blob autenticado.
- Estados honestos: «anexado ≠ validado», checklist permanece «Esperado».

### E4 — Help e testes frontend

- `helpTooltips.ts` sincronizado: formatos, 25 MB, competência vs item, anexar≠validar, erros comuns, autorização — sem promessas de SLICE-2.
- `ClosingDocumentsPanel.test.tsx` (5 testes): listagem, vazio, upload com key, retry mesma key, 403.
- MFE: `105 passed` vitest + `25 passed` estrutural · build `tsc -b && vite build` ok · lint com 3 warnings pré-existentes em arquivos não tocados.

### E5 — PostgreSQL real e regressão

- Banco efêmero `cf_test_*` com prova de ownership (mecanismo R4): `test_pg_closing_documents.py` — 10 testes (FK item↔competência, replay idempotente, conflito divergente, corrida 4 threads → 1 vencedor, auditoria append-only, cross-competence 404, mesmo binário 2 docs).
- Suíte completa com `CF_TEST_PG_*` ativo: **242 passed** (BFF + PG + guardas).
- `TEST_NOT_RUN`: recreate literal de container (durabilidade inferida de volume host + publish/resolve); smoke autenticado ponta a ponta (não há ambiente deployado).

### Residuais honestos preservados

Antivírus inexistente (não improvisado) · housekeeping de órfãos PLANNED (não ativo) · retenção corporativa pendente · OFX/QIF/TXT com TÉO · E05/E06 · `RQ-P2-039`.

## Adendo — Rework funcional SLICE-1 (`CF-C3-P2-UPLOAD-SLICE1-REWORK-001`)

Correções sobre `ad78082222`, sem reimplementar o slice:

- **R-W1 — resource scope efetivo.** U1–U4 agora aplicam `capability AND resource_scope AND business_rule`: `branch_scope` (dimensão de dado MATRIX|BRANCH|BOTH, nunca permission) declara o filial-contexto do request; o documento herda o escopo do item (competência = BOTH). Fora do contexto = 404 sem vazamento (`item_not_found`/`document_not_found`). Não existe fonte canônica de filial por usuário — audiência `access` autorizada para o dataset compartilhado (doc 49 §8); permission por filial permanece proibida e membership não foi inventado.
- **R-W2 — limpeza de `.part`.** Toda exceção entre `write_temp()` e `publish()` (validação de conteúdo/assinatura/extensão/MIME, request_hash, idempotência, falha de publicação) chama `discard_temp()` — idempotente e com log, nunca mascarando a causa. Testes: PDF corrompido, XLSX inválido, mismatch de tipo, extensão não suportada e falha de publish — nenhum `.part` permanece.
- **R-W3 — auditoria de download.** `DOCUMENT_DOWNLOADED` registra a decisão de autorização — `result=AUTHORIZED|DENIED|FAILED` + `phase=authorization|delivery` no detail. DENIED quando o documento existe mas está fora do contexto (auditável); FAILED quando o binário está ausente. `FileResponse` não prova transmissão: nenhuma linha afirma entrega concluída.
- **R-W4 — erros de download no MFE.** `.catch(() => undefined)` removido; banner acessível classifica a causa (autorização 401/403, documento fora do escopo 404, arquivo indisponível `file_missing`/503, falha de rede) com «Tentar novamente».
- Evidência: backend `242 passed` · PG isolado `58 passed` (escopo herdado, filtro por contexto, fase de auditoria) · frontend `109 passed` + `25` estrutural · `tsc -b && vite build` ok · lint limpo nos arquivos tocados.

## Adendo — Evidência de execução P2-Upload SLICE-2 (CF-C3-P2-UPLOAD-SLICE2-IMPL-GO-001)

Baseline: SLICE-1 aceito ACCEPT_WITH_RESIDUAL (7d5e0402e0). Zero migrations novas — V003 já provia state/current_version_no/revision OCC/document_version/uploaded_by/closing_audit_event. D-U1..D-U7=A preservadas integralmente.

### E1/E2 — Backend

- U5 replace (POST .../documents/{id}/versions multipart com idempotency_key, revision, branch_scope?): uploader original ou manage elegível (D-U1) — access genérico sem manage é negado; manage sem access é 403 na pipeline. FOR UPDATE + verificação de revision na mesma transação ⇒ 1 vencedor; perdedores stale_revision 409. Nova versão ATTACHED (version_no+1), anterior SUPERSEDED, binário antigo nunca reescrito, VERSION_ADDED na tx. Mesma sequência .part→sha256→os.replace→tx→compensação do U1; .part descartado em toda rejeição.
- U6 versions (GET .../versions): histórico imutável com metadados + sha256, sem storage_key; persiste após cancel; paginação ≤100.
- U7 cancel (POST .../cancel com revision): CANCELLED != DELETED — sai da listagem ativa, consultável via U3/U6/U8, arquivos/versões/auditoria intactos; duplo cancel = conflito tipado; DOCUMENT_CANCELLED na tx.
- U8 events (GET .../events): closing_audit_event filtrado por documento — upload, download (result/phase), versão, cancel; sem dados sensíveis; append-only.
- Scope aplicado em U5–U8 (capability AND resource_scope AND business_rule); cross-competence e cross-branch = 404 sem vazamento; service principal 403; ator não-UUID 401.

### E3/E4 — MFE e Help

- ClosingDocumentsPanel: ações por documento (substituir, versões, cancelar, baixar, eventos) via AttachmentFileList itemActions (extensão backward-compatible do kit); file picker para replace; diálogo de versões com download por versão; ConfirmModalPanel para cancelar; diálogo de eventos; erros tipados 403/404/409 com retry seguro; ações desabilitadas em CANCELLED.
- helpTooltips atualizado: substituir, SUPERSEDED, cancelar (histórico preservado), quem pode, anexar≠validar — sem promessas de P5/validação.
- Evidência: BFF 308 passed (PG real R4 — corrida 4 threads → 1 vencedor, cancel/histórico/eventos, escopo); MFE 115 passed vitest + 25 estrutural; tsc -b && vite build ok; lint limpo nos arquivos tocados.
- TEST_NOT_RUN: AC-P2-UP-20 (trava P5 — runtime de submissão inexistente; boundary reservado, não improvisado); smoke autenticado ponta a ponta.

### Residuais honestos preservados

Antivírus inexistente · housekeeping de órfãos PLANNED · retenção corporativa · OFX/QIF/TXT com TÉO · E05/E06 · RQ-P2-039 · trava P5 pendente de runtime canônico.

### Rework pós-revisão SLICE-2 (REWORK do GPT sobre 62f111ea — doc 104 §1)

Dois resíduos corrigidos sem redefinir decisões:

- **Idempotência U5:** a key da mutação agora é persistida e verificada — `V004__document_version_idempotency.sql` adiciona `idempotency_key`/`request_hash` a `document_version` com `UNIQUE(document_id, key)` (v1 herda a key do upload; replaces trazem key própria — nunca a key U1 reutilizada). Replay idêntico ⇒ `deduplicated` 200 **antes** do OCC (revision obsoleta no replay não vira `stale_revision`); mesma key + payload divergente ⇒ `idempotency_conflict` 409; corrida com mesma key ⇒ 1 criador + N dedups, um único `VERSION_ADDED`; binário publicado em corrida perdida é compensado.
- **Imutabilidade real de `document_version`:** a coluna `state` foi removida — a linha nunca é atualizada; `SUPERSEDED`/`ATTACHED` é derivado de `closing_document.current_version_no` em toda leitura (get/list/download).
- Evidência: `test_replace_idempotent_replay_no_second_version`, `test_replace_same_key_divergent_hash_conflicts`, `test_concurrent_same_key_replace_deduplicates`, `test_version_rows_never_updated` (PG real R4); service `test_replace_idempotent_replay_deduplicates`, `test_replace_same_key_divergent_payload_conflicts`, `test_replace_requires_idempotency_key`, `test_replace_race_lost_compensates_published_binary`; rota `test_replace_deduplicated_returns_200`, `test_replace_requires_idempotency_key`; MFE retry reutiliza a mesma key. Suíte completa: **318 passed** BFF+PG.

## Adendo — Evidência de execução A2 validação humana P2 (CF-PROC0072-E2E-MASTER-EXECUTION-001)

Baseline: `9a1cf4ea53` remoto (A1 `883872e4a9` publicado em cima). Pacote A2 do doc 104 — validação humana do ciclo documental, sem reabrir decisões U1–U8.

### Backend e dados

- `V005__p2_item_validation.sql` (aditiva): `validation_scope` em template item + snapshot (`PER_ATTACHMENT`/`WHOLE_SET`), `evidence_decision` append-only (composição `document_id:version_no`, `reason_code`, `result_state`, `reverses_decision_id`), `item_correction` (request/review separados, nova `revision` no approve), `state`/`state_reason`/`exceptional`/`revision` no snapshot item; relaxa NOT NULL de origem de template para item excepcional.
- `closing_validation_repository.py`: decisões por versão (per-attachment) e por conjunto (composição exata — drift `set_composition_changed`); recomputação de estado do item após decisão/upload/substituição/cancel (`ACCEPTED`→`EXPECTED` quando a evidência corrente muda — RQ-P2-05); N/A só em `CONDITIONAL` com justificativa (`not_applicable_not_allowed`); cancel terminal `CANCELLED` sem apagar histórico; reversão só do mesmo validador e bloqueada por versão nova (`replacement_requires_revalidation`); item excepcional só na competência (mestre intacto); correção estrutural request(ACCESS)→review(MANAGE)→nova revision; escopo `branch_scope` declarado × herdado = 404 sem vazamento; documentos de competência (sem item) decididos normalmente.
- `validations_routes.py` registrada em `main.py` — envelope padrão, erros tipados, authorization fail-closed.
- `closing_document_repository.add_version`/`cancel_document` reabrem a validação do item afetado na mesma transação.

### MFE e Help

- `ItemValidationPanel.tsx` (novo): decisões por anexo com badge/ator/data, rejeição com motivo estruturado + comentário obrigatório em «Outro», aceite/rejeição de conjunto, reversão com justificativa e estado resultante, N/A/reversão/cancelamento de item, solicitação e revisão de correção, histórico de decisões — tudo render-only, autoridade no backend.
- `ClosingDocumentsPanel`: evidência de competência sem item ganha Aceitar/Rejeitar (motivo estruturado); item docs seguem decididos no `ItemValidationPanel`.
- `competencesApi.ts`: contratos `ItemValidation`/`EvidenceDecision`/`ItemCorrection` + 11 operações.
- Página do checklist: novos estados (`Aceito`, `Não aplicável`, `Cancelado`), regra de validação e flag «excepcional» no detalhe, botão «Adicionar item excepcional» com justificativa; Help sincronizado (`checklist.validation`, `checklist.state`, `checklist.exceptionalItem`).

### Evidência executada

- BFF: **367 passed** com PostgreSQL real descartável (suíte `test_pg_closing_validations.py` 21 casos: append-only, escopo, WHOLE_SET/per-attachment, revalidação pós-substituição, N/A, excepcional, correção, item sem evidência, `test_item_out_of_declared_scope_404`, `test_validation_events_in_audit`) + `test_closing_validations_routes.py` 28 casos.
- MFE: **126 vitest** + 25 estruturais · `tsc -b` e `vite build` ok · lint limpo nos arquivos tocados.
- TEST_NOT_RUN: RQ-P2-11 (notificações — dependência T02 fora de A2); smoke autenticado; demo humana (G2).

## Adendo — Evidência de execução A3 administração P6 (CF-PROC0072-E2E-MASTER-EXECUTION-001)

Baseline: `5c9d23ce6f` (A2 deployado). Pacote A3 do doc 104 — superfície administrativa do checklist mestre sobre o backend P6-MIN existente, sem criar identidades/permissões locais.

### Backend

- `ClosingChecklistRepository.list_template_events(template_id, version?)` — eventos append-only (`closing_audit_event` ⋈ versão) com filtro opcional por versão; template inexistente → `template_not_found`.
- Rota `GET /admin/checklist-templates/{id}/events?version=` — `authorized_admin` (MANAGE efetivo), envelope padrão; ACCESS → 403.
- Lifecycle já vigente preservado: um DRAFT por template (índice parcial), `update_draft_items` OCC `revision` (`stale_revision` 409, `version_not_draft`, `template_not_found`), `publish_version` com `effective_from_period` prospectivo, `inactivate_version` prospectivo sem delete — zero migrations novas.

### MFE

- `adminApi.ts` — contratos `ChecklistTemplate(Version|Item|AuditEvent)` + 8 operações (`httpPut` adicionado ao `httpClient` para JSON mutations).
- `ChecklistAdminPage.tsx` (`closing/admin`): versões com estado/vigência; itens read-only fora de DRAFT; edição atômica de DRAFT (adicionar/editar/remover + «Salvar rascunho» com `revision`); diálogo de publicação `AAAA-MM`; inativação confirmada; eventos por template; `stale_revision`→mensagem de recarga; erros 401/403/404/409/5xx tipados; render-only — autoridade integral no backend.
- Rotas: `closing/admin` no `pluginRoutes`, manifest (`permission=manage`, `showInMenu=false`), hub `requiredCap="manage"` (oculto para ACCESS).
- Help: `CF_HELP.admin.page/versions/items/editDraft` — lifecycle, snapshot imutável, OCC, sem gestão de usuários.

### Evidência executada

- BFF: **371 passed** (PG real R4 — `test_list_template_events`, filtros por versão; rotas: events happy/filtro/ACCESS→403).
- MFE: **138 vitest** (9 novos: render, draft bloqueado, 403, vazio, save com revision, `stale_revision`→recarga, publish, inactivate, events) + **25 estruturais** atualizados (manifest 5 rotas, catálogo com `checklist_admin`).
- `tsc -b`, `vite build`, lint limpos.
- TEST_NOT_RUN: smoke autenticado da página; demo humana (G2).
- Residual P6 mantido: catálogos bancos/motivos/roles/targets e etapa REVIEW do lifecycle permanecem `TARGET` (RQ-P6-05..08, RQ-ADM-01/02/05/07/08).

## Adendo — Aceite integrado do Pacote A (A4, CF-PROC0072-E2E-MASTER-EXECUTION-001)

Suíte `test_pg_package_a_acceptance.py` (PostgreSQL real, banco efêmero R4 — **3 testes, PASS**) demonstra o cenário de aceite do doc 104 §4 ponta a ponta pelos repositórios canônicos:

- **Duas competências independentes** (2027-01/2027-02) abertas sobre a mesma v1 publicada — snapshots separados, itens e estados isolados.
- **Anexar ≠ validar** — `EXPECTED` até decisão humana; aceite por anexo deriva `ACCEPTED` só quando toda evidência corrente está aceita.
- **Rejeição com motivo** (`WRONG_DOCUMENT` + comentário) mantém `EXPECTED`; **reversão** pelo mesmo validador (`REVERSED` append-only); novo aceite conclui o ciclo.
- **Substituição exige revalidação** — `add_version` rebaixa `ACCEPTED`→`EXPECTED` na mesma transação; nova decisão sobre a versão corrente restaura `ACCEPTED`.
- **Histórico íntegro** — sequência `evidence_decision` append-only (`ACCEPTED,ACCEPTED` / `REJECTED,REVERSED,ACCEPTED`), eventos documentais (`DOCUMENT_UPLOADED`, `EVIDENCE_REJECTED`, `EVIDENCE_ACCEPTED`) e trilha administrativa (`VERSION_PUBLISHED`, `DRAFT_CREATED`, `DRAFT_UPDATED`, `COMPETENCE_OPENED`, `VERSION_ADDED`, `REJECTION_REVERSED`).
- **Snapshot preservado** — publicar v2 (vigência 2027-03) não reescreve itens nem estados das competências abertas; 2027-03 abre já na v2.
- **Autorização negativa** — ator inelegível coberto nas suítes de rota (ACCESS→403 em admin/correção-review, não-uploader→403 em replace/cancel, scope→404 sem vazamento); mesmo usuário anexa e valida somente quando autorizado independentemente para ambas as ações (ACCESS documental + decisão humana registrada por ator distinto nos testes).

Suíte completa do contexto: **374 passed** (BFF + PG real). Pacote A (A1–A4) **PROVEN** no nível de implementação/teste; aceite humano de negócio = G2 pendente (não inferido de testes automatizados).

## Adendo — Regularização operacional (verificação somente-leitura, PO)

**Classificação:** deploy de A1–A3 em `srv-api` antes de G2/G3 = `EXECUTION_DRIFT` de release (conforme orientação do PO). Código publicado ≠ deploy autorizado ≠ aceite de negócio. Verificação somente-leitura executada via `operador@192.168.1.237` — nenhum deploy, migration ou rollback realizado durante a verificação.

### Estado observado (read-only)

- **SHA implantado:** `8ca4e25124` (A3) em `~/projetos/delpi-central` — idêntico ao `main` publicado à época (A4 `ea2bbbcd28` é somente-teste e não requer deploy).
- **Containers:** `delpi-controllership-finance-api` Up **(healthy)**, `delpi-controllership-finance` Up; imagens `infra-controllership-finance{,-api}:latest` reconstruídas pelo script canônico.
- **Migrations aplicadas** (`controllership_finance.schema_migrations`): V001–V005, aplicadas em 2026-10-24, checksums registrados.
- **Saúde/gateway:** `…/controllership-finance-api/health` = 200; `remoteEntry.js` = 200; `admin/checklist-templates` e `closing/competences` sem credencial = **401** (fail-closed).
- **Persistência:** volume host `/var/lib/delpi/cf-closing-documents` montado em `/app/data/cf-closing-documents`.
- **Backup/recuperação:** `infra/scripts/restore-delpi-backups.sh` existe (pg_dump -Fc); `~/backups` contém dumps de outros contextos. **Não há evidência de dump do schema `controllership_finance` imediatamente anterior a V004/V005** — risco registrado.
- **Exposição de funcionalidades:** nenhuma permission nova; admin gated por `controllership-finance.manage`; documentos sem URL pública; nenhuma escrita TOTVS.
- **Riscos imediatos:** nenhum risco material de segurança/integridade detectado. Aviso pré-existente de infra: collation mismatch em `plugins_hub` (não causado por A1–A3). Funcionalidades de validação/admin estão live sob autorização vigente (ACCESS/MANAGE), porém aceite de negócio G2 permanece **pendente** — superfícies operáveis, não aprovadas.

### Classificação de estado

- `CODE_PUBLISHED`: A1–A4 em `main` (`883872e4a9`, `5c9d23ce6f`, `8ca4e25124`, `ea2bbbcd28`).
- `DEPLOY_REPORTED`: A3 runtime verificado em produção (`8ca4e25124`, healthy, V001–V005 aplicadas).
- `OPERATION_PROVEN`: **NO** — aceite humano G2 e smoke autenticado permanecem TEST_NOT_RUN.
- `DEPLOY_SUSPENDED`: novos deploys produtivos suspensos até G2/G3 conforme orientação vigente.


---

## ADENDO — PACOTE B (P4 + P3 + matriz R01–R15), commit `c19d08fb31`

Execução: CF-PROC0072-E2E-MASTER-EXECUTION-001, baseline `ea2bbbcd28`.
Publicado em `main` via push `HEAD:main` (fast-forward após rebase sobre
`405575f745`). Deploy produtivo **suspenso** — nenhuma ação em
`srv-api`, nenhuma migration produtiva, nenhum rollback.

### Implementado (código + testes, não operação)

- **P4 (V006):** `closing_pendency` — grafo fechado
  `OPEN→IN_ANALYSIS/WAITING_EXTERNAL→RESOLVED|DISMISSED`; claim e
  reatribuição mudam só responsabilidade (histórico append-only via
  `closing_audit_event`); sugestão determinística/IA é recomendação —
  `confirmed_classification` exige ator humano `manage` e é uma vez;
  `DISMISSED` exige justificativa e não é `NOT_APPLICABLE`; OCC por
  `revision`; `branch_scope` com fail-closed fora de contexto.
- **P3 (V007):** `closing_cutoff` (único por competência),
  `closing_reconciliation` (ENTRADAS_SAIDAS/P7/H02, `numeric(19,2)`),
  `closing_revalidation` (append-only, `input_fingerprint`),
  `closing_stock_state` (somente sincronização do owner — linha ausente
  = `UNAVAILABLE`, sem fallback manual, zero escrita TOTVS).
  Readiness derivada: `READY_TO_CLOSE` exige cutoff + revalidação
  vigente + todas as sources `AVAILABLE` + divergência exatamente
  `R$ 0,00` por domínio; `R$ 0,01` ou `-R$ 0,01` bloqueiam; zero
  pré-cutoff/revalidação é preliminar.
- **Matriz R01–R15:** `GET /closing/competences/{period}/reports` —
  agregação derivada do snapshot (itens por R-ID × estado de
  validação) + catálogo canônico fonte/owner (doc 93). R01/R02/R03
  marcados `OPERATIONAL_VIEW` (auxiliares, não oficiais); R04, R06,
  R07, R09, R12, R15 `PENDING_CONTRACT`; R05, R08, R10, R11
  `MANUAL_EVIDENCE`; R13, R14 `EXTERNAL`.
- **MFE:** `P3CutoffPanel` + `ReportsMatrixPanel` embutidos no
  checklist; página `/closing/pendencies`; clientes `p3Api`,
  `pendenciesApi`, `reportsApi`; Help contextual sincronizado;
  manifest + catálogo do hub atualizados.
- **Autorização:** somente `access`/`manage` existentes — leitura e
  claim/transições `access`; reassign, confirmação de classificação,
  cutoff, revalidação e registro de sources `manage`. Nenhuma
  permission nova.

### Testes executados

- Backend: **438 passed** (rotas P3/P4/reports + PostgreSQL real
  descartável com prova de ownership — V001→V007).
- MFE: **149 vitest** (inclui `P3CutoffPanel` 4, `PendenciesPage` 6) +
  **25 estruturais** + `tsc -b` limpo + `vite build` OK.

### Estado honesto

- `HUMAN_ACCEPTANCE`: G2 pendente — testes verdes ≠ aceite.
- `DEPLOY_STATUS`: não deployado — `srv-api` continua em `8ca4e25124`
  (A3) até regularização G2/G3; V006/V007 pendentes de aplicação
  produtiva no startup autorizado.
- `SMOKE_AUTHENTICATED`: TEST_NOT_RUN.
- R01–R15: nenhuma integração automática nova com fonte oficial neste
  pacote — o que não tem owner/contrato confirmado permanece
  `PENDING_CONTRACT`/`MANUAL_EVIDENCE` com proveniência explícita.
- Pauta G1 residual: owners/contratos das fontes PENDING_CONTRACT
  (R04, R06, R07, R09, R12, R15), sync canônico de `closing_stock_state`
  (T03), e catálogos P6 TARGET herdados do Pacote A.

## ADENDO — PACOTE C (P5 packages/review/C2 + cockpit + controles B/C)

Execução: CF-PROC0072-E2E-MASTER-EXECUTION-001, baseline `a2921167cf`.
Veredito Pacote B: ACCEPT_WITH_RESIDUAL. Deploy produtivo
**suspenso** — nenhuma ação em `srv-api`, nenhuma migration produtiva.

### Implementado (código + testes, não operação)

- **P5 (V008):** `closing_package` por `recipient_area`,
  `closing_package_version` imutável (DRAFT→FINALIZED→SUBMITTED,
  `previous_version_id`+`change_reason` para complementos/reopen),
  `closing_review_assignment` (REVIEWER por área/pacote, COORDINATOR por
  competência), `closing_area_decision` (append-only, por área obrigatória
  da versão vigente, terminal — sem edição/estorno),
  `closing_clarification` (OPEN bloqueia conclusão),
  `closing_notification_event` (outbox informativa — nunca critério),
  `closing_terminal_rejection` (só coordenador designado, motivo
  obrigatório, reversível com trilha).
- **Finalize ≠ Submit:** `finalize` congela a versão com snapshot de
  composição (itens P2 aceitos, resultados P3, pendências P4,
  `required_areas` derivados do snapshot) — não notifica nem envia.
  `submit_for_review` torna a versão visível in-portal aos revisores
  designados (nunca anexo de e-mail). Submissão usa OCC por `revision`.
- **Revisão:** visibilidade fail-closed por assignment — revisor sem
  vínculo não lista nem abre pacote sibling; decisão exige assignment
  ativo na área obrigatória da versão vigente; aceite é terminal; nova
  versão zera exigências de aceite (histórico preservado);
  reatribuição/desativação preserva decisões passadas e autoria —
  substituto atua só futuramente. Pacote pode ser submetido sem
  revisor, mas nunca conclui sem aceite humano real.
- **C2 — conclusão derivada, nunca forçável** (`derive_closing_state`):
  todos os pacotes aplicáveis SUBMITTED + aceite por área obrigatória da
  versão vigente + zero esclarecimento OPEN + zero rejeição terminal
  ACTIVE + todo domínio P3 com proveniência OFFICIAL. Vacuidade nunca
  conclui: zero pacotes aplicáveis → `no_applicable_packages`; versão
  sem `required_areas` → `no_required_areas`.
- **Controle B/C — P3 proveniência (V009):** `provenance_kind`
  (DECLARED|OFFICIAL) + `official_document_id` em
  `closing_reconciliation`. OFFICIAL exige documento anexado na
  competência (fail-closed). Conclusão exige OFFICIAL em todos os
  domínios — conciliação registrada/declarada não comprova fechamento.
- **Controle B/C — ownership P4:** claim sobre pendência de terceiro e
  transição por ator sem ownership/papel elegível são bloqueados
  (`PendencyOwnershipRequired`, 409); ator `manage` segue elegível para
  transições governadas; terminal continua imutável; escopo de filial
  fail-closed.
- **Cockpit (`GET …/cockpit`):** composição read-only dos estados reais
  P2 (snapshot por estado), P3 (por domínio: source_state,
  provenance_kind, divergência), P4 (por estado) e P5 (closing-state
  derivado com `blocking_reasons`) — fonte indisponível é bloqueio,
  nunca sucesso.
- **MFE:** `packagesApi`, página `/closing/packages` (lista por
  destinatário, detalhe com versões/áreas/decisões/esclarecimentos,
  ações manage e de revisor) e `/closing/cockpit`; rotas no manifest +
  catálogo do hub; Help contextual `packages`/`cockpit` sincronizado
  com docs 12/29/37.

### Testes executados

- Backend: **475 passed** — inclui suíte PG `test_pg_package_c.py`
  (19): ownership P4 (claim indevido, transição não-owner, owner e
  manage positivos), proveniência P3 (OFFICIAL exige artefato, default
  DECLARED, DECLARED bloqueia conclusão, OFFICIAL desbloqueia),
  visibilidade sibling, finalize bloqueado por checklist pendente,
  submit+freeze de áreas, outbox de notificação, decisão exige
  assignment, clarification bloqueia, aceite terminal, nova versão zera
  aceites, rejeição terminal exige coordenador, reopen preserva
  histórico, reatribuição preserva aceite, independência entre
  destinatários, falha de notificação não afeta conclusão, e
  não-vacuidade (zero pacotes aplicáveis = PENDING mesmo com P3
  oficial).
- MFE: **158 vitest** (PackagesPage 6, CockpitPage 2) + **25
  estruturais** + `tsc -b` limpo + `vite build` OK.

### Estado honesto

- `HUMAN_ACCEPTANCE`: G2 pendente — testes verdes ≠ aceite de negócio.
- `DEPLOY_STATUS`: não deployado — `srv-api` continua no estado A3;
  V008/V009 aditivas pendentes de aplicação produtiva no startup
  autorizado (G3).
- `SMOKE_AUTHENTICATED`: TEST_NOT_RUN.
- Revisão depende de contratos Core de elegibilidade: assignments são
  governados por `manage` localmente; a elegibilidade canônica por
  grupo/função corporativa permanece pauta G1 (Core é owner).
- R01–R15: classificações preservadas — nenhum relatório oficial
  inventado, nenhuma sincronização T03 fabricada, zero escrita TOTVS.
- Pauta G1 residual: owners/contratos das fontes `PENDING_CONTRACT`
  (R04, R06, R07, R09, R12, R15); sync canônico de
  `closing_stock_state` (T03); contratos Core de elegibilidade por
  grupo/função e vínculo formal de coordenador; catálogos P6 TARGET
  herdados.

## ADENDO — PACOTE D (E2E, integração, homologação preparada)

Execução: CF-PROC0072-E2E-MASTER-EXECUTION-001, baseline `bc6d85a7f6`.

### D1 — Teste integrado do fechamento (PROVEN)

Suíte `tests/test_pg_e2e_closing_flow.py` em PostgreSQL real
descartável (R4, V001→V009 em banco limpo), cobrindo o cenário
completo do doc 104 §D1 sem estado inferido:

- competência aberta do template publicado → snapshot imutável;
- P2: attach → aceite humano; rejeição com motivo → reversão →
  aceite; substituição → rebaixa para EXPECTED → revalidação;
- matriz R01–R15 derivada do snapshot (itens vinculados por R-ID
  validados — nada promovido a relatório oficial);
- P3: cutoff único, conciliação DECLARED → READY_TO_CLOSE, upgrade
  OFFICIAL com artefato → C2 satisfeito;
- P4: pendência criada → classificação confirmada → claim →
  IN_ANALYSIS → RESOLVED pelo responsável; não-owner bloqueado;
- P5: dois destinatários (CONTABIL/FISCAL) independentes, dois
  revisores, duas PackageVersions (complemento exige novo aceite),
  esclarecimento open→resolve, rejeição terminal pelo coordenador →
  reversão → conclusão derivada apenas quando C2 satisfeito;
- negativos: revisor não designado, OCC obsoleto, divergência
  R$ 0,01, pendência não-owner, rejeição terminal ativa;
- trilha append-only: eventos de todos os ciclos presentes;
- segunda competência isolada — estados não compartilhados.

### D2 — Pendências de integração (verificação)

| Item | Estado |
|---|---|
| Ownership P4 | PROVEN (claim/transição exigem owner ou manage) |
| Elegibilidade Core p/ decisões | PARTIAL — assignments governados por `manage`; contrato Core grupo/função = pauta G1 |
| Proveniência oficial P3 | PROVEN (DECLARED ≠ OFFICIAL, artefato obrigatório) |
| Sync T03/STOCK_CLOSED | PROVEN (só `closing_stock_state` canônico; sem sync fabricado) |
| Imutabilidade evidência no PackageVersion | PROVEN (snapshot referencia `document_version_id` imutável) |
| Catálogos P6 p/ destinatários/áreas | TARGET — pauta G1 (seed CONTABIL/FISCAL funciona) |
| Quórum de revisão por área | PROVEN (aceite por área obrigatória da versão vigente) |
| Conclusão mensal C2 | PROVEN (derivada; vacuidade bloqueada) |
| Notificações | PROVEN outbox EMITTED/UNAVAILABLE — nunca critério C2 |
| Minhas tarefas | NOT_IMPLEMENTED — superfície TASK-01..12 segue TARGET |
| Integridade arquivos pós-recreate | TEST_NOT_RUN — verificação de volume é passo G3/D4 |
| Histórico/auditoria append-only | PROVEN |
| R01–R15 sem contrato | PROVEN (`PENDING_CONTRACT`, sem falso oficial) |

### D3 — Qualidade executada

- Backend: **478 passed** (unitários, rotas HTTP/BFF, PG real R4,
  OCC, autorização +/−, aceite pacotes A/B/C, E2E integrado).
- Migrations: suíte PG executa V001→V009 em banco limpo a cada
  execução; sem reset produtivo.
- Frontend: **159 vitest** + **25 estruturais** + `tsc -b` limpo +
  `vite build` OK.
- Deep links `closing/packages/{period}` e `closing/cockpit/{period}`
  adicionados; refresh é server-driven.
- Acessibilidade: páginas usam componentes do design system
  (CfDialog, CfSectionCard, ActionButton) — auditoria formal de
  a11y/teclado/mobile registrada como TEST_NOT_RUN (não executada
  com ferramenta dedicada nesta execução).
- Core indisponível / Core contracts: rotas falham fechado (401/403)
  — coberto na suíte de rotas.

### Matriz RQ/AC (doc 23) vinculada ao SHA de release

| Família | Estado |
|---|---|
| RQ-P1 (abertura/snapshot) | PROVEN |
| RQ-P2 (67 — documentos/validação) | PROVEN |
| RQ-P3 (cutoff/conciliação) | PROVEN c/ proveniência |
| RQ-P4 (pendências) | PROVEN c/ ownership |
| RQ-P5/P5-AREA/P5-F..J (pacotes/revisão/C2) | PROVEN |
| RQ-P6 (admin) | PARTIAL — admin de versões PROVEN; catálogos TARGET |
| RQ-AUTHZ/SEC (autorização/segurança) | PROVEN em rotas/repos |
| RQ-HELP | PROVEN (help contextual sincronizado) |
| RQ-HOME/NAV | PROVEN (hub/catálogo) |
| RQ-OVW/RQ-ROOM/RQ-TASK/RQ-USER | TARGET — superfícies futuras, não implementadas |
| RQ-UX | PARTIAL — padrões aplicados; auditoria a11y TEST_NOT_RUN |
| AC-P2-UP-01..24, AC-P2-VAL-01..13, AC-P3-PARITY-01 | PROVEN (suítes dedicadas) |

### G2/G3 — estado honesto

- `G2_HUMAN_ACCEPTANCE`: PENDENTE — pacote de demonstração
  preparado neste adendo; a decisão é humana e não pode ser
  substituída por testes.
- `G3_RELEASE_AUTHORIZATION`: PENDENTE — bloqueado por G2.
- `DEPLOY_STATUS`: NÃO DEPLOYADO — `srv-api` permanece no estado A3.
- `POST_DEPLOY_CHECKS` (D4): TEST_NOT_RUN — depende de G3.

### Pauta G1 consolidada (decisões materiais pendentes)

1. Contrato Core de elegibilidade por grupo/função corporativa e
   vínculo formal de coordenador de competência (hoje: assignments
   governados por `manage` local).
2. Owners/contratos das fontes `PENDING_CONTRACT` (R04, R06, R07,
   R09, R12, R15) e confirmação de `MANUAL_EVIDENCE`/`EXTERNAL`.
3. Sincronização canônica de `closing_stock_state` pelo owner T03.
4. Catálogos P6 TARGET: bancos/contas, motivos de rejeição,
   attachment roles, notification targets (RQ-P6-05..08,
   RQ-ADM-01/02/05/07/08).
5. Escopo das superfícies RQ-OVW/RQ-ROOM/RQ-TASK/RQ-USER em roadmap
   posterior.

---

## CF-PROC0072-E2E-G1-G2-CLOSURE-001 — correção cirúrgica C2 + consolidação G1/G2

Baseline: `215c5821be`. Escopo: segurança da decisão de conclusão C2,
origem das áreas obrigatórias (P5-H), pauta G1 única e matriz de
homologação G2. Pacotes A–D não reabertos; auditoria geral não repetida.

### 1. Correção da segurança C2

`ClosingPackageRepository.derive_closing_state` antes só exigia
`provenance_kind=OFFICIAL` por domínio. Agora a conclusão exige a
pré-condição P3 **vigente completa**, reutilizando
`ClosingP3Repository.get_p3_state` como fonte canônica (sem duplicar
fingerprint/divergência):

- cutoff confirmado;
- revalidação vigente (`input_fingerprint` igual ao estado atual);
- todas as fontes `AVAILABLE`;
- divergência monetária exatamente zero por domínio;
- `provenance_kind=OFFICIAL` por domínio (registrado != comprovado).

`STOCK_CLOSED` canónico **não** mascara inputs obsoletos:
`get_p3_state` retorna `STOCK_CLOSED` antes de avaliar blockers —
o C2 passou a consultar `p3.blockers` em vez do estado derivado, e
`_readiness_blockers` (gate do finalize) recebeu a mesma correção.
Estado de estoque e conclusão mensal são conceitos distintos.

Blockers novos no C2: `p3_cutoff_not_confirmed`,
`p3_revalidation_required`, `p3_source_unavailable:<dom>`,
`p3_divergence:<dom>` — além dos já existentes
`p3_reconciliation_missing:<dom>` / `p3_declared_only:<dom>`.

### 2. Origem das áreas obrigatórias (P5-H)

Antes: `required_areas` = conjunto de áreas dos assignments ativos no
momento da submissão — conflação entre obrigação e vínculo operacional.

Agora: `required_areas = [recipient_area]` congelado na PackageVersion
na submissão. A obrigação por área vem do **tipo de pacote**; o reviewer
assignment é vínculo operacional avaliado na decisão (um revisor
designado depois da submissão consegue aceitar normalmente).

`DECISION_REQUIRED (G1)`: o contrato P5-H pede "áreas obrigatórias
versionadas por tipo de pacote" mantidas pelo P6. Esse catálogo físico
P6 **não existe** (doc 37 §17 lista "P6 versioned snapshot" como
TO_INVENTORY). A V1 assume a auto-área do pacote como obrigação —
sem catálogo inventado. Se o PO quiser tipos com múltiplas áreas
obrigatórias, é decisão de contrato P6, não improviso de código.

### 3. Testes (PostgreSQL real, suíte `test_pg_package_c.py`)

| Caso | Resultado |
|---|---|
| Input de conciliação alterado após submissão+aceite | `PENDING` com `p3_revalidation_required` + `p3_divergence`; decisões/versões preservadas; restaura+revalida → `COMPLETED` |
| Fonte `UNAVAILABLE` após conclusão | `PENDING` com `p3_source_unavailable`; restaura → `COMPLETED` |
| `STOCK_CLOSED` + inputs alterados | `PENDING` — estoque fechado não mascara inputs obsoletos |
| `STOCK_CLOSED` + inputs limpos | `COMPLETED` (estado canónico respeitado) |
| Submissão sem reviewer | `required_areas=["FISCAL"]` congelada; `area_not_reviewed` — nunca vacuidade |
| Revisor designado pós-submissão | Consegue aceitar (vínculo na decisão, não na submissão) |
| Aceite oficial + revalidação vigente | `MONTHLY_CLOSING_COMPLETED` (caminho positivo preservado) |

Backend completo: **482 passed** (478 + 4 novos). E2E: 3 passed.

### 4. Pauta G1 consolidada — única

**Impedem a conclusão mensal C2 (material, precisam de decisão):**

1. **Fonte T03 / `closing_stock_state`**: quem é o owner que escreve
   a linha canónica? Sem sync, o estado fica `UNAVAILABLE` — não
   bloqueia C2 (C2 exige P3, não estoque), mas o cockpit e o estado
   `STOCK_CLOSED` dependem disso. *Decisão: owner + contrato de sync.*
2. **Comprovação de relatórios oficiais**: owners/contrato das fontes
   `PENDING_CONTRACT` (R04, R06, R07, R09, R12, R15). Sem elas, os
   domínios P3 só chegam a `DECLARED` — `p3_declared_only` bloqueia
   C2. *Decisão: qual fonte TOTVS/documento comprova cada domínio
   (ENTRADAS_SAIDAS, P7, H02).*
3. **Elegibilidade Core**: contrato T05 grupo/função corporativa por
   área + designação formal de coordenador (DEC-01). Hoje assignments
   são governados por `manage` local. Não bloqueia a *regra* C2, mas
   bloqueia a *legitimidade* dos aceites em produção.

**Podem ficar para entrega posterior (decisão do PO, não bloqueiam C2):**

4. **Catálogo P6 de áreas obrigatórias multi-área por tipo de pacote**
   — V1 usa auto-área; evoluir requer contrato físico P6.
5. **Catálogos P6 TARGET** (bancos/contas, motivos de rejeição,
   attachment roles, notification targets).
6. **Superfícies comuns TARGET**: RQ-OVW / RQ-ROOM / RQ-TASK / RQ-USER.
7. Minhas tarefas/TaskProjection P5 (depende do item 3).

### 5. Matriz de homologação G2

| Dimensão | Estado |
|---|---|
| **Funciona em runtime** | P1 abertura/snapshot; P2 anexo/validação/rejeição/reversão/substituição; P3 cutoff/conciliação/revalidação; P4 pendências/ownership; P5 pacotes/versões/submissão/revisão/esclarecimentos/rejeição terminal/reversão; C2 derivado com P3 vigente; cockpit agregado; admin P6 de versões |
| **Comprovado com dados oficiais** | Em teste: reconciliação `OFFICIAL` exige `official_document_id` anexado — provado em PG real. Em produção: nenhuma fonte oficial sincronizada ainda (G1 itens 1–2) |
| **Funciona manualmente** | `MANUAL_EVIDENCE` R05/R08/R10/R11: anexar artefato + `provenance_kind=OFFICIAL` via upsert autenticado — fluxo completo provado em teste |
| **Permanece TARGET** | RQ-OVW/RQ-ROOM/RQ-TASK/RQ-USER; catálogos P6; R04/R06/R07/R09/R12/R15 `PENDING_CONTRACT`; CLARA/DRE fora de escopo |
| **Impede conclusão mensal** | Fontes oficiais não sincronizadas (C2 exige OFFICIAL vigente); elegibilidade Core/coordenador formal pendente; sync T03 ausente |
| **Testado com atores reais** | TEST_NOT_RUN — smoke autenticado exige sessão humana em ambiente implantado (pós-G3) |
| **Exige aceite da Controladoria** | Fluxo completo P1→C2; classificação R01–R15; operação manual de evidências; bloqueios honestos do cockpit; critério de rejeição terminal |

### 6. Estado residual

- `DEPLOY_STATUS`: NÃO DEPLOYADO — `srv-api` em estado A3;
  V004–V009 aditivas pendentes de startup autorizado.
- `PRODUCTION_MIGRATIONS`: NOT_RUN.
- `SMOKE_AUTHENTICATED`: TEST_NOT_RUN.
- `G2_HUMAN_ACCEPTANCE`: PENDENTE — matriz acima pronta para decisão.
- `G3_RELEASE_AUTHORIZATION`: PENDENTE — bloqueado por G2.

---

## Adendo — GO 105: conclusão integral das pendências antes do refinamento

**Execução**: `CF-PROC0072-REMAINDER-BUILD-GO-001` · baseline `acfdd136f1` →
HEAD `0b44b48d3d` (commits `924c7662ee`, `04b4fc3d7a`, `0b44b48d3d`).

### F1 — P6 completo (implementado)

- Lifecycle governado `DRAFT → REVIEW → PUBLISHED → INACTIVE`:
  `submit_version_for_review`, `return_version_to_draft` (motivo
  obrigatório, auditado), publicação somente a partir de `REVIEW`.
  Um único slot aberto (`DRAFT|REVIEW`) por template; publicação exige
  ≥1 item; eventos `VERSION_SUBMITTED_FOR_REVIEW` e
  `VERSION_RETURNED_TO_DRAFT` na trilha.
- `closing_catalog_entry` (V010): 6 catálogos governados
  (`BANK_ACCOUNT`, `REJECTION_REASON`, `ATTACHMENT_ROLE`,
  `NOTIFICATION_TARGET`, `PACKAGE_REQUIRED_AREA`, `REVIEW_ELIGIBILITY`),
  código = identidade imutável, edição com `revision`/OCC, desativação
  prospectiva, reativação, auditoria. Rotas `/admin/closing-catalogs*`
  (MANAGE) + página `CatalogsAdminPage` no MFE.
- P5-H: `required_areas` consumido do catálogo `PACKAGE_REQUIRED_AREA`
  (attrs `package_type`/`recipient_area` → `areas`); sem entrada,
  fallback auditado para `[recipient_area]` com `source` registrado —
  nada é inferido silenciosamente. Seeds multi-área físicas = decisão
  G1 (catálogo vazio é estado legítimo).

### F2 — elegibilidade Core (implementado com binding governado)

- `REVIEW_ELIGIBILITY` por área: binding configurado ⇒ decisão exige
  interseção entre `user.groups` (resolvidos pelo RBAC Core no
  middleware) e o conjunto configurado — `reviewer_not_eligible` 403,
  fail-closed. Sem binding ⇒ modo `assignment_only` registrado, nunca
  inventado. TaskProjection aplica o mesmo binding na projeção.
- Coordenador formal/S2S group-function dedicado: **G1** (o binding por
  catálogo cobre o caso contratual disponível; contrato Core dedicado
  permanece decisão externa).

### F3 — R01–R15, P3 e T03 (honestidade preservada)

- R01/R02 (SE5 baixas) e R03 (SB9/P7 estoque) já operacionais via
  api-delpi owner (JWT delegado + gateway S2S) — nenhuma promoção a
  "oficial" sem contrato. Classificação da matriz preservada:
  `PENDING_CONTRACT` (R04/R06/R07/R09/R12/R15), `MANUAL_EVIDENCE`
  (R05/R08/R10/R11), externos (R13/R14). Contratos oficiais = G1.
- P3: cutoff/revalidação/fingerprint/divergência R$0,00 intactos; C2
  revalida blockers (pacote anterior). T03 `STOCK_CLOSED`: owner/sync
  = G1 — estado tratado como `UNAVAILABLE` quando ausente, nunca
  inferido.

### F4 — P5 completo (implementado)

- Outbox `closing_notification_event` (V010) + dispatcher Core T02:
  `POST /integrations/notifications` com S2S token, `sourceApp`,
  `portal_route` action, `userIds`, permission codes e dedupe.
  Emissão atômica para `PACKAGE_SUBMITTED_FOR_REVIEW`,
  `PACKAGE_CLARIFICATION_OPENED`/`RESOLVED`,
  `COMPETENCE_TERMINALLY_REJECTED`/`REJECTION_REVERTED`. Falha de
  entrega marca `FAILED` — nunca toca estado de negócio (testado com
  Core indisponível).
- TaskProjection self-only `GET /me/tasks` (pendências P4 sob
  responsabilidade, revisões P5 pendentes por área, esclarecimentos
  abertos do próprio submitter) — nunca task de outro usuário; deep
  links autorizados por recurso.
- `GET /me/profile`: read-through self-only ao Core
  `/me/person-profile` + identidade/grupos/permissões do contexto —
  sem cadastro paralelo; `/viewer-photo` read-through existente.
- Lock pós-submissão: `locked_item_keys` congela evidência e decisões
  de itens presentes na PackageVersion SUBMITTED —
  `item_locked_by_submitted_package` (409) em upload, replace, cancel,
  decide-per-attachment e decide-per-set; correção só via nova versão.

### F5 — páginas comuns (implementado o que tem contrato)

- `closing/my-tasks` — `MyTasksPage` (projeção real, filtros por
  competência, resumo por tipo, deep links por recurso).
- `profile` — `ProfilePage` (dados Core read-through, grupos,
  permissões, foto; self-only, sem edição local).
- `closing/admin/catalogs` — `CatalogsAdminPage` (cartões por
  catálogo, CRUD com OCC, desativação confirmada, reativação).
- `ChecklistAdminPage` — lifecycle REVIEW: "Enviar para revisão" em
  DRAFT, "Publicar"/"Devolver" (com motivo) em REVIEW, badge `Em
  revisão`, eventos novos no histórico.
- Nav/home: "Minhas tarefas" entra no shell nav e no hub; highlight
  `tasks` do hero passa a exibir contagem real de `/me/tasks`
  (indisponível permanece "—" para competência/atenções sem fonte).
- `Visão geral` dedicada com indicadores owner/fórmula/origem e
  `Sala de interação`: **G1** — sem contrato de indicadores nem
  capability de mensagens; nada foi fabricado.

### F6 — qualidade

- Migrations V001→V010 aplicadas limpas em PostgreSQL descartável por
  execução (ownership-token); checksum/imutabilidade mantidos.
- Testes novos: 9 PG (lifecycle, catálogo OCC, P5-H catálogo+fallback,
  binding fail-closed, outbox+dispatch sucesso/falha, lock de
  validação, lock de upload, TaskProjection self-only) + 11 rotas
  (bearer/manage/access/self) + 8 vitest (2 lifecycle admin, 4
  MyTasksPage, 4 CatalogsAdminPage).
- Resultados: **502 backend passed** · **169 vitest passed** ·
  7 estruturais .mjs passed · `tsc -b` limpo · build Vite OK ·
  eslint sem erros (warnings iguais aos preexistentes).

### Pauta G1 — estado após este GO

| Item | Estado |
|---|---|
| T03 `closing_stock_state` owner + contrato de sync | DECISION_REQUIRED |
| Comprovação oficial R04/R06/R07/R09/R12/R15 (owners, operações reais) | DECISION_REQUIRED |
| Core T05: contrato S2S group/function dedicado + coordenador formal (DEC-01) | DECISION_REQUIRED (binding por catálogo implementado) |
| Seeds físicas multi-área P5-H (`PACKAGE_REQUIRED_AREA`) | DECISION_REQUIRED (mecânica pronta, fallback auditado) |
| Visão geral dedicada (owner/fórmula/origem dos indicadores) | DECISION_REQUIRED |
| Sala de interação (capability de mensagens cross-app) | DECISION_REQUIRED |
| Seeds E01/E05/E06 dos demais catálogos | DECISION_REQUIRED (conteúdo, não contrato) |
| CLARA/MCP e Accounting/DRE | FORA DE ESCOPO — gates próprios preservados |

### Residuais honestos

- `G2_HUMAN_ACCEPTANCE`: PENDENTE — homologação humana, não inferível
  de testes.
- `G3_RELEASE_AUTHORIZATION` / deploy: PENDENTE — `srv-api` intocado;
  migrations V004–V010 aguardam startup autorizado.
- `SMOKE_AUTHENTICATED`: TEST_NOT_RUN.
- Refinamento visual único: executado em nível de consistência de
  código (heros, help, a11y, tokens) — revisão visual operacional
  depende de ambiente implantado (pós-G3).
