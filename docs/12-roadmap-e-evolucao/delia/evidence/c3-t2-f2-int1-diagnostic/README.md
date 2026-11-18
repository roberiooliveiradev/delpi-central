# C3/T2 — F2 INT-1 Investigation Diagnostic (READ_ONLY)

**TASK:** `DELIA-C3-T2-F2-INVESTIGATION-CONTINUITY-PAGINATION-CONVERGENCE-DIAGNOSTIC-01`
**BASE_HEAD:** `1b2d56f740` · **MODE:** DIAGNOSTIC / READ_ONLY / NO_DEPLOY
**Escopo:** mapear mecanismos vigentes de INT-1 (continuidade, paginação,
progresso/no-progress, budget, capability selection, feedback de Suficiência)
e priorizar o próximo bounded fix. Zero alteração de runtime.

## RQ ledger — status + evidência file:line

| RQ | Status | Evidência |
|---|---|---|
| RQ-1 fluxo INT-1 | PROVEN | `delia-api/app/infrastructure/orchestration/pydantic_ai_investigation.py`: `InvestigationDeps` :385-430 (state/authority closed-over), tool invoke :1884-2160, output validator :2900-3070, run loop :3263+ (`UsageLimits(request=12, tool_calls=8)` config `delia-api/config/pydantic_ai.runtime.delpi.json:17-18`); handoff two-agent :3095-3120 (Application-owned, subtractive). Determinístico: acceptor/gates/budget/fingerprint. Modelo: seleção de capability, declaração de goal, continuação, resposta. |
| RQ-2 paginação | PARCIAL | Envelope `generic_evidence_renderer.py:1304-1365` (`items`+`page/page_size/has_more/total`, nested `pagination{}`, `truncated` declarado → `has_more=True`); `next_page=page+1` só com `page` int (`pydantic_ai_investigation.py:1118`); `continuation_note` :1130-1147; `aggregate_paginated_pages` :1392-1560 (complete exige walk assinada; casos t01–t22 `tests/test_r45_pagination_integrity_rework.py`); cursor NÃO suportado (contrato page/offset apenas); página vazia intermediária tolerada pelo agregador; conflito de total coberto (t12). |
| RQ-3 progresso | PROVEN | `classify_investigation_progress` `semantic_capability_support.py:2092-2142` (NEW/RELATED/NONE/DISCOVERY); `uncovered_user_identifiers` `pydantic_ai_investigation.py:1152-1175`; `_authoritative_structure_root` `semantic_capability_support.py:2155+`; obrigações via `_evaluate_material_obligations` (~3051). |
| RQ-4 no-progress | PROVEN | Fingerprint cap+args `non_progress_calls` short-circuit :2020-2032 (`repeated_equivalent_call`; `repeated_equivalent_failure` só sem `authoritative_root_code`); body fingerprint `observed_content_fingerprints` :2083-2096 (`repeated_observation_no_progress`); continuidade one-shot `continuity_model_retry_allowed` :500-525 (nega AUTHZ_DENIED e schema-rejected); `observation_content_fingerprint` `semantic_capability_support.py:2144-2152`. |
| RQ-5 budget | PROVEN | `TurnDeadline` `interaction/turn_budget.py:31-80` (monotonic, `check()`, `stage_timeout` bounded, `TurnBudgetExhausted`); `UsageLimits(12/8)` :3270; `_TurnUsageCountingModel` :433-487 (uso real incl. exceções); `deadline.check` por tool (:1884, :2312, :2705, :2756); `PROCESSING_TIMEOUT` ≤2s :3413. |
| RQ-6 capability selection | PROVEN | catálogo live prefetch :2157+; AuthZ re-check por invoke via `gates._governed_semantic_tool_invoke` :2045; `discovery_metadata_observation` nunca progresso (:2108 classificador); binding de plano em `deps.investigation_plan`. |
| RQ-7 feedback sufficiency | PROVEN | gates ModelRetry nomeiam obrigações abertas :3030-3068 (`unmet` via `_evaluate_material_obligations` — mesmo helper do acceptor); `coverage_unknown` sinalizado por observação :1095-1100; veredito permanece determinístico no acceptor. |
| RQ-8 segurança | PROVEN | AUTHZ_DENIED nunca gera retry (:490-498, gate continuidade); testes negativos `test_c3_t2_evidence_closure_negatives.py`, `test_int1_authz_denial_communication.py`, `test_int1_partial_authorization_finalize.py`, `test_int1_provider_request_boundary_integrity.py`; logs só metadados tipados :3340-3380. |
| RQ-9 reprodução | PARCIAL | 50 testes paginação/progresso PASS (container local, exit 0); controle 109 (40+40+29, group-split) REMEDIATED_PROVEN no ledger :2163; holdouts A/R5/E/R6mt = corpus existente `scripts/int1_openrouter_qwen14b_instrumented_eval.py` (INT2_SCENARIOS :212-462), não reexecutados (modelo real exige credencial/custo — fora de READ_ONLY). |
| RQ-10 candidatos | PROVEN | matriz abaixo. |

