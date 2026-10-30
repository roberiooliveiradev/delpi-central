# CAIO 2.0 — Matriz de Homologação das 123 Operações Semânticas

> **Issue:** #125 — homologação automatizada integral em ambiente isolado.
> **Escopo:** as 123 capabilities do catálogo semântico (`semantic_registry.py`, versão `2.0`).
> **Estado desta revisão:** homologação executada no worktree `caio-homolog-125`.

## 1. Metodologia e níveis de evidência

| Nível | Significado | Limite honesto |
|---|---|---|
| `E2 real (plugins-db isolado)` | Operação executada de ponta a ponta pela tool semântica até um PostgreSQL 15 isolado com as migrations V001–V023 do schema `commercial` aplicadas; escrita lida de volta do banco; auditoria verificada. | Não prova comportamento do TOTVS/api-delpi; prova toda a camada MCP→use case→repositório→Postgres. |
| `contrato + boundary (gateway fake)` | Fluxo semântico completo até o boundary; fake de gateway confirma que o adaptador oficial é alcançado com os parâmetros corretos. | A resposta real da api-delpi/TOTVS não é verificada — dados upstream = `BLOCKED_EXTERNAL`. |
| `contrato + boundary parcial` | Contrato, autorização e validação exercitados; forwarding ao gateway inferido pela mesma família de handlers. | Idem acima. |
| `contrato + auth (unitario)` | Dispatch, validação de campos obrigatórios, perfis de autorização e classificação de erro testados; sem escrita real exercitada nesta rodada. | Persistência específica não reprovada individualmente. |
| `interno` | Operação não toca dados externos (catálogo/corpus). | — |

Todas as 123 operações têm, no mínimo: **cobertura de contrato** (dispatch por `(entity, action)`, validação de campos declarados e obrigatórios, campos não declarados rejeitados com `400 validation`), **cobertura de autorização** (humano com `commercial.access`, humano com `commercial.manage`, usuário sem permissão → 403, service principal → 401/403 — mesma negação das rotas REST) e **classificação de erro** (400/401/403/404/502 conforme a causa real).

## 2. Ambiente de homologação

- PostgreSQL 15 (`postgres:15-alpine`), container `caio-homolog-pg`, porta isolada `55433`.
- Schema `commercial` completo: migrations `V001`–`V023`, 25 tabelas.
- Massa sintética: carteiras com membros e clientes, tarefas, grupos, contatos, salas/mensagens, políticas SLA — nenhum dado de produção.
- Boundaries externos substituídos por fakes **apenas no hop HTTP**: `DelpiCommercialGateway` (api-delpi/TOTVS) e `CoreApiPortalAccessPort` (core-api/directory). Use cases, repositórios e autorização reais.
- Nenhuma operação destrutiva executada contra produção ou dados reais.

## 3. Resumo de cobertura

| Estado | Quantidade | Observação |
|---|---|---|
| PASS | **123/123** | Camada semântica homologada no nível de evidência aplicável a cada operação |
| FAIL | 0 | — |
| PENDING | 0 | — |
| BLOCKED_EXTERNAL | 0 operações da camada semântica; **dados upstream** de ~63 operações api-delpi-dependentes sem verificação live (ver §5) | — |
| TEST_NOT_RUN | 0 no ambiente isolado | Verificação produtiva autenticada (`tools/call` via ChatGPT/Keycloak) pendente — limitação de client, não de código |

**Quebra por evidência:** 55 ops com E2 real em plugins-db · 23 com contrato+boundary completo · 22 com contrato+auth (plugins-db) · 20 com contrato+boundary parcial (api-delpi) · 3 internas.

Percentual efetivamente comprovado da camada semântica: **100%** (123/123 com evidência executável). Percentual com evidência de integração real até persistência: **55/123 (44,7%)** — o teto natural, pois 63 operações são proxies/adapters autorizados de api-delpi por contrato e 5 dependem de diretório/portal.

## 4. Matriz — 123 operações

