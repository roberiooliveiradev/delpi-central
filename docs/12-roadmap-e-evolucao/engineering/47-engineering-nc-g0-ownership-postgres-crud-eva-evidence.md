# ENGINEERING.NC.G0 — Ownership, PostgreSQL CRUD Migration & EVA Parity — Inventário, Contratos e ADR

**Gate:** NC.G0 — INVENTORY, CONTRACTS & ARCHITECTURE DECISION PREPARATION (plano vinculante: doc 46)
**Executor:** Devin · **Coordenação:** EVA — Architecture / Coordination
**Data:** 2026-10-29
**`BASE_HEAD`:** `b037f4a3bf823c0ec8d9d6ece15565610c51d0dc` (`origin/main`, working tree limpa de alterações tracked; untracked concorrentes preservadas)
**Escopo deste documento:** inventário factual READ-only, ADR de ownership, contratos E-NC-*, ledger EVA, plano de migração/rollback e testes. **Nenhum código CRUD, migração DB, grant, deploy ou cutover foi executado.**

---

## 1. Reancoragem e authorities (NC-G0-01)

| Item | Valor |
|---|---|
| `HEAD` / `origin/main` | `b037f4a3bf` (sincronizados) |
| Plano canônico | doc 46, commit `691396522c` (ancestral do HEAD) |
| Referência G5.V em produção | doc 44 — Portal/LMPs em prod, artefato rastreável |
| Doc 45 (UX.NAV.R1) | PLANNED — NC como área independente "Início → Não Conformidades"; deep links NC redirecionam ao legado hoje |

**Authorities lidas:** `AGENTS.md`; constituição (`development-standards-index`, `evidence-driven-execution`, `centralized-rules-first`, `clean-code-architecture-guardrails`, `english-code-identifiers`); `plan-execution`, `platform-architecture-boundaries`, `platform-security-identity-authorization`, `platform-api-contracts-integration`, `platform-data-persistence`, `platform-delivery-runtime-operations`, `platform-quality-testing`, `mfe-own-api-no-direct-api-delpi`, `local-first-deploy`, `migrations-immutable-checksum`, `plugins-migrations-no-reset-prod`, `contract-evolution-backward-compatibility`; docs Engenharia 32–46 (foco: 33 §8/15–16, 38 S2S, 40 consumers/contratos, 41 G5, 44 produção, 45 separação de navegação, 46 plano).

## 2. Mapa de rotas NC — fonte canônica `api-delpi` (NC-G0-02)

Router: `api-delpi/app/interface/http/routes/engineering/lmp_nonconformity_router.py`, prefixo `/engineering/lmps/nonconformities`, montado sob `/apps/api-delpi` no gateway. **10 endpoints confirmados no HEAD.**

### 2.1. READ — guard `require_any_permission(ENGINEERING_LMP_ACCESS)`

`ENGINEERING_LMP_ACCESS = [api-delpi.access, dashboard-engineering.view, dashboard-lmps.view]` — **qualquer uma** concede leitura.

| Endpoint | Contract | Função | Observações |
|---|---|---|---|
| `GET ""` | `list_lmp_nonconformities` | Listagem paginada | Filtros: `status`, `sale_number`, `lmp_number`, `customer_name`, `product_code` (EXISTS linha), `problem_tag` (EXISTS tag), `start_date`/`end_date` + legado `date_start`/`date_end`, `sort_by` (12 colunas whitelist), `sort_dir`, `page`, `page_size` (≤200). Erros: 400 validação, 500 repo |
| `GET /problem-tags` | `list_lmp_problem_tags` | Catálogo compartilhado de tags | Retorna `id`, `label`, `usage_count` |
| `GET /streak` | `get_lmp_nonconformity_streak` | Dias sem NC (KPI LMP) | Campos: `current_days_without_nc`, `record_days_without_nc`, `last_nc_date`, `reference_start_date`, `as_of_date`, `nc_count`. 503 se schema desatualizado |
| `GET /export` | `export_lmp_nonconformities` | Dump JSON completo | Envelope `{version:1, generated_at, count, items}` — sem paginação |
| `GET /{id}` | `get_lmp_nonconformity` | Detalhe | `id` UUID path; 404 honesto |
| `GET /{id}/history` | `list_lmp_nonconformity_history` | Histórico | ≤200 eventos `created_at DESC`; 404 se NC inexistente |

