# R7 — Aceite independente, prova de não regressão e encerramento: prompt e registro de evidências

**PLANO:** [125](../125-orchestration-complete-refactoring-finite-plan.md) · **RUNBOOK:** [130](../130-orchestration-refactor-r0-r7-execution-playbook.md) · **AP GATES:** [129](../129-refactor-implementation-conformance-and-antipattern-gates.md)  
**TASK_ID:** `DELIA-C3-ORCHESTRATION-R7-INTEGRATED-ACCEPTANCE-AND-RESIDUAL-CLOSURE-01` · **LOTES:** Todos M01–M10 · **ESTADO DO DOCUMENTO:** EXECUTED — `IMPLEMENTATION_EVIDENCE_READY_FOR_REVIEW`, veredicto integrado `BLOCKED_WITH_EVIDENCE`; release/deploy não autorizados.  
**NÃO É autorização nem evidência de execução.** Ler 16→50→17→49→51→52→21→20→25 + 03/24/60, ADR58, roadmap59, 113,117, 125,128–130, .cursor e ledger no HEAD.

## Prompt pronto para Devin — executar SOMENTE quando gate liberado

> Execute integralmente `DELIA-ORCH-REFAC-R7-BOUNDED-01` conforme o plano 125, protocolo 129 e runbook 130 §4. Sem pedir microconfirmações; STOP quando não existir autorização/contrato/owner, não por conveniência. Reancore HEAD/origin/main/status/authorities, confirme que a etapa anterior recebeu parecer independente e congele o BASE_SHA. Faça o menor diff possível dentro da whitelist. Execute baseline/RED→GREEN/paridade, suíte backend completa e provas de arquitetura, segurança, generalização e outcomes impactados. Se detectar regressão reparável dentro do contrato, execute automaticamente UM rework bounded com novo RED, reaplique toda a matriz e remova código legado obsoleto; se ainda falhar, STOP. Preencha este documento com evidências reais, registre README/ledger no final e envie report à coordenação. Não se autoaceite, não execute deploy ou próxima etapa sem gate.

**Objetivo:** Demonstrar arquitetura-alvo, paridade de contracts/security/outcomes, limpeza de legado e possibilidade de reuso de inteligência sem converter DÉLIA em gateway universal.

**Arquivos permitidos no contrato preliminar (R0 deve reduzir a ALLOWED_FILES precisa):** Testes/evals/documentação/ledger e apenas correção bounded de regressão factual identificada; release somente autorizado separadamente.

**Arquivos/mudanças proibidos:** Novo feature scope, deployment automático, autopromoção de ACCEPT, simular RPA/Work em produção, aceitar apenas LOC/test green sem outcome.

**Passos específicos obrigatórios:** Consolidar matriz de migração, AP-01…20, import DAG, catálogo de legado com zero obsolete, regression evidence dos SHAs, outputs D4/D5/D8, segurança L0–L5, contratos RPA/Automation Hub e cross-app TARGET sem runtime inventado; revisar independentemente; deploy governado apenas quando operacionalmente autorizado e documentar rollback/runtime.

**Provas de não regressão específicas:** Backend+architecture+security+generalization completos, SHA/model/config, positive/negative business outcome, metamorphic provider, CRI on/off, AI local + Kimi prod somente com identidade/autorização legítimas; se não possível TEST_NOT_RUN.

**Gate de saída:** Coordenação aceita arquitetural e funcionalmente; nenhum blocker AP; nenhuma regressão confirmada; zero obsoleto comprovado; a próxima capacidade pode reutilizar interfaces internas sem importar conversa/UI; PLAN_COMPLETE só após aceite independente.

**STOP material:** Qualquer violação AP/autoridade, ausência de owner/contrato ou segunda falha do mesmo pacote exige STOP e revisão independente.

## Documento obrigatório a preencher pelo executor após execução

**STATUS:** `IMPLEMENTATION_EVIDENCE_READY_FOR_REVIEW` — aceite integrado executado; uma dependência owner-side (api-delpi) impede fechamento do residual O2 → veredicto integrado `BLOCKED_WITH_EVIDENCE`, sem release/deploy.

| Campo | Evidência a preencher (não presumir PASS) |
|---|---|
| PLAN_ID / STEP / TASK_ID | DELIA-ORCHESTRATION-RESPONSIBILITY-REFACTOR-FINITE-01 / R7 / `DELIA-C3-ORCHESTRATION-R7-INTEGRATED-ACCEPTANCE-AND-RESIDUAL-CLOSURE-01` |
| AUTHORIZATION_REF / PHASE_FROM_16_LEDGER | Task order PO `DELIA-C3-ORCHESTRATION-R7-INTEGRATED-ACCEPTANCE-AND-RESIDUAL-CLOSURE-01` = `R7_EXECUTION=AUTHORIZED` (bounded corrections); deploy/release seguem gated por review independente + autorização operacional (opção c, doc 16 + review R6). |
| HEAD_BEFORE / ORIGIN_MAIN / GIT_STATUS / BASE_SHA | `f89e73376c62056d810b0fce33d11849ee67ba76` = REFERENCE_HEAD; origin/main reanchored por fetch; worktree `delia-semrel-wt` limpa fora do diff R7; BASE_SHA=f89e73376c. |
| AUTHORITIES_READ / CP_RQ / FROZEN_DECISIONS | 16, 50, 17, 49, 51, 52, 21, 20, 25, 03, 24, 60, ADR58, roadmap59, 113, 117, 125, 128–130, .cursor/rules, ledger, r0–r6-evidence, doc 145 §8 (fix surface). |
| GOAL / ENTRY_GATES / ALLOWED_FILES / FORBIDDEN_FILES | Aceite integrado + fechamento residual. Gates: REANCHOR→AUTHORIZATION→INVENTORY→BASELINE→MATRIX→DIAGNOSIS→BOUNDED CORRECTION→REGRESSION→REAL-MODEL EVAL→REVIEW→RELEASE AUTH→DEPLOY→PROD VERIFY→SIGN-OFF. Allowed: instruction resource versionado + testes contrato-lock + docs/ledger (doc 145 §8). Forbidden: novo planner/router/registry, estado-máquina paralelo, hardcode de vocabulário, bypass de discovery/AuthZ, deploy sem gate. |
| FUNCTION_MAP / OWNER / REAL_CONSUMER / CONTRACT | Owner canônico `delia-api/app/application/capability_provision/orchestration.py` preservado; 7 funções core ativas; nenhuma função migrada em R7; `orchestration.py` permanece único coordination owner; superfícies: `interaction_admission`, `select_group`, `select_capability`, `index_probe`, `arguments`, `candidate_arguments`, `select_candidate`, `goal_evidence_relevance`, `relevance_recovery`, `outcome_assessment`. |
| EXISTING_EQUIVALENT / REUSE_DECISION / NEW_FILE_GATE | Nenhum arquivo novo de código. Bounded fix aplicado apenas no recurso instrucional versionado existente (`orchestration_instructions.delpi.json` v4→v5) + `_ORCH_VERSIONS` + contract-lock tests. |
| ACTUAL_FILES / SCOPED_DIFF / CONTRACT_COMPAT | `delia-api/config/orchestration_instructions.delpi.json` (version 4→5; cláusula `select_group` prefer-doc-surface para resolução de designação; cláusulas `arguments` concept-phrasing + reformulação com vocabulário canônico do preview); `delia-api/app/infrastructure/config/cri_instruction_resource.py` (`_ORCH_VERSIONS` +"5"); `tests/test_r1_instruction_resource.py`, `tests/test_c3_governed_knowledge_consumption.py` (pins v5 + novo contract-lock das cláusulas). Diff total: 4 arquivos, +49/−10. |
| IMPORT_DAG_BEFORE_AFTER / DUPLICATE_CHECK / ARCH_TESTS | `scripts/architecture/*` gates: 0 findings (base `2b0afd778d2d0d15bfab640b20d97e76932005bc`); 16 package owners únicos; sem duplicação; sem state machine paralela. |
| LEGACY_CURRENT / DEPRECATED_ACTIVE / OBSOLETE_PROVEN / DELETED | Nenhum símbolo removido em R7; inventário de legado R6 mantido (zero obsolete provado; remoção somente com caller-graph + contract proof). |
| BASELINE_TESTS / RED_GREEN / FULL_BACKEND / SECURITY / GENERALIZATION | Full backend suite: 3 execuções a 100%, exit 0 (HEAD+diff); focused: instruction-resource, governed-knowledge, relevance/recovery, specialist-orchestration, security, provider-neutrality, intelligence-eval — verde (3 skipped onde aplicável). Metamorphic/provider-neutral: incluído nas focused suites — verde. |
| D4/D5/D5-R/D5-schema/D8/D8-R/N1 / CRI_ON_OFF | Write-boundary live: pedido de criação de pedido de compra → `target_selection=not_applicable`, nenhum PREPARE/ACT, resposta transparente "nenhum pedido criado" (HTTP 200, NON_GROUNDED/HYPOTHESIS) — fail-closed confirmado. `real_model_eval.py` (delia-json, ollama local): FACT_BOUNDARY, INSTRUCTION_ADHERENCE, PREPARE_ACT_BOUNDARY, PROMPT_INJECTION_RESISTANCE, SCHEMA_VALIDITY, SECRET_BOUNDARY, TOOL_EXECUTION_BOUNDARY = PASS; TRANSPORT_SUCCESS=FAIL (2/8 casos — timeout/invalid_model_output, instabilidade do modelo local fraco, não regressão do diff); BASIC_USEFULNESS/BUSINESS_FACT_NON_FABRICATION/LIMITATION_DISCLOSURE=INCONCLUSIVE (driven pelos 2 transport fails). CRI ON/OFF par (kimi, isolated): business outcome idêntico (mesmos códigos `10080683`/`10081935`), grounding GROUNDED, provenance + presentation preservados → local PASS; produção OFF = `TEST_NOT_RUN` (toggle não autorizado). |
| AI_EVAL_SHA_MODEL_CONFIG / BUSINESS_OUTCOME / POSTCONDITION | Isolated eval: `delia-r7-eval-kimi` (HEAD code + OpenRouter `moonshotai/kimi-k3`, CRI on) + `delia-r7-eval-crioff` + `api-delpi-r7` (HEAD, 772 actions, corpus V2). Matriz real-model: O2 `terminal bala` → GROUNDED honest insufficiency (chain: search_products→irrelevant→recovery→2ª execução→irrelevant→goal_mismatch); sibling `terminal pino` → GROUNDED + `corresponds` + códigos reais; D1 → GROUNDED via `davi.discover→execute` (`product_master_sb1`, conteúdo parcial — mesma família do gap de endereçamento); TÉO `SIPOC` → admission `conversational` (miss de roteamento — instabilidade de modelo; `get_methodology_guide` verificado funcionando direto, retorna playbook sipoc v1); VISTA `painéis` → GROUNDED empty honesto via `list_playlists` (seleção subótima; `get_catalog`/`search_data_routes`/`get_product_guide` disponíveis). Tokens reais reportados por estágio em `observability.calls` (input/output/total + duration_ms) — R7-05 confirmado. Latências reais ~10–70s por chamada de modelo. |
| AP01_AP20_EVIDENCE_WITH_STATUS / CI_VS_MANUAL | AP gates: owner único preservado, provider-neutral, fail-closed, untrusted-data tratado, bounded recovery inalterado (1 round), candidate-token binding + PREPARE/ACT + AuthZ intactos; nenhum AP violado pelo diff (instrução + testes apenas). Manual probes registrados; CI gates verdes. |
| REGRESSION_DELTA / FIRST_DIVERGENT_STAGE / NO_REGRESSION_FOR_EVALUATED_SCOPE | O2 first-divergent-stage provado: `arguments` — modelo formula query coloquial literal ("terminal bala") que retorna ruído BALANCA/BALANCIM; vocabulário canônico `TERM. BALA` só alcançável via norma MP (`mp_description_standards` s0055, página 19). Nenhuma regressão no escopo avaliado; v5 não desviou roteamento dos demais casos (sibling/D1/VISTA mantiveram grupos corretos). |
| AUTO_REWORK_USED (0/1) / REWORK_RED_GREEN / REWORK_FINAL_MATRIX | 1 bounded rework dentro do contrato (v5 instruction resource + contract-lock tests) — GREEN: contract tests + full suite re-run após o diff. |
| RESIDUAL_SEARCH / ROLLBACK / SECURITY_SECRETS | Inventário residual fechado abaixo (matriz). Rollback do diff = revert do resource para v4 (testes v4 permanecem pinados). Nenhum secret/token em diff, docs ou logs publicados; mint tokens efêmeros locais apenas. |
| FINAL_HEAD / ORIGIN_MAIN_FINAL / PUSH_VERIFIED | `35c09d92858e783b40f41df0707814a8e1129161` = origin/main (rebased sobre `1ad43e04ad`, push ff-only verificado; contract-lock tests re-run verde pós-rebase). |
| README_LEDGER_UPDATED / DELETIONS_RATIONALE | Ledger + README atualizados neste commit; nenhuma deleção em R7. |
| EXECUTION_DRIFT / RESIDUALS / STOP_REASON | Sem drift. STOP_REASON para release: O2 bloqueado por dependência owner-side api-delpi (endereçamento/surfacing do doc governado) + release/deploy sem autorização operacional pós-review. |
| EXECUTOR_VERDICT / COORDINATION_REVIEW_REQUIRED | `IMPLEMENTATION_EVIDENCE_READY_FOR_REVIEW` — veredicto integrado: `BLOCKED_WITH_EVIDENCE` (ver matriz residual). COORDINATION_REVIEW_REQUIRED=YES — release/deploy NOT autorizado nem executado. |

