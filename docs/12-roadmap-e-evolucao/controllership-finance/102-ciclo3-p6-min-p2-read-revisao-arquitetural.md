# Documento 102 — Revisão arquitetural independente do incremento P6-MIN + P2-READ

**Data:** 2026-10-24. **Task:** `CF-C3-P6-MIN-P2-READ-GPT-ARCHITECTURE-REVIEW-001`.
**BASE/HEAD revisado:** `f27dc307a48a5c9b37e6469e1c12d5f56ddbd896` (main) — commit da implementação. **Branch/worktree:** detached HEAD limpa.
**Método:** leitura adversarial do diff, revisão linha-a-linha de persistência/AuthZ/contratos/MFE, reexecução de suítes e **probes adicionais em PostgreSQL real** além dos testes reportados. O relatório do executor (doc 100) foi tratado como evidência, não como prova — duas imprecisões dele foram corrigidas nesta revisão (operationIds reais e path de `open`).

## 1. Arquivos efetivamente revisados

- `migrations/V001__create_closing_checklist_schema.sql` + `V002__seed_monthly_closing_checklist_v1.sql` (integral)
- `infrastructure/persistence/{plugins_db, migrations_runner, closing_checklist_repository}.py` (662 linhas, integral)
- `interface/http/{authz.py, routes/admin_checklist_routes.py, routes/competences_routes.py}` (integral)
- `domain/closing_checklist/errors.py`, `startup/run_migrations_on_startup.py`, `config.py`, `main.py`, `requirements.txt`, `infra/docker-compose.yml` (diff)
- `shared/delpi_auth/{authz_core.py, middleware/fastapi_auth.py}` — autoridade de effective permissions e fail-closed
- MFE: `competencesApi.ts`, `httpClient.ts` (`httpPost`), `ClosingChecklistPage.tsx`, manifest, rotas, catálogo, Help
- Testes: `test_pg_closing_checklist.py`, `test_admin_checklist_routes.py`, `test_closing_competences_routes.py`, `test_migrations_runner.py`, `ClosingChecklistPage.test.tsx`, estruturais

## 2. Matriz RQ/AC → implementação → teste → evidência

| Invariante/contracto | Implementação | Evidência | Estado |
|---|---|---|---|
| Schema isolado `controllership_finance` | V001; `_q()` qualifica toda tabela | PG real: nenhum objeto fora do schema | PROVEN |
| Migrations imutáveis + SHA-256 | `migrations_runner.run_migrations` | restart no-op + checksum divergence → `MigrationError` (teste unitário) | PROVEN |
| Seed 53 itens `DRAFT`, sem publish automático | V002 (53 tuplas verificadas, contagem SQL) | `test_seed_53_items_draft` | PROVEN |
| DRAFT não abre competência | `resolve_published_version` filtra `PUBLISHED` | `test_open_without_publish_fails` → `no_published_template` 409 | PROVEN |
| Publish só por operação autorizada | rota `manage` efetivo + UPDATE `status='DRAFT'` atômico | route tests + probe real: 4 threads → 1 winner, 3×`version_not_draft` | PROVEN |
| Edição de publicado negada | `WHERE status='DRAFT' AND revision=%s` | `test_published_immutable` | PROVEN |
| OCC/stale revision | `revision` otimista | `test_stale_revision_rejected` | PROVEN |
| Um DRAFT por template | índice parcial único | `test_second_draft_rejected` | PROVEN |
| Abertura concorrente ⇒ 1 competência | `UNIQUE(period)` + `ON CONFLICT DO NOTHING` + refetch | **probe real nesta revisão: 8 threads → 1 created, 7 replays, 1 registro, 53 `EXPECTED`** | PROVEN |
| Replay idempotente | retorna existente, 200 | `test_open_replay_idempotent` + probe | PROVEN |
| Snapshot imutável, v1×v2 isolados | cópia congelada `competence_checklist_item`, `source_*` sem FK | `test_competence_resolution_uses_vigente` | PROVEN |
| `EXPECTED ≠ entregue/validado` (RQ-P2-13) | `CHECK (state IN ('EXPECTED'))`; UI explícita | PG: `all(state='EXPECTED')`; teste UI | PROVEN |
| Sem R-ID sem automação fictícia (RQ-P2-14) | `totvs_report_ref` nullable, propagado nulo | seed + render honesta | PROVEN |
| Audit append-only (draft/publish/inactivate/open) | `_audit` dentro da mesma transação, só em criação real | `test_audit_trail_append_only` | PROVEN |
| ACCESS ≠ MANAGE | `authorized_user`/`authorized_admin` separados | `test_access_only_is_forbidden`, `test_manage_only_is_forbidden` | PROVEN |
| Service principal rejeitado | `principal_type != "user"` → 403 | `test_service_principal_denied` | PROVEN |
| Core indisponível ⇒ fail-closed | `rbac_unavailable` → 503; sem claims de permissão | `test_rbac_unavailable_fails_closed` | PROVEN |
| Sem permission nova | manifest permanece 2 permissions | manifest + residual search | PROVEN |
| Deep link/F5, Help, estados honestos | rotas `:period`, `CfQueryErrorBanner`, Help no diff | 100 vitest + 25 estruturais | PROVEN |
| Smoke autenticado E2E | — | não executado | TEST_NOT_RUN |