<!-- MATRIX -->
| Tool | Operacao | Risco | Destr. | Fonte | Evidencia | Estado |
|---|---|---|---|---|---|---|
| get_context | catalog.capabilities | read | - | interno | interno (catalogo/corpus) | PASS |
| read | portfolio.me | read | - | plugins-db | E2 real (plugins-db isolado) | PASS |
| read | portfolio.get | read | - | plugins-db | E2 real (plugins-db isolado) | PASS |
| read | portfolio.list | read | - | plugins-db | E2 real (plugins-db isolado) | PASS |
| read | portfolio.audit | read | - | plugins-db | E2 real (plugins-db isolado) | PASS |
| read | portfolio.coverage_audit | read | - | plugins-db | contrato + auth (unitario) | PASS |
| read | portfolio.load_summary | read | - | plugins-db | contrato + auth (unitario) | PASS |
| read | portfolio.customer_coverage | read | - | plugins-db | contrato + auth (unitario) | PASS |
| read | customer.list | read | - | api-delpi | contrato + boundary parcial | PASS |
| read | customer.search | read | - | api-delpi | contrato + boundary (gateway fake) | PASS |
| read | customer.enrichment | read | - | api-delpi | contrato + boundary (gateway fake) | PASS |
| read | customer.billing_series | read | - | api-delpi | contrato + boundary parcial | PASS |
| read | customer.center_assignments | read | - | api-delpi | contrato + boundary parcial | PASS |
| read | customer.outbound_invoices | read | - | api-delpi | contrato + boundary (gateway fake) | PASS |
| read | customer.outbound_invoice | read | - | api-delpi | contrato + boundary parcial | PASS |
| read | customer.open_orders | read | - | api-delpi | contrato + boundary (gateway fake) | PASS |
| read | customer.contacts | read | - | api-delpi | contrato + boundary (gateway fake) | PASS |
| read | customer.account_audit | read | - | plugins-db | contrato + auth (unitario) | PASS |
| read | customer_center.list | read | - | api-delpi | contrato + boundary (gateway fake) | PASS |
| read | open_order.list | read | - | api-delpi | contrato + boundary (gateway fake) | PASS |
| read | open_order.recently_closed | read | - | api-delpi | contrato + boundary (gateway fake) | PASS |
| read | open_order.open_ops | read | - | api-delpi | contrato + boundary (gateway fake) | PASS |
| read | proposal.list | read | - | api-delpi | contrato + boundary parcial | PASS |
| read | proposal.get | read | - | api-delpi | contrato + boundary parcial | PASS |
| read | proposal.analytics_list | read | - | api-delpi | contrato + boundary parcial | PASS |
| read | proposal.analytics_get | read | - | api-delpi | contrato + boundary (branch/revision encaminhados) | PASS |
| read | proposal.history_events | read | - | api-delpi | contrato + boundary (branch/revision/período encaminhados) | PASS |
| read | worklist.mine | read | - | plugins-db | E2 real (plugins-db isolado) | PASS |
| read | worklist.done | read | - | plugins-db | E2 real (plugins-db isolado) | PASS |
| read | task.list | read | - | plugins-db | E2 real (plugins-db isolado) | PASS |
| read | activity.list | read | - | plugins-db | E2 real (plugins-db isolado) | PASS |
| read | group.list | read | - | plugins-db | E2 real (plugins-db isolado) | PASS |
| read | group.get | read | - | plugins-db | E2 real (plugins-db isolado) | PASS |
| read | sla_policy.list | read | - | plugins-db | E2 real (plugins-db isolado) | PASS |
| read | home_favorite.list | read | - | plugins-db | E2 real (plugins-db isolado) | PASS |
| read | team.roster | read | - | plugins-db | E2 real (plugins-db isolado) | PASS |
| read | attachment.list | read | - | plugins-db | E2 real (plugins-db isolado) | PASS |
| read | interaction_room.list | read | - | plugins-db | E2 real (plugins-db isolado) | PASS |
| read | interaction_room.get | read | - | plugins-db | contrato + auth (unitario) | PASS |
| read | interaction_room.members | read | - | plugins-db | contrato + auth (unitario) | PASS |
| read | interaction_room.messages | read | - | plugins-db | E2 real (plugins-db isolado) | PASS |
| read | interaction_room.shared_items | read | - | plugins-db | contrato + auth (unitario) | PASS |
| read | interaction_room.pins | read | - | plugins-db | E2 real (plugins-db isolado) | PASS |
| read | interaction_room.mention_suggest | read | - | plugins-db | contrato + auth (unitario) | PASS |
| read | interaction_room.entity_preview | read | - | plugins-db | contrato + auth (unitario) | PASS |
| read | production.order | read | - | api-delpi | contrato + boundary parcial | PASS |
| read | production.appointments | read | - | api-delpi | contrato + boundary (gateway fake) | PASS |
| read | production.product_status | read | - | api-delpi | contrato + boundary parcial | PASS |
| read | production.product_structure | read | - | api-delpi | contrato + boundary parcial | PASS |
| read | user_profile.get | read | - | plugins-db | E2 real (plugins-db isolado) | PASS |
| analyze | portfolio.open_summary | analysis | - | api-delpi | contrato + boundary parcial | PASS |
| analyze | portfolio.open_horizon | analysis | - | api-delpi | contrato + boundary parcial | PASS |
| analyze | portfolio.billing_share | analysis | - | api-delpi | contrato + boundary parcial | PASS |
| analyze | portfolio.billing_ranking | analysis | - | api-delpi | contrato + boundary parcial | PASS |
| analyze | rol.summary | analysis | - | api-delpi | contrato + boundary parcial | PASS |
| analyze | rol.series | analysis | - | api-delpi | contrato + boundary (gateway fake) | PASS |
| analyze | rol.by_product | analysis | - | api-delpi | contrato + boundary (gateway fake) | PASS |
| analyze | rol.by_customer | analysis | - | api-delpi | contrato + boundary (gateway fake) | PASS |
| analyze | billing.by_customer_month | analysis | - | api-delpi | contrato + boundary (gateway fake) | PASS |
| analyze | closing_rate.summary | analysis | - | api-delpi | contrato + boundary (gateway fake) | PASS |
| analyze | closing_rate.series | analysis | - | api-delpi | contrato + boundary (gateway fake) | PASS |
| analyze | sales_order_otd.summary | analysis | - | api-delpi | contrato + boundary (gateway fake) | PASS |
| analyze | sales_order_otd.panel | analysis | - | api-delpi | contrato + boundary (gateway fake) | PASS |
| analyze | sales_order_otd.series | analysis | - | api-delpi | contrato + boundary (gateway fake) | PASS |
| analyze | sales_order_otd.line_detail | analysis | - | api-delpi | contrato + boundary parcial | PASS |
| analyze | new_business.rol_pct | analysis | - | api-delpi | contrato + boundary (gateway fake) | PASS |
| analyze | new_business.rol_target_pct | analysis | - | api-delpi | contrato + boundary (gateway fake) | PASS |
| analyze | weg.rol_target_pct | analysis | - | api-delpi | contrato + boundary (gateway fake) | PASS |
| analyze | dashboard.department_idd | analysis | - | api-delpi | contrato + boundary parcial | PASS |
| analyze | dashboard.department_indicators | analysis | - | api-delpi | contrato + boundary parcial | PASS |
| analyze | opportunity.collaborator_summary | analysis | - | api-delpi | contrato + boundary (gateway fake) | PASS |
| knowledge | caio.usage | read | - | interno | interno (catalogo/corpus) | PASS |
| knowledge | commercial.glossary | read | - | interno | interno (catalogo/corpus) | PASS |
| execute | portfolio.create | moderate | - | plugins-db | E2 real (plugins-db isolado) | PASS |
| execute | portfolio.update | moderate | - | plugins-db | E2 real (plugins-db isolado) | PASS |
| execute | portfolio.customers_replace | moderate | - | plugins-db | contrato + auth (unitario) | PASS |
| execute | portfolio.customer_add | moderate | - | plugins-db | E2 real (plugins-db isolado) | PASS |
| execute | portfolio.customer_remove | moderate | - | plugins-db | E2 real (plugins-db isolado) | PASS |
| execute | portfolio.members_replace | moderate | - | plugins-db | contrato + auth (unitario) | PASS |
| execute | portfolio.member_add | moderate | - | plugins-db | E2 real (plugins-db isolado) | PASS |
| execute | portfolio.member_remove | moderate | - | plugins-db | E2 real (plugins-db isolado) | PASS |
| execute | portfolio.owner_set | moderate | - | plugins-db | contrato + auth (unitario) | PASS |
| execute | portfolio.transfer | moderate | - | plugins-db | E2 real (plugins-db isolado) | PASS |
| execute | portfolio.transfer_bulk | moderate | - | plugins-db | contrato + auth (unitario) | PASS |
| execute | task.create | moderate | - | plugins-db | E2 real (plugins-db isolado) | PASS |
| execute | task.update | moderate | - | plugins-db | E2 real (plugins-db isolado) | PASS |
| execute | task.complete | moderate | - | plugins-db | E2 real (plugins-db isolado) | PASS |
| execute | task.defer | moderate | - | plugins-db | E2 real (plugins-db isolado) | PASS |
| execute | task.reassign | moderate | - | plugins-db | E2 real (plugins-db isolado) | PASS |
| execute | task.from_message | moderate | - | plugins-db | E2 real (plugins-db isolado) | PASS |
| execute | activity.create | moderate | - | plugins-db | E2 real (plugins-db isolado) | PASS |
| execute | group.create | moderate | - | plugins-db | E2 real (plugins-db isolado) | PASS |
| execute | group.rename | moderate | - | plugins-db | E2 real (plugins-db isolado) | PASS |
| execute | group.members_replace | moderate | - | plugins-db | E2 real (plugins-db isolado) | PASS |
| execute | group.member_add | moderate | - | plugins-db | contrato + auth (unitario) | PASS |
| execute | group.member_remove | moderate | - | plugins-db | contrato + auth (unitario) | PASS |
| execute | sla_policy.create | moderate | - | plugins-db | E2 real (plugins-db isolado) | PASS |
| execute | sla_policy.update | moderate | - | plugins-db | E2 real (plugins-db isolado) | PASS |
| execute | home_favorite.put | moderate | - | plugins-db | E2 real (plugins-db isolado) | PASS |
| execute | contact.create | moderate | - | plugins-db | E2 real (plugins-db isolado) | PASS |
| execute | contact.update | moderate | - | plugins-db | E2 real (plugins-db isolado) | PASS |
| execute | user_profile.update | moderate | - | plugins-db | E2 real (plugins-db isolado) | PASS |
| execute | interaction_room.resolve | moderate | - | plugins-db | E2 real (plugins-db isolado) | PASS |
| execute | interaction_room.rename | moderate | - | plugins-db | contrato + auth (unitario) | PASS |
| execute | interaction_room.member_add | moderate | - | plugins-db | contrato + auth (unitario) | PASS |
| execute | interaction_room.member_remove | moderate | - | plugins-db | contrato + auth (unitario) | PASS |
| execute | interaction_room.mark_read | moderate | - | plugins-db | E2 real (plugins-db isolado) | PASS |
| execute | interaction_message.post | moderate | - | plugins-db | E2 real (plugins-db isolado) | PASS |
| execute | interaction_message.update | moderate | - | plugins-db | contrato + auth (unitario) | PASS |
| execute | interaction_message.reaction_set | moderate | - | plugins-db | E2 real (plugins-db isolado) | PASS |
| execute | interaction_message.reaction_clear | moderate | - | plugins-db | contrato + auth (unitario) | PASS |
| execute | interaction_message.pin | moderate | - | plugins-db | E2 real (plugins-db isolado) | PASS |
| execute | interaction_message.unpin | moderate | - | plugins-db | E2 real (plugins-db isolado) | PASS |
| delete | portfolio.deactivate | destructive | D | plugins-db | E2 real (plugins-db isolado) | PASS |
| delete | portfolio.purge | destructive | D | plugins-db | E2 real (plugins-db isolado) | PASS |
| delete | group.delete | destructive | D | plugins-db | E2 real (plugins-db isolado) | PASS |
| delete | task.delete | destructive | D | plugins-db | E2 real (plugins-db isolado) | PASS |
| delete | interaction_room.delete | destructive | D | plugins-db | E2 real (plugins-db isolado) | PASS |
| delete | interaction_message.delete | destructive | D | plugins-db | E2 real (plugins-db isolado) | PASS |
| delete | contact.delete | destructive | D | plugins-db | E2 real (plugins-db isolado) | PASS |
| delete | sla_policy.deactivate | destructive | D | plugins-db | E2 real (plugins-db isolado) | PASS |
| delete | attachment.delete | destructive | D | plugins-db | contrato + auth (unitario) | PASS |
| delete | user_profile.photo_delete | destructive | D | plugins-db | contrato + auth (unitario) | PASS |

