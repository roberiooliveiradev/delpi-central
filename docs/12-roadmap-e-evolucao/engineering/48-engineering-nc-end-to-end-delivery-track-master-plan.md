# ENGINEERING.NC.MASTER — Trilha integrada de entrega NC + PostgreSQL + Portal + EVA

**Status:** PLANNED — plano mestre executável em gates sequenciais; **não** é autorização para ACT produtivo, transferência de ownership, grants, migração destrutiva ou cutover.  
**Coordenação:** EVA — Architecture / Coordination. **Data:** 2026-10-29.  
**Repositório:** `roberiooliveiradev/delpi-central`. **Autoridades:** AGENTS + Constituição e authorities vigentes no HEAD; docs Engenharia 32–47.  
**Precedência:** doc 47 = inventário factual NC.G0; doc 46 = proposta inicial; doc 45 = UX de navegação LMP/NC independente. Revalidar HEAD e diff concorrente, jamais tratar plano como runtime comprovado.

## 0. Instrução de execução para reduzir iterações

Executar uma **trilha contínua e encadeada**, avançando pelos gates cujas pré-condições, autoridades e testes estejam comprovados, no mesmo ciclo de trabalho, com commits pequenos e evidência por gate. Não parar apenas para pedir novo prompt entre gates técnicos **autorizados por este plano**. Bloquear somente em decisão material de owner, privilégio/segredo indisponível, falha de teste, risco à integridade de dados, mudança de authority, ação em produção, cutover ou mudança de contrato incompatível. Em bloqueio: registrar `PENDING`/`ARCHITECTURE_DECISION_REQUIRED` e continuar apenas tarefas independentes e seguras (documentação, testes sintéticos, UI sem ativação, ports sem acesso real). NÃO inferir aprovação por silêncio.

**Autorizado como plano de execução futura:** inventário incremental, design/implementação de código e testes em sandbox/dev autorizado, contratos READ, ports/adapter de leitura sob autorização DB, WRITE em ambiente isolado mediante controles e testes, UI nativa em dev, EVA READ, PREPARE sem side effects; documentação e PR/commits conforme convenções. **Não autorizado automaticamente:** obter ou provisionar segredos/grants de produção; mudar owner DB; criar/alterar Keycloak/Core em produção; deploy; rodar migrations em produção; alterar API DELPI legada em produção; habilitar EVA ACT; congelar writers; executar cutover; excluir dados; remover endpoints legados.

## 1. Alvo e invariantes

**Objetivo final:** `Início → Não Conformidades` como feature independente em Portal Engenharia; CRUD/auditoria/histórico e persistência sob Engineering API no PostgreSQL existente com role dedicada e escritor único; dados de OV/produto/BOM enriquecidos exclusivamente através de gateways oficiais para API DELPI/TOTVS; EVA com capacidades governadas em paralelo aos contratos Engineering API. LMP Dashboard mantém dias sem NC e não tem aba de NC (doc 45, missão separada).

**Boundaries obrigatórios:** Keycloak AuthN; Core RBAC efetivo (engineering.access para READ e operações legítimas; engineering.manage apenas admin, não implica acesso); Engineering API owner de NC; API DELPI owner de facts TOTVS, nunca guarda engineering.*; Portal host/UI; PostgreSQL com least privilege; EVA inteligente mas não SoT nem autorização; MCP/A2A interoperability, não authority. Human JWT não vira token S2S; S2S engineering-api com `engineering-facts.read`, `api-delpi` audience e `azp` allowlist; browser sem API DELPI direta. Clean Architecture/ports-adapters; sem DB alheio por atalho, sem import entre bounded contexts; transferência do schema/ownership explícita antes do acesso efetivo.