## 3. Achados adversariais

### R1 — Erro não tipado em `item_key` duplicado (menor)
`update_draft_items` com payload contendo `item_key` repetido dispara `UniqueViolation` **não mapeada** → exceção crua → HTTP 500 em vez de 409/422 tipado. Provado em PG real (probe P3). Critério de correção: traduzir `UniqueViolation` de `checklist_template_item` para erro de domínio (ex.: `duplicate_item_key`, 409/422) com teste.

### R2 — Fallback de `_actor` para e-mail quebra coluna UUID (menor)
`_actor(user) = user.id or user.email`; `actor_subject`/`opened_by` são `UUID`. Principal humano real sempre tem `id` = sub UUID do Core, então o caminho é inalcançável em produção — mas o fallback sugere semântica que falharia com `InvalidTextRepresentation` → 500 (probe P4). Correção mínima: remover fallback ou validar UUID.

### R3 — Drift de nomenclatura contratual vs doc 96 (não material)
Doc 96 era candidato, não congelamento: `:{publish,inactivate}` → implementado `/publish`, `/inactivate`; operationIds camelCase → snake_case (impl segue a convenção real dos irmãos — `list_portal_purchase_requests`); `already_published` → `version_not_draft` (409 equivalente); `db_unavailable` → `persistence_unavailable`. Recomendado reconciliar doc 96 ou registrar variantes aceitas. Doc 100 foi corrigido nesta revisão (operationIds reais e path de `open` = `POST /closing/competences {period}`, como o contrato).

### R4 — Fixture PG faz `DROP SCHEMA controllership_finance CASCADE` (observação)
`test_pg_closing_checklist.py` destrói o schema no banco-alvo. Hoje é opt-in via `CF_TEST_PG_*` e roda só em ambiente de teste; se apontado para um banco com dados reais, apaga. Sugerido: schema de teste dedicado/sufixo ou guarda explícita de ambiente. Não é migration — não viola `plugins-migrations-no-reset-prod`, mas merece endurecimento.

### R5 — RBAC com fallback de cache stale (observação de plataforma)
`load_user_rbac` (middleware compartilhado) serve cache stale quando o Core falha; permissões revogadas podem ser servidas dentro da janela de stale. Política transversal vigente, idêntica nos irmãos; mutações materiais poderiam futuramente usar `force_refresh`. Não é defeito do slice.

### R6 — Append-only por convenção (observação)
`closing_audit_event` é append-only por contrato de aplicação; não há `REVOKE UPDATE/DELETE`. Idêntico ao padrão dos irmãos.

### R7 — TOCTOU resolve×inactivate (observação teórica)
`resolve_published_version` executa fora da transação de `open_competence`; uma inativação concorrente na janela permite abertura com a versão recém-inativada. O snapshot é ponto-no-tempo, logo o efeito é defensável (a versão estava publicada no instante da resolução); registrado como janela teórica, sem impacto prático observado.

### R8 — `opened_by` retornado ao leitor (observação)
`open`/`get` retornam `opened_by` (UUID do abridor). Baixo risco (UUID opaco, rota access-gated); consistente com auditoria visível.

## 4. Checkpoints adicionais do handoff (doc 101)