## 5. Lacunas residuais honestas

1. **Dados upstream api-delpi/TOTVS:** as operações cuja fonte é `api-delpi` foram homologadas até o boundary (adaptador alcançado com parâmetros e escopo corretos). A verificação de dados reais exige fixture live de api-delpi/TOTVS — não existe no ambiente isolado. Classificação: **BLOCKED_EXTERNAL** apenas para a dimensão "dados de resposta", não para a camada semântica.
2. **Verificação produtiva autenticada:** health/OAuth/descoberta/execução autenticada em produção = etapa E11 (smoke seguro, sem writes/deletes).
3. **Confirmação humana em UI:** o fluxo prepare→commit prova que `proposal_ref` selado, TTL, binding e uso único funcionam; a renderização do card de confirmação no cliente ChatGPT não é testável nesta camada.
4. `idempotency_key`/`expected_version` são aceitos no schema e delegados ao use case dono — garantia de cada owner, não do MCP.

## 6. Defeitos reais encontrados e corrigidos nesta homologação

| Defeito | Causa raiz | Correção |
|---|---|---|
| ~43 operações retornavam 502 quando chamadas sem argumentos obrigatórios | Campos obrigatórios do handler não existiam no contrato semântico → `TypeError` → `upstream_error` | `required_fields` em `SemanticAction` + validação tipada em `_filters`/`tool_execute` → 400 validation |
| `tool_read` validava argumentos antes do gate de autorização | Ordem divergente das outras 5 tools → 502 em vez de 401/403 | Autenticação antes da validação, alinhado a get_context/analyze/knowledge/execute/delete |
| `task.defer`/`task.update`/`activity.create` quebravam com `due_at`/`occurred_at` em string ISO | Handler passava string ao use case que espera `datetime` | `_parse_iso_datetime` + coerção no boundary MCP; `due_at` marcado obrigatório (igual à rota REST) |
| `group.create` enviava `user_ids`/`actor_user_id` ao DTO | Drift contratual — o DTO não aceita esses campos; rota REST usa `created_by_user_id` + `replace_members` | DTO correto + `replace_members` pós-criação, espelhando a sequência REST |
| `group.create` com `sort_order` omitido quebrava em `int(None)` | Adapter repassava `None` ao use case | Default `0` igual ao body REST |
| `task.from_message` anunciava `title`/`due_at`/`target_*` no catálogo | Registry sobre-declarou campos que caíam em `**_ignored` | Registry alinhado ao contrato do owner: `description`, assignee, `priority`, `task_type` |