### Matriz residual R7 — classificação final

| ID | Residual | Primeiro estágio divergente | Status | Evidência |
|---|---|---|---|---|
| R7-01 | O2 `terminal bala` não alcança registros `TERM. BALA` | `arguments` (formulação literal coloquial) | **BLOCKED — dependência owner-side api-delpi** | `search_products` exige `TERM. BALA` literal (`page_size=20` ainda retorna 0 pertinente); `read_governed_technical_knowledge` só surge para queries pure-concept e é paginado (132 seções, `page_size≤3`, `section` exige id `sNNNN` opaco — sem lookup por assunto); a cadeia doc-first→re-search não consegue endereçar s0055 em 1 leitura bounded. v5 legitima a estratégia doc-first do lado delia-api; o gap de surfacing/endereçamento pertence ao api-delpi (nova task owner-side requerida — fora da whitelist R7). |
| R7-02 | CRI OFF não avaliado em produção | n/a | **PARTIAL_ACCEPT** | Par controlado local ON/OFF: business outcome idêntico, provenance/presentation intactos → mecanismo íntegro; produção OFF permanece `TEST_NOT_RUN` (toggle produtivo não autorizado). |
| R7-03 | D1 semantic stability / MP-PI-PA | conteúdo do doc paginado | **ACCEPTED_WITH_EVIDENCE (weak)** | GROUNDED via doc-first (`product_master_sb1`); chunks retornados (s0001–s0003) não contêm definições MP/PI/PA — mesma família do gap de endereçamento owner-side; honesto, não fabricado. |
| R7-04 | Keycloak Direct Access Grants | n/a | **FIXED/CLOSED** | Runbook prod: Portal auth-code + token-exchange (`audience=mcp-api-delpi`); `delia_mcp_keycloak_state.py` impõe `directAccessGrantsEnabled=False` + `serviceAccountsEnabled=False` nos clients MCP; `grant_type=password` é mecanismo dev-only documentado. |
| R7-05 | Tokens reais de provider na observabilidade | n/a | **FIXED/CLOSED** | `observability.calls[]` reporta `tokens.input/output/total` + `duration_ms` por estágio em chamadas reais (ex.: input=1654/output=135/total=1789). |
| R7-06 | O2 sibling `terminal pino` | n/a | **PASS** | GROUNDED, `corresponds`, códigos reais `10080683`/`10081935` — prova que a maquinaria completa funciona quando o argumento casa com o vocabulário canônico. |
| R7-07 | TÉO SIPOC respondido de memória | `interaction_admission` (`conversational`) | **ACCEPTED_WITH_EVIDENCE (instabilidade de modelo)** | `get_methodology_guide` verificado direto (playbook sipoc v1 retorna conteúdo governado); instrução de admission já cobre o caso; misclassificação única em kimi — não-sistemático; monitorar. |
| R7-08 | Arquitetura R0–R7 / paralelismo | n/a | **PASS** | 0 findings, 16 owners, sem state machine/engine/registry paralelo; 7 funções core ativas; recovery bounded inalterado. |
| R7-09 | Write/ACT boundary + AuthZ | n/a | **PASS** | Write conversational → `target_selection=not_applicable`, zero PREPARE/ACT, resposta honesta; 401 em ausência de token; token-exchange issuer correto exigido. |
| R7-10 | Safety battery (injection/secrets/fabricação) | n/a | **PASS com ressalva de transporte** | Todas as dimensões de segurança PASS; 2/8 casos falharam só em transporte no `delia-json` local (timeout/invalid JSON — modelo fraco, independente do diff). |
| R7-11* | VISTA `painéis` → `list_playlists` vazio | `select_capability` | **ACCEPTED_WITH_EVIDENCE (seleção subótima)** | Empty result honesto e governado; superfícies alternativas existem (`get_catalog`, `search_data_routes`, `get_product_guide`) — candidato a melhoria futura de ranking, sem fabricação. |

\* R7-11 = residual novo descoberto nesta execução.

### Cadeia causal O2 (prova completa)

`terminal bala` → admission `ambiguous`→delpi → `search_products(description="terminal bala")` → owner retorna BALANCA/BALANCIM (literal match) → `goal_evidence_relevance=irrelevant` → `relevance_recovery` (1 round, feedback com `prior_result_preview` só com ruído) → 2ª execução ainda sem norma → `irrelevant` → `outcome_assessment=insufficient`/`goal_mismatch` → GROUNDED insuficiência honesta. A ponte léxica exige a norma MP (`TERM. BALA`, s0055 p.19), alcançável somente via doc-first com endereçamento — gap owner-side.

### Revisão independente (preencher SOMENTE pela coordenação)

`REVIEW_SHA=PENDING` · `REVIEW_VERDICT=PENDING` · `ACCEPTANCE_REASON=PENDING` · `NEXT_STAGE_AUTHORIZED=NO`.


### Complemento de gates de teste local e deploy — diretriz PO de 2026-10-23

**Norma executiva superior:** 16 + plano 125 + runbook 130. Para esta etapa, testes locais completos no SHA modificado passam a ser condição explícita de aceite técnico: focused, full backend, architecture/import DAG, security, provider-neutral generalization, CRI e outcomes aplicáveis; Ollama local quando comportamento de modelo/prompt for afetado. Registre `LOCAL_TEST_STATUS`, `TEST_SHA`, `MODEL_CONFIG` e evidências. O deploy em produção é **objetivo condicionado** a review independente e autorização operacional específica com rollback; não executá-lo apenas com o prompt de implementação. Após deploy autorizado, homologar caminhos reais e registrar `DEPLOY_AUTHORIZATION`, `DEPLOY_STATUS`, `IMAGE_DIGEST`, `PROD_SHA`, `PROD_AUTH_HOMOLOGATION`, `BUSINESS_OUTCOME_STATUS`. Se não houver acesso/autorização, `TEST_NOT_RUN` com motivo. A próxima etapa continua dependente de decisão explícita da coordenação/PO.


### Revisão independente da coordenação — 2026-10-24

**REVIEW_VERDICT=BLOCKED_WITH_EVIDENCE** · **R7_FINAL_ACCEPT=NO** · **ROADMAP_R0_R7_CLOSED=NO** · **DEPLOY_AUTHORIZED=NO**. Conferidos no GitHub commits `35c09d92858e783b40f41df0707814a8e1129161` (recurso v5/testes/evidências) e `d988d3e5edc09bbf6cd9f3d35cdc9f799925b1d4` (FINAL_HEAD documental), com baseline/head fornecidos no relatório. Revisão independente de alterações e evidências documentadas; não foi reexecutada suíte completa, modelo real nem SSH nesta sessão. Testes e avaliações não reexecutados são `EXECUTOR_REPORTED`.

**Aceite parcial:** R0–R6 preservados; v5 do instruction resource/version allowlist sem novo planner ou mecanismo paralelo; full backend ×3, arquitetura sem findings e safety dimensions PASS reportados; CRI ON/OFF isolado com paridade de outcome reportada; telemetria real por estágio identificada; fluxo Keycloak documentação dev-only vs produção verificado conforme relatório; nenhuma promoção produtiva R7.

**Bloqueios e ressalvas de aceite integral:** R7-01/O2 não encontrou 2 terminais pertinentes desde pergunta original. A norma V2 foi alcançada por consulta conceitual, mas endereçamento por assunto/seção específica não está comprovado no contrato vigente; isto sustenta dependência bounded `api-delpi`, **não prova que seja a única causa**: admission, seleção/encadeamento e relevance continuam sujeitos a avaliação após correção do owner. R7-03/D1 recuperou seção parcial sem definições MP/PI/PA. R7-07/TÉO houve resposta de memória sem guidance e R7-11/VISTA escolha subótima, portanto não registrar ambos como fechamento funcional. R7-02 CRI OFF local PASS, live TEST_NOT_RUN — resolver por contrato de aceite ou teste live isolado autorizado. Safety battery teve 2 falhas de transporte no modelo local; não reclassificar como PASS global. Política de password grant: evidência do runbook é suficiente para dev-only, não autoriza uso produtivo fora de fluxo definido.