- **Seed × matriz doc 95:** 53/53 tuplas conferidas; `CK-E-27` com nome exato da fonte, `totvs_report_ref=NULL` e `requirement_notes` honesta ("Produtor R-ID pendente (CP-D03 / TO_INVENTORY)") — sem R-ID inventado; distribuição de R-IDs confere (R13×12 extratos, R14×4 importações/câmbio, R01×3, R02×2 etc.); `recipient_area=NULL` preservado onde a fonte deixa lacuna; contexto industrial legado não vazou; planilha privada não versionada. `PROVEN`.
- **Admin scope:** implementação interpreta "escopo administrativo" como o próprio `manage` efetivo — única permission administrativa do produto — padrão `can_administer` dos irmãos e decisão CP-D05=A. **Advertência registrada:** se o PO pretender roster administrativo mais restrito que "todo usuário manage", será necessário mecanismo de escopo dedicado (não existe hoje no Core para este produto). Interpretação corrente: aceita; risco documentado.
- **Sem acesso direto à api-delpi pelo MFE:** confirmado — cliente bate só na BFF do produto (`cfApiUrl`).

## 5. Residual search e escopo

Confirmado no HEAD: zero upload/anexo, zero validação documental, zero R01–R15 oficial, zero P3/P4/P5, zero CLARA, zero permission/página DRE, zero escrita ERP/TOTVS, zero deploy. Imports cross-domain: nenhum. Segredos em logs/migrations: nenhum. Seed: rótulos oficiais apenas, sem bancos/pessoas/valores — lacunas (responsável/validador/destinatário) preservadas como `NULL`, sem invenção (CP-D02/03 honestos).

## 6. Testes executados nesta revisão

- BFF: `131 passed` (10 PG reais) — reexecutado no HEAD.
- MFE: `100 passed`/13 arquivos, `tsc` OK, eslint 0 problemas, estruturais `25/0`, build OK.
- Probes novos em PG real: concorrência 8 threads (1 competência), publish concorrente (1 winner), `item_key` duplicado (R1), actor não-UUID (R2).
- Smoke autenticado: `TEST_NOT_RUN` — declarado, não inflado.

## 7. Avaliação do GO e veredito

O GO `CF-C3-P6-MIN-P2-READ-RUNTIME-GO-001` foi cumprido: menor diff correto, decisões CP-D01/04/05 respeitadas, invariantes provados em PostgreSQL real (incluindo concorrência verdadeira, agora evidenciada), AuthZ backend-first fail-closed, UI honesta sem falso entregue. Nenhum desvio de escopo, nenhuma brecha de autorização material, nenhuma regressão.

**Veredito: `ACCEPT_WITH_RESIDUAL`.** Nenhum achado bloqueia o aceite. R1/R2 são endurecimento de erros tipados (REWORK menor recomendado como task de higiene, ~30 linhas + 2 testes); R3 é reconciliação documental; R4–R8 são observações de prateleira.

## 8. Próximo checkpoint permitido

`CF-C3-P2-UPLOAD-CONTRACT-GATE-001` — **documental apenas**: contrato de upload (documentos externos, PDFs/extratos/planilhas, storage persistente, metadados+hash, versionamento, download autorizado, retenção/auditoria, vínculo ao item do checklist). `P2-Upload ≠ validação humana`. Implementação exige contrato fechado e GO próprio; `DEPLOY_PRODUCTION_AUTHORIZED=NO` permanece.

---

## Adendo — Hardening R1/R2/R4 (`CF-C3-P6-P2-POST-REVIEW-HARDENING-R1-R2-R4-001`)

Executado sobre BASE_SHA `73a02393dc` (pós-revisão). Escopo estrito de hardening; nenhuma feature, tela, permission, workflow ou deploy novo. Achados históricos das seções anteriores preservados.

### R1 — CORRIGIDO (PASS)

- **Causa raiz:** `update_draft_items` deixava `UniqueViolation` de `item_key` duplicado escapar → HTTP 500.
- **Correção:** novo erro de domínio `DuplicateItemKey` (`duplicate_item_key`, 409); o repositório traduz `psycopg.errors.UniqueViolation` no INSERT dos itens do DRAFT — dentro de `conn.transaction()`, logo DELETE+UPDATE+INSERT fazem rollback integral (sem substituição parcial; `revision` e itens anteriores intactos). Mesmo padrão já usado por `DraftAlreadyOpen`.
- **Evidência:** `test_duplicate_item_key_typed_and_atomic` em PG real — payload com `item_key` duplicado levanta `DuplicateItemKey`; versão DRAFT mantém `revision`, `status=DRAFT` e lista de itens byte-a-byte; mapeamento HTTP `duplicate_item_key → 409` coberto na matriz parametrizada de erros. Concorrência/OCC: `test_stale_revision_rejected` e `test_second_draft_rejected` seguem verdes.

