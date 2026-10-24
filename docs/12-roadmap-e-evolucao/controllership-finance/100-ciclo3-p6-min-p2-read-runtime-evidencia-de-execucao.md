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