**Baseline PROVEN a revalidar:** doc 47 aponta seis READ, quatro WRITE NC na API DELPI; cinco tabelas `engineering.lmp_*` no `postgres-plugins`; migrations V001–V009 (V010–V011 são metalografia, NÃO usar/versionar NC sobre elas); history append-only com trigger e GUC `app.allow_lmp_nc_history_delete`; PG principal `PLUGINS_DB_USER` usado por ~18 serviços; `api-delpi.access` isoladamente confere WRITE NC legado (risco); import substitui integralmente acervo, `dry_run`, dedup natural key, `skip_existing` ignorado; UPDATE full replace exige occurrence_date; DELETE hard+CASCADE; EVA NC ainda PLANNED. Telemetria de consumidores 30–60d = TO_INVENTORY.

## 2. Gates encadeados, inputs, outputs e autorização

| Gate | Objetivo e entregáveis | Critério de saída | Bloqueio específico |
|---|---|---|---|
| **NC.T1 — ADR + contratos baseline** | Atualizar inventário HEAD, decisões owner, RQ/AC, matriz rotas/campos, DB topology, schema, writers, PII, consumidores e capacidade EVA; contratos E-NC-01..11 versionados; pacote de aprovação da role DB/migration runner; ledger | ADR ratificado pelos owners, ou `PENDING` com atividades desacopladas prosseguindo | Ownership/ACL do schema e writer não se presumem |
| **NC.T2 — Domínio + ports + READ** | Domain/Application/Repository port, adapter Postgres READ somente após autoridade DB e role DEV dedicada; API E-NC-01..06 e E-NC-11 BFF; testes, shadow/parity | READ sem alterações de dados, parity 0-diff, Core fail-closed, sem direct API DELPI | Sem role/grants, construir port e fake adapter/testes, não ler DB indevidamente |
| **NC.T3 — EVA READ** | Tool bridge MCP com search/get/history/streak/tags/context somente quando endpoints READ oficiais passarem; catálogo, schemas, filtros, source/provenance e testes | Capabilities `PROVEN`, testes authz/grounding/task outcomes; nenhuma tool ACT | Se endpoint incompleto, manter `PLANNED` sem exposição |
| **NC.T4 — WRITE em DEV isolado** | E-NC-07..10 Domain use cases; transação/history/import/export/delete; concurrency & idempotency; adapter gravável em sandbox isolado autorizado; write security e audit | Golden synthetic tests, rollback rehearsal, zero double-write e sem prod ACT | Sem owner/DB writer authority, implementar contra fake+isolated DB separado sem shared NC writes |
| **NC.T5 — UI nativa independente + EVA PREPARE** | Páginas Início→NC list/new/detail/edit/history/import/export, estados e a11y, enrich OV/produto/BOM BFF; PREPARE gera candidato/diff sem write | Browser real temas, tamanhos, fluxos e negativas; EVA PREPARE sem side effects | Novo link só habilitar quando endpoints+grants READY; não redirecionar para legado |
| **NC.T6 — homologação integrada pré-prod** | Paridade legada READ/WRITE sob dataset controlado, testes de perf, concorrência, 401/403, migration checksums, segurança, multi-instância, ledger de consumidores e rollback | Review de owners e evidências, runbook PREPARE/ACT, Go/No-go | Falha crítica = NO-GO; pode corrigir e repetir em DEV |
| **NC.T7 — ACT produtivo/ writer handoff** | Janela aprov., backup verified, freeze writer legado, checksum, grants/role, rollout Engineering API/Portal, switch writer único, smoke, monitoramento+reconciliação; EVA READ habilitada conforme AuthZ | Aprovação operacional separada e provas de integridade/runtime | ACT NÃO AUTORIZADO por este plano |
| **NC.T8 — legado deprecation + EVA ACT separado** | Consumidores migrados, telemetria zero, rem. endpoints/grants antigos conforme owners; se aprovado, contratos específicos e ACT NC EVA | Aprovação nova de owner/segurança e evidência real | Não desativar legado cedo nem habilitar tools mutáveis por default |