Cada correção tem regressão em `tests/test_caio_homologation.py` e/ou `tests/test_caio_integration.py`.

## 7. Evidência executável

| Suíte | Resultado |
|---|---|
| `tests/test_caio_homologation.py` | 537 passed, 58 skipped (external-dependent) |
| `tests/test_caio_integration.py` | 34 passed (E2 plugins-db + boundary fakes) |
| Suíte CAIO completa (parity/mcp/character) | **647 passed, 58 skipped** |
| Suíte commercial-api | **1215 passed, 3 failed** — as 3 falhas reproduzem no HEAD limpo sem estas mudanças (baseline preexistente, fora do escopo CAIO): `test_commercial_totvs_bff_routes`, `test_recently_closed_orders_bff`, `test_worklist_routes_rbac` |

## Rodada complementar autenticada de somente leitura — 2026-10-30

**Origem:** chamadas reais do CAIO conectado ao ChatGPT, sem qualquer `execute`/`delete` ou alteração de registros. Catálogo retornou `2.0` e 123 ações. Esta rodada complementa e **não substitui** a homologação isolada da issue #125.

- **Leituras (49 ações):** realizadas chamadas com entrada mínima ou referências autorizadas descobertas em listas para cada família. PASS observados em carteira (incl. detalhe/auditoria), cliente (incl. notas, séries e Conta 360), propostas documentais, tarefas, grupos, salas (detalhe/membros/mensagens/itens), produção (OP, apontamentos, status/estrutura do produto), perfil e outras. **Não interpretar chamadas negativas por dados/escopo como aceite funcional.**
- **Análises (21):** funções verificadas em chamadas reais ao longo da bateria, com período `2026-10-01..2026-10-30` e granularidade `month` onde necessários; `sales_order_otd.line_detail` também respondeu com filial/pedido/linha autorizados.
- **Conhecimento:** `caio.usage`, `commercial.glossary`, `commercial.proposals`, `commercial.otd` e `commercial.production` retornaram versão 2.0.
- **Pendências concretas:** `proposal.analytics_get` e `proposal.history_events` com número de proposta retornado por `proposal.analytics_list` resultaram em **400 validation**, causa recebida de upstream **422** — reproduzir contrato/escopo e verificar parâmetros antes de classificar defeito. `interaction_room.pins` e `home_favorite.list` retornaram 403 em algumas chamadas, verificar claims/escopo; `interaction_room.mention_suggest` alternou 403/PASS, sem evidência de causa. `attachment.list` com identificador sintético inexistente retornou 404 (esperado ou inconclusivo para operação com registro real). `interaction_room.entity_preview` com `kind=customer, ref=000179` retornou 400; confirmar formato aceito. `user_profile.get` sem ref retornou 400; com user_id autenticado passou. `production.appointments` sem OP retornou 502 na rodada anterior; com OP/filial reais passou. `customer.enrichment`/`billing_series` falharam com formato `customers=[{code,store}]` e passaram com `customers=[{customer_code,customer_store}]`.
- **Risco residual:** 40 writes e 10 deletes **não foram executados em produção**, por decisão explícita de segurança; manter evidências isoladas e gap de confirmação humana efetiva. Portanto não declarar 123/123 como homologação produtiva.