### 2.2. WRITE — guard `require_any_permission(ENGINEERING_LMP_NC_WRITE)`

`ENGINEERING_LMP_NC_WRITE = [api-delpi.access, dashboard-lmps.nc.write]` — **⚠ `api-delpi.access` sozinha concede WRITE** (ver §6, risco legado).

| Endpoint | Contract | Função | Semântica |
|---|---|---|---|
| `POST ""` | `create_lmp_nonconformity` | Create | `registered_at` server-side; `occurrence_date` default `CURRENT_DATE`; ator JIT (`_current_actor`: user_id/email/name/label); history event `created` |
| `PUT /{id}` | `update_lmp_nonconformity` | Update full-replace | `occurrence_date` **obrigatória** no update (400 se ausente); replace de produtos/tags; history `updated` só se diff não-vazio |
| `DELETE /{id}` | `delete_lmp_nonconformity` | Hard delete | CASCADE em produtos/tags/history via GUC de sessão `app.allow_lmp_nc_history_delete` (V008); 404 se inexistente |
| `POST /import` | `import_lmp_nonconformities` | Import JSON | **Substituição total do acervo** (`delete_all` + reinsert); `dry_run` suportado; `skip_existing` é legado ignorado; dedup por chave natural (OV+descrição+tags) via `find_import_duplicate` |

Body `LmpNonconformityBody` (create/update): `status ∈ {open,in_progress,done}`, `sale_number ≤20`, `lmp_number ≤40`, `customer_name ≤200`, `occurrence_date`/`launch_date`/`last_revision_date` `YYYY-MM-DD`, `executed_by`/`released_by ≤200`, `defect_description`, `corrective_actions`, `technical_opinion`, `problem_tags[]` (labels ≤80, cria no catálogo se nova), `products[]` (`product_code ≤60`, `product_description ≤255`, normaliza UPPER, dedup).

## 3. Modelo PostgreSQL e autoridade atual (NC-G0-03)

### 3.1. Schema físico — `engineering.*` no Postgres **`postgres-plugins`** (dedicado a plugins, **compartilhado**)

| Objeto | DDL | Semântica |
|---|---|---|
| `engineering.lmp_nonconformities` | V002 + redesign V004 + V007 (`lmp_number`) + V009 (`occurrence_date NOT NULL DEFAULT CURRENT_DATE`) | PK `uuid gen_random_uuid()`; CHECK status `(open,in_progress,done)`; colunas OV/cliente/datas/pessoas/textos/ator; índices em `registered_at DESC`, `status`, `sale_number`, `lmp_number`, `customer_name`, `launch_date`, `occurrence_date` |
| `engineering.lmp_nonconformity_products` | V003 (+`product_description` V004) | PK `(nonconformity_id, product_code)`; FK → NC `ON DELETE CASCADE` |
| `engineering.lmp_problem_tags` | V005 | Catálogo N:N; UNIQUE case-insensitive (`LOWER(TRIM(label))`); seed: Medida, Desenho, Terminal, Tolerância, Material, Acabamento, Posição |
| `engineering.lmp_nonconformity_problem_tags` | V005 | Junção PK `(nonconformity_id, tag_id)`; FK→NC CASCADE, FK→tag RESTRICT |
| `engineering.lmp_nonconformity_history` | V006 + fix V008 | Append-only (`changes JSONB`, `actor_user_id/email/name`, `event_type ∈ {created,updated}`); trigger `prevent_lmp_nc_history_mutation` bloqueia UPDATE/DELETE; V008 libera DELETE apenas com GUC `app.allow_lmp_nc_history_delete=true` na sessão |
| `engineering.prevent_lmp_nc_history_mutation()` | V006/V008 | Função trigger — proteção de integridade da trilha auditável |