### R2 — CORRIGIDO (PASS)

- **Causa raiz:** `_actor(user) = user.id or user.email` admitia string não-UUID em coluna `UUID` → `InvalidTextRepresentation` → 500.
- **Correção:** `actor_subject(user)` canônico em `interface/http/authz.py` — aceita somente `user.id` validado por `uuid.UUID()`; ausente/malformado ⇒ `Unauthorized` (fail-closed, antes de qualquer persistência); sem fallback, sem identidade alternativa, sem log de token/e-mail. Todas as mutações auditáveis (create/update/publish/inactivate/open) usam o resolvedor canônico.
- **Evidência:** testes de rota — UUID válido alcança o repositório (`actor == sub`), id não-UUID ⇒ 401 sem chamada ao repo, `sub` ausente ⇒ 401 no middleware, service principal ⇒ 403 (pré-existente). Em PG real, `closing_audit_event.actor_subject` contém apenas UUIDs válidos.

### R4 — CORRIGIDO (PASS)

- **Causa raiz:** fixture executava `DROP SCHEMA controllership_finance CASCADE` no banco indicado por `CF_TEST_PG_*`, sem prova de descartabilidade.
- **Correção:** banco **dedicado e recriável** (`CF_TEST_PG_NAME`), validado por `assert_safe_test_database` — nome SQL-safe, obrigado a conter `test`, e jamais `plugins_hub`/`postgres`/`delpi_core`/`template*`. A limpeza é `DROP DATABASE`/`CREATE DATABASE` do banco dedicado via conexão administrativa (`CF_TEST_PG_ADMIN_DB`, default `postgres`), exigindo opt-in `CF_TEST_PG_ALLOW_DESTRUCTIVE=1`. Destino ambíguo falha (erro de fixture) **antes de qualquer DDL**; sem opt-in a suíte faz skip explícito. Migrations produtivas intactas.
- **Evidência:** `test_pg_test_target_guard.py` (16 casos: bancos protegidos, ambíguos, injeção, vazio × dedicados). Probes reais: `CF_TEST_PG_NAME=plugins_hub` + opt-in ⇒ 11 erros de fixture, `plugins_hub.controllership_finance` preservado; `controllership_finance_test` sem opt-in ⇒ 11 skips; com opt-in ⇒ 11 testes PG executam de verdade (migrations, publish, concorrência, idempotência, auditoria, atomicidade R1) e o banco é dropado no teardown — `plugins_hub` nunca alvo.

### Regressão pós-hardening

- BFF: `143 passed` (era 131; +12 testes R1/R2/guarda) + 11 skips sem env PG.
- PG real dedicado: `27 passed` (11 integração + 16 guarda).
- MFE closing: `41 passed`/3 arquivos — zero alteração de MFE neste diff.
- Residual search: zero fallback de e-mail, zero `DROP SCHEMA` em fonte, `UniqueViolation` sempre traduzido, permissions inalteradas (`access`/`manage`/`home`), zero conteúdo fora de escopo.

R3 (drift documental) permanece como observação de prateleira; R5–R8 inalterados. Deploy de produção: NÃO REALIZADO.

---

## Adendo 2 — Rework de segurança R4 (`CF-C3-HARDENING-R4-SAFETY-REWORK-001`)

Revisão arquitetural independente do hardening `1ad43e04`: **REWORK restrito a R4**. R1/R2 aceitos como consistentes e preservados. Achados históricos das seções anteriores mantidos.

### Problema residual confirmado pelo revisor

A proteção anterior exigia nome com `test` + opt-in, mas executava `DROP DATABASE IF EXISTS "<CF_TEST_PG_NAME>"` sobre o nome configurado. Nome não prova descartabilidade e opt-in não prova ownership: um banco preexistente `plugins_hub_test` seria destruído com credenciais administrativas suficientes — e o próprio teste de guarda o classificava como admissível.

### Mecanismo adotado — banco efêmero com prova de ownership

`tests/pg_test_isolation.py` (novo, testável sem PG real):