**Método para execução contínua:** T1→T6 podem ocorrer num trabalho principal, observados gates e condicionais acima; T7/T8 são missões ACT explícitas. Ao final de cada gate criar commit/evidência/status, sem depender de nova conversa para seguir quando o gate tiver PASS e todas as autoridades forem satisfeitas. Entrega final agrupa matriz de gates, não mascara gates PENDING.

## 3. Reancoragem e Abstraction Gate

Executar `git fetch origin`, `git rev-parse HEAD`, `git rev-parse origin/main`, `git status --short`, `git log -10 --oneline`. Ler AGENTS/constituição e authorities `plan-execution`, security, API contracts, DB persistence, migrations immutability, quality, frontend, Module Federation, deploy/rollback, EVA MCP. Verificar HEAD de docs 45–47 e mudanças concorrentes. `owner → fonte canônica → consumer → contrato → implementação → teste → outcome`. Antes de abstrações: necessidade, owner, consumer, equivalente, menor diff, rollback e revogação.

Matriz source→consumer deve incluir MFE legado, histórico/detalhe/CRUD, LMP NC-streak, Engineering API delegates, EVA/DÉLIA, ETL/scripts/telas, outras apps. Falta de telemetria **não** autoriza concluir zero consumer. Buscar código e logs/telemetria somente pelo acesso aprovado, sem colocar PII no relatório.

## 4. ADR e modelo físico de dados

**Target já escolhido pela Coordenação: Opção B**, reuso do cluster `postgres-plugins` com domínio NC sob Engineering API e sem movimentação física presumida. **TRANSFERÊNCIA DE AUTORIDADE PENDENTE**: obter e documentar aprovação verificável do atual owner API DELPI/Platform DB, Engenharia, Security, Core/EVA nos limites de cada um.

- Cinco tabelas atuais e function/trigger de história devem ser preservadas; nunca editar migrations V001–V009; outras V010/V011 pertencem a metalografia. Numerar novas migrations observando ledger real de versões globais e checksum; **não inferir V012 livre sem inventário HEAD**, embora doc 47 indique ≥V012 como expectativa.
- Definir runner owner de migrations (novo diretório separado ou tooling governado), strategy de role dedicada e allowlists de schema/tabela; NÃO conceder `engineering_api` acesso a todos os schemas do PG compartilhado. Isolar write/read de outros ~18 serviços gradualmente, como trabalho de plataforma; não fazer revoke em massa.
- NC history contém user_id/email/name; designar PII policy/retention; SELECT expõe somente campos autorizados. Trigger append-only não deve ser contornado por GUC persistente global; caso delete autorizado, GUC apenas no escopo de transação e com testes negativos da proteção.
- Confirmar grants em sequences, funções e triggers; schema-qualified queries, transação, pooling, timeouts, retries; sem espalhar SQL pelo Domain/Application.
- Plano shadow READ, comparativo PK/status/datas/produtos/tags/history/streak e business date/timezone; invariantes após migração contagem/checksum/revision.
- Freeze writer durante cutover, backup íntegro testado, replay/reconciliação de delta caso houver, writer único; rollback **com recuperação de writes novos**, não apenas rollback de imagem.

## 5. Contratos E-NC versionados

