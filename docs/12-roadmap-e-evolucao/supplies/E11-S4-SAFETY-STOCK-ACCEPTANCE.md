# E11.S4 — Help, correções residuais, testes e aceite funcional — Estoque de Segurança (WF-16)

> **Status:** `ACCEPT_WITH_RESIDUAL` proposto — aceite em código; `VISUAL_AUTHENTICATED = INCONCLUSIVE`, `FEDERATED_SMOKE = TEST_NOT_RUN`.
> **Owners:** `plugins/supplies` (MFE) e `supplies-api` (BFF), exclusivamente.
> **Revisão GPT de base:** `e8f8a932d9c73b53f69f85a858fd376a6adf898c` — ancestral do HEAD (verificado).

## Baseline

- BASE HEAD: `8ecce3f836d9963fa7485089200afdf8edd32f43`
- ORIGIN MAIN no corte do trabalho: `68f97f6d65e88479df3d68f706352504e0809c03` (main avança rápido — rebase antes do push)
- E11.S1/S2/S3 implementadas e revisadas (ACCEPT / ACCEPT_WITH_RESIDUAL).

## Residuais inventariados → correções

| Residual | Correção | Owner |
|---|---|---|
| `isSafetyStockItemDetail` não cruzava `product_code`/`branch` da resposta com o item solicitado | Novo `detailMatchesTarget(detail, target)` — comparação estrita de strings após trim, sem coerção numérica, sem match parcial, sem filial irmã; divergência → `SafetyStockContractError` em `getSafetyStockItemDetails` | `plugins/supplies` |
| Envelope upstream malformado virava `{}` com HTTP 200 no BFF | `_require_safety_stock_dict(data, operation, required_keys)` nos 5 métodos safety-stock de `SuppliesDelpiReads` — `data` não-dict ou dict sem chaves contratuais → `DelpiApiGatewayError(code="invalid_upstream_payload")` → 502 via `_gateway_error_response`. Empty legítimo (`items=[]`, `total=0`) e 404 legítimo preservados. Métodos não-safety-stock intactos | `supplies-api` |
| 2 warnings `react-hooks/set-state-in-effect` em S3 (modal) | Modal refatorado para estado chaveado pelo target (`LoadState.key` vs `targetKey`) — setState só em callbacks assíncronos | `plugins/supplies` |
| 2 warnings equivalentes em S2 (página) | Listagem refatorada para `ItemsLoadState` chaveado por `JSON.stringify([query, reloadKey])` — mesmo padrão do modal; removido `eslint-disable` órfão | `plugins/supplies` |
| Manual/FAQ sem seção dedicada a Estoque de segurança | Nova seção `safety-stock` + 5 FAQs + linhas «want»/«screens» atualizadas | `plugins/supplies` |

## Correção da identidade produto + filial (S4.A)

- Boundary: `plugins/supplies/src/features/safety-stock/api.ts` — `detailMatchesTarget()` + `getSafetyStockItemDetails()`.
- Códigos permanecem strings; zeros à esquerda significativos (`"00100708"` ≠ `"100708"`; filial `"1"` ≠ `"01"`).
- Payload inconsistente → erro de contrato, nunca render de produto diverso sob o cabeçalho solicitado.
- Testes: produto correto/errado × filial correta/errada, ambos errados, zeros à esquerda, sem match parcial (`query.test.ts`, describe `safety stock detail guards`).

## Envelope inválido no BFF (S4.B)

- Reproduzido e corrigido na fronteira `supplies-api` (`supplies_delpi_reads.py`); mecanismo canônico `DelpiApiGatewayError` → HTTP 502 `bad_gateway`.
- Chaves mínimas por endpoint: filters `product_groups/units/statuses`; summary `total_materials`; items `items/total/page`; details `product/stock`; suppliers `items/total`.
- `branch_catalog`/`all_scope` são injetados pelo service BFF — **não** exigidos no envelope upstream (corrigido após reprodução em teste).
- Fixture `_details_envelope` completada com `stock`/`purchase_coverage` (chaves reais do produtor — o fixture estava sub-especificado).
- Novos testes: `data=None` → 502, `data=[]` → 502, `data={}` → 502 para as 5 rotas; `success=false`; 404 legítimo de item preservado.

## Help / Manual / Tooltips (S4.C/D)