- `create_owned_test_database`: `CREATE DATABASE` sem `IF NOT EXISTS` sobre nome efêmero `cf_test_<prefixo>_<uuid12>` (retry de identificador em `DuplicateDatabase`, nunca DROP); grava `cf_test_run_ownership.run_token` dentro do banco criado;
- `drop_owned_test_database`: lê o marcador no alvo; DROP somente se `token == owned.run_token`; qualquer incerteza ⇒ `False`, nenhum DDL;
- o teardown usa o objeto `owned` capturado — mutação de env pós-setup não redireciona o DROP;
- `require_test_environment` exige `CF_TEST_PG_CLUSTER=test` (cluster declarado) **e** `CF_TEST_PG_ALLOW_DESTRUCTIVE=1` (opt-in) antes de qualquer DDL;
- `assert_safe_test_prefix` mantém fail-closed sobre prefixo ambíguo/protegido; identificadores sempre via `sql.Identifier`.

### Respostas à revisão adversarial (com evidência)

| Pergunta | Resposta |
|---|---|
| Nome manipulado alcança outro recurso? | Não — nome gerado por execução (uuid), prefixo regex-validado, quoting `sql.Identifier` (teste de injeção prova identificador único). |
| Env muda entre setup e teardown? | Teardown usa `owned`/`admin_db` capturados — teste de mutação prova. |
| Falha parcial ⇒ DROP no recurso errado? | Token conferido; incerteza ⇒ `False` sem DROP (3 cenários testados). |
| Preexistente confundido com o da execução? | `CREATE` sem `IF EXISTS` + uuid + marcador — probe real com `plugins_hub_test` isco preservado. |
| Jobs simultâneos destroem-se mutuamente? | Nomes e tokens exclusivos por execução; cada teardown só dropa o próprio token. |
| Cleanup atrasado atinge banco reutilizado? | Token divergente ⇒ nenhum DROP. |
| Proteção depende só de convenção de nome? | Não — ownership provado por marcador interno. |
| Opt-in interpretado como prova de isolamento? | Opt-in apenas autoriza; a prova é o token de ownership. |
| Credencial permite destruição fora do esperado? | `CF_TEST_PG_CLUSTER=test` exigido; mesmo em cluster errado, o único alvo possível é o efêmero próprio. |
| Erro de conexão ⇒ comportamento inseguro? | `psycopg.Error` capturado ⇒ `False`/raise sem DROP (testado). |
| Testes negativos verificam ausência de DDL? | Todo DDL emitido é registrado no fake; asserts exigem `DROP` ausente. |
| Cleanup seguro diante de exceções? | Teardown do fixture roda no `yield` mesmo com falha; `drop_owned` fail-closed. |

### Evidência PostgreSQL real (cluster local `delpi-postgres-plugins`, descartável)

- Isco `plugins_hub_test` criado com sentinela e apontado via `CF_TEST_PG_NAME` + opt-ins completos ⇒ suite executou 45 testes; pós-condições: `plugins_hub_test` preservado com dado sentinela, `cf_test_orphan_deadbeef` (resíduo sem ownership) preservado, `plugins_hub` intacto (159 itens), efêmero `cf_test_*` criado e removido pela execução.
- Suíte PG no efêmero próprio: `11 passed` — migrations, seed 53 DRAFT, publish, concorrência, idempotência, atomicidade `duplicate_item_key` (R1), auditoria UUID-only (R2).

### Regressão

- BFF: `161 passed` + 11 skips sem env PG (143 → 161: +18 testes de guarda isolamento).
- PG real: `11 passed` (integração) + `34 passed` (guarda) = 45.
- R1/R2: inalterados e re-verificados (`duplicate_item_key` 409 tipado + atomicidade; ator UUID fail-closed; service principal 403; access≠manage).
- MFE: nenhuma alteração; `41 passed` closing.
- Migrations produtivas V001/V002: intactas. Contratos HTTP/permissions: inalterados.
- Residual search: zero `DROP SCHEMA`/`DROP DATABASE` fora do isolamento owned; zero fallback de e-mail; zero conteúdo fora de escopo.

### Estado

R4 re-implementado com prova de ownership — submetido à revisão arquitetural independente para aceite formal. Riscos remanescentes: resíduos `cf_test_*` de execuções abortadas (seguros; limpeza manual); dependência de role com `CREATEDB` no cluster de teste (já constatada no ambiente local). Smoke autenticado: `TEST_NOT_RUN`. Deploy de produção: NÃO REALIZADO.
