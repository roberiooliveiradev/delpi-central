# 241 — DÉLIA · Confiabilidade do runtime investigativo e conclusão de outcome

**TASK_ID:** `DELIA-C3-PYDANTIC-AI-INVESTIGATION-RUNTIME-RELIABILITY-AND-OUTCOME-COMPLETION-01`  
**BASE_HEAD:** `82999eed900d1d74706275924b38a65b8cd8b09e`  
**SDK:** pydantic-ai `2.50.0`  
**MODEL:** `qwen3:4b-instruct-2507-q4_K_M` via `openai_compatible` (`MODEL_CONFIG_HASH=d382ec2d6fdc7d7d`)  
**PRODUCTION_DEPLOY:** `NOT_AUTHORIZED`  
**PHASE_ADVANCE:** `NONE`

O cabeçalho histórico do Documento 16 permanece com decisões de outubro/2026. Esta execução não avança fase nem reescreve essa authority. O ledger é o registro factual desta task.

## 1. Causas comprovadas e correção

| Frente | Causa observada | Correção no owner existente |
|---|---|---|
| Catálogo sob carga (doc 240) | Três timeouts de admissão eram logados como `budget_exhausted` e a listagem que falhava sumia do catálogo sem dizer que o owner não enumerou | Retry único de falha transitória de listagem; timeout de admissão não é repetido; falhas ficam em `_LAST_CATALOG_FAILURES` e no log `failures=`; sem evidência de negócio o terminal é `SOURCE_UNAVAILABLE` / `catalog_owner_unavailable` |
| Repetição | Resume não checkpointa execute com erro; a mesma assinatura voltava a gastar owner e orçamento | Fingerprint `capability_id` + argumentos canônicos em `InvestigationDeps.non_progress_calls`; repetição idêntica não reinvoca o owner |
| Esclarecimento após READ | Pergunta do modelo substituía evidência já coletada | `request_user_clarification` é rejeitada quando já existe evidência de negócio |
| Identificador sem raiz | Conhecimento com `SUCCESS` virava `GROUNDED` mesmo com o identificador do usuário sem `data.root.code` | Finalize devolve `investigation_partial_coverage`, conteúdo preservado, `NON_GROUNDED` |
| Ferramentas chamadas sem evidência | `NOT_APPLICABLE` + `OWNER_PATH_UNBOUND` narrava “não há capacidade” depois de consultas reais | `investigation_no_business_evidence` (e códigos de cobertura incompleta) usam a frase de evidência insuficiente e nomeiam `uncovered_identifier` |
| Cliente HTTP | `AsyncOpenAI` por turno | Fechado no `finally` quando `model_factory` existe; sem reuso de lock entre loops |

Não houve planner, registry, seletor por produto nem inclusão permanente de DAVI. O catálogo continua a projeção live autorizada. `UsageLimits` permanece `request_limit=12` e `tool_calls_limit=8`. `retries=1`.

`output_type` e tool search não foram adotados: continuam `TARGET` / `TO_INVENTORY` no Documento 239. Comparação com `qwen3:8b` (presente no Ollama local) não foi executada; o modelo de runtime não foi trocado.

## 2. Matriz local neste código

Stack: `docker-compose.dev.yml` + `docker-compose.minimal.yml`, bind-mount, sem `up-prod-sequential.sh`. Catálogo em todos os turnos medidos: `catalog_len=10`, `api-delpi:2,transformometro-api:4,tv-dashboard-api:4`, `failures=-`.

| Caso | HTTP | ms | Grounding | Leitura owner | Resultado |
|---|---|---|---|---|---|
| E01 | 200 | 17941 | NON_GROUNDED | nenhuma | Explicação de SIPOC, sem dado operacional inventado como fato |
| E02 | 200 | 33774 | GROUNDED | discover+execute `get_product_structure` raiz `90260147` | Observação preservada; limite de tools após leituras extras de contexto |
| E03 | 200 | 39027 | GROUNDED | discover `90260147` e `90260148`; execute só `90260147` | Duas raízes observadas; `composed=False`; sem veredito comparativo |
| E04 | 200 | 30233 | GROUNDED | discover→execute raiz `90260147` | Estrutura obtida; o guia não entrou como obrigação declarada nem como lacuna |
| E05 isolado | 200 | 30816 | GROUNDED | discover+execute raiz `90260148` | Catálogo 10 |
| E05 após E04 | 200 | 42322 | GROUNDED | discover+execute raiz `90260148` | Catálogo 10 sob a carga sequencial medida; o timeout de admissão do doc 240 não se repetiu |
| E06 | 200 | 26258 | NON_GROUNDED | conhecimento; raiz da estrutura ausente | `uncovered_identifier:90260147`; conteúdo do guia parcial preservado |
| E07a | 200 | 34191 | NON_GROUNDED | sem raiz | Esclarecimento: pede o produto |
| E07b | 200 | 39453 | GROUNDED | execute raiz `90260147` | Continuação com o código no turno seguinte e contexto do esclarecimento |
| E08 | 200 | 4640 | NON_GROUNDED | nenhuma escrita | `owner_path_unbound`; tool_calls=0 |
| E09 | 200 | 35146 | NDJSON | execute raiz `90260147` na releitura | 11 linhas, terminal `turn_result`. A primeira tentativa da matriz foi HTTP 401 por token expirado, não por contrato |
| E10 | 200 | 39349 | NON_GROUNDED | `search_products` e contexto; nenhuma raiz | `investigation_no_business_evidence`; identificadores `90260147`, `90260148`, `50220013` explícitos; `tool_calls_limit_reached` |

`FALSE_GROUNDED=0` para identidade de produto nesta matriz. Tokens do provider ficaram `partial` na maior parte dos turnos (`NOT_MEASURED` como total quando `total` veio nulo).

## 3. Aceite

| Critério | Estado |
|---|---|
| AC01 catálogo | PASS na carga medida: 10 capabilities, falha de owner não é ausência silenciosa no código |
| AC02 recuperação | PASS para repetição idêntica; E04 não repetiu o erro de execute do doc 240 |
| AC03 limites | PASS quando há observação: conteúdo fica e a limitação é explícita |
| AC04 E02 | PASS |
| AC05 E03 | PARCIAL: duas raízes, um execute de estrutura, sem composição verificada |
| AC06 E04 | PARCIAL: estrutura real; guia não coberto e não declarado como pendente |
| AC07 E05 | PASS isolado e na sequência medida; o cenário de três timeouts de admissão não foi reinduzido ao vivo |
| AC08 E06 | PARCIAL: lacuna honesta; investigação cross-owner não fechou |
| AC09 E07 | PASS: pergunta e depois leitura da raiz informada |
| AC10 E08 | PASS |
| AC11 E09 | PASS na releitura com token válido |
| AC12 E10 | PARCIAL: três identificadores nomeados como descobertos; três leituras de estrutura não ocorreram |
| AC13 generalização | PASS: nenhuma trilha por pergunta, owner ou código de produto |
| AC14 regressão | `delia-api` pytest `tests/ --ignore=tests/live` exit 0 no diff final |
| AC15 arquitetura | PASS: Pydantic AI segue o único runtime semântico |

`FUNCTIONAL_ACCEPTANCE_CANDIDATE=NO` para a matriz multi-etapas completa. Veredito da task: `ACCEPT_WITH_RESIDUAL`.
