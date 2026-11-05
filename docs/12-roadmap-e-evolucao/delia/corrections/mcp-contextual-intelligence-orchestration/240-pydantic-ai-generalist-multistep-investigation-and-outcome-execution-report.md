# 240 — DÉLIA · Investigação generalista multi-step — Execution Report

**TASK_ID:** `DELIA-C3-PYDANTIC-AI-GENERALIST-MULTISTEP-INVESTIGATION-AND-OUTCOME-01`  
**DATE:** 2026-11-04  
**STATUS:** EXECUTED — validação local; PRODUCTION_DEPLOY NOT_AUTHORIZED  
**BASE_HEAD:** `945036c6a1db9c39dc33c866f13abd147e117c31`  
**PREDECESSORS:** docs 237–239  

## Authorities / reanchor

Reancorado em `main`. Runtime continua `PydanticAiInvestigationOrchestrator` (pydantic-ai 2.50.0) com gates da Application. Doc 239 permanece a biblioteca nativa: structured output e tool search seguem TARGET / TO_INVENTORY e não foram adotados. Rollback `DELIA_ORCHESTRATION_ENGINE=delia` e `_governed_owner_path` permanecem. Nenhum segundo planner, nenhum seletor por produto ou por formato de pergunta.

`EXECUTION_DRIFT=NONE`.

## EXISTING_EQUIVALENT / REUSE_DECISION

| Concern | Equivalent | Decision |
|---|---|---|
| Tool loop | Agent + FunctionToolset dinâmico | REUSE |
| Identidade de estrutura | `_authoritative_structure_root` (`data.root.code`) | REUSE |
| Próximo identificador | `uncovered_user_identifiers` + `focus_arguments_on_next_identifier` | EXTEND |
| Cliente HTTP do modelo | `investigation_model_factory` por turno | EXTEND |
| Estouro de tool calls | `UsageLimitExceeded` finaliza o que já foi coletado | EXTEND |
| Texto vazio do owner | não conta como evidência de negócio | EXTEND |
| Catálogo live | `_project_semantic_tool_catalog` | EXTEND (loga `failures`) |

## Causa observada

1. **E03 esclarecia cedo.** A Application aceitava a pergunta de esclarecimento mesmo com identificadores ainda sem raiz. Agora `request_user_clarification` devolve `CONTINUE_REQUIRED` enquanto houver identificador descoberto.
2. **A mesma query era repetida.** Com vários literais, ou com um literal já coberto, a descoberta do DAVI recebia de novo o primeiro código. O foco mantém o texto do usuário e troca somente o literal já coberto pelo próximo literal que o usuário já escreveu.
3. **Resultado vazio virava evidência.** "Nenhum resultado encontrado." entrava no conjunto de negócio e o resume reapresentava os mesmos argumentos. Esse texto deixou de contar como evidência de negócio.
4. **Cliente OpenAI compartilhado.** `run_sync` reutilizava o lock de outro event loop. Cada turno constrói um cliente novo.
5. **`UsageLimitExceeded` apagava o turno.** O limite agora finaliza as observações já coletadas e registra `tool_calls_limit_reached`.
6. **E05 sob carga perdeu o DAVI.** Três timeouts de admissão esgotaram o prazo; o catálogo projetou 8 capabilities, só Transformômetro e TV Dashboard. O modelo não tinha a tool de estrutura. Com o catálogo completo (10, `failures=-`), o mesmo pedido fechou a raiz `90260148`.

Código de produto sozinho continua sem casar a descoberta (`CAPABILITY_NOT_MATCHED`). O foco não reduz a frase a um código nu.

## LIVE_MATRIX (docker-compose.dev, modelo local qwen3:4b)

Identidade de estrutura é `data.root.code`, não o prefixo renderizado dos componentes.

| Caso | HTTP | Grounding | Evidência |
|---|---|---|---|
| E01 SIPOC | 200 ~29464ms | conversacional `explanation`; sem tool de owner | honesto |
| E02 estrutura 90260147 | 200 ~22788ms | GROUNDED | raiz `90260147`; `get_product_structure`; correlation `4ba91f83` |
| E03 compare | 200 ~43307ms | GROUNDED | raízes `90260147` e depois `90260148`; collected=2; correlation `f3daf363` |
| E04 estrutura + guia | 200 ~48901ms | NON_GROUNDED | execute com erro, resume do mesmo erro, `usage_limit`; correlation `ea23c62e` |
| E05 isolado | 200 35602ms | GROUNDED OBSERVATION | raiz `90260148`; in=2376 out=60; correlation `445b3a40` |
| E05 sob carga | 200 ~181656ms | NON_GROUNDED | catálogo sem `api-delpi`; correlation `5b5d468c` |
| E06 cross-owner | 200 34430ms | GROUNDED parcial | conhecimento real; `90260147` ficou descoberto; `tool_calls_limit_reached` |
| E07a ambíguo | 200 25018ms | NON_GROUNDED | não formulou esclarecimento; `owner_path_unbound` |
| E07b continuação | 200 25057ms | GROUNDED | raiz `90260147` depois do código no turno seguinte |
| E08 exclusão | 200 6484ms | NON_GROUNDED | nenhuma tool; nenhuma escrita |
| E09 NDJSON | 200 11498ms | stream | 10 linhas; terminal `turn_result`; a leitura fechou raiz `90260147` |
| E10 três alvos | 200 32788ms | NON_GROUNDED | os três literais permaneceram descobertos |

`FALSE_GROUNDED=0` para identidade de produto. E06 está fundamentado num trecho real de conhecimento e não numa estrutura de produto inventada; a obrigação do produto ficou aberta.

## Regressão

`delia-api` `pytest tests/ --ignore=tests/live` GREEN antes do log de `failures` do catálogo. `test_focus_query_targets_next_uncovered_identifier` e `test_usage_limit_finalizes_collected_evidence` GREEN depois do redirecionamento de identificador coberto.

## Veredito

`ACCEPT_WITH_RESIDUAL`. E02, E03 e E05 isolado provam leitura real de owner escolhida pelo modelo, com duas raízes distintas no compare. E04, E06 completo, E07 esclarecimento e E10 não fecharam o resultado de negócio. `FUNCTIONAL_ACCEPTANCE` da matriz multi-step completa = NO. `PRODUCTION_DEPLOY=NOT_AUTHORIZED`.
