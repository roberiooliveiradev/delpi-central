# Documento 96 — Gate de contrato e persistência do slice `P6-MIN + P2-READ`

**Rodada:** `CF-C3-P6-MIN-P2-READ-CONTRACT-GATE-001` (2026-10-24)
**Base:** `7c53a01044` (main, worktree limpa). **`IMPLEMENTATION_AUTHORIZED=NO`**
— este documento é especificação e proposta; nada aqui é contrato aprovado,
migration aplicada ou endpoint implementado.
**Authorities:** instruções oficiais, `.cursor` (arquitetura, segurança,
contratos, dados/persistência, frontend, qualidade), docs 09, 13, 14, 21, 23,
30, 45, 59, 92, 93, 95. Decisão vinculante: **CP-D01=A APPROVED**
([doc 95 §8](./95-ciclo3-cp00-cp01-rebaseline-e-brief-primeiro-slice-p2.md)) —
persistência própria da `controllership-finance-api`, schema isolado no
`postgres-plugins`.

---

## 1. Inventário do padrão real de persistência (PROVEN no HEAD)

Comparado `supplies-api`, `commercial-api`, `requests-api`,
`travel-expenses-api` (e `maintenance-api`, `production-control-api`):

| Aspecto | Padrão vigente | Evidência |
|---|---|---|
| Driver | `psycopg` (psycopg3), `dict_row`, autocommit=False | `supplies-api/app/infrastructure/persistence/migrations_runner.py` |
| Credenciais | env `PLUGINS_DB_HOST/PORT/NAME/USER/PASSWORD/CONNECT_TIMEOUT/SSLMODE` via `.env` + compose `environment:` | `infra/docker-compose.yml` (supplies/transformometro) |
| Banco | serviço `postgres-plugins` (`delpi-postgres-plugins`), `POSTGRES_*` do `.env` | compose linha ~1378 |
| Isolamento | **um schema por app** (`supplies`, `travel_expenses`, ...), `CREATE SCHEMA IF NOT EXISTS` | V001 de cada API |
| Controle de versões | tabela `<schema>.schema_migrations` (version UNIQUE, name, checksum **SHA-256**, executed_at); arquivos `V###__nome.sql` ordenados; **checksum divergente aborta** (imutabilidade) | `migrations_runner.py` |
| DDL | `BEGIN;`/`COMMIT;` explícitos, `CREATE EXTENSION IF NOT EXISTS pgcrypto`, `CREATE TABLE` sem `IF NOT EXISTS` nas tabelas de domínio (imutável após aplicada) | `supplies-api/migrations/V001–V003` |
| Seed de catálogo | `INSERT INTO` dentro de migration versionada já existe na plataforma | `travel-expenses-api/V001`, `commercial-api/V010`, `maintenance-api/V004` |
| Execução | startup opcional: `RUN_MIGRATIONS_ON_STARTUP` + `plugins_db_configured()` → `run_migrations()` | `supplies-api/app/startup/run_migrations_on_startup.py` |
| Concorrência | `revision INTEGER` + cheque de versão (`ReviewRevisionConflictError`), `ON DELETE RESTRICT` | `V002__supplier_enrichment_reviews.sql`, port/repository |
| Idempotência | `UNIQUE (…, idempotency_key)` + conflito tipado `IdempotencyConflictError` | idem |
| Auditoria | tabela de eventos append-only (decision operations) | `V003__supplier_enrichment_decision_operations.sql` |
| Testes PG | integração real em Postgres isolado, `pytest.mark.skipif(SUPPLIES_TEST_PG_HOST)`; **mocks não aceitos** como prova de atomicidade | `tests/infrastructure/test_supplier_enrichment_repository_pg.py` |
| Camadas | `domain` (lifecycle) → `application` (services/contracts) → `infrastructure.persistence` (repository + runner) → `interface.http` | estrutura supplies-api |

**Conclusão do inventário:** a implementação correta é replicar esse padrão
na `controllership-finance-api` com `SCHEMA_NAME = "controllership_finance"`.
Nenhuma arquitetura exclusiva é proposta.