Usar `/v1/nonconformities` como proposta inicial, checar colisões na Engineering API, versioning, operation_id e padrão de envelope. IDs esperados:
- E-NC-01 list filtros/ordenação whitelist/paginação; 02 detalhe; 03 histórico; 04 streak; 05 problem-tags; 06 export;
- E-NC-07 POST create; 08 PUT full-replace; 09 DELETE hard (não mudar semântica silenciosamente); 10 POST import replace-total e dry-run; 11 GET context enriquecido OV/produto/BOM via Engineering API → API DELPI facts.
- Cada endpoint: owner, consumer, request/response, code/errors, AuthN/AuthZ, 401/403/404/409/422, rate/size limits, pagination, idempotency (especialmente import/create), optimistic concurrency, transaction, postcondition, audit actor, provenance, PII, observability, compatibility e rollback.
- WRITE protegido por human principal e Core `engineering.access` **ao executar**, não só no prepare; `engineering.manage` não implica access; tokens S2S e EVA não têm write default. Deny on Core unavailable. Não usar `api-delpi.access` ou `dashboard-lmps.nc.write` em Engineering API.
- Preservar behavioral truth do legado até explicitamente deliberar: status 3, `occurrence_date` required PUT, tags case-insensitive, history só update com diff, import replace-all, delete hard+GUC. Importação e exclusão são **operações destrutivas**; exigir confirmação reforçada, dry-run, escopo/limites e autorização humana específica. **Não** habilitar importação destrutiva pela EVA automaticamente.
- Enriquecimento: products/search, /products/{code}/structure e OV são dados externos TOTVS; os contratos da Engineering API devem expor somente o contexto necessário com estados unavailable/forbidden honestos; nenhum front/MCP acessa API DELPI diretamente.

## 6. Engenharia da implementação — Clean Architecture

- Bounded context Engineering/NC, entidades/value objects e errors; Application use cases separados: list/get/history/streak/tags/export/create/update/delete/import/context.
- `NonconformityRepositoryPort` desacoplado de framework/driver, SQL no adapter, gateway `EngineeringFactsPort` para produto/OV; Core AuthorizationPort/actor resolvidos na borda de aplicação.
- Transactions/UoW se necessário, sem abstração genérica antes de Abstraction Gate; reuse estrutura real da Engineering API, preserve contract/API conventions.
- Role DB DEV dedicada configurada via mecanismos oficiais/secret store; nunca secret em prompt/logs; sem shared PLUGINS_DB_USER em TARGET; acesso efetivo apenas após owner aprovação.
- Evitar backdoor: MFE novo → Engineering API; EVA MCP → Engineering API use case autorizado; ambos com mesmo contrato e live AuthZ.

## 7. Estratégia EVA parity, por capacidade

Cada novo endpoint: mesma PR/gate deve produzir linha `API contract | EVA consumer | tool id | READ/PREPARE/ACT | status | permissions | safety | tests | outcome`.

READ planejadas: `search_nonconformities`, `get_nonconformity`, `get_nonconformity_history`, `get_nonconformity_indicators`, `get_nonconformity_tags`, `get_nonconformity_context`. Implementar apenas após API oficial READY, no tool bridge governado, sem mapear automaticamente rota→tool; auditar source/revision/uncertainty, no PII no model quando desnecessária. Testar schema/capability discovery, grounding, authz (grant/no-grant/manage-only/Core-down), forbidden, no cross-tenant, no hallucination, task outcome.

PREPARE: `prepare_nonconformity_mutation` = validação, preview e diff de candidato, **sem** efeitos ou escrita; dar atenção a source/version e expiração de candidate, evitar confirmação implícita. ACT de create/update/delete/import EVA permanece **PENDING** até contrato específico, approval, live AuthZ, explicit human confirmation, idempotency, audit/postcondition/revoke/rollback. Sem ACT tools na trilha T1–T6.

## 8. UX Portal Engenharia

- Home catálogo: NC é card independente `Início → Não Conformidades`; não aninhar em `/lmps/nonconformities`; rota final independente a confirmar com conventions do Portal (ex.: `/apps/engineering/nonconformities`, `TARGET` até registrada), refletir status em catálogo; não criar rota clicável vazia.
- Reference design: Home/Visão Geral e kit `engineeringUi`, não copiar visual antigo; responsive light/dark, a11y, loading/empty/forbidden/unavailable, status badges, histórico/provenance.
- List filters/sort/pagination/search, form create/edit, attach OV/produto/BOM via Engineering API, tags, status, dates, history, import dry-run/confirmation, export; preserve warnings e honest error boundaries; no unauthorized fetching.
- Deep links antigos e link direto legado devem coexistir; não remover `/apps/dashboard-lmps/nonconformities` antes de cutover. O doc 45 remove duas tabs da página LMP, mas preserva Dias sem NC.