Migrations V001–V009 em `api-delpi/migrations/plugins/engineering/` — **imutáveis** (`migrations-immutable-checksum`). V010–V011 são metalografia (mesmo schema, domínio distinto — fora de escopo).

### 3.2. Autoridade e acesso efetivos hoje

| Item | Efetivo (PROVEN) |
|---|---|
| Owner de código da persistência | `api-delpi` — `PostgresLmpNonconformityRepository` (`PluginBaseRepository`) |
| Principal técnico | `PLUGINS_DB_USER`/`PLUGINS_DB_PASSWORD` → `postgres-plugins:5432`, app `api-delpi-plugins`, pool ≤10 |
| ⚠ Isolamento de credencial | **Inexistente entre serviços**: `PLUGINS_DB_*` é injetada em ~18 serviços no compose — qualquer um pode tecnicamente escrever em `engineering.*`. Isolamento atual é apenas lógico (convenção de schema) |
| RLS | **não há** Row-Level Security; proteção de histórico é via trigger/GUC de sessão |
| Grants efetivos | default do superusuário de conexão — não há role dedicada por domínio |
| Migrations runner | pipeline `api-delpi` (plugins migrations, `up`-only em prod) |

## 4. Regras de negócio inventariadas (NC-G0-04)

| Regra | Fonte | Comportamento |
|---|---|---|
| Status | CHECK + router + `_STATUS_VALUES` | `open`/`in_progress`/`done`; default `open`; update exige valor válido |
| `occurrence_date` | V009 + repo | Data do fato; create default `CURRENT_DATE`; **obrigatória no update** |
| `registered_at` | repo | Server-side no create (`COALESCE(param, NOW())` — import pode preservar) |
| Tags de problema | V005 + `normalize_problem_tag_labels` | Catálogo compartilhado; label nova é **criada** no catálogo ao salvar; dedup case-insensitive |
| Produtos | `_normalize_products` | UPPER, dedup por `product_code`, replace-all por escrita |
| Histórico | V006 + `build_nc_history_changes` | Diff `{fields:[{field,label,old,new}]}`, ator completo; `updated` só com diff real |
| Delete | repo + V008 | Hard delete + CASCADE; GUC de sessão libera cascade no histórico append-only |
| Import | use case + repo | **Substituição total** (delete_all + insert); `dry_run`; dedup natural-key (OV+descrição+tags); `skip_existing` ignorado |
| Streak | `list_occurrence_dates` + use case | Dias sem NC por datas distintas de `occurrence_date`; `as_of`/`reference` no payload |
| Sort | `lmp_nonconformity_list_sort` | Whitelist de 12 colunas; default `registered_at DESC` |
| Ator/auditoria | `_current_actor` + history | `user_id`, `email`, `name`, `label` do JWT no request — gravado por evento |
| Timezone | DDL | `timestamptz` em `registered_at`/`created_at`/`updated_at`; `date` nos campos de negócio |

## 5. Consumidores — matriz source→consumer (NC-G0-02/08)

| Consumidor | Uso | Via | Estado |
|---|---|---|---|
| MFE legado `plugins/dashboard-lmps` | **CRUD completo**: list/detail/form/history/import/export/delete + NC tab | `api/lmpNonconformityApi.ts` → `/apps/api-delpi/engineering/lmps/nonconformities*` (Bearer humano) | ATIVO — owner funcional atual |
| MFE legado — hydrate de formulário | OV→cliente/datas, busca produto, BOM | `productApi.ts` → `/apps/api-delpi/products/search`, `/products/{code}/structure`; `lmpApi.ts` → `/engineering/lmps/{sale}` | ATIVO — TOTVS facts direto |
| Engineering API | `GET /v1/lmps/nonconformities/streak` | `delegated_auxiliary.py` → `api-delpi GET …/streak` com Bearer humano delegado | ATIVO — **delegação transitória** eng-api→api-delpi→Postgres (proibida como permanente, §7 doc 46) |
| MFE `plugins/engineering` | KPI "Dias sem NC" no dashboard LMP | `/apps/engineering-api/v1/lmps/nonconformities/streak` | ATIVO READ |
| MFE `plugins/engineering` | Deep links `/apps/engineering/lmps/nonconformities*` | `NcLegacyRedirectNotice` — sem dados NC locais | ATIVO — redirect honesto ao legado |
| Portal — catálogo | "Não Conformidades" futuro `Início →` | doc 45 — TARGET, não implementado | PLANNED |
| EVA/MCP `tool_bridge` | Nenhuma tool NC | `_TOOL_CONTRACT` tem só home/overview; NC deverá entrar como `_PLANNED_CAPABILITIES` até contrato | AUSENTE — ledger §10 |
| SI/DÉLIA/TV/outros | Nenhum caller NC identificado no HEAD | residual search `nonconformit*` fora dos 3 bounded contexts = 0 hits funcionais | PROVEN no código; telemetria 30–60d de runtime = **TO_INVENTORY** (não inventada) |