### 1.1 Gaps de wiring a fechar no GO (inventariados, não implementados)

| Item | Estado atual | Diff proposto |
|---|---|---|
| `requirements.txt` da BFF | sem `psycopg` | adicionar `psycopg` pinado |
| compose `controllership-finance-api` | sem `PLUGINS_DB_*`, sem `depends_on: postgres-plugins` | adicionar 7 envs padrão + `depends_on` |
| `migrations/` + runner + startup | inexistentes | criar `migrations/V001`, `app/infrastructure/persistence/migrations_runner.py` (adaptado do padrão), `app/startup/run_migrations_on_startup.py` |
| Settings | sem flags DB | `PLUGINS_DB_*`, `RUN_MIGRATIONS_ON_STARTUP`, `plugins_db_configured()` |
| Deploy | — | migrations no startup (flag) conforme `local-first-deploy`/`plugins-migrations-no-reset-prod`; **nunca** reset |

## 2. Modelo lógico (proposta — nomes técnicos EN)

```text
checklist_template ──────────────< checklist_template_version
   (template_id, code, name)          │ 1..N  (version, status, revision,
                                     │       published_by/at, activated_period)
                                     └───────< checklist_template_item
                                                  (item_key CK-*, sheet,
                                                   name, origin_kind,
                                                   recipient_area,
                                                   applicability,
                                                   branch_scope,
                                                   totvs_report_ref R-ID?)

monthly_competence ──< competence_checklist_item
   (competence_id, period UNIQUE,       (snapshot_id, competence_id,
    template_version_id, opened_by/at,   item_key, source_template_item_id,
    status 'OPEN')                       frozen fields, state='EXPECTED')

closing_audit_event (append-only, genérico por entidade)
   (event_id, entity_type, entity_id, event_type,
    actor_subject, competence_id?, detail jsonb, created_at)
```

### 2.1 Entidades e invariantes

| Entidade | Campos-chave | Invariantes |
|---|---|---|
| `checklist_template` | `template_id` UUID PK, `code` UNIQUE (`monthly-closing-checklist`), `name`, `created_by`, `created_at` | um template por processo no V1 |
| `checklist_template_version` | `version_id` PK, `template_id` FK RESTRICT, `version` INT, `status` `DRAFT\|PUBLISHED\|INACTIVE`, `revision` INT (optimistic), `published_by/at`, `effective_from_period` CHAR(7) | `UNIQUE(template_id, version)`; PUBLISHED é **imutável** (edição cria nova versão); INACTIVE prospectivo, sem delete |
| `checklist_template_item` | `item_id` PK, `version_id` FK, `item_key` (`CK-E-01..30`, `CK-F-01..23`), `sort_order`, `sheet` `ELETRONICO\|FISICO`, `name`, `purpose?`, `origin_kind` `TOTVS\|EXTERNAL\|MIXED`, `recipient_area` `CONTABIL\|FISCAL\|NULL`, `applicability` `REQUIRED\|CONDITIONAL\|OPTIONAL`, `branch_scope` `MATRIX\|BRANCH\|BOTH`, `totvs_report_ref` VARCHAR NULL (`R01..R15`), `requirement_notes` TEXT | `UNIQUE(version_id, item_key)`; `totvs_report_ref` NULL válido; `applicability` conforme regra comprovada — não comprovada ⇒ `CONDITIONAL` + nota |
| `monthly_competence` | `competence_id` PK, `period` CHAR(7) `YYYY-MM` **UNIQUE**, `template_version_id` FK RESTRICT, `status` `OPEN`, `opened_by` UUID, `opened_at` | 1:1 com período; UNIQUE(period) resolve concorrência e idempotência |
| `competence_checklist_item` | `snapshot_item_id` PK, `competence_id` FK, `item_key`, `source_template_item_id`, `source_version_id`, cópia congelada (name, purpose, origin_kind, recipient_area, applicability, branch_scope, notes), `state` `EXPECTED` | `UNIQUE(competence_id, item_key)`; snapshot nunca referencia conteúdo mutável por valor |
| `closing_audit_event` | `event_id` PK, `entity_type`, `entity_id`, `event_type` (`TEMPLATE_PUBLISHED`, `TEMPLATE_INACTIVATED`, `COMPETENCE_OPENED`), `actor_subject`, `competence_id` NULL, `detail` jsonb (sem payload sensível), `created_at` | append-only; sem UPDATE/DELETE |