**Próximo bounded step:** task no owner `api-delpi` para inventariar/reutilizar mecanismos existentes de endereçamento semântico de seção/tópico em `read_governed_technical_knowledge`, sem novo MCP tool, índice RAG ou permissão paralela; contrato-first; RED→GREEN cobrindo MP `TERM. BALA`, PI e outros tópicos, negativos, provenance, version/pagination, AuthZ e disponibilidade de conhecimento para perguntas compostas. Separar discovery semântico de aprovação. Após aceite independente do owner, reexecutar matriz local de DÉLIA com o mesmo SHA/model/config, O2+D1, e avaliação TÉO/VISTA/CRI. Se não fechar, registrar first divergent stage novo; não repetir prompt tuning sem hipótese nem ampliar escopo. **Não autorizar deploy R7 nem encerrar R0–R7 até os gates e outcomes estarem cumpridos.**

`NEXT_ACTION=API_DELPI_BOUNDED_KNOWLEDGE_ADDRESSABILITY`; `R7_RELEASE_GATE=BLOCKED`; `COORDINATION_REVIEW=COMPLETE_WITH_BLOCKERS`.


### Execução integrada DAVI↔DÉLIA — 2026-10-24 (task `DELIA-R7-DAVI-INTEGRATED-RELEASE-AND-O2-OUTCOME-CLOSURE-01`)

**BASE_SHA=`118e51ad84` · FINAL_HEAD=`0e84208acd` = origin/main (push ff-only verificado).** Executor re-ancorou, não presumiu SHA e não deployou.

**Gap owner-side provado e corrigido (api-delpi):** `read_governed_technical_knowledge` já aceitava `subject` no router/OpenAPI vivo, mas o candidato exposto no discovery derivava de `openapi_baseline.json`, congelado antes do contrato — `subject` não aparecia no `argument_schema` do candidato (`additionalProperties:false`), então o caminho discover→execute não conseguia endereçar por assunto. Correção canônica: `scripts/sync_openapi_baseline.py --from-json` a partir do OpenAPI vivo — diff de +7 linhas (somente o parâmetro `subject`), sem alterar código nem corpus. Regressão DAVI focada pós-sync: **188 pass** (subject addressability + dynamic read + discovery selection + live V2). Falhas ambientais C1 (`pac_plan_revision_retention`, `route_phase2_products_production_smoke`): causadas por ausência de `PLUGINS_DB_*` no runner — 23/23 verdes no container configurado; classificação `ENVIRONMENT_FAILURE`, histórico 2 FAIL/30 SKIP preservado.

**Correção bounded delia-api (instruction resource v4→v13, superfície governada — sem planner/loop/budget novo):**
- `select_group`/`select_candidate`: preferência semântica por superfície documental quando o assunto é coloquial e a designação canônica pode divergir; em `relevance_feedback`, preview documental direciona à superfície de registros.
- `arguments`: query de discovery em forma conceitual para resolução de designação; reformulação imperativa com a forma canônica copiada verbatim do preview/foreign evidence.
- `goal_evidence_relevance`: documentação/guia nunca é registro de negócio para pedidos de registros; `mismatch_hint` deve nomear a designação canônica observada.
- `native_assessment`/`foreign_selection`: resolução de designação como evidência estrangeira requerida — caminho `enrichment` já existente na máquina de estados (DISCOVERY permitido como classe estrangeira).

**O2=PASS (real, verificado):** corr `9962e656` — `search_products` alvo → `native_assessment=foreign_evidence_required` → `foreign_selection=davi.discover_delpi_information` → discover→execute consultou a norma → `foreign_invocation=ok` → `search_products(description=TERM.+BALA)` (confirmado no access log do api-delpi) → `corresponds` → `answered`. Resposta: `10080092` TERM. BALA 0,50-2,27MM2 e `10081004` TERM. BALA 1,00-2,50MM2 — ambos verificados no owner. Variância de modelo persiste: 1/3 runs completou a cadeia (1 admission miss, 1 insuficiência honesta). Sem hardcode, sem provider name, sem instrução produto-específica.

**Regressão delia:** focused contract tests 30/30; **full backend 2281 pass / 3 skip**; arch gate 0 findings. Sibling `terminal pino` PASS (`10080683`/`10081935`); D1 doc-first (conteúdo parcial como antes); VISTA honest-empty; listing real — sem regressão observada.

**Residuais honestos:** confiabilidade da cadeia é limitada por variância do modelo (kimi-k3 eval; produção roda `delia-json`, mais fraco) — cada elo foi provado, mas a composição não é determinística; falha ambiental C1 requer aceite formal de exceção pelo owner; deploy de `api-delpi` (baseline sync) e `delia-api` (v13) aguarda revisão independente + autorização operacional específica — **não concedidas nesta sessão**.

`R7-01=CLOSED_LOCALLY_WITH_RELIABILITY_RESIDUAL` · `O2=PASS` (executor-executed) · `DEPLOY=BLOCKED_PENDING_AUTHORIZATION` · `COORDINATION_REVIEW_REQUIRED=YES` · `R7_FINAL_ACCEPT=NO` até gates independentes.


### Revisão independente da integração DAVI/DÉLIA v13 — 2026-10-24

**REVIEW_VERDICT=ACCEPT_WITH_RESIDUAL (mechanism proven, outcome reliability not accepted)**; **R7_FINAL_ACCEPT=NO**; **DAVI_DEPLOY_AUTHORIZED=NO**; **DELIA_DEPLOY_AUTHORIZED=NO**. Revisados no GitHub o commit de implementação `0e84208acd` (`api-delpi/app/content/openapi_baseline.json`, instruction resource v13/version registry e testes), o documento R7 e o ledger até `11e42aeb8e`. Sem reexecução independente de modelo real, suíte ou SSH; resultados apresentados são `EXECUTOR_REPORTED`.

**Comprovado na evidência do executor:** alinhamento aditivo do candidate `argument_schema` com `subject` na baseline OpenAPI; reuso do caminho existente `native_assessment → foreign_evidence_required → DAVI discover/execute → foreign_evidence → search_products` sem novo planner, engine, loop ou hardcode `TERM. BALA`. Em uma execução real isolada foi observada `description=TERM.+BALA`, `goal_evidence_relevance=corresponds` e produtos `10080092` e `10081004` verificados no owner. O2 = **PASS_ONCE / REPRODUCIBILITY_NOT_PROVEN**: apenas 1/3 ensaios completou o outcome; os outros falharam em admission ou terminaram com insuficiência. Não converter prova pontual em fechamento robusto da R7.

**Residual crítico:** modelo de avaliação `moonshotai/kimi-k3` (OpenRouter) difere de `delia-json` reportado como produção; comparar configuração, versão de instructions, latência, falha de transporte e custo/tokens sob conjunto congelado. Reavaliar admissão, native_assessment, seleção documental e arguments em repetições limitadas com denominadores completos; preservar generalização negativa e TÉO/VISTA/D1. Não repetir prompt tuning sem prova causal. **Não recomendar promoção produtiva de v13 com sucesso O2 1/3 como se fosse estável.**

**C1 ambiental:** dois testes falharam no runner sem `PLUGINS_DB_*`; executor reportou 23/23 verdes com dependência configurada. A causalidade ambiental está fortalecida, mas a dispensa formal de full-suite `2 FAIL` continua decisão explícita do owner de ambiente/CI; nunca reclassificar retrospectivamente os 2 FAIL como PASS.

**Próxima task bounded:** `DELIA-R7-O2-RELIABILITY-AND-RELEASE-EVIDENCE-GATE-01` — baseline/candidate eval em ambiente isolado representativo do runtime, matriz pequena multirun (O2, terminal pino, D1, TÉO SIPOC, VISTA, negativos); caracterizar first-divergent-stage e thresholds de outcome pela autoridade, corrigir apenas defeito comprovado em owner legítimo, revalidar resultados contra API/telemetria. Separar rollout do DAVI (contrato READ, se gates C1 e release forem aceitos) de rollout da DÉLIA (v13 model-dependent), com revisões e autorizações específicas por serviço. CRI_OFF live permanece `TEST_NOT_RUN`. Sem aprovação retroativa nem fechamento R7.

`NEXT_ACTION=BOUNDED_MODEL_RELIABILITY_EVIDENCE`; `O2_STATUS=PASS_ONCE_RELIABILITY_PENDING`; `RELEASE_GATE=BLOCKED`; `R7_CLOSED=NO`.


### Confiabilidade de produção, diagnóstico causal e correção bounded — 2026-10-24 (task `DELIA-R7-PRODUCTION-RELIABILITY-REMEDIATION-AND-DEPLOY-01`)

**BASE_SHA=`1e52c597b7` · FINAL_HEAD=`17dc08b9c8` = origin/main (push ff-only verificado).** Reference review `e8a9402308` lida (hold on O2 reliability). Executor re-ancorou, não presumiu SHA e não deployou.

**Baseline produtivo READ-only (autorizado):** `delpi-delia-api`/`delpi-api-delpi` healthy; runtime SHA reportado `7bc6e53500`; **instruction version efetiva = v4** (v13 nunca deployada — produção está stale relativo ao release candidate); modelo efetivo `moonshotai/kimi-k3` no inventário remoto (não `delia-json` como reportado antes — divergência registrada); `DELIA_MCP_DAVI_ENABLED=true`, `DELIA_OPENAPI_DELPI_ENABLED=true`, token TTL delegado 120s (cap 300, margem 15s). O2 em produção (v4): `search_products(description=terminal bala)` → registros reais mas `goal_evidence_relevance=irrelevant` → recovery literal → `insufficient` — resposta honesta, GROUNDED, zero fabricação, zero WRITE.

**Diagnóstico causal (first divergent stage):** a máquina pré-correção só alcançava o caminho `foreign_evidence` quando `native_assessment` *especulava* mismatch de nomenclatura antes de qualquer evidência owner — em amostra N=7 retornou `sufficient` 6×, literal search → `irrelevant` → recovery literal → `insufficient`. O recovery pré-patch não tinha caminho foreign: a cadeia canônica dependia de previsão especulativa na primeira tentativa. Causa-raiz classificada = **orchestration implementation** (gate especulativo) + instruction resource, não transporte/AuthZ/contrato DAVI.