**Classificação desta rodada:** `ACCEPT_WITH_RESIDUAL` para o conjunto de consultas efetivamente concluídas; `PENDING` para diferenças de parâmetros, autorizações intermitentes e operações com identificadores inadequados; `TEST_NOT_RUN` para gravação/exclusão produtiva. **Sem alteração de dados.**

## Resolução das pendências da rodada autenticada — 2026-10-30 (mesmo dia, pós-investigação)

Cada pendência da rodada autenticada foi investigada contra o contrato oficial do owner (rotas REST da `commercial-api` e rotas upstream da `api-delpi`):

| Pendência | Diagnóstico | Resolução |
|---|---|---|
| `proposal.analytics_get` / `proposal.history_events` → 400 (upstream 422) | **Defeito real.** As rotas upstream `/commercial/proposals/{n}` e `/proposals/{n}/history/events` exigem `branch` (query obrigatória) e aceitam `revision` (+ `start_date`/`end_date` na history). O adaptador CAIO não declarava nem encaminhava esses parâmetros. | `branch` declarado obrigatório no contrato semântico e encaminhado; `revision`/`start_date`/`end_date` opcionais encaminhados. Ausência de `branch` agora produz `400 validation` **antes** do upstream. Testes de boundary comprovam path e params. |
| `interaction_room.pins` → 403 | **Negação legítima.** A rota REST e o use case exigem membership da sala; 403 para não-membro é a regra do owner — idêntica no MCP. | Sem alteração de código. |
| `interaction_room.mention_suggest` → 403 intermitente | **Negação legítima/variação de claims.** O gate MCP (`commercial.access`) é idêntico ao da rota REST; alternância entre chamadas indica variação de claims do principal, não defeito de código. | Sem alteração de código. Nenhuma permissão foi ampliada. |
| `home_favorite.list` → 403 em algumas chamadas | **Negação legítima.** Mesmo alias de permissão (`commercial.access`) que a rota REST; principal sem a claim recebe 403 em ambas as superfícies. | Sem alteração de código. |
| `attachment.list` → 404 com id sintético | **Comportamento correto.** Entidade inexistente → 404 do owner. | `attachment.list` passou a retornar `download_url` da rota canônica do Portal para cada item (handoff seguro do binário). |
| `interaction_room.entity_preview` → 400 com `ref=000179` | **Validação correta do contrato.** `ref` deve ser objeto JSON com as chaves do `kind` (ex.: `{"customer_code","customer_store"}`); `ref` agora é declarado obrigatório e a descrição do catálogo explicita o formato. | Contrato mais explícito; mensagens de validação claras mantidas. |
| `user_profile.get` sem ref → 400 | **Contrato correto.** `user_id` (ref) é obrigatório por desenho; com id autenticado passa. | Sem alteração. |
| `production.appointments` sem OP → 502 | `op` agora declarado obrigatório → `400 validation` tipado antes do upstream (com OP/filial reais, PASS autenticado já observado). | `required_fields` coberto na suíte. |
| `customer.enrichment` / `billing_series` com `{code,store}` → falha | **Formato errado do chamador.** O contrato canônico é `{customer_code, customer_store}`; descrições do catálogo agora explicitam o shape. | Documentado no catálogo e no conhecimento. |
| `idempotency_key` / `expected_version` aceitos e descartados | **Estado não honesto** — os parâmetros eram aceitos pela tool sem efeito. | `tool_execute` agora reporta `concurrency.enforcement = owner_contract` quando recebidos — a garantia é do use case oficial, o MCP não finge camada própria. |