### 2.2 Regras de abertura/publicação

- Snapshot só de versão `PUBLISHED` e `effective_from_period <= period`.
- Publicar v2 **não** toca competências existentes (FK congela origem).
- `POST` de abertura é **idempotente**: período já aberto ⇒ retorna 200 +
  recurso existente (não 409), UNIQUE(period) é a garantia física;
  corrida simultânea ⇒ um vencedor, perdedor re-lê.
- Item inicia `EXPECTED` — nunca `DELIVERED/VALIDATED/ACCEPTED`.
- Filial é filtro de dados: `branch_scope` define aplicabilidade, não grant.
- Toda escrita gera `closing_audit_event` com ator e competência.

### 2.3 DDL documental (proposta V001+V002)

`V001__create_controllership_finance_schema.sql`: extensão pgcrypto, schema
`controllership_finance`, `schema_migrations`, as 6 tabelas acima +
índices (`items(version_id)`, `snapshot(competence_id)`,
`audit(entity_type, entity_id)`).

`V002__seed_checklist_v1.sql`: `INSERT` do template `monthly-closing-checklist`,
versão 1 **`DRAFT`** com os **53 itens** derivados da matriz sanitizada do
[doc 95 §1](./95-ciclo3-cp00-cp01-rebaseline-e-brief-primeiro-slice-p2.md)
(sem bancos/contas/nomes). A **publicação** da v1 ocorre via API admin com
`manage`+escopo → audit real. Alternativa de seed já `PUBLISHED` fica como
`DECISION_REQUIRED` secundária se o PO preferir dispensar o ato administrativo.

## 3. Contratos HTTP candidatos (não aprovados)

Owner: `controllership-finance-api`. Consumidor: MFE. Erros tipados no
envelope `fail()` existente (`code`, `message`, `details`).

### 3.1 Operação administrativa (P6-MIN)

| operationId | Método/Path | Capability | Body/Resp | Erros |
|---|---|---|---|---|
| `listChecklistTemplates` | GET `/admin/checklist-templates` | manage+admin_scope | `[{template_id, code, name, current_version}]` | 401/403/503 |
| `listTemplateVersions` | GET `/admin/checklist-templates/{templateId}/versions` | idem | versões + status + revision | +404 `template_not_found` |
| `getTemplateVersion` | GET `/admin/checklist-templates/{templateId}/versions/{version}` | idem | versão + itens completos | idem |
| `createTemplateDraft` | POST `/admin/checklist-templates/{templateId}/versions` | idem | novo DRAFT (clona última); body vazio | +409 `draft_already_open` |
| `updateTemplateDraft` | PUT `.../versions/{version}` | idem | itens completos + `revision`; stale ⇒ 409 `stale_revision` | +409/422 |
| `publishTemplateVersion` | POST `.../versions/{version}:publish` | idem | `{effective_from_period}`; status→PUBLISHED, evento de audit | +409 `already_published` |
| `inactivateTemplateVersion` | POST `.../versions/{version}:inactivate` | idem | prospectivo, sem delete | +409 |
| `listChecklistTemplateEvents` | GET `.../{templateId}/events?version=` | idem | eventos append-only por versão (audit trail) | +404 `template_not_found` |

> Escopo P6-MIN deliberado: edição de itens via API existe só para DRAFT
> (PUT com revision). Adendo A3 (doc 104): UI administrativa do checklist
> implementada em `closing/admin` (MFE, gated por `manage`) — catálogos
> complementares (bancos, motivos, roles, targets) seguem doc 28.

### 3.2 Operação de leitura/abertura (P2-READ)