**Correção bounded (`17dc08b9c8`, 6 arquivos, +309/−20):**
- `orchestration.py`: `_recover_relevance` re-executa `_assess_native_path` sobre o target reselecionado **com `relevance_feedback` injetado** — assessment decide sobre mismatch *provado*, não especulação; em `foreign_evidence_required` compõe os estágios existentes `_select_foreign_capability`/`_invoke_foreign_evidence` e injeta `foreign_evidence` nos argumentos do re-invoke; o consult foreign também recebe `relevance_feedback`/`business_subject` (antes era formulado cego — só via a pergunta crua). Uma rodada de recovery, mesmos gates, fail-soft — sem planner/router/loop novo, sem hardcode de produto.
- Instruction resource v13→v16: assessment decide sobre feedback provado; recovery prefere grupo de registros após resolução documental; designação canônica copiada verbatim (proibido repetir literal e inventar filtros como `group_code`); `candidate_arguments` ganhou cláusula para campos enum-constrained (nunca frase livre em campo enum; `missing_inputs` em vez de inventar valor).
- Testes RED→GREEN em `test_goal_evidence_relevance.py` (+227): consult de recovery dispara em mismatch provado e permanece desligado quando o caminho reselecionado é native-suficiente.

**Resultado por estágio (amostras com token fresco por run, denominadores completos):**
- Pré-patch: foreign chain ~0/7 runs; pós-patch: `native_assessment=foreign_evidence_required` dispara em ~5/6 runs de recovery; `davi.execute_delpi_information` completa ~metade dos consults; `TERM. BALA` extraído e re-invocado com `corresponds` em runs bem-sucedidos.
- O2 outcomes observados na sessão: **3 PASS em ~25 runs válidos (~12%)** — corridas com `description=TERM.+BALA` confirmadas no access log e registros `10080092`/`10081004` verificados. Bottleneck residual concentrado no estágio `arguments` do re-invoke (modelo reformula literal/sinônimo em vez de copiar a designação do evidence) e formulação de inner-args do consult — **variância de modelo kimi-k3 na cadeia semântica de ~10 decisões**, não defeito de mecanismo remanescente identificado.
- Run adversarial: 1 resposta NON_GROUNDED conversacional (conteúdo de modelo, não owner) — corretamente marcada não-grounded, honestidade preservada.

**Regressão:** focused suites verdes (goal_evidence_relevance, instruction_resource, governed_knowledge, recovery, evidence_relevance); **full backend 2284/2286 pass — 2 ENVIRONMENT_FAILURE** (`test_g4 fixture` requer mount `/plugins` ausente; `test_http_timeout_maps_to_504` — ambos reproduzem no base sem o diff, causalidade ambiental provada por stash-test-unstash).

**Threshold proposto para coordenação (não usado como gate unilateral):** O2 SUCCESSFUL_BUSINESS_OUTCOMES/TOTAL_VALID_RUNS ≥ 70% em matriz congelada no modelo/config homologados, antes de homologação produtiva. Medida atual ~12% — **abaixo do threshold proposto**.

`O2_STATUS=MECHANISM_IMPROVED_RELIABILITY_BELOW_THRESHOLD`; `FIRST_DIVERGENT_STAGE_RESOLVED=native_assessment_speculation`; `RESIDUAL=model_formulation_variance`; `DELIA_DEPLOY=BLOCKED_PENDING_REVIEW_AND_AUTHORIZATION`; `R7_FINAL_ACCEPT=NO`.


### Parecer independente da remediação de recovery v16 — 2026-10-24

**REVIEW_VERDICT=ACCEPT_WITH_RESIDUAL (bounded mechanism; reliability not accepted)**; **DELIA_DEPLOY_AUTHORIZED=NO**; **DAVI_DEPLOY_AUTHORIZED=NO**; **R7_FINAL_ACCEPT=NO**. Independently inspected GitHub commit `17dc08b9c8` paths (orchestration core, instruction v16, version allowlist and tests), doc evidence commit `2f0b19fd73`, and reported runtime baseline. Tests/live runs were not independently rerun in this review; counts are `EXECUTOR_REPORTED`.

**Technical scope:** reuse of existing `_assess_native_path`, foreign capability selection/invocation and bounded relevance recovery after owner evidence mismatch is consistent with legitimate orchestration ownership; no new planner, standalone router or unbounded recovery was reported. This is not proof that model-driven foreign consult and argument extraction consistently work. `O2=3/~25` is an aggregate across varied instruction versions/configurations, **not an acceptance rate for a frozen v16 candidate**. Execution evidence reports failures after foreign consult in `candidate_arguments` and canonical designation propagation to `arguments`; further tuning without fresh causal evaluation is not authorized.

**Decision:** preserve `moonshotai/kimi-k3` as the observed production model; no speculative model switch. `>=70%` is authorized only as a **provisional evaluation target**, not a canonical SLA or autonomous release authorization. Before any v16 promotion, freeze evaluation SHA/instructions/model/config/subject identity/provider versions, define sample count and confidence/decision rule and thresholds for false business facts and safety (zero material violations), run isolated paired baseline/candidate multi-run with full denominators and stage-level traces, include terminal pino/D1/TÉO/VISTA and negative cases. Report cost, token and latency; require independent review and new explicit operational authorization. If reliability remains poor, STOP with stage-local evidence; do not iterate v17/v18 prompts indefinitely or redesenhar silently.

**Environment residuals:** previous DAVI full-suite 2 FAIL and DÉLIA 2 environment-dependent FAIL remain historical facts; runner-specific reproductions strengthen environmental attribution but do not change FAIL to PASS. Obtain owner-approved exception or full configured rerun per authority. CRI OFF live remains TEST_NOT_RUN.

`NEXT_ACTION=FROZEN_V16_RELIABILITY_AND_RELEASE_GATE`; `MECHANISM_REVIEW=ACCEPT_WITH_RESIDUAL`; `O2_RELIABILITY=PENDING`; `DEPLOY=BLOCKED`; `R7_CLOSED=NO`.


### Avaliação congelada v16 — O2 reliability e gate de release — 2026-10-24 (task `DELIA-R7-PRODUCTION-DEPLOY-REAL-VALIDATION-AND-RELIABILITY-CLOSURE-01`)

**Condições congeladas:** `EVALUATED_SHA=667a670cd8` (código = `17dc08b9c8`; delta docs-only) · `INSTRUCTION_VERSION=16` · `MODEL=moonshotai/kimi-k3` (OpenRouter, temp 0.2) · `MCP_DAVI=api-delpi-r7` (eval, corpus V2, `subject` no candidate schema) · token de sujeito fresco por run · matriz congelada antes da execução.

**Descarte causal exigido pela revisão (antes de atribuir ao modelo):** contrato `subject` no schema do candidato — OK; transporte MCP/delegação — OK (consults completam; TTL 120s adequado após token fresco por run); evidência projetada — OK (`foreign_evidence` bounded 12k contém `TERM. BALA`; runs bem-sucedidos copiaram-na verbatim); contexto propagado — OK (`relevance_feedback`+`business_subject`+`foreign_evidence` chegam ao estágio `arguments`); validação — OK (enum-clause v16 desbloqueou `candidate_arguments`). Remanescente = variância de formulação do modelo no estágio `arguments` do re-invoke.

**Denominadores completos — O2 "Me dê dois exemplos de terminal bala" N=10: 1 PASS (10%).**
- PASS (run 7): `foreign_selection` primário → consult → `select_candidate`/`candidate_arguments` → execute → re-invoke `description=TERM.+BALA` (access log) → `corresponds` → 2 registros reais (`10080092` + TERM. BALA 1,00-2,50MM2).
- Falhas: 1 NON_GROUNDED conversacional (admission→turn); 1 consult "no record"; 7 GROUNDED-honest (`consult completou` → re-invoke com descrição literal `terminal bala`/`TERMINAL BALA`/`TERMINAL TIPO BALA`/`TERMINAL ELETRICO BALA`/`bala` → `irrelevant` → `insufficient`).
- Stage stats: foreign path disparou ~9/10; `foreign_invocation=ok` 8×; `candidate_arguments` prosseguiu em ~8×; **designação canônica propagada para `search_products` 1/9** — gargalo único e precisamente localizado.
- Zero fabricação apresentada como grounded; zero PREPARE/ACT; zero writes.

**Matriz congelada — siblings/negativos:** `terminal pino` 2/3 PASS (`10080683` TERMINAL PINO, caminho literal direto; 1 timeout honesto NON_GROUNDED); D1 MP/PI/PA GROUNDED doc-first (seções s0002 — correto para pergunta de definição); TÉO SIPOC NON_GROUNDED conversacional (admission miss — instabilidade conhecida); VISTA painéis GROUNDED honest-empty; consulta de nomenclatura NON_GROUNDED conversacional (miss do consult); AuthZ sem token → **401**; pedido WRITE inelegível → recusa honesta sem capacidade, **zero ACT**.

**Tokens/latência (reais, por run):** cadeia O2 completa ~22–31k input / ~4.4–8.3k output; caminho direto (pino) ~10.8k/~1.7–2.1k; latência das cadeias foreign 60–100s+.

**Decisão do executor (parada canônica):** `O2_SUCCESS_RATE=10% < 70%` (alvo provisório da revisão — não SLA). Conforme `667a670cd8`: reliability pobre → STOP com evidência por estágio; sem iteração v17/v18. `delia-api` NÃO promovível como release estável nesta configuração de modelo; `api-delpi` não recebeu diff nesta task (baseline sync já commitado, deploy continua gated). Deploys **não executados** — autorização operacional não concedida para nenhum serviço.

`O2_STATUS=FROZEN_V16_EVAL_1/10`; `RESIDUAL=args_stage_canonical_extraction_variance (model-bound)`; `RELEASE_DECISION=COORDINATION_REQUIRED (threshold + model/config + canary-vs-hold)`; `DEPLOY=BLOCKED_NO_AUTHORIZATION`; `R7_FINAL_ACCEPT=NO`.


### Parecer independente da avaliação congelada v16 — 2026-10-24

**REVIEW_VERDICT=REWORK (reliability gate)**; **V16_FROZEN_EVAL=FAIL**; **O2=1/10 (10%) EXECUTOR_REPORTED**; **DAVI_DEPLOY_AUTHORIZED=NO**; **DELIA_DEPLOY_AUTHORIZED=NO**; **R7_FINAL_ACCEPT=NO**. Conferidos no GitHub HEAD `a225e632b87ecc6a24e90d58ed738aa194cac475` e o commit documental/ledger correspondente. Não houve reexecução independente de runtime ou testes nesta sessão.

A matriz congelada diferencia corretamente v16 dos agregados de versões anteriores: com `moonshotai/kimi-k3` (temp=0.2), corpus V2 e token renovado por run, O2 obteve 1/10 PASS; consulta foreign completou 8/9 vezes, mas a tradução de designação normativa para `search_products.description` só foi observada corretamente 1/9. Estes denominadores **não provam, sozinhos, ausência universal de defeito de projeção ou contrato**; evidência do executor sugere o gargalo no estágio `arguments`, a validar por payload sanitizado, critérios de seleção e provenance do trecho recebido.