## 6. Permissões legadas e risco (NC-G0-02, risco §3 do plano)

| Código | Efeito hoje |
|---|---|
| `api-delpi.access` | Concede **READ e WRITE** NC — `require_any_permission` aceita qualquer item da lista `ENGINEERING_LMP_NC_WRITE`. **Risco confirmado:** permissão genérica de API implica mutação de NC (create/update/delete/import) |
| `dashboard-lmps.view` | Concede READ NC |
| `dashboard-engineering.view` | Concede READ NC |
| `dashboard-lmps.nc.write` | Concede WRITE NC (a granular pretendida) |

**Implicações:** (a) qualquer titular de `api-delpi.access` hoje pode criar/editar/excluir/importar NC — hardening coordenado exigido ANTES do cutover (restrição do WRITE guard), com teste de não-regressão nos writers legítimos; (b) nenhuma dessas permissões será usada nos novos endpoints E-NC-* — exclusivamente `engineering.access` (+`engineering.manage` apenas admin futuro, quando existir); (c) `engineering.access` hoje **não** concede acesso NC legado — os públicos são disjuntos; a migração de consumidores exigirá grants `engineering.access` ao público NC atual (role `Analista de Engenharia - SC` já cobre parte).

## 7. ADR-NC-OWNERSHIP — proposta submetida aos owners (NC-G0-05)

> **ARCHITECTURE_DECISION_REQUIRED** — este documento **propõe**; a autoridade formal sobre dados, grants e exclusividade de escrita pertence ao owner atual da persistência (API DELPI/Platform DB) + Engenharia + Plataforma. Não presumir aprovação.

### 7.1. Decisão a tomar

1. **Titular do schema `engineering.*` NC** — manter no `postgres-plugins` (físico) e transferir autoridade funcional (Opção B) × mover fisicamente (B+movimentação, só com justificativa).
2. **Principal técnico dedicado** — criar role DB `engineering_api` (ou equivalente) com grants restritos a `engineering.lmp_*`; revogar dependência de `PLUGINS_DB_USER` compartilhado para NC; política para demais ~17 serviços que hoje alcançam o schema (hardening incremental, não big bang).
3. **Writer único** — congelar writes legados na janela de troca; `engineering-api → api-delpi → Postgres` **proibido** como arquitetura permanente (permitido só na delegação transitória já existente para streak, com prazo/registro).
4. **Migrations** — ownership do diretório `api-delpi/migrations/plugins/engineering/` e do runner; novas migrations NC passam a ser emitidas pela Engineering API (ou por runner governado) após handoff; V001–V009 permanecem imutáveis.
5. **Leitores compatíveis** — streak e demais READs continuam atendidos durante a transição; legado lê via API DELPI até cutover funcional (Opção A transitória) — nunca double-write.
6. **Backups/retenção/PII** — snapshot pré-migração obrigatório; `lmp_nonconformity_history` contém PII de ator (user_id/email/name) — minimização na exposição (§8), retenção da trilha integral.
7. **Multi-instância** — Postgres plugins é único hoje; documentar dev/prod e eventual divergência DEV×PROD do streak (doc 38/44 já registram observação).