| operationId | Método/Path | Capability | Semântica | Erros |
|---|---|---|---|---|
| `listCompetences` | GET `/closing/competences` | access | lista `period`, `template_version`, `status`, `opened_at` — ordenada desc | 401/403/503 |
| `openCompetence` | POST `/closing/competences` `{period}` | access | cria competência + snapshot da versão PUBLISHED vigente; **idempotente** | 422 `invalid_period`; 409 `no_published_template`; 503 `db_unavailable` |
| `getCompetence` | GET `/closing/competences/{period}` | access | metadados + versão de origem | 404 `competence_not_opened` |
| `listCompetenceItems` | GET `/closing/competences/{period}/items?sheet&origin&recipient&branch_scope&state` | access | snapshot congelado; filtros são dimensões de dados | 404 + 422 filtros inválidos |
| `getCompetenceItem` | GET `/closing/competences/{period}/items/{itemKey}` | access | detalhe + `totvs_report_ref` + notes | 404 `item_not_found` |

### 3.3 Distinção obrigatória de estados de erro

| Situação | Código | Nunca |
|---|---|---|
| competência não aberta | 404 `competence_not_opened` | lista vazia |
| template nunca publicado | 409 `no_published_template` | sucesso com zero itens |
| checklist válido sem itens aplicáveis | 200 + `items: []` + flag | erro |
| Core/RBAC indisponível | 503 `rbac_unavailable` | permitir |
| DB indisponível | 503 `persistence_unavailable` | lista vazia |
| corrida de abertura | 200 idempotente | duplicata |
| `manage` sem escopo admin | 403 | publicar |
| item/revisão inexistente | 404 / 409 `stale_revision` | ecoar dados |

## 4. Matriz de autorização

| Operação | authenticated | principal=user | `access` efetivo | `manage` efetivo | admin scope | Outras regras |
|---|---|---|---|---|---|---|
| list/open/get competences e items | ✔ | ✔ | ✔ | — | — | rbac_unavailable→503; service principal→403 |
| admin list/get | ✔ | ✔ | — | ✔ | ✔ | `access` sozinho→403 |
| draft/publish/inactivate | ✔ | ✔ | — | ✔ | ✔ | +revision/+audit; `manage` sem escopo→403 |

Core permanece authority de effective permissions; JWT não autoriza; filial
não é permission; nenhum permission code novo; future DRE permission (doc 91)
herdada quando autorizada — fora deste slice.

## 5. RQ/AC e matriz de testes

RQs vigentes (doc 23): RQ-P6-01/02/03/09, RQ-P2-01/02/12. Novos do doc 95:
**RQ-P2-13** (`EXPECTED` ≠ entregue) e **RQ-P2-14** (sem R-ID ⇒ sem
indicação de automação) — **propostos ao ledger**; registro definitivo no
doc 23 no GO de implementação.

| Cenário | Caso | Teste |
|---|---|---|
| Positive | seed v1 DRAFT → publish autorizado → abrir 2026-10 → 53 itens `EXPECTED` | PG real + rota BFF |
| Positive | F5/deep link `…/competences/2026-10/items` | MFE |
| Sibling | publish v2 depois de abrir 2026-10 ⇒ competência continua na v1; 2026-11 usa v2 | PG real (RQ-P6-02/RQ-P2-01) |
| Sibling | item externo (CK-F-xx) sem `totvs_report_ref` | contrato |
| Negative | sem `access`→403; `manage` sem `access`→403 nas rotas de leitura | rota |
| Negative | publish com `access`→403; `manage` sem admin scope→403 | rota |
| Negative | open sem versão publicada→409 | PG real |
| Negative | item inexistente→404; período malformado→422 | rota |
| Negative | REQUIRED→N/A rejeitado (não aplicável neste slice — sem mutação de item; coberto quando C04/C05) | — |
| Concorrência | 2× POST mesmo período ⇒ 1 competência; publish simultâneo ⇒ 1 winner (UNIQUE/revision) | PG real |
| Idempotência | replay POST open ⇒ 200 mesmo recurso | rota+PG |
| Falhas | DB down→503; Core down→503 fail-closed | BFF |
| UI | states loading/empty/error/forbidden; tema claro/escuro; teclado; helpCoverage | vitest + estrutural |