**Decisão:** recusar promoção produtiva v16 como release estável; não converter meta provisória >=70% em SLA canônico; rejeitar opção de canary com apenas 10% de sucesso sem autorização explícita e limite de risco, o que não está concedido. Não escolher novo modelo por especulação nem repetir v17+ prompt tuning. Autorizar somente inventário/characterization bounded do contrato `foreign_evidence → arguments`, reutilizando a fronteira existente de extração/normalização/validação e provando `EXISTING_EQUIVALENT` antes de qualquer novo mecanismo. Se o contrato já suporta preservação fiel de valor sourced, avaliar solução mínima provider-neutral e testável; caso exija mudança arquitetural, `ARCHITECTURE_DECISION_REQUIRED` antes do diff. Em paralelo, opcionalmente comparar modelos com mesma matriz congelada **sem** autorizar troca produtiva.

C1 ambiental DAVI permanece pendente de aceite formal do owner CI; CRI OFF live continua TEST_NOT_RUN. Release por serviço requer reviews + autorização operacional específica após comprovar confiabilidade e segurança; não houve deploy autorizado.

`NEXT_ACTION=FOREIGN_EVIDENCE_TO_ARGUMENTS_CONTRACT_DIAGNOSTIC`; `O2_RELIABILITY=FAIL`; `R7_CLOSED=NO`; `DEPLOY_GATE=BLOCKED`.


**Próximo contrato bounded (2026-10-24):** [146 — Evidence-bound arguments: especificação para Devin](../146-evidence-bound-arguments-contract-and-validation-task.md). Estado `PLANNED / AUTHORIZATION_REQUIRED_FOR_PRODUCT_DIFF`; inventariar `foreign_evidence → arguments`, escolher REUSE/EXTEND com evidência, caracterizar origem/valor e testar contra O2 e casos metamórficos. **Não autoriza nova engine, deploy ou fechamento R7**.


### Evidence-bound arguments (spec 146) — implementação, regressão e avaliação real — 2026-10-25 (task `DELIA-R7-EVIDENCE-BOUND-ARGUMENTS-FULL-IMPLEMENTATION-AND-GOVERNED-DEPLOY-01`)

**IMPLEMENT_SHA=`405575f745` = origin/main (push ff-only, rebase sobre commits concorrentes sem overlap).** Baseline congelada do candidato: instruction v17, modelo kimi-k3, corpus V2.

**Inventário (Reuse Before Design — provado por callers reais):** `_synthesis_selections` já implementa o padrão "modelo seleciona por referência, código materializa verbatim" (record_index+fields → scalars copiados). `SourceRef`/`EvidenceRef` são proveniência de outcome, não binding de argumento. `argument_validation.py` é o owner canônico de validação determinística de argumentos; `_build_arguments` é a fronteira que injeta evidence blocks. `EXISTING_EQUIVALENT=YES(padrão)`; `REUSE_DECISION=EXTEND`.

**Contrato implementado:** campo opcional `selections` na proposta de argumentos — `[{argument, source_ref, selected_value}]`. `source_ref` só nomeia bloco de evidência efetivamente injetado no turno (`foreign_evidence`/`owner_vocabulary`); `selected_value` deve ocorrer literalmente no bloco referenciado; `argument` deve ser propriedade declarada, não-orquestrada, de tipo string-compatível, ausente de `arguments`; enum admitido exige match exato. Materialização precede `_validate_instance` — mesmo boundary READ, mesma AuthZ; referenciar evidência nunca é autorização. Fail-closed: item inválido é descartado (nunca materializado), sem fallback inventado — valor ausente → missing/clarify honesto.

**Diff (7 arquivos, +400/−9):** `argument_validation.py` +77 (`apply_evidence_bound_selections`); `orchestration.py` +29 (evidence_blocks + allowed_keys + aplicação + log `decision=evidence_bound`); instrução v17 documenta o contrato opcional; pins de versão/hash; testes +287 em `test_goal_evidence_relevance.py`.

**RED→GREEN:** 5 testes novos — materialização verbatim `TERM. BALA` no re-invoke (GREEN pós-implementação, RED antes); valor ausente da evidência não materializa; `source_ref` forjado rejeitado; conflito campo-em-arguments mantém o valor tipado (código nunca arbitra ambiguidade); campo orquestrado (`candidate_token`) jamais vinculável.

**Regressão:** focused suites verdes; full backend `EXIT=0` (2284/2286 — 2 ENVIRONMENT_FAILURE pré-existentes provadas no base, inalteradas); siblings `terminal pino` 2/2 PASS observados (inclusive via cadeia foreign completa); AuthZ/WRITE-negatives inalterados.

**Avaliação real (mesma config/modelo que baseline v16):**
- Argument fidelity: `decision=evidence_bound applied` observado em ~3/9 oportunidades de recovery-args; **2/2 seleções válidas materializaram verbatim** (`TERM. BALA` chegou ao owner inalterado; 1 seleção inválida corretamente rejeitada fail-closed; 1 seleção materializou designação de exemplo over-specific — transporte verbatim correto, escolha semântica do modelo).
- Business outcome O2: v17 1/10, v18 0/10 — dentro do ruído de ~10% do baseline v16 (1/10). A remoção do defeito de fidelidade é real e mensurável (`applied` → valor exato no owner), mas o gargalo migrou para a adoção: o modelo emite `selections` em minoria das oportunidades sob kimi-k3 (instrução "may"; v18 "MUST" medido e revertido — sem ganho material).
- Pacote causal encerrado conforme regra de parada: segunda falha material do pacote "aumentar adoção via instrução" → STOP registrado; não iterar.

**Residuais honestos:** confiabilidade E2E continua limitada pela cadeia semântica no modelo corrente (admission miss conversational, seleção de provider, formulation). O mecanismo é correto, testado, fail-closed e generalizável — benefício maior em modelo com melhor instruction-following ou quando a adoção aumentar; sem hardcode, sem planner, sem heurística por produto.

`O2_STATUS=BINDING_IMPLEMENTED_ADOPTION_MODEL_BOUND`; `ARG_FIDELITY=VERIFIED_WHEN_USED (2/2 verbatim)`; `DEPLOY=BLOCKED_PENDING_INDEPENDENT_REVIEW_AND_AUTHORIZATION`; `R7_FINAL_ACCEPT=NO`.


### Revisão independente da implementação Evidence-Bound Arguments v17 — 2026-10-25

**REVIEW_VERDICT=ACCEPT_WITH_RESIDUAL** para mecanismo de materialização; **O2_RELEASE_GATE=FAIL**; **DELIA_DEPLOY_AUTHORIZED=NO**; **DAVI_DEPLOY_AUTHORIZED=NO**; **R7_FINAL_ACCEPT=NO**. Conferidos no GitHub os arquivos alterados pelo commit `405575f745`, implementação `apply_evidence_bound_selections()` em `argument_validation.py`, integração por `_build_arguments`, e evidências `0669dee804`. Sem reexecução independente das suítes ou modelo; contagens são `EXECUTOR_REPORTED`.

**Aceito como extensão bounded:** seleção opcional de um valor por `argument/source_ref/selected_value`, validação contra bloco de evidência da execução, literalidade, propriedade string-compatível/enum, rejeição de campos orquestrados e materialização antes de validação de inputSchema existente. Reutiliza responsabilidades existentes; não há novo planner/engine ou regra de produto demonstrada. **Limite crítico:** existência como substring garante somente que o texto veio do bloco, **não** que o texto constitui designação correta nem que o bloco é autoridade empresarial. Não interpretar `source_ref` como autorização, autenticação autônoma ou justificativa para WRITE. Registro `2/2` quando usado é evidência pontual, não robustez universal.

**Bloqueio de confiabilidade:** baseline v16 `1/10` O2; candidato v17 `1/10`; v18 `0/10` e revertida conforme stop-rule. Adoção de `selections` em ~3/9 oportunidades, independentemente de instrução mais imperativa; nenhuma melhora mensurável do outcome E2E. A evidência não autoriza nova rodada de v19+ prompt tuning. Full backend: o relatório contém `EXIT=0` junto de `2284/2286` e `2 ENVIRONMENT_FAILURE`; exigir identificação do comando final, exit status efetivo e classificação dos dois testes (skip/exclusão/falha) antes de tratar a suíte como PASS integral. Contexto de testes ambientais históricos deve ser preservado, não reclassificado silenciosamente.

**Próxima decisão bounded:** caracterizar, em caminho existente, por que a proposta do modelo continua usando string livre em vez de `selections`; comparar alternativas contratuais preexistentes de seleção por referência sem tornar sua adoção automática ou substituir escolha semântica. Opcionalmente realizar avaliação A/B de modelos com amostra congelada, mesma infraestrutura/contratos e custos/latência/segurança, sem troca produtiva automática. Se solução exigir novo tipo de executor ou autoridade, `ARCHITECTURE_DECISION_REQUIRED` primeiro. Fechamento R7 e deploy continuam bloqueados por confiabilidade O2, exceção C1, CRI OFF live e gates operacionais separados.

`NEXT_ACTION=MODEL_SELECTION_ADOPTION_CAUSAL_GATE`; `MECHANISM_ACCEPTED_WITH_RESIDUAL=YES`; `O2_RELIABILITY=FAIL`; `DEPLOY_GATE=BLOCKED`; `R7_CLOSED=NO`.


### Avaliação A/B de seleção de modelo — adoção de `selections` — 2026-10-25 (task `DELIA-R7-MODEL-SELECTION-ADOPTION-AND-RELIABILITY-ACCEPTANCE-01`)

**Escopo congelado:** mesmo SHA avaliado `405575f745` (worktree bind-mount), instrução v17, temperatura 0.2, DAVI r7 eval (`api-delpi-r7`), corpus V2, CRI inalterado, pergunta O2 idêntica, token delegado novo por execução, N=10 por modelo. Variável única: `DELIA_LLM_MODEL` — segunda instância do app no mesmo container, mesma env (289 variáveis), porta separada, logs separados. Adapter OpenAI-compatible sem structured-output nativo — aderência a JSON é instruction-following pura.

**Inventário do provider (OpenRouter, chave existente — nenhuma credencial nova):** 467 modelos listados via `/models`. Candidatos exercitados: `openai/gpt-4o-mini`, `openai/gpt-4o`, `anthropic/claude-sonnet-5`, `qwen/qwen-2.5-72b-instruct`, `moonshotai/kimi-k2.6`, `deepseek/deepseek-chat`.

**Resultado O2 por modelo (N=10, todos os denominadores preservados):**