## 9. Testes e release gates

| Categoria | Mínimo verificável |
|---|---|
| Contracts | Golden fixtures atuais, roundtrip schema, parity 0-diff READ por mesmos filtros, datas, timezone, erro e limites |
| DB | migrations idempotentes/checksum, least grants, isolation negativo contra outros schemas, triggers, transaction GUC, backup/restore ensaiado |
| Writes DEV | create/update/delete/history/import dry-run, dedup, replace-all em dataset isolado, concurrency 409, idempotency e audit actor |
| AuthZ | 401 sem token; 403 sem access; manage-only; service identity; Core down fail-closed; no legacy-permission fallback |
| Security | zero S2S token no browser/prompt/log; PII minimizada; bounds para exports/imports; no injection |
| EVA | capability catalog, grounding, tool schema, forbidden, fake/write PREPARE zero side-effects, provenance, task outcome |
| UX | Playwright real pelo host/Keycloak, desktop/tablet/mobile e light/dark, navigation+refresh/back+deep-link, screenshots e request audit |
| Legacy | MFE legado lê/escreve como antes até handoff; streak KPI LMP sem regressão; sem call API DELPI pelo MFE novo |
| Runtime | health, P95, cold-start, Core/S2S, fail closed; teste no SHA final com evidence |
| Cutover T7 | backup, single-writer, checksums, read/write production smoke autorizado, rollback rehearsal, monitoramento, owner sign-off |

**Critério de paridade:** 0-diff semântico quando mesmo dataset e same snapshot/time; documentar divergências de date/ref/DEV×PROD como diferenças contextualizadas, nunca mascará-las. Não executar destructive/fault-injection tests em produção.

## 10. Mapa de dependências e bloqueios

- T1→T2 DB real depende de ownership DB e role/grants DEV; sem isso, T2 ports/fakes podem avançar.
- T2 READ→T3 EVA tools só se rotas implementadas e testadas; caso contrário ledger PLANNED.
- T4 WRITE DB real depende de owner + role DEV + isolated test DB, nunca writer concorrente no storage compartilhado.
- T5 catálogo ativo depende de API/authz/UX test; pode preparar UI com mocks antes.
- T6 integrated release depends T2–T5; bloqueio não altera status dos demais.
- T7 depende de autorização operacional distinta, owner sign-offs, reconciliação e rollback.
- T8 depende de telemetria/consumidores reais e separate deprecation and EVA ACT decisions.
- Outro owner, novo SoT, novo bounded context ou authority não prevista = `ARCHITECTURE_DECISION_REQUIRED` e voltar à Coordination.

**Hardening do legado:** `ENGINEERING_LMP_NC_WRITE = [api-delpi.access, dashboard-lmps.nc.write]` é risco real. Preparar alteração de guard + grants com Matrix de impactos e testes. O ACT do hardening em ambiente que atende usuários exige autorização do owner e estratégia de compatibilidade. Não corrigir silenciosamente em T1/T2.

## 11. Entregáveis documentais por gate

Cada gate deve gerar evidência numerada nova na pasta `docs/12-roadmap-e-evolucao/engineering/` (reconsultar próxima numeração), contendo: baseline SHA, authorities, paths reais, contratos, decisions e approvals, diffs, commands/testes no SHA, evidência browser/MCP/DB conforme escopo, risks, residual search, statuses e next bounded step. Manter ledger-mestre de gates, a tabela abaixo com ACTUAL:

| Gate | Estado inicial | Evidência exigida |
|---|---|---|
| T1 | PLANNED | ADR/approval matrix, contracts |
| T2 | PLANNED | README contracts + shadow parity |
| T3 | PLANNED | EVA MCP READ tools + test outcomes |
| T4 | PLANNED | DEV WRITE + audit/idempotency |
| T5 | PLANNED | Portal UX + EVA PREPARE |
| T6 | PLANNED | Integrated test/cutover runbook |
| T7 | PENDING AUTHORIZATION | PROD ACT evidence |
| T8 | PENDING AUTHORIZATION | Deprecation + EVA ACT owner evidence |