Mock apenas para camada HTTP; persistência testada em Postgres isolado
(padrão `SUPPLIES_TEST_PG_*` ⇒ `CF_TEST_PG_*`).

## 6. Especificação de UI (sem implementação)

- Nova deep route candidata `/closing/checklist/{period?}` — **alteração de
  manifest necessária** (1 rota nova; permission `access` existente). Não
  alterar manifest fora do GO.
- Entrada: card/ação na Home "Central de Fechamento → Checklist da
  competência" (visível só quando `access` efetivo), deep link estável.
- Composição: `plugin-ui` — filtros (período, origem, destinatário,
  branch_scope, estado), `DataTable` do kit (mesma família das páginas
  vigentes), estados loading/empty/error/forbidden, Help contextual
  (helpCoverage estrutural).
- Colunas mínimas: item_key, nome, aba/origem, destinatário, aplicabilidade,
  escopo de filial, estado `EXPECTED`, vínculo R-ID quando existir.
- Honestidade: sem percentuais de conclusão, sem badge de entregue; lacunas
  (responsável/validador `TO_INVENTORY`) exibidas como pendência de
  configuração, não como falha.
- Abertura: ação "Abrir competência" (somente quando não aberta; confirm
  com período); resultado idempotente.
- Admin mínimo (opcional no slice): listar versões + publish/inactivate —
  se excluída do slice, publicação v1 ocorre uma única vez via API/script
  governado; registrar a escolha no GO.

## 7. CLARA e Contabilidade (dependências, não escopo)

- CLARA (doc 94): tools READ futuras `list_competences`,
  `get_competence_checklist` após o slice existir; nenhum PREPARE/ACT até
  haver operação real. Nada implementado.
- Contabilidade/DRE (doc 91): sem alteração de manifest/Core/rotas.

## 8. Riscos e residual search

- `unresolved_branch` 100% nas baixas (doc 95 §2.A) — irrelevante para
  este slice (sem consumo do contrato settlements); permanece residual E-cat.
- Destinatário da aba Físico vazio na fonte → seed usa `recipient_area=NULL`
  e `TO_INVENTORY` explícito (não inventar `CONTABIL`).
- Sinais de tema não decodificados (4 células) → itens marcados
  `CONDITIONAL` + nota, aguardando Controladoria (CP-D02).
- Item CK-E-27 sem R-ID ⇒ `totvs_report_ref=NULL`, `origin_kind='TOTVS'`.
- Diff futuro toca compose + requirements + manifest ⇒ gate de runtime
  próprio; nenhum destes arquivos alterado nesta rodada.

## 9. Checklist de autorização de runtime (GO pendente)

- [ ] PO/GPT aprovam contratos §3 (nomes podem mudar; semântica não).
- [ ] `migrations/`, runner, startup, settings, requirements, compose env.
- [ ] Manifest +1 rota; teste estrutural de manifest atualizado.
- [ ] Seed V002 revisado contra doc 95 §1.
- [ ] Testes PG reais + rota + MFE; CI/estruturais.
- [ ] Deploy canônico `local-first-deploy` (`up-prod-sequential.sh --build
      controllership-finance-api`), migrations no startup.
- [ ] Registry de RQ-P2-13/14 no doc 23.

**Estado do gate:** contratos e modelo **PRONTO PARA DECISÃO**
(`DECISION_REQUIRED` residual: seed v1 DRAFT×PUBLISHED; UI admin mínima
in/out do slice). Nenhum runtime autorizado.


## 10. Decisões do PO posteriores ao gate — 2026-10-24

**Fechadas as duas escolhas residuais do §9:** (1) seed v1 dos 53 itens em `DRAFT`, não `PUBLISHED`; publicação por ato administrativo governado; (2) API administrativa mínima **incluída**, sem página P6 nesta fatia. A autoridade da decisão e a solicitação formal de GO estão no [doc 97](./97-ciclo3-p6-min-p2-read-decisoes-po-e-solicitacao-go-transversal.md). `IMPLEMENTATION_AUTHORIZED=NO` até revisão transversal e autorização expressa posterior. Os contratos deste documento continuam candidatos sujeitos à ratificação; nenhum código foi executado.