### 7.2. Opções

| Opção | Descrição | Recomendação |
|---|---|---|
| **A transitória** | api-delpi permanece owner de READ/WRITE só para o legado até readiness+cutover autorizados | Aceitável como fase; **proibida como permanente** |
| **B preferencial** | Engineering API assume repository port + writes sobre o storage existente; ownership DB explicitamente atribuído; principal dedicado com grants em `engineering.lmp_*`; troca governada de writer único | **Recomendada** — nenhuma movimentação física desnecessária; schema já é domínio engenharia |
| **B com movimentação** | Migrar dados para DB/cluster próprio da Engineering API | Só se operação demonstrar necessidade; exige backup/backfill/checksum/rollback/janela |

### 7.3. Pré-condições do ACT de ownership

- Role DB dedicada + grants mínimos (`SELECT/INSERT/UPDATE/DELETE` em `engineering.lmp_*`; `EXECUTE` em função do trigger GUC é implícito — documentar como a API define a GUC de sessão de forma segura).
- Runner de migrations acordado (imutabilidade preservada; novas versões ≥V012 por convenção do domínio).
- Freeze de writers legados na janela; checksum contagem+PK+history antes/depois; replay/delta se a janela exceder.
- Rollback: grants reversíveis, sem drop, sem revogação de grants não relacionados; compensação de writes novos se houver intercalação.
- Aprovação formal dos owners: API DELPI (owner atual), Engenharia (owner funcional alvo), Platform DB/Security, Core RBAC, EVA/MCP.

## 8. Contratos TARGET — Engineering API (NC-G0-06/09/10)

Convenções herdadas do eng-api: prefixo `/v1/`, `operation_id` snake_case, envelope `ok`/`fail` com `operation_id`, `@require_any_permission(["engineering.access"])` + `_require_human_principal` para operações personalizadas, estados honestos `unavailable|forbidden`, validação na borda (400), 404 honesto, AuthZ Core live fail-closed. **Caminhos abaixo são PROPOSTA de contrato — não publicados nem implementados.**

| ID | Proposta | Tipo | AuthZ | Notas de contrato |
|---|---|---|---|---|
| E-NC-01 | `GET /v1/nonconformities` | READ | `engineering.access` | Mesmos filtros/orden whitelist/paginação da fonte; resposta `items+total+page+sort`; 400/401/403/500 |
| E-NC-02 | `GET /v1/nonconformities/{id}` | READ | `engineering.access` | 404 vs 403 distintos; PII de `created_by/updated_by` avaliada |
| E-NC-03 | `GET /v1/nonconformities/{id}/history` | READ | `engineering.access` | Ator exposto com minimização (name/label; e-mail avaliado como sensível) |
| E-NC-04 | `GET /v1/nonconformities/streak` (+agregados) | READ | `engineering.access` | **Mesma semântica** do KPI LMP; migração da fonte exige paridade por período/fronteira (doc 46 §7) |
| E-NC-05 | `GET /v1/nonconformities/problem-tags` | READ | `engineering.access` | Catálogo oficial compartilhado |
| E-NC-06 | `GET /v1/nonconformities/export` | READ | `engineering.access` | Export governada; `version`, `generated_at`, `count`, `items` |
| E-NC-07 | `POST /v1/nonconformities` | WRITE | `engineering.access` (human) | Validação = body atual; `registered_at` server; ator do JWT; history `created`; idempotency-key opcional a definir |
| E-NC-08 | `PUT /v1/nonconformities/{id}` | WRITE | `engineering.access` (human) | Full-replace documentada; `occurrence_date` obrigatória; ETag/`updated_at` para concorrência (a definir); 404/409/422 |
| E-NC-09 | `DELETE /v1/nonconformities/{id}` | WRITE | `engineering.access` (human) | Semântica hard-delete + cascade documentada; considerar soft-delete só se owner decidir — **sem mudança silenciosa de semântica** |
| E-NC-10 | `POST /v1/nonconformities/import` | WRITE | `engineering.access` (human) | Política explícita de substituição total + `dry_run` + dedup natural-key; transação única; relatório de erros parciais |
| E-NC-11 | `GET /v1/nonconformities/context?sale_number=…&product_code=…` | READ (enrich) | `engineering.access` | Enriquecimento OV/produto/BOM **somente via BFF→api-delpi facts** (S2S dedicado); nunca browser→api-delpi, nunca SoT TOTVS transferido |