Não afirmar PASS de gate com provas de outro SHA; `PROVEN | TO_INVENTORY | PLANNED | TARGET` para fatos; `PASS | FAIL | PENDING | INCONCLUSIVE | TEST_NOT_RUN | STALE_EVIDENCE` para execução; `EXECUTION_DRIFT` quando premissas alteradas.

## 12. Aceite consolidado

- **NC-M01** todas as rotas/regras/schema/consumidores revalidados no HEAD;
- **NC-M02** ADR ownership e authority sign-offs explícitos;
- **NC-M03** DB role dedicada e migration runner governados sem quebrar outros domínios;
- **NC-M04** Engineering API READ contratos com paridade;
- **NC-M05** EVA READ parity no mesmo ciclo, permission/grounding/outcome;
- **NC-M06** Engineering API WRITE full CRUD/Import em sandbox com audit/idempotency;
- **NC-M07** EVA PREPARE honesto; ACT não habilitado;
- **NC-M08** Portal NC independente nativo com fluxo end-to-end;
- **NC-M09** fatos de TOTVS apenas via API DELPI/BFF;
- **NC-M10** legacy read/write e KPI streak preservados até cutover;
- **NC-M11** authz live, privacy, deny boundary e negatvos testados;
- **NC-M12** paridade/QA browser/perf/DB/TOTVS no SHA final;
- **NC-M13** plano cutover escritor único com backup/reconciliação/rollback testados;
- **NC-M14** nenhuma mudança produtiva ou deprecation sem ACT separado;
- **NC-M15** docs+ledger+report íntegros, bloqueios/approvals explícitos.

## 13. Formato final do relatório Devin

```text
EVA EXECUTION REPORT
TASK: ENGINEERING.NC.MASTER — Integrated Delivery Track T1-T6
BASE_HEAD:
FINAL_HEAD:
AUTHORITY_FILES_READ:
GATE_STATUS_MATRIX: T1=...,T2=...,T3=...,T4=...,T5=...,T6=...,T7=NOT_AUTHORIZED,T8=NOT_AUTHORIZED
ADR_OWNERSHIP_APPROVALS:
POSTGRES_SCHEMA_AND_ROLE:
MIGRATION_RUNNER_AND_CHECKSUM:
CONSUMER_TELEMETRY:
READ_API_CONTRACTS:
READ_SHADOW_PARITY:
WRITE_API_CONTRACTS:
WRITE_ISOLATED_TESTS:
SINGLE_WRITER_PLAN:
IMPORT_DELETE_SAFETY:
AUTHZ_CORE:
LEGACY_GUARD_HARDENING_PLAN:
PRODUCT_OV_BOM_BFF:
PORTAL_NC_NAV_AND_UX:
EVA_READ_TOOL_LEDGER:
EVA_PREPARE_TOOL:
EVA_ACT_STATUS:
SECURITY_NEGATIVE_TESTS:
BROWSER_EVIDENCE:
PERFORMANCE:
LEGACY_COMPATIBILITY:
TESTED_SHA:
TEST_COMMANDS:
TEST_RESULTS:
COMMITS_BY_GATE:
DOCS_BY_GATE:
ARCHITECTURE_AUDITS:
RESIDUAL_SEARCH:
EXECUTION_DRIFT:
ARCHITECTURE_DECISION_REQUIRED:
UNRESOLVED:
NEXT_BOUNDED_STEP:
```

**Mandato:** concluir o máximo possível da trilha T1–T6 na mesma execução, sem pedir novos prompts por gate quando os pré-requisitos estiverem satisfeitos; registrar limites reais. Nenhuma regra do plano constitui autorização operacional ACT, mudança de ownership, DB production ou EVA writes.