## Matriz de problemas candidatos (RQ-10)

| Problema | Reproduzido? | Primeira divergência | Owner | Equivalente existente | Impacto | Próxima decisão |
|---|---|---|---|---|---|---|
| **P1** retry idêntico após falha TRANSIENTE é bloqueado como `repeated_equivalent_failure` sem alcançar owner; listing tem 1 retry transiente, invoke não | PROVEN (caminho de código; teste existente cobre só classe terminal `arguments_schema_rejected`, `test_pydantic_ai_real_owner_tool_loop_rework.py:776`) | `non_progress_calls` short-circuit `pydantic_ai_investigation.py:2020-2032` — projection cacheada para qualquer tentativa (incl. transiente); sem consulta a classificador transiente | INT-1/Application (seam invoke) | `_listing_failure_is_transient` `semantic_capability_support.py:5838-5854` + bounded retry `governed_capability_orchestrator.py:1601-1619` → EXTEND | médio: perde recuperação legítima única em falha transiente dentro do turno | **candidato priorizado** |
| **P2** oráculo de completude multipage `aggregate_paginated_pages` (22 asserts em testes) sem consumidores em `app/` — finalize não consulta merge íntegro | PROVEN (zero chamadas fora do módulo; só returns próprios) | `_finalize_agent_collected_attempts` não agrega páginas por capability/args | INT-1 finalize + Evidence | oráculo existente → REUSE (wire, não reconstruir) | médio-alto: COMPLETE/PARTIAL/INCONCLUSIVE multipage pode errar em página faltante/dup-id | candidato maior — exige decisão de contrato de veredito |
| **P3** convergência do loop do modelo em continuação multipage não provada sistematicamente (só controle 109) | TO_INVENTORY (lacuna de eval, não defeito de código) | holdouts sem checagem de aderência de continuação | avaliação/Coordenação | harness + corpus existentes → REUSE | evidência de convergência ausente | bounded live-eval proposta |
| **P4** paginação por cursor não suportada (next_page=page+1) | NOT_PROVEN — nenhum owner com cursor observado | contrato de envelope | contratos de owner | N/A | adormecido | monitorar só se provider exigir |
| **P5** `insufficiency_retry_used` compartilhado por 5 gates de correção — primeiro disparo consome o único slot | TO_INVENTORY (hipótese; sem trace de perda real) | cluster :2900-3070 | INT-1 | flags one-shot existentes → EXTEND se reproduzido | baixo-médio, especulativo | aguardar ocorrência real |

## Candidato bounded prioritizado — P1

- **Escopo:** seam invoke; classificar `attempt.error_code` anterior com o
  mesmo critério transiente de listing (`timeout|unavailable|transport|
  connection` = transiente; `denied|forbidden|unauthorized|authz` +
  schema/contract = terminal) e permitir UMA reinvocação idêntica só
  quando a falha anterior for transiente, mantendo short-circuit total
  para terminal e para repetição após sucesso.
- **Critério de aceite:** retry idêntico após `mcp_transport_error`/
  timeout reinvoca owner UMA vez; segunda repetição idêntica volta a
  short-circuit; falha terminal nunca reinvoca; AUTHZ intocado;
  no-progress counters preservados.
- **Testes:** positive (transiente → 1 reinvoke), negative terminal
  (schema_rejected → 0 reinvoke, igual ao teste :776), sibling (retry
  com args diferentes segue invocando), segurança (AUTHZ_DENIED).
- **REUSE_DECISION:** EXTEND (classificador + padrão bounded já existem).

## Baselines preservados

`comprehension-v4` default intacto; F1 byte-idêntico; `R2-CONTINUITY-MULTIPAGE-GROUP-SPLIT` REMEDIATED_PROVEN (109); `R2-CONTINUITY-PAGINATION` PARTIAL_REMEDIATED (envelope fix live `has_more:true`; residual = convergência do loop); 50 testes paginação/progresso PASS no HEAD.

**LIMITES:** sem reexecução de eval real (credencial/custo); P3/P5 não reproduzidos; sem alteração de runtime, stash ou WIP.