- Manual (`userManualContent.ts`): nova seção `safety-stock` (13 bullets: objetivo, filial, filtros, indicadores, 4 status, déficit por UM, ordenação, detalhe, cobertura, projeção, fornecedores, atualizar, vazio legítimo, erros/403) + linha dedicada em «Mapa das áreas» + «want» expandida + 5 FAQs (detalhe, deep-link, projeção/ruptura, lista vazia, falha parcial).
- FAQ não documenta exportação CSV nem features futuras; não instrui permission por filial; PT-BR user-facing.
- Tooltips `SP_HELP.safetyStock*`: cobertura completa já existente (filtros, indicadores, déficit, status, tabela, refresh, cobertura/projeção/fornecedores do detalhe); `safetyStockDetail` ligado ao título da seção de identificação do modal — zero chaves órfãs no domínio.
- Terminologia consistente com o Manual («Todas» = consolidado, filial = filtro, servidor calcula).

## Estados de interface (S4.E) — revisão em código

- Loading/empty/error por canal independente (listagem × resumo × filtros; detalhe × fornecedores).
- `«—»` para indisponível; nunca zero falso (hero `metric()`).
- 401/403/404/422/502 mapeados (`mapDetailError`, `ApiRequestError.status`).
- Payload inválido → erro de contrato, não empty.
- Estado chaveado: troca rápida de item/filial nunca exibe dados do recorte anterior (modal e lista).
- Retry por canal preserva filtros; URL inválida recupera defaults; F5/deep-link cobertos por testes.

## Acessibilidade / responsividade (S4.F)

- Modal do kit (`SuppliesModal`): abertura via linha/botão com `aria-label` por produto, Escape/fechar, foco do kit, scroll interno.
- Status com texto + cor (badge); labels de filtro; hint contextual `SuppliesSectionHintLabel`.
- `VISUAL_AUTHENTICATED = INCONCLUSIVE` — sem browser autenticado federado; teclado/contraste/temas não verificados em runtime.

## Testes e regressões

| Suíte | Resultado |
|---|---|
| `plugins/supplies` vitest | **430 pass** (45 arquivos) — incl. novos testes de identidade e manual |
| `supplies-api` pytest | **505 pass / 21 skip** — incl. 3 novos testes de envelope malformado × 5 rotas |
| `tsc -b` (supplies) | PASS (exit 0) |
| `vite build` (supplies) | PASS (chunk-size warning pré-existente) |
| eslint `plugins/supplies/src` | **baseline 10 erros / warnings 24→22**; `src/features/safety-stock/` = **0 problemas** (delta −2; erros restantes são preexistentes fora da feature) |

## Contratos e segurança (S4.J)

- 5 rotas BFF read-only revalidadas; `supplies.access`/`can_use_operations` Core-first intacto.
- `branch=all|01|02` filtro; detalhe exige filial concreta; nenhuma `supplies.unit.*` criada.
- Service token somente backend; zero acesso MFE→api-delpi; zero escrita ERP; zero POST/PUT; zero N+1.
- `BranchAccessGate`, Core RBAC e manifest intocados; trusted-BFF (caller+token efetivos) inalterado.
- Métodos do gateway fora de safety-stock inalterados — sem impacto em outros consumidores.

## Matriz AC

- AC-01/02 identidade validada + testes negativos: **PASS**
- AC-03/04/05 envelope/empty/HTTP: **PASS** (502 malformed; `items=[]`/`total=0` empty; 404 passthrough)
- AC-06 estados parciais: **PASS** (canais independentes + keyed state)
- AC-07/08/09/10 Manual/FAQ/tooltips sem promessa futura: **PASS**
- AC-11/12 filial filtro + Core-first: **PASS**
- AC-13/14 cinco rotas, sem N+1: **PASS**
- AC-15/16 a11y/responsividade/temas: **INCONCLUSIVE** (sem runtime autenticado)
- AC-17/18/19 TS/build/regressões: **PASS**
- AC-20 lint baseline/delta: **PASS com baseline** (10 erros preexistentes; safety-stock limpa)
- AC-21 docs sincronizadas: **PASS**
- AC-22 zero escrita ERP: **PASS**
- AC-24 nenhum deploy: **PASS**
- AC-25 readiness E11.S5: fundamentada — resta smoke federado autenticado

## Residuais remanescentes

- `VISUAL_AUTHENTICATED = INCONCLUSIVE`, `FEDERATED_SMOKE = TEST_NOT_RUN` — GATE-FEATURE E11 não pode ser declarado PASS sem runtime autenticado.
- `peer_branch_stock` continua não exposto (TO_INVENTORY — decisão de escopo).
- 10 erros de lint preexistentes fora do escopo E11 (não refactorados por regra de escopo).
- Deploy: **não realizado** (task proíbe).

## Veredito

`ACCEPT_WITH_RESIDUAL` — correções comprovadas aplicadas nos owners corretos, suítes verdes, Help sincronizado; pendente apenas evidência visual/runtime autenticada para o gate final (E11.S5).