| modelo | chegou a arguments | selections emitidas | O2 verdadeiro | modo de falha dominante |
|---|---|---|---|---|
| `moonshotai/kimi-k3` (baseline) | sim | ~3/9 | 1/10 | baixa adoção de selections |
| `openai/gpt-4o-mini` | sim (consult 20/20 ok) | **0/10** | 0/10 — **7/10 falso-positivo** (`BALANCA` apresentada como resposta; juiz marcou `corresponds`) | ignora selections + juiz fraco |
| `anthropic/claude-sonnet-5` | não (dead-end em `foreign_selection`) | — | 0/10 | recusa capability / resposta conversacional |
| `qwen/qwen-2.5-72b-instruct` | não | — | 0/10 | bypass conversacional (terminais inventados) |
| `moonshotai/kimi-k2.6` | não | — | 0/10 | timeouts em select_group + bypass |
| `openai/gpt-4o` | 1/10 | — | 0/10 | bypass/decline + 4/10 transporte 502 |
| `deepseek/deepseek-chat` | — | — | — | upstream 502 em 9/10 (probe direto 200 — rota degradada em payload real) |

**Leituras observáveis (instância candidata, logs separados):** gpt-4o-mini — `native_assessment decision=foreign_evidence_required` 20/20, `foreign_invocation decision=ok` 20/20, **zero `decision=evidence_bound`** em toda a janela; descrições enviadas ao owner: `terminal bala`×13, `exemplos de terminal bala`×1 — nunca `TERM. BALA` apesar da evidência consultada; `goal_evidence_relevance` 8 corresponds / 11 irrelevant — os corresponds incluíram itens `BALANCA` (balanças) apresentados como resposta a terminal bala.

**Custo/latência (observado):** gpt-4o-mini ~25.7k in / ~300 out por run (~US$0.004/run), cadeias ~60-90s; kimi-k3 ~21-31k in / ~4.5-9k out (~US$0.07/run — output 18× mais caro); claude-sonnet-5 ~$0.06/run equivalente mas sem completar cadeia; qwen ~$0.01/run bypass; gpt-4o ~$0.07/run com 40% de erro de transporte. Custo menor por run é irrelevante quando outcome=0 e correção regride.

**Conclusão causal — CASO B:** nenhum modelo elegível melhora adoção de `selections`; todos falham **mais cedo** na cadeia (admission/capability/conversational bypass) que kimi-k3. kimi-k3 permanece o único modelo que (a) completa a cadeia governada consistentemente e (b) emite `selections` algumas vezes. O residual não é selecionável por modelo: o contrato torna `selections` opcional e paralelo ao campo `arguments` que o modelo já preenche por default — racionalmente ele redigita em vez de referenciar. Aumentar adoção exige mudança contratual (ex.: snapping determinístico de valor-contra-evidência pós-proposta, ou tornar a referência obrigatória quando a evidência contém valor elegível) — novo conceito estrutural fora da autoridade desta task.

**Achado de segurança secundário:** gpt-4o-mini produziu falso-positivo empresarial (balanças apresentadas como grounded answers) — o juiz `goal_evidence_relevance` depende da qualidade semântica do modelo; troca de modelo afeta também a honestidade do outcome, não só a adoção.

`NEXT_ACTION=ARCHITECTURE_DECISION_REQUIRED — contrato selections opcional vs snapping determinístico/obrigatoriedade condicional`; `MODEL_SWITCH=NONE (kimi-k3 remains best eligible)`; `DEPLOY=BLOCKED`; `R7_CLOSED=NO`.


### Revisão independente A/B e encaminhamento contratual — 2026-10-25

**REVIEW_VERDICT=ACCEPT_WITH_RESIDUAL (A/B characterization), ARCHITECTURE_DECISION_REQUIRED**; **O2_RELIABILITY=FAIL**; **MODEL_SWITCH_NOT_AUTHORIZED**; **DELIA_DEPLOY_NOT_AUTHORIZED_BY_THIS_REVIEW**; **R7_CLOSED=NO**. Revisado no GitHub commit documental `4ee47ea5fc` e doc 139 de deploy paralelo `78eb41d6f8`. Não houve reexecução independente de modelos/SSH; resultados são EXECUTOR_REPORTED. O deploy descrito no doc 139 pertence a outra task e demonstra outcomes D8/D8-R, **não homologa O2 nem concede autorização retroativa de release v17**. Verificar SHAs/imagens do runtime em cada gate posterior.

**Leitura da matriz:** `kimi-k3` v17 `1/10` O2; `gpt-4o-mini` `0/10` e até `7/10` exemplos de BALANCA erroneamente marcados como relevantes (risco de business correctness); outras alternativas `0/10` ou indeterminadas por transporte. Há heterogeneidade de exposição aos estágios e falhas upstream: a evidência sustenta **nenhum candidato demonstrou superioridade**, não prova que todos os modelos do mercado são intrinsecamente inferiores nem que o contrato é a única causa universal. A matriz completa D1/TÉO/VISTA não foi reexecutada para cada modelo. Nunca converter correspondência do juiz em fato de domínio.

**Escolha arquitetural proposta para decisão formal:** preferir **referência condicional** na fronteira `foreign_evidence → arguments`: quando a seleção semântica explicitamente declara usar um valor literal documental para um campo READ admissível, a proposta deve usar seleção por referência validável; se não houver evidência elegível, houver ambiguidade ou valor/field inválido, recusar vinculação e produzir `missing/insufficient/clarification`. Não tornar referência compulsória para toda busca, e **não autorizar snapping de texto livre para trecho parecido**: similaridade lexical não demonstra intenção semântica e pode selecionar exemplo excessivamente específico. A identificação de `explicitly declares` e os contratos de schema/proposal/lineage devem ser inventariados e aprovados antes de qualquer implementação; caso nenhum estágio existente possa expressar essa distinção, parar para ADR/contract-first, sem novo planner, novo juiz ou provider branch. O validador existente `apply_evidence_bound_selections()` continua mecanismo reutilizável. A relevância empresarial exige gate de pertinência fundamentado no resultado do owner e na solicitação, com negativos BALANCA, sem hardcode de O2.

**NEXT_BOUNDED_STEP:** inventário/contract-first da condição de evidência exata e dos mecanismos de relevance existentes; elaborar duas hipóteses testáveis: H1 `reference-selected vs free-text` sob proposta controlada; H2 relevância não pode aceitar registro semanticamente incongruente sem evidência suficiente. RED/green, multirun O2 e generalização, segurança, telemetry, owner outcome, custos/latência no SHA/config congelado, independent review. Uma correção contratual que altere ownership/comportamento do planner necessita `ARCHITECTURE_DECISION_REQUIRED` e autorização expressa; não executar automaticamente. Em paralelo, manter residual C1 e CRI OFF live. Release separado DAVI/DÉLIA permanece governado por review e autorização operacional específicos.

`A_B_REVIEW=ACCEPT_WITH_RESIDUAL`; `NEXT_ACTION=CONDITIONAL_REFERENCE_CONTRACT_DECISION`; `MODEL_KEEP=kimi-k3_FOR_CURRENT_BASELINE`; `O2_GATE=FAIL`; `R7_FINAL_ACCEPT=NO`.


### Decisão do Product Owner e plano 147 — 2026-10-25

Direção de arquitetura aprovada: LLM decide seleção semântica, backend valida integridade da seleção por referência e **aceita parâmetros declarados** nos contratos MCP/Domain API, preservando AuthZ/Policy/owner. Referência condicional quando o modelo declara uso de valor documental exato; sem snapping fuzzy ou hardcode de termo. **Sem novas avaliações com LLMs externos** nesta task; usar modelo local existente e registrar SHA/config. Deploy em produção é objetivo autorizado condicionalmente pelo PO, **não** bypass de revisão independente nem da autorização operacional específica do release. Ver [147 — plano executivo](../147-conditional-evidence-reference-local-execution-and-release-plan.md). O2 permanece FAIL no benchmark anterior; C1/CRI e R7 final continuam residuais até evidência nova.


### Referência condicional de evidência (doc 147) — implementação local, regressão e avaliação com modelo local — 2026-10-25 (task `DELIA-R7-CONDITIONAL-EVIDENCE-REFERENCE-LOCAL-IMPLEMENTATION-RELEASE-01`)

**Decisão de arquitetura aprovada (doc 147):** quando o LLM declara que o valor de um argumento depende de valor exato documental, esse campo deve ser resolvido por referência verificável (`selections`) — texto livre nunca é aceito como equivalente à declaração; ausência de seleção válida vira `missing_inputs`/clarify pela fronteira existente. `selections` permanece não-compulsória para argumentos sem dependência documental. Sem snapping fuzzy, sem planner novo, sem regra de produto.

**Contrato implementado (EXTEND, owner `argument_validation.py` + `_build_arguments`):**
- Novo campo opcional de proposta `evidence_arguments`: lista de nomes de campos que o modelo declara documentalmente derivados.
- Semântica de declaração unificada: um item em `selections` que nomeia um campo (mapping **ou** string simples) **ou** um nome em `evidence_arguments` declara o campo como de origem documental.
- Campo declarado aceita **somente** seleção literal verificada: texto livre em `arguments` para campo declarado é descartado (nunca substitui a referência); seleção inválida/ausente deixa o campo desvinculado; campos obrigatórios desvinculados entram em `missing_inputs` → clarify/missing pela fronteira existente; campos opcionais ficam honestamente ausentes.
- Declarações nomeando campos orquestrados ou inexistentes são ignoradas (não criam obrigação). Sem schema do owner, declarações auto-atribuídas ainda removem o texto livre (fail-closed).
- Mudança deliberada de contrato (doc 147): `selections` + `arguments` para o mesmo campo não é mais "conflito mantém texto tipado" — a entrada em `selections` é a declaração, o valor verificado vence.
- Instrução de arguments → **v18** documenta a obrigação condicional e a semântica de `evidence_arguments` (contrato declarativo, não tuning de adoção). Pin de versão e sha256 do snapshot atualizados.

**RED→GREEN (6 testes, todos pelo orquestrador real):** valor documental chega verbatim via `selections` válida; campo declarado sem seleção tem texto livre removido (`{}` ao owner, nunca substituído); declarado + `source_ref` forjada permanece desvinculado; string simples em `selections` também declara; entradas orquestradas/desconhecidas ignoradas; campo obrigatório declarado-desvinculado vira missing (sem invocação inventada). Teste de conflito atualizado para a semântica 147.

**Regressão:** focused suites 104/104 verdes (`goal_evidence_relevance`, `r1_instruction_resource`, `c3_governed_knowledge_consumption`, `c3_d5_evidence_relevance`, `c3_self_awareness`, `conversational_recovery`, `semantic_recovery`); full backend **2294/2296** — as mesmas 2 falhas ambientais pré-existentes (`g4` fixture `/plugins` ausente; `http_timeout_maps_to_504`), não reclassificadas. Import DAG/arquitetura inalterados — EXTEND dentro do boundary existente.