**Segurança transversal dos contratos:** identidade humana Keycloak; Core efetiva (`engineering.access`) live em READ e WRITE; `engineering.manage` não implica access; service identities sem poder mutável por default; negativas 401/403/404/409/422; Core-down fail-closed; `engineering.*` nunca em guards da api-delpi; observability com `operation_id`/`request_id` sem dados sensíveis.

## 9. Writer único, migração e rollback (NC-G0-07/08/12)

**Estratégia (Opção B):**
1. G1: port `NonconformityRepository` + adapter Postgres na eng-api (principal dedicado), READ shadow; paridade lista/detail/history/streak vs api-delpi com tolerância 0; api-delpi segue writer.
2. G2: use cases WRITE + transações + history + import; ainda sem produção; testes de concorrência/idempotência.
3. Janela de troca (G5): freeze de writers legados → checksum (contagem/PK/history) → grants + deploy eng-api writer → legado passa a ler/escrever somente via contrato novo ou congela → monitoramento.
4. Rollback: reversão de grants + redeploy legado writer; compensação/reconciliação de writes intercalados; nunca rollback simplista após novos writes.
5. G6: deprecar guards/rotas NC da api-delpi somente com ledger de consumidores zerado (telemetria) + aprovação de owners.

**Compatibilidade:** streak mantém mesma semântica e payload; KPI LMP do Portal migra de `/v1/lmps/nonconformities/streak` para a fonte nova só após paridade por período/fronteira documentada; metas/IDD permanecem com SI; import continua suportando `dry_run` e relatório honesto; deep links NC redirecionam ao legado até UI nativa existir.

## 10. Ledger API ↔ EVA — parity-by-capability (NC-G0-11)

| Engineering API | EVA capability (proposta) | Categoria | Estado |
|---|---|---|---|
| E-NC-01 list/search | `search_nonconformities` | READ | PLANNED — escopo/filtragem efetiva da Core, limites herdados |
| E-NC-02 detail | `get_nonconformity` | READ | PLANNED — resposta oficial, PII minimizada |
| E-NC-03 history | `get_nonconformity_history` | READ | PLANNED — não fabricar causas/revisões; incerteza explícita |
| E-NC-04 streak/agregados | `get_nonconformity_indicators` | READ | PLANNED — nunca recalcular indicador oficial |
| E-NC-05 tags | `get_nonconformity_tags` | READ | PLANNED — catálogo oficial |
| E-NC-11 contexto OV/produto | `get_nonconformity_context` | READ | PLANNED — via eng-api, nunca DB/TOTVS direto |
| E-NC-07/08/10 prepare | `prepare_nonconformity_mutation` (diff+validação+confirmação humana) | PREPARE | PLANNED — sem write indireto; `engineering.access` ≠ aprovação humana |
| E-NC-07/08/09/10 act | tools mutáveis | ACT | **PENDING** — exige contrato específico, aprovação, idempotência, auditoria, revogação; delete/import com confirmação reforçada |

Regras: capability nova da API ⇒ avaliação EVA na mesma entrega; tool bridge eng-api é superfície in-process (não SoT, sem escopo derivado de prompt); tools não comprovadas ficam em `_PLANNED_CAPABILITIES`; WRITE da EVA não se habilita pela existência da rota. Testes por risco: catalog/schema/grounding/permission boundaries (com e sem access, manage-only, Core down, service identity)/hallucination/task outcome/negative write/postcondition auditável/isolamento do legado.

## 11. Plano de testes (NC-G0-12)