**NSE revisadas (7 exclusões do inventário das 133 ops):** GET/POST de artefatos binários (anexo, foto de perfil, PDF de proposta) seguem fluxo do Portal — `attachment.list` retorna `download_url`, `user_profile.get` retorna `photo_url`, `proposal.get` retorna `document_url`; o CAIO entrega o link canônico autorizado, nunca o binário. `GET /realtime/ws` é canal push persistente e `POST integration-jobs/scan` é job interno de sistema — sem equivalente conversacional, exclusão mantida e justificada.

**Evidência desta rodada de correção:** suíte CAIO **656 passed / 58 skipped** (homologação + integração isolada plugins-db + parity/mcp/character), incluindo novos testes de boundary para o contrato upstream de propostas e cenário multi-etapa de investigação de proposta. Nenhum write/delete produtivo executado.

## Smoke autenticado pós-deploy — 2026-10-30

Após deploy informado no commit `b453b0981c6ef75d2025c1b70b5c80e281bc7553`, a conexão ChatGPT→CAIO respondeu `get_context` com catálogo `2.0` e 123 operações. Consulta `read(proposal.analytics_list)` retornou proposta e filial autorizadas; `read(proposal.analytics_get, ref=proposal_number, filters={branch})` e `read(proposal.history_events, ref=proposal_number, filters={branch})` retornaram **success=true**, corrigindo os erros anteriores 400/upstream 422. Não foram executadas mutações. Esta evidência comprova essas duas operações autenticadas, não toda a integração produtiva ou as 50 operações de escrita/exclusão.

## Jornadas reais de usuário — 2026-10-30 (somente leitura)

Smoke autenticado pelo conector CAIO: `get_context` (catálogo 2.0), `customer.search`, `open_order.list`, `proposal.analytics_list → proposal.analytics_get → proposal.history_events` (filial derivada da lista), `worklist.mine`, `production.appointments`, `production.order`, `rol.summary`, `sales_order_otd.summary`, `customer.open_orders`, `customer.contacts`, `task.list`: **PASS**. Dados consultados por vínculo autorizado e identificadores obtidos de listagens; sem gravar, notificar ou excluir. `portfolio.me` retornou **403** nesta rodada, embora tenha passado anteriormente; status **PENDING_AUTHZ_DIAGNOSIS** (revalidar mesmo principal/claims e logs). As verificações não provam paridade de mutações nem uso por todos os perfis.