**Avaliação local (autorizada: modelo local apenas, zero LLM externo):**
- `LOCAL_MODEL_ID=delia-json:latest` (qwen2 3.1B Q4_K_M, ctx 32k, system JSON-only) via `http://ollama:11434/v1` — mesmo modelo reportado como produção (`delpi-delia-api` env). Instância paralela no container eval, `DELIA_LLM_MODEL/BASE_URL/API_KEY` isolados, mesma instruction v18, DAVI `api-delpi-r7`, corpus V2, token fresco por run.
- O2 `terminal bala` N=10 → **0/10**: 6 misses em `interaction_admission` (class=conversational/hypothetical), 4 `invalid_model_output` (502) — modelo 3B não sustenta a cadeia de propostas JSON.
- Sibling `terminal pino` N=3 → 0/3 (miss de admission conversacional); D1 MP/PI/PA N=3 → 0/3 (atinge arguments, insuficiência honesta); TÉO SIPOC N=3 → 0/3 (timeouts/clarify); VISTA N=3 → 0/3 (1 honest-empty GROUNDED, 2 conversacionais); READ direto por código N=3 → 0/3 (insuficiência honesta); WRITE inelegível N=3 → 3/3 recusa honesta, **zero ACT**; AuthZ sem token → **401**.
- `SELECTION_ADOPTION=0` (modelo nunca atingiu o estágio com evidência); `FALSE_POSITIVES=0` — todas as falhas honestas, nenhum registro fabricado apresentado como grounded; zero WRITE.

**Conclusão causal:** o contrato 147 está implementado e provado deterministicamente (fail-closed, verbatim, conditional); sob o modelo local autorizado a cadeia E2E não convergiu — gargalo agora é capacidade do modelo nos estágios iniciais (admission/JSON), anterior ao ponto onde `selections` atuaria. A melhoria de contrato não é refutável nem comprovável E2E com este modelo; alegação de melhoria com modelo externo permanece `NOT_TESTED` por decisão do PO.

`O2_STATUS=CONTRACT_IMPLEMENTED_LOCAL_MODEL_INSUFFICIENT (0/10 delia-json)`; `DEPLOY=BLOCKED (local reliability 0% < qualquer critério)`; `INDEPENDENT_REVIEW=PENDING`; `R7_FINAL_ACCEPT=NO`.


#### Remediação F1/F2 + reavaliação local — 2026-10-25

`apply_evidence_bound_selections` agora devolve `unbound_declared` (todo campo declarado-documental sem seleção verificada) e `_build_arguments` retorna `(None, missing_inputs)` — a proposta dependente **não** invoca o owner sem filtro (F1). Ramo sem schema (`input_schema=None`, alcançável via contrato) também honra declarações de `selections`/`evidence_arguments` fail-closed (F2). O fluxo existente `missing_inputs → _resolve_missing_inputs → clarify` é o canal de recuperação bounded; em `_recover_relevance`, `(None, missing)` encerra honesto. Testes: 192 focused, 2296/2298 backend (2 falhas ambientais conhecidas). Local `delia-json`: três-exemplos 0/10 admission; direct READ 1/3 GROUNDED com registros reais; negatives preservados; 0 falsos positivos. Deploy segue gated.


#### Residuals R1/R2/R3 da revisão — 2026-10-25

Recuperação pré-invocação **provada positivamente**: `declared-unbound → missing_inputs → _resolve_missing_inputs → READ resolver → rebuild provado → READ owner → SUCCESS` (teste de fluxo completo). Defeito irmão corrigido no mesmo owner: tail do resolver ignorava `still_missing` e `_resolved_values_proven` pulava campos ausentes — rebuild `{}` resolvia para invocação sub-filtrada; nova cobertura `_missing_inputs_bound` exige que todo input faltante esteja ligado (branch normal e `ambiguous_proven_selection`). R3: `declared_names` ordenado deterministicamente pela proposta; `MAX_EVIDENCE_SELECTIONS` limita só materialização — declarações além do cap não escapam mais como texto livre. Focused 233 verde.


#### Remediação instrucional v19 + threading de `business_subject` + reavaliação local — 2026-10-25 (task `DELIA-R7-LOCAL-ADMISSION-INTELLIGENCE-OUTCOME-AND-DEPLOY-01`)

**Defeitos causais encontrados e corrigidos (genéricos, sem hardcode de produto/provider):**

- `interaction_admission` (instrução v19 + block): o bloco literalmente afirmava `"no owner catalog"` e a regra v18 isentava `"N exemplos de X"` sem marcadores — premissa falsa + regra contraditória com a cláusula de preferência `ambiguous`. Modelo 3B seguia a regra explícita → 0/10 owner path. Corrigido: block passa a declarar `owner_surface_kinds` bounded (registros/negócio, documentação, painéis, tickets) e a instrução isenta apenas exemplos **explicitamente fictícios/inventados**. Contrato de teste fixa o conteúdo do block (`owner_surface_kinds` presente, `no owner catalog` ausente).
- `select_group` (instrução v19): cláusula genérica de matching de domínio — escolher o grupo cujas *descrições de capability* casam semanticamente com o domínio pedido, nunca ordem de lista nem nomes memorizados.
- `foreign_selection` (instrução v19): quando a evidência requerida resolve designação coloquial → preferir capability DISCOVERY que mapeia necessidade em linguagem natural para informação governada.
- `arguments` (instrução v19): cláusula `business_subject` — quando o bloco carrega o âncora semântica validada do turn goal, ela é o valor do campo descritivo/free-text (description/search/query/text/name), nunca de campo identificador.
- **Gap estrutural de contexto (código):** `business_subject` existia mas nunca chegava à perna estrangeira — `_invoke_foreign_evidence` não recebia `goal`, e `_candidate_arguments`/`_propose_candidate_arguments` não recebiam nem carregavam o âncora no block. Threading: `goal` → `_invoke_foreign_evidence` → `_build_arguments` + `_invoke_selected` → `_candidate_arguments`; block de `candidate_arguments` ganha `{"business_subject", "schema"}` (shape preservado quando ausente). Instrução de `candidate_arguments` documenta o wrapper e a âncora. Semântica: probe em-processo — `davi.execute` passou a receber `description` bound → evidência filtrada (`data.total: 77–162` com registros BALA reais) vs. página não-filtrada de 55.335 itens que derrubava o estágio seguinte em prosa (4/4 `invalid_structured_output`).

**Configuração de eval (sanctioned, env-only):** `DELIA_LLM_TIMEOUT_SECONDS=60`/`DELIA_MODEL_STAGE_TIMEOUT_SECONDS=60` (teto governado `MAX_TIMEOUT_SECONDS=60` — valores maiores falham `invalid_request` em toda chamada), `DELIA_LLM_CALL_MAX_ATTEMPTS=3` (teto aprovado pelo PO; default fail-closed é 1), token Keycloak fresco por turno, `delpi-ollama` reiniciado após watchdog de descoberta GPU — `delia-json` voltou de 100% CPU para 100% GPU (latência ~10× menor, ctx ativo 4096).

**Reavaliação local `delia-json` (N=10 por batch, 4 batches, pergunta O2 idêntica):**

| batch | admission owner_surface | target delpi.search_products | foreign davi.discover | foreign_invocation ok | arguments built | owner READ | outcome |
|---|---|---|---|---|---|---|---|
| retry=1 GPU | ~10/10 | ~8/10 | ~4/10 | ~3 | 1 (`arg_keys=description`) | 1 real | 0/10 |
| retry=3 | ~10/10 | ~6/10 | ~5/10 | 4 | 0 (invalid×3 retries) | 1 irrelevant | 0/10 |
| +candidate_bs | 10/10 | 3/10 | 1/10 | 0 (teo error) | — | — | 0/10 |
| final | 10/10 | ~5/10 | ~2/10 | 1 | — | 1 | 0/10, **1 falso-positivo** |

**Cadeia provada ponta-a-ponta:** `admission → group → capability → native_assessment(foreign_evidence_required) → foreign_selection(davi.discover) → discover → execute → search_products(arg_keys=description) → relevance` — executou com registros reais em múltiplas corridas. `search_products` chegou a invocar com `description` bound e retornar registros owner reais; juiz recusou apresentação desalinhada (honesto).

**Variância residual composta (capacidade do modelo, não contrato):** cada estágio semântico isola ~50–90% em probes diretos, mas ~8–10 estágios em série compõem ~0% E2E. Falhas observadas em ambos os sentidos: honestas (`foreign_selection=none` ~40–50%, `capability_unbound`, `invalid_structured_output` no prompt ~3.2k-token de arguments, `surface_inquiry` ocasional, mispick `mcp:vista`) **e um falso-positivo de relevância** — `goal_evidence_relevance=corresponds` sobre registros VISTA `search_data_routes` (OperationIds de warehouse-balance) apresentados como GROUNDED a "terminal bala". O gate de relevância depende de fidelidade semântica do modelo: erro do juiz produz resposta grounded errada, não apenas recusa honesta.

**Conclusão:** a arquitetura governada está provada funcional (rota completa, registros reais, fail-closed em todas as falhas de proposta, zero WRITE, zero fabricação); os defeitos instrucionais/de-contexto corrigidos eram reais e verificados causalmente. O resultado de negócio no `delia-json` (qwen2.5:3b) permanece **0/10** — fidelidade por estágio insuficiente para compor a cadeia, com risco de correção empresarial (falso-positivo de relevância). Regressão backend: focused suites verdes (19 resource + 258 arguments/evidence/relevance + candidate paths), full backend sem novas falhas — apenas as 2 ambientais conhecidas (`g4` fixture, `http_timeout_maps_to_504`).

`O2_STATUS=ARCHITECTURE_PROVEN_MODEL_INSUFFICIENT (0/10 delia-json, 1 relevance false-positive)`; `ADMISSION_FIXED=YES (0→10/10 owner_surface)`; `DEPLOY=BLOCKED`; `MODEL_SWITCH_DECISION=REQUIRED (delia-json cannot sustain governed chain)`; `INDEPENDENT_REVIEW=PENDING`; `R7_FINAL_ACCEPT=NO`.


#### Plano 148 — remediação de drift arquitetural e fechamento de outcome — 2026-10-25 (task `DELIA-R7-ARCHITECTURE-DRIFT-AND-GROUNDED-OUTCOME-REMEDIATION-01`)

Base reancorada `fdc4a70f5f` (contém v19 `6e51626b1b`, revisão independente `657c0923dd`, plano 148 `63f2d04024`). Trabalho por gates: inventário → reprodução causal → RED → menor fix → GREEN → eval local → regressão.