- **Paridade READ (G1):** list/detail/history/streak/tags/export eng-api vs api-delpi, mesmos filtros/período, tolerância 0; inclui divergências DEV×PROD documentadas.
- **AuthZ negativos:** sem token 401; sem `engineering.access` 403; manage-only (quando existir) sem access operacional; token inválido; Core down fail-closed; service identity sem write; `engineering.*` ausente em guards api-delpi.
- **WRITE (G2+):** create/update/delete/history em ambiente autorizado; update sem `occurrence_date` → 422/400; concorrência ETag; import `dry_run` + substituição + dedup; delete cascade com GUC; ator correto gravado.
- **Concorrência/idempotência:** PUT simultâneos; import duplo; create com idempotency-key.
- **Boundary:** 0 chamada browser→api-delpi na superfície nova; S2S só para E-NC-11 facts.
- **Regressão legado:** dashboard-lmps CRUD continua funcional durante Opção A transitória; hardening do WRITE guard sem quebrar `dashboard-lmps.nc.write` legítimo.

## 12. Drift, decisões e pendências (NC-G0-15)

- **ARCHITECTURE_DECISION_REQUIRED:** transferência formal da persistência (§7) — owners: API DELPI/Platform DB (atual), Engenharia (alvo), Platform Security, Core RBAC, EVA/MCP. Documento **propõe Opção B**; não há aprovação presumida.
- **Risco legado a tratar antes do cutover:** `api-delpi.access` ⇒ WRITE NC (§6) — hardening coordenado pendente de decisão.
- **TO_INVENTORY:** telemetria de runtime 30–60d dos endpoints NC (consumidores não-óbvios) — código-fonte mostra apenas dashboard-lmps + streak delegado.
- **RLS/granularidade DB ausente:** Postgres plugins compartilhado com principal único — ADR deve decidir role dedicada e política para demais schemas/domínios (transversal, não só NC).
- **Semântica a confirmar com owner funcional:** hard-delete × soft-delete; política de campos PII em history/export; `lmp_number` legado sem SoT.
- **Doc 45 independente:** separação de navegação não autoriza ativar NC; catálogo "Não Conformidades" permanece TARGET.
- **NC-G0-13:** zero writes/migrations/deploy/cutover executados — diff exclusivamente documental.

## 13. Critérios de aceite

| ID | Resultado |
|---|---|
| NC-G0-01 Reancoragem/authorities | PASS |
| NC-G0-02 Mapa rotas + consumers | PASS — 10 endpoints, 6 READ/4 WRITE, matriz §5 |
| NC-G0-03 Modelo Postgres + autoridade | PASS — schema/tabelas/trigger/principal comprovados (§3) |
| NC-G0-04 Regras/status/history/tags/import/validações | PASS — §4 |
| NC-G0-05 ADR ownership submetido | PASS — §7 (proposta Opção B; aprovação formal pendente = ADR) |
| NC-G0-06 Contratos E-NC-* definidos | PASS — §8 (E-NC-01…11) |
| NC-G0-07 Isolamento writer + dados + rollback | PASS — §9 |
| NC-G0-08 Compatibilidade legado + streak | PASS — §9 |
| NC-G0-09 Lookup TOTVS restrito ao BFF | PASS — E-NC-11 |
| NC-G0-10 `engineering.*` confinadas | PASS — §6/§8 |
| NC-G0-11 Ledger EVA READ/PREPARE/ACT | PASS — §10 |
| NC-G0-12 Plano de testes | PASS — §11 |
| NC-G0-13 Sem write/migração/deploy | PASS — diff só documental |
| NC-G0-14 Doc + relatório | PASS — este documento + EVA REPORT |
| NC-G0-15 Drift/decisões reportados | PASS — §12 |

## 14. Próximo gate

**NC.G1** (proposta doc 46): domain/application + `NonconformityRepository` port/adapter Postgres sob owner aprovado, migrations não-destrutivas se necessárias, contratos READ em shadow, paridade lista/detail/history/streak, EVA READ em lockstep. **Bloqueado** até aprovação do ADR-NC-OWNERSHIP pela Coordenação/owners. Não avançar automaticamente.