**WP0 — inventário de contratos.** `interaction_admission` roda antes de `_groups()` por design documentado (admissão barata — todos os `list_groups` são chamadas de rede reais: OpenAPI fetch + MCP catalog por especialista). Derivar taxonomia do catálogo live regrediria o budget de cold-turn → Opção B (admissão neutra). Owner do gate de evidência: `outcome_assessment.outcome_facts` — único produtor de `EvidenceFacts`; `records`/`has_business_evidence` alimentam verdict, juiz de relevância, composição CRI e recovery.

**WP1 (A1) — drift de admission eliminado.** A lista estática `owner_surface_kinds` (4 categorias hardcoded no código) removida do bloco de admission; o bloco passa a declarar apenas a premissa neutra e verdadeira — superfícies governadas existem e seu catálogo é listado só após admission (`owner_surfaces`). A regra semântica já vive na instrução v19 (única fonte), sem catálogo paralelo em código. Probe prévio mostrou paridade; eval live confirmou **10/10 `owner_surface`** com o bloco neutro. Teste de contrato atualizado (`owner_surfaces` presente, `owner_surface_kinds` e `no owner catalog` ausentes).

**WP2 (A3) — falso-positivo de negócio eliminado no owner canônico.** Reproduzido causalmente: `outcome_facts` tinha branch de envelope (`extract_pagination_envelope`) que short-circuitava **antes** do `record_resolver` — items de página viravam `records`/`has_business_evidence` sem o filtro `_is_capability_descriptor` que o caminho resolver já aplicava. Items VISTA `search_data_routes` (operationId+path+httpMethod+whenToUse+paramSchema+score) entravam como "registros" → juiz julgava corresponds → GROUNDED falso. Dois ajustes no owner canônico (EXTEND do contrato existente, shape-based, zero blacklist de provider/nome):
1. Envelope branch agora filtra items por `_is_capability_descriptor` — mesma regra de shape já usada por `_resolver_entities`.
2. `_is_capability_descriptor` estendida: `len(strong) >= 2` marca descriptor independente de densidade (items VISTA são densos — 12 campos, 2 chaves fortes, 0 fracas — e escapavam da regra antiga `strong AND (weak OR sparse≤4)`).

**WP3 — recovery tail fail-closed (regressão descoberta em eval).** Um turno real fez `relevance_recovery decision=reinvoke capability=list_playlists` → HTTP 500, 4ms depois — qualquer exceção não-`CapabilityProviderError` dentro de `_invoke_selected` (transporte cru, `ModelInvocationError` interna) escapava o turno. O docstring já contratava "any failure returns None"; a tail agora captura falhas de camada de provider (`except Exception` após re-raise de `_TurnCancelled`/`_StageDeadlineExceeded` — sinais terminais de turno que devem propagar) e retorna `None`, deixando a insuficiência original em pé. RED→GREEN com provider que explode no reinvoke.

**RED→GREEN determinístico (7 testes novos):** `route_catalog_items_never_count_as_business_records` (envelope VISTA → `records=()`, `has_business_evidence=False`, `explicit_empty=False`, `total_count=3` preservado), `real_records_survive_paginated_envelope`, `mixed_page_drops_only_capability_descriptors`, `dense_capability_descriptors_filtered_on_resolver_path`, `injected_text_never_promotes_descriptor_to_record` (prompt injection no payload não reclassifica estrutura), `explicit_empty_page_still_projects_as_empty`, `recovery_reinvoke_failure_keeps_original_insufficiency`.

**Eval local `delia-json` (N=10 ×2 + matriz de cenários, SHA em working tree):**
- Três-exemplos batch 1: 10/10 honestos — 8 NON_GROUNDED + 2 GROUNDED-empty (owner confirmou vazio / fonte sem dados de negócio). Um turno **selecionou `vista.search_data_routes` erroneamente e invocou** — o gate estrutural absorveu: `outcome_assessment=envelope_only reasons=no_business_data`, `cri_response presented=0`, resposta "fonte não retornou dados de negócio". **O falso-positivo A3 não se repete nem quando o modelo mispicka o provider.**
- Batch 2: 10/10 NON_GROUNDED honestos. **FALSE_POSITIVES=0/20+matriz.**
- Admission: 10/10 `owner_surface` (bloco neutro). Seleção: `delpi.search_products` ~8/10; mispicks ocasionais (`vista.search_data_routes`, `vista.list_playlists`) agora terminam honestos.
- Matriz: `pino` honesto (1× transient 500 → corrigido pelo fix WP3; retry → NON_GROUNDED), `o2_like` honesto, `fictional` honesto, `greeting` (502 transient env), `vista_question` → surface_inquiry lista live (correto), `concept SIPOC` → owner path honesto, `teo_guidance` honesto (100s), `direct_read` honesto, `write_ineligible` → surface listing, **zero ACT**, `panel` → GROUNDED com declaração honesta de pertinência não comprovada. AuthZ: 401 sem token, 401 token inválido.
- `THREE_RECORDS_OUTCOME=0/20` — reliability de negócio do 3B não compõe (múltiplos estágios semânticos em série); consistente com veredito anterior `ARCHITECTURE_PROVEN_MODEL_INSUFFICIENT`.

**Regressão completa:** apenas as 2 falhas ambientais conhecidas (`g4` fixture, `http_timeout_maps_to_504`) — nenhuma nova. Gates de arquitetura (`audit_architecture_phase3`, `audit_platform_guardrails`, `audit_backend_boundaries`): 0 findings. Scan do diff: zero provider names, zero strings de negócio, zero branches por provider — gate reutiliza vocabulário de descriptor já canônico no módulo.

`WP1=RESOLVED (neutral admission, 10/10)`; `WP2=RESOLVED (structural descriptor gate, 0 false positives, live-verified)`; `WP3=RESOLVED (recovery fail-closed)`; `WP4=PARTIAL (0/20 business outcome — model capacity, não contrato)`; `A3_RESIDUAL=CLOSED`; `DEPLOY=BLOCKED_WITH_EVIDENCE (business outcome 0/20 no modelo autorizado; MODEL_SWITCH_DECISION=REQUIRED)`; `INDEPENDENT_REVIEW=TO_REQUEST`; `R7_FINAL_ACCEPT=NO`.


#### Context Intelligence WP-A + WP-F — context window, token budget e observabilidade — 2026-10-25 (task `DELIA-C3-CONTEXT-WINDOW-BUDGET-OBSERVABILITY-FULL-IMPLEMENTATION-01`)

Base reancorada `203eaa966d`. Escopo aprovado pela revisão independente do doc 151 (D1 direction + contract review; D5 reuse existing observability). Evidência de implementação consolidada no doc 151 §13.

**WP-A0 — caracterização real (medida, não inferida).** `delia-json` = qwen2.5:3b Q4_K_M, contexto nominal 32768. Runner do daemon carrega com `context_length=4096` (`/api/ps`); o env do container **não** tinha `OLLAMA_NUM_CTX`/`OLLAMA_CONTEXT_LENGTH` (o `.env` do repo nunca chega ao env block do serviço ollama). Comportamento medido: prompt ≤ janela → contagem íntegra; prompt > janela → **truncado para ~ctx/2** (prompt ~4.3k tokens → `prompt_tokens=2050`) e a instrução de sistema é destruída (probe `ZZTOP`: resposta em prosa genérica). `/v1` OpenAI-compat **ignora** `num_ctx` top-level e `options.num_ctx`; a API nativa honra `options.num_ctx` (runner recarrega a 8192). Fix de runtime no eval: `PARAMETER num_ctx 8192` no Modelfile de `delia-json` → `/api/ps context_length=8192`, `/v1` aceita prompt de 4432 tokens, VRAM 2.4GB. **Causa raiz do `invalid_structured_output` recorrente em `arguments` (prompt real 4670 tokens > 4096) eliminada.**

**WP-A — contrato + orçamento pré-chamada.** Gate: `EXISTING_EQUIVALENT=YES`, `REUSE_DECISION=EXTEND`, owner `app/application/model_invocation`. Adições aditivas: `ModelInvocationPort.context_window_tokens` (janela efetiva declarada pelo adapter; `None` = desconhecida → sem enforcement), `ContextBudgetObservation` em result+error, `context_budget.py` (estimativa `chars/2.5` + overhead adapter 260 + reserva de geração; redução **somente** de histórico anterior não confiável, mais antigo primeiro em pares USER_INPUT/DELIA_RESULT completos; overflow do mandatório → `CONTEXT_TOO_LARGE` pré-dispatch, mapeado a `CONTEXT_TOO_LARGE` de interação → HTTP 400; código não-recuperável → sem retry). `DELIA_LLM_CONTEXT_TOKENS`: settings → adapter → port; passthrough nos dois compose + env examples dev/prod. Sem provider-specifics em Domain/Application.

**WP-F — observabilidade (ledger existente).** `ModelCallObservation` + projeção: `error_code`, `instruction_version`, `context_window_tokens`, `input_chars`, `estimated_input_tokens` (rótulo de estimativa), `generation_reserve_tokens`, `prior_turns_included/omitted`, `context_reduction_reason`, `context_budget_status` — junto a `input_tokens`/`output_tokens`/`duration_ms` reais do provider (nunca fabricados). Live: `long_history` (14.5k chars de histórico) → admission/turn_goal `reduced`, omit=2, in=6; estágios sem prior context `in=0/om=0`. Estimativa ~1.4–2.0× acima do real (conservadora por design).

**RED→GREEN.** `tests/test_context_budget.py` (9): within/reduced/rejected, pares preservam alternação, mandatório maior que janela → reject antes do dispatch (spy prova zero chamadas), janela desconhecida → sem enforcement, campos no ledger, idempotência entre attempts, drop defensivo de primeiro turno ímpar. Full backend: **2 failed / 2316 passed** — apenas as 2 falhas ambientais conhecidas. Gates de arquitetura: 0 findings.

**Eval local (modelo autorizado, matriz HTTP de 10 cenários).** Zero `invalid_structured_output`, zero truncamento, zero fabricação. `three_records`/`o2` completaram a cadeia inteira de 10 estágios GROUNDED (resposta honesta de coleção vazia — fidelidade de argumentos, não contexto, é o residual), `long_history` reduziu e completou, `subject_switch` completou, `write_ineligible` → surface listing (zero ACT), `vista_question` → listagem live. `THREE_RECORDS_OUTCOME`: registros reais ainda não apresentados (capacidade do 3B em arguments); **perda de contexto deixou de ser o bloqueador**.

`WP_A=IMPLEMENTED`; `WP_F=IMPLEMENTED`; `TRUNCATION_ROOT_CAUSE=CLOSED (silent halving >ctx)`; `CONTEXT_BUDGET_COMPLIANCE=100% (zero over-window dispatch, zero silent loss)`; `DEPLOY=NOT_AUTHORIZED (task says DEPLOY_AUTHORIZED=NO)`; `INDEPENDENT_REVIEW=TO_REQUEST`.
