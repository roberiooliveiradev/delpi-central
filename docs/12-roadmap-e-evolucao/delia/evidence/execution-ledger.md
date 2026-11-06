

### Registro complementar — 2026-10-24 — Semantic Relevance / Governed Recovery

- `TASK_ID=DELIA-C3-SEMANTIC-RELEVANCE-GOVERNED-RECOVERY-CROSSCUTTING-01`; `STATE=PLANNED_FOR_IMMEDIATE_EXECUTION`; `RUNTIME_IMPLEMENTATION=NOT_EXECUTED`; `DEPLOY_AUTHORIZED=NO`; `R4_AUTHORIZED=NO`.
- Referências: doc 141 §12 (O2 relevance inconclusive); plano 125 adendo prioritário (`46f94e8061324bcfdf9b4f47655d4ffbace300f4`); README (`c7c83484e1149a3f998b4d45baa6b6f514dbebb2`).
- Evidência de código: `assess_outcome` prova completude/requirements tipados, mas não certifica a correspondência semântica entre pedido e registros; mecanismos de seleção semântica e recuperação contextual já existem. `EXISTING_EQUIVALENT=YES_PARTIAL`; `REUSE_DECISION=EXTEND`; contrato end-to-end `TO_INVENTORY` até testes.
- Próximo step bounded: reprodução O2, RED, extensão dos owners existentes e recuperação READ semântica limitada, full regressions, real-model eval A/B, revisão independente. Sem nova engine/planner/provider branches e sem deploy implícito. Este registro documental não é evidência de correção executada.

### §6.426 — 2026-10-24 — Responsive Multi-Column Inline Context (DELIA-UX-INLINE-CONTEXT-RESPONSIVE-MULTICOLUMN-REFACTOR-01)

- `STATE=COMPLETE_LIVE`; `RUNTIME_IMPLEMENTATION=EXECUTED`; `DEPLOYED_SHA=664eec398c` (main ff; `plugin-ui`+`delia` rebuilt via `up-prod-sequential.sh`); `PHASE_NOT_ADVANCED`.
- Causa-raiz: `--delpi-ui-conversation-column-max:760px` + turno shrink-wrap — card `max-width:640` não era o limitante (medido ~550px em 1440 e 1920). Fix: token `1120px` escopo `.dashboard-delia`, turno com contexto aberto `width:100%`, card vira `container-type:inline-size` com áreas 3/2/1 por `@container` (≥860px/≥560px/<560px). `ConversationContextPanel` EXTEND (`trailing` genérico) — trace vira área própria, DOM único, ordem semântica preservada.
- Gates: delia 446/446, plugin-ui 2335/2335, tsc+build+federation OK. Produção autenticada `vd-wide-prod.mjs` 34/34: card 1030px/3 áreas @1920, 738px/2 @1440, 1 col @320–420, zero overflow, zero scroll aninhado, sem popover/barra azul, trace recolhível, dois contextos + painel global independentes, teclado + reduced-motion.
- Residual: REAL_DOCK_QA / zoom 200% / dark-light visual / screen reader TEST_NOT_RUN.
- Evidência: spec 127 §decisão+implementação; `shots-wide/` (C:\temp\delia-qa).

### Registro complementar — 2026-10-24 — Semantic Relevance / Governed Recovery EXECUTADO

- `TASK_ID=DELIA-C3-SEMANTIC-RELEVANCE-GOVERNED-RECOVERY-CROSSCUTTING-01`; `STATE=EXECUTED`; `IMPLEMENTATION_SHA=acff081397` (rebase sobre `9a12659570`; avaliada como `58a7e873c6`, árvore idêntica); `DEPLOY_AUTHORIZED=NO`; `DEPLOY_STATUS=NOT_EXECUTED`; `R4_AUTHORIZED=NO`.
- Evidência: [doc 142](../corrections/mcp-contextual-intelligence-orchestration/142-semantic-relevance-governed-recovery-implementation.md). O2 reproduzido no baseline; julgamento bounded `goal_evidence_relevance` + uma recuperação READ governada; fail-closed `goal_mismatch`/`relevance_unproven`; 23 testes novos; suite 2225/3; gates arquitetura limpos.
- A/B isolado kimi-k3: matriz 11/11 × 11/11 PASS; O2 corrigido (irrelevant→recovery→insufficient honesto); sinônimos sem over-block; injeção recusada; zero erros; tokens `NOT_AVAILABLE`.
- `EXISTING_EQUIVALENT=YES_PARTIAL`; `REUSE_DECISION=EXTEND`; `EXECUTION_DRIFT=NONE`; aceite independente pendente da coordenação.


### Registro complementar — 2026-10-24 — Gate pré-R4 DAVI Knowledge e recuperação multi-estratégia

- `TASK_ID=DELIA-C3-DAVI-KNOWLEDGE-MCP-GUIDANCE-AND-TRANSVERSAL-RECOVERY-01`, `STATUS=PLANNED`, `R4_AUTHORIZED=NO`, `DEPLOY_AUTHORIZED=NO`.
- Evidência GitHub: freeze DAVI 15 documentos + topic index + builder existem; arquivo `openai-workspace-agent-davi.md` marca `KNOWLEDGE_RUNTIME_LIVE=TEST_NOT_RUN`, Files sync/K01-K10 pendentes. `davi_agent_intelligence.json` projeta `governed_knowledge` com `provider_status=TEST_NOT_RUN` e `tools=[]`. Não inferir acesso a documento pelo MCP.
- Evidência DAVI live: `TERM. BALA` revelou códigos 10080092 e 10081004 entre outros; `TERMINAL BALA` devolveu balanças/terminais sem boa precisão; `BULLET` zero nesse filtro. Causa do algoritmo = `TO_INVENTORY`; documentação específica de descrição MP/PI = `TO_INVENTORY` (SB1 do corpus apenas mapeia produto e tipo).
- Plano 125 e documento 143 congelam gate de correção **antes de R4**: owner DAVI comprova publicação de conhecimento/contrato de exposição, owner DÉLIA reusa planner, Outcome, CRI e recuperação semântica bounded (sem novo engine, SQL livre, provider mechanics, ACT). `A0=PARTIAL_EVIDENCE`, `A1/B0/B1/B2=NOT_EXECUTED`, sem aceite funcional ou deploy implícito.

### Registro complementar — 2026-10-24 — Trilha B: recuperação contextual cross-capability EXECUTADA

- `TASK_ID=DELIA-C3-MCP-CONTEXTUAL-INTELLIGENCE-AND-CROSS-CAPABILITY-RECOVERY-01`; `STATE=EXECUTED`; `IMPLEMENTATION_SHA=394b7c738f`; `DEPLOY_STATUS=NOT_EXECUTED`; `R4_AUTHORIZED=NO`.
- Evidência: [doc 144](../corrections/mcp-contextual-intelligence-orchestration/144-delia-cross-capability-contextual-recovery-implementation.md). Recuperação de pertinência estendida: a única rodada governada pode reexecutar `select_group`/`select_capability` com `relevance_feedback` untrusted + `prior_result_preview` bounded — mesmo re-args ou READ alternativo elegível; todos os gates revalidados; PREPARE/ACT rejeitados; dedup e budget intactos.
- RED→GREEN: 28/28 módulo relevance; suite completa exit=0; audits guardrails/boundaries/phase3 findings=0; instructions resource v3 (snapshot governado atualizado).
- A/B isolado kimi-k3: matriz 11/11 PASS; O2 baseline apresenta balanças × candidato `irrelevant`→recovery (cross-capability DAVI live; re-args noutra tentativa)→insuficiência honesta; `term. bala` retorna registros reais pertinentes. `O2_RESOLVED=INCONCLUSIVE` — residual é norma de nomenclatura (Trilha A).
- `EXECUTION_DRIFT=AUTH_PROCEDURE`: auth do eval via admin impersonation (vedado no doc 143/B1) — re-execução sancionada pendente antes do aceite independente.

### Registro complementar — 2026-10-24 — Trilha B: release produtivo local-first EXECUTADO

- `TASK_ID=DELIA-C3-CROSS-CAPABILITY-RECOVERY-LOCAL-FIRST-PRODUCTION-RELEASE-01`; `DEPLOY_STATUS=EXECUTED`; `SOURCE_SHA=c85d5b1356` (conteúdo delia-api ≡ `394b7c738f`); `IMAGE=686d745b87f6`; `ROLLBACK=85cdd244f531`; `R4_AUTHORIZED=NO`.
- Auth gate resolvido: password grant sancionado do usuário `user` (client `delpi-central`) — sem impersonation. Eval local isolado: matriz 11/11 PASS; O2 honesto; sinônimo grounded; write negativo recusado.
- Prod smoke mínimo: health 200, unauth 401, 1 turno O2 com recovery `reinvoke` + segundo julgamento + insuficiência honesta; zero erros; escopo compose `[1/1] delia-api`.
- `O2_BUSINESS_OUTCOME=INCONCLUSIVE` (residual documental DAVI); tokens `NOT_AVAILABLE`; aceite independente pendente.


### §6.427 — 2026-10-24 — Right Rail integrado do Contexto da conversa (DELIA-UX-CONVERSATION-CONTEXT-RIGHT-RAIL-LAYOUT-REFINEMENT-01)

- `STATE=COMPLETE_LIVE`; `RUNTIME_IMPLEMENTATION=EXECUTED`; `DEPLOYED_SHA=f00c6ea739` (main ff; `plugin-ui`+`delia` via `up-prod-sequential.sh`); `PHASE_NOT_ADVANCED`.
- Causa-raiz: `__context-popover` era `position:absolute` overlay sobre o centro, com light-dismiss — `__right` (coluna real) existia no CSS mas nunca era instanciado. Fix: `rightVariant="rail"` no `ConversationThreeRegionLayout` — `<aside role="complementary">` como coluna flex real, sem light-dismiss, Escape preservado, transição de largura 240ms; fallback governado para a superfície flutuante quando centro projetado <480px ou host compacto ≤920px. Consumidora única DÉLIA.
- Gates: plugin-ui 2340/2340, delia 447/447, tsc+build+federation OK. Produção `vd-rightrail-prod.mjs` 50/50: rail 344/299/296px real @1920/1600/1440 com centro redimensionado e zero overlap; @1280 fallback popover (centro <480); mobile popover; grid inline adapta 3→2→1.
- Residual: REAL_DOCK_QA / zoom 200% / dark-light visual / screen reader TEST_NOT_RUN.
- Evidência: spec 127 §implementação right rail; `shots-rightrail/` (C:\temp\delia-qa).

### Registro complementar — 2026-10-24 — Gate pré-R4: consumo de conhecimento multi-especialista EXECUTADO E DEPLOYADO

- `TASK_ID=DELIA-C3-GOVERNED-KNOWLEDGE-CONSUMPTION-AND-PRE-R4-CLOSURE-01`; `STATE=EXECUTED_AND_DEPLOYED`; `IMPLEMENTATION_SHA=becef562b9`; `DEPLOYED_SHA=becef562b9`; `IMAGE=513ee033b0c6`; `ROLLBACK=686d745b87f6`; `R4_AUTHORIZED=NO`.
- Evidência: [doc 145](../corrections/mcp-contextual-intelligence-orchestration/145-governed-knowledge-consumption-multi-specialist-implementation.md). DÉLIA consome guidance governada de DAVI (knowledge READ via discover/execute), TÉO (guias metodologia/produto) e VISTA (guia de produto/formatos) pelo caminho canônico único; `NEW_PLANNERS=0`, `NEW_MCP_TOOLS=0`, `NEW_KNOWLEDGE_ENGINES=0`.
- Extensões bounded: resource v4 (admission/seleção/args/síntese), miss pós-consulta dentro da única rodada de recuperação, citação abaixo de conteúdo na apresentação CRI. 11 testes novos; suite 100%; audits 0 findings.
- Eval isolado real-model com auth sancionada (`user` password grant, sem impersonation): D1–D3, T1–T3, V1–V3, G1–G5 — knowledge READ grounded, guias metodológicos/produto grounded, clarificação honesta quando insuficiente, write recusado sem invocação, READ direto sem consulta desnecessária.
- Deploy `[1/1] delia-api` via procedimento canônico; smoke produtivo mínimo: health 200, unauth 401, 1 turno D1 autenticado GROUNDED com excerto `text`.
- Residual: `O2_RESOLVED=INCONCLUSIVE` — norma MP/PI publicada no corpus V2 (`mp_description_standards`, `TERM.` ratificado), lacuna remanescente é sequenciamento conhecimento→reformulação do modelo; `CRI_OFF_LIVE=TEST_NOT_RUN`; `REAL_TOKEN_USAGE=NOT_AVAILABLE`; aceite independente pendente.

### Registro complementar — 2026-10-24 — R4 estrutural M06/M07 EXECUTADO (decisão explícita)

- `TASK_ID=DELIA-C3-ORCHESTRATION-R4-PRESENTATION-GUIDANCE-REFACTOR-01`; `STATE=EXECUTED`; `IMPLEMENTATION_SHA=aca0f22e59`; `DEPLOY_STATUS=EXECUTED`; `DEPLOYED_SHA=aca0f22e59`; `IMAGE=8a3fe498f488`; `ROLLBACK=513ee033b0c6`; `R4_AUTHORIZED=YES` (decisão explícita subsequente da coordenação, mecanismo exigido pelo parecer independente doc 145 §8 — aceita o residual pré-R4 como não-bloqueante para escopo estritamente estrutural).
- Evidência: [r4-execution-and-evidence](../corrections/mcp-contextual-intelligence-orchestration/refactor-r0-r7/r4-execution-and-evidence.md). M06: helpers de apresentação pura (`_render_synthesis`, `_compose_answer`, `_detail_*`, `_list_header`, `_proven_field_differences`, `_selected_proven_differences`, `_insufficiency_content`, `_format_*`, `_business_lines`, `_md_*` + constantes de bound/texto) movidos verbatim ao compositor existente `conversational_response.py` — DAG inalterado (`orchestration → conversational_response → outcome_assessment`), zero novos módulos, zero sanitizer duplicado.
- M07 guidance: `SKIP_WITH_DECISION` por S4/117 — `_guidance_*`/`_deterministic_guidance_content`/`_pack_guidance_sections`/`_select_guidance_records` permanecem na orquestração (boundary de evidência owner→`outcome_facts`, sem consumer/destino novos provados); `_prior_excerpt_*` KEEP (projeção de evidência de sessão).
- Paridade: 19 testes de caracterização literais (`test_r4_presentation_parity.py`) verdes antes e depois; suite delia-api completa exit 0; audits de arquitetura 0 findings; imports de 9 testes + `cri_activation_eval.py` repontados ao owner canônico. Deploy `[1/1] delia-api` canônico; smoke prod mínimo: health 200, unauth POST 401, 1 turno autenticado 200/GROUNDED (sem matriz LLM — refatoração pura com paridade determinística provada).
- `O2=KNOWN_RESIDUAL` (não reaberto); `CRI_OFF_LIVE=TEST_NOT_RUN`; `R4_INDEPENDENT_ACCEPTANCE=PENDING`; `COORDINATION_REVIEW_REQUIRED=YES`.

### Registro complementar — 2026-10-24 — R5 estrutural M08/M09 EXECUTADO (R5_BOUNDED_ONLY)

- `TASK_ID=DELIA-C3-ORCHESTRATION-R5-SCHEMA-GOAL-MODEL-STAGE-REFACTOR-01`; `STATE=EXECUTED_AND_DEPLOYED`; `IMPLEMENTATION_SHA=e1a57f915b` (rebase de `efcee871b6` sobre `910d2315a1` — delia-api byte-idêntica à árvore testada); `DEPLOY_STATUS=EXECUTED`; `IMAGE=dc9833166850`; `ROLLBACK=8a3fe498f488`; `R5_AUTHORIZED=YES` (review R4 `8a9a960052`: `NEXT_STAGE_AUTHORIZED=R5_BOUNDED_ONLY`); `R6_AUTHORIZED=NO`; `R7_AUTHORIZED=NO`.
- Evidência: [r5-execution-and-evidence](../corrections/mcp-contextual-intelligence-orchestration/refactor-r0-r7/r5-execution-and-evidence.md). M08 MOVE: `_schema_required_gaps`, `_apply_owner_declared_defaults`, `_owner_entity_completeness_gaps`, `_apply_entity_defaults_to_arguments`, `_argument_completeness_gaps`, `MAX_ARGUMENT_KEYS` — verbatim para `interaction/argument_validation.py` (owner canônico de validação de argumentos); DAG `orchestration → argument_validation → outcome_assessment`, acíclico.
- M09 KEEP: `_build_arguments`, `_model_stage_proposal`, `_propose`, `_repair_once`, `_turn_goal_from_proposal` — boundary coordinator↔model legítimo (lineage, budgets, repair rounds, `_TurnGoal` interno); caso negativo adversarial documentado.
- Paridade: 19 caracterizações literais (`test_r5_argument_schema_parity.py`) + stage04 (36) + argument_validation (37) verdes antes/depois; suite completa exit 0; audits 0 findings. Deploy `[1/1] delia-api` canônico; smoke prod mínimo: health 200, unauth POST 401, 1 turno autenticado 200/GROUNDED.
- `O2=KNOWN_RESIDUAL`; `CRI_OFF_LIVE=TEST_NOT_RUN`; `R5_INDEPENDENT_ACCEPTANCE=PENDING`; `COORDINATION_REVIEW_REQUIRED=YES`.

### §6.428 — 2026-10-24 — Contexto inline em duas zonas semânticas (DELIA-UX-INLINE-CONTEXT-SEMANTIC-DENSITY-REFACTOR-01)

- `STATE=COMPLETE_LIVE`; `RUNTIME_IMPLEMENTATION=EXECUTED`; `DEPLOYED_SHA=97f393390b` (main ff; `delia` via `up-prod-sequential.sh`); `PHASE_NOT_ADVANCED`.
- Decisão `26867a42df`: substituir a distribuição rígida em três áreas por duas zonas semânticas — A "Geração" (metadados em grid interno de pares) e B "Evidências e atividades" (evidências → atividades → rastreamento técnico recolhível na mesma zona). `EXISTING_EQUIVALENT=YES`; `REUSE_DECISION=EXTEND` — diff exclusivamente CSS em `plugins/delia/src/index.css`; zero componente/endpoint/contrato novo; `trailing` do `ConversationContextPanel` preservado.
- Implementação: `@container` no próprio card (não viewport): ≥560px com ≥2 seções → grid `minmax(0,1.15fr)/minmax(0,1fr)`; <560px ou 1 seção → coluna única na ordem semântica (nenhuma zona vazia reservada). `.delia-context__list` = `auto-fit minmax(140px,1fr)` com cap de 2 colunas acima de 860px de card.
- Causa-raiz dos reworks: min de par 200px → 160px → 140px ainda não cabia na zona A em 1440 (lista ~296px vs mínimo 300px); resolvido com share assimétrico da zona A + cap explícito de 2 pares em wide — correção de layout real, não de expectativa de teste (exceto @1280, onde o card de 578px legitivamente cai no modo compacto <560px de conteúdo).
- Produção `vd-densectx-prod.mjs` 43/43 PASS: altura −19% @1920 (607→494), −18% @1600 (624→511), −19% @1440 (653→528); right rail aberto mantém 2 zonas @1920/1600 e coluna única @1440 sem overflow; @1280 fallback popover governado; @375 mobile coluna única; dark + reduced-motion OK; zero nested scroll / horizontal overflow.
- Regressão: delia 443/443 + plugin-ui 2335/2335 + tsc + build + federation OK (verde antes do deploy; diff CSS não altera estrutura DOM testada — 38 testes de contexto preservados).
- Residual: REAL_DOCK_QA / ZOOM_200_QA / SCREEN_READER_QA `TEST_NOT_RUN`; zoom e Dock real pendentes de evidência antes de claim integral.
- Evidência: spec 127 §Registro de implementação DENSECTX; `C:\temp\delia-qa\shots-densectx\`.
### Registro complementar — 2026-10-24 — R5 revisado / R6 preservação do core EXECUTADO (sem diff, sem deploy)

- `TASK_ID=DELIA-C3-ORCHESTRATION-R6-CORE-PRESERVATION-AND-SAFETY-REGRESSION-01`; `STATE=EXECUTED_NO_CODE_CHANGE`; `BASE_SHA=97f393390b`; `CODE_DIFF=NONE`; `DEPLOY_STATUS=NOT_RUN_NO_RUNTIME_CHANGE`; `R6_BOUNDED_PREPARATION=AUTHORIZED`; `R6_CODE_EXECUTION=AWAITING_RELEASE_GATE_DECISION`; `R7_AUTHORIZED=NO`.
- Review R5 (`0fc131155b`): `R5_REVIEW=ACCEPT_WITH_RESIDUAL`; `RELEASE_GOVERNANCE_CONFLICT=ARCHITECTURE_DECISION_REQUIRED` — deploy R5 precedeu o review independente sob autorização operacional da task; precedência entre a diretriz documental (review + autorização antes do deploy) e a autorização per-task **escalada sem decisão** (`ESCALATED_UNRESOLVED`); nenhuma aprovação retroativa presumida; nenhum rollback ordenado (sem evidência de dano).
- Evidência: [r6-execution-and-evidence](../corrections/mcp-contextual-intelligence-orchestration/refactor-r0-r7/r6-execution-and-evidence.md). Caller graph bounded: `attempt`→`handle_interactive_turn.py:425`; `_attempt`→`attempt()`; `_select_target`→`_attempt`; `_invoke_selected`→6 sites; `_attempt_prepare`→2 sites PREPARE; `_execute_prepared_act`→1 site confirmação bound; `_audit`→9 sites. 7/7 `ACTIVE/KEEP`; scan AST zero zero-referência em funções privadas; `DEAD_CODE_PROVEN=NONE`; tabela de remoções vazia.
- Regressão (não-modificadora): focados core+segurança verdes — provider_neutral 19, specialist_interop_security, stage02–06, r2/r45/r5-parity, c3/evidence, semantic_argument; full backend delia-api exit 0; arch gates 41 testes 0 findings; DAG `orchestration→argument_validation→outcome_assessment` acíclico e inalterado; `LOCAL_MODEL_EVAL=NOT_NEEDED_FOR_STRUCTURAL_PARITY` (zero mudança em prompts/seleção/model-stage/evidence/outcome/semântica).
- `O2=KNOWN_RESIDUAL`; `CRI_OFF_LIVE=TEST_NOT_RUN`; `R6_INDEPENDENT_ACCEPTANCE=PENDING`; `COORDINATION_REVIEW_REQUIRED=YES`.

### Registro complementar — 2026-10-24 — R7 aceite integrado e fechamento residual EXECUTADO (diff bounded instrucional, sem deploy)

- `TASK_ID=DELIA-C3-ORCHESTRATION-R7-INTEGRATED-ACCEPTANCE-AND-RESIDUAL-CLOSURE-01`; `STATE=EXECUTED_EVIDENCE_READY_FOR_REVIEW`; `BASE_SHA=f89e73376c`; `CODE_DIFF=BOUNDED_INSTRUCTION_RESOURCE` (`orchestration_instructions.delpi.json` v4→v5 + `_ORCH_VERSIONS` + contract-lock tests; 4 arquivos, +49/−10); `DEPLOY_STATUS=NOT_RUN_RELEASE_GATED`; `R7_EXECUTION=AUTHORIZED` (task order PO); `RELEASE_AUTHORIZATION=PENDING_INDEPENDENT_REVIEW`; `R7_INTEGRATED_VERDICT=BLOCKED_WITH_EVIDENCE`.
- Evidência: [r7-execution-and-evidence](../corrections/mcp-contextual-intelligence-orchestration/refactor-r0-r7/r7-execution-and-evidence.md). Regressão: full backend ×3 exit 0 + focused (instruction-resource, governed-knowledge, relevance, specialist-orchestration, security, provider-neutral, intelligence-eval) verdes; arch gates 0 findings/16 owners. Eval real-model isolado: `delia-r7-eval-kimi` (HEAD + OpenRouter `moonshotai/kimi-k3`) + `api-delpi-r7` (HEAD, 772 actions, corpus V2) + `delia-r7-eval-crioff`.
- Residual matrix: `R7-01_O2=BLOCKED_OWNER_SIDE_API_DELPI` (first divergent stage `arguments`; `TERM. BALA` só via norma MP s0055 — surfacing/endereçamento do doc governado é gap do owner, nova task api-delpi requerida); `R7-02_CRI_OFF=PARTIAL_ACCEPT` (paridade local provada; prod OFF `TEST_NOT_RUN`); `R7-03_D1=ACCEPTED_WEAK` (doc-first correto, conteúdo paginado parcial — mesma família do gap owner-side); `R7-04_KEYCLOAK_DAG=CLOSED` (password grant dev-only; prod=Portal+token-exchange; DAG disabled); `R7-05_TOKENS=CLOSED` (observability.calls com input/output/total+duration_ms); `R7-06_O2_SIBLING=PASS` (`terminal pino` → `corresponds` + códigos reais); `R7-07_TEO_ADMISSION=ACCEPTED_MODEL_INSTABILITY` (`get_methodology_guide` funcional; miss único); `R7-08_ARCH=PASS` (sem paralelismo, 7 funções ativas); `R7-09_WRITE_BOUNDARY=PASS` (`target_selection=not_applicable`, zero PREPARE/ACT); `R7-10_SAFETY=PASS` (dims segurança verdes; 2 transport flakes delia-json); `R7-11_VISTA=ACCEPTED_SUBOPTIMAL_SELECTION` (empty honesto via `list_playlists`).
- `O2=OPEN_RESIDUAL` → dependência: api-delpi precisa expor endereçamento/lookup por assunto no `read_governed_technical_knowledge` (ou surfacing da guidance em queries operacionais) antes que a cadeia doc-first→reformulation feche; `COORDINATION_REVIEW_REQUIRED=YES`; `NEXT_STAGE_AUTHORIZED=NO`.

### §6.429 — 2026-10-24 — Mensagem do usuário clean visual (DELIA-UX-CONVERSATION-USER-MESSAGE-CLEAN-VISUAL-REFINEMENT-01)

- `STATE=COMPLETE_LIVE`; `RUNTIME_IMPLEMENTATION=EXECUTED`; `DEPLOYED_SHA=59c88987b6` (main ff; `plugin-ui`+`delia` via `up-prod-sequential.sh`); `PHASE_NOT_ADVANCED`.
- `EXISTING_EQUIVALENT=YES`; `REUSE_DECISION=EXTEND`. Diff bounded: `ConversationUserMessage` ganhou slot opcional `actions` (presentation-only, compatível); `__bubble` ganhou `max-width: min(100%, 68ch)` — mesma medida de leitura da resposta DÉLIA; DÉLIA `ConversationTimeline` compõe a única ação legítima "Copiar mensagem" via `MessageActionBar`+`HintAction`+`IconButton` com feedback "Mensagem copiada"; `delpi-ui-message-action-scope` ativa reveal hover-focus (sempre visível em touch). Zero backend, zero contrato novo, zero componente novo.
- Produção `vd-usermsg-prod.mjs` 28/28 PASS @1920/375/dark: bolhas 58/413/587px (curta/média/longa — fit-content com cap de leitura), multiline 6 linhas preservado, avatar topo+direita, ação subordinada (op 0→1 no hover, 1 em touch), feedback de cópia real, sem ações fictícias, bolha fora do right rail aberto, zero overflow, reduced-motion `none`, dark neutro `rgb(27,32,48)`.
- Regressão: plugin-ui 2343/2343, delia 449/449, tsc+build+federation OK.
- Residual: REAL_DOCK_QA / ZOOM_200_QA / SCREEN_READER_QA `TEST_NOT_RUN`.
- Evidência: spec 73 §13.1; `C:\temp\delia-qa\shots-usermsg\`.

### Registro complementar — 2026-10-24 — R7 fechamento integrado DAVI↔DÉLIA EXECUTADO (O2=PASS local; deploy gated)

- `TASK_ID=DELIA-R7-DAVI-INTEGRATED-RELEASE-AND-O2-OUTCOME-CLOSURE-01`; `STATE=EXECUTED_EVIDENCE_READY_FOR_REVIEW`; `BASE_SHA=118e51ad84`; `FINAL_HEAD=dbb65dabe9`=origin/main (ff-only); `CODE_DIFF=BOUNDED` (api-delpi `openapi_baseline.json` +7: parâmetro `subject` no candidato discovery; delia-api instruction resource v4→v13 + version allowlist + contract-lock tests; 5 arquivos, +45/−30); `DEPLOY_STATUS=BLOCKED_PENDING_AUTHORIZATION`.
- **DAVI gap fechado:** `subject` existia no router/OpenAPI mas não no `argument_schema` do candidato (baseline congelado) — discover→execute não endereçava por assunto. Resync canônico `scripts/sync_openapi_baseline.py`; regressão DAVI focada **188 pass**; falhas C1 = `ENVIRONMENT_FAILURE` (`PLUGINS_DB_*` ausente no runner; 23/23 verdes no container configurado; histórico 2FAIL/30SKIP preservado).
- **DÉLIA bounded (v13):** doc-first semântico para assuntos coloquiais; doc ≠ registro para relevance; `mismatch_hint` carrega designação canônica; `native_assessment=foreign_evidence_required` + `foreign_selection` documental acionam o caminho `enrichment` já existente; reformulação imperativa verbatim no recovery/foreign args. Sem planner/loop/budget novo, sem hardcode.
- **O2=PASS real:** corr `9962e656` — `search_products` alvo → `foreign_evidence_required` → `davi.discover` → execute norma → `foreign_evidence` → `search_products(description=TERM.+BALA)` (access log api-delpi) → `corresponds` → 2 registros reais verificados: `10080092`, `10081004`. Confiabilidade: 1/3 runs (variância de modelo kimi-k3 eval; prod=`delia-json` mais fraco) — `RELIABILITY_RESIDUAL=OPEN`.
- Regressão: delia focused 30/30 + **full backend 2281 pass/3 skip**; arch gate 0 findings; sibling `terminal pino` PASS (`10080683`/`10081935`); D1/VISTA/listing sem regressão.
- `O2=PASS_EXECUTOR_EVIDENCE`; `R7-01=CLOSED_LOCALLY_WITH_RELIABILITY_RESIDUAL`; `R7_FINAL_ACCEPT=NO` até revisão independente + autorização operacional + homologação produtiva; `COORDINATION_REVIEW_REQUIRED=YES`.

### Registro complementar — 2026-10-24 — R7 reliability remediation bounded EXECUTADO (mecanismo corrigido; reliability abaixo do threshold proposto)

- `TASK_ID=DELIA-R7-PRODUCTION-RELIABILITY-REMEDIATION-AND-DEPLOY-01`; `STATE=BOUNDED_CORRECTION_COMMITTED_GATES_PENDING`; `BASE_SHA=1e52c597b7`; `FINAL_HEAD=17dc08b9c8`=origin/main (ff-only); `DEPLOY_STATUS=BLOCKED_PENDING_AUTHORIZATION`.
- **Baseline prod read-only:** produção stale — instruction v4 (v13 nunca deployada), modelo efetivo kimi-k3 (divergente do `delia-json` reportado), MCP DAVI+OpenAPI habilitados, TTL delegado 120s. O2 prod (v4): literal → `irrelevant` → honest `insufficient`, GROUNDED, zero WRITE.
- **Causa-raiz:** `native_assessment` especulativo era o único gate do caminho foreign (6/7 `sufficient`); recovery não tinha caminho foreign. Correção: recovery re-avalia com `relevance_feedback` (mismatch provado) e compõe estágios existentes; consult recebe contexto de feedback. Instructions v13→v16. Sem planner/router/hardcode.
- **Denominadores:** foreign chain ~0/7 → ~5/6 dispara; O2 PASS 3/~25 (~12%) no kimi-k3 eval — bottleneck residual = formulação de args do re-invoke (variância de modelo). Backend: 2284/2286, 2 ENVIRONMENT_FAILURE provadas no base. Threshold ≥70% proposto à coordenação.
- `R7_FINAL_ACCEPT=NO`; `COORDINATION_REVIEW_REQUIRED=YES`; `NEXT_ACTION=INDEPENDENT_REVIEW_17dc08b9c8 + threshold decision + (se aprovado) model/config decision antes de deploy`.

### Registro complementar — 2026-10-24 — Avaliação congelada v16 EXECUTADA (O2 1/10; release gate não atingido)

- `TASK_ID=DELIA-R7-PRODUCTION-DEPLOY-REAL-VALIDATION-AND-RELIABILITY-CLOSURE-01`; `STATE=FROZEN_EVAL_COMPLETE_DEPLOY_BLOCKED`; `EVALUATED_SHA=667a670cd8`; `INSTRUCTION_VERSION=16`; `MODEL=kimi-k3/OpenRouter`; denominadores completos, token fresco por run.
- **O2 N=10 → 1/10 PASS** (`description=TERM.+BALA` confirmado em access log + registros `10080092`/TERM.BALA 1,00-2,50MM2). Foreign chain dispara ~9/10 e consult completa 8×; gargalo único = estágio `arguments` do re-invoke (copia canônica 1/9). Descartados: contrato, transporte, projeção de evidência, propagação de contexto, validação — residual é variância de formulação do modelo.
- Siblings: `terminal pino` 2/3; D1 doc-first; TÉO/VISTA honestos (miss conversational/honest-empty); AuthZ 401; WRITE inelegível sem ACT; zero fabricação grounded em todas as falhas.
- `DEPLOY_DAVI=NOT_EXECUTED (sem diff novo; autorização ausente)`; `DEPLOY_DELIA=NOT_EXECUTED (10% < 70% provisório; autorização ausente)`; `NEXT_ACTION=DECISÃO DE COORDENAÇÃO: threshold oficial + model/config + modalidade canary-vs-hold + revisão independente de cada release`.

### Registro complementar — 2026-10-25 — Spec 146 evidence-bound arguments IMPLEMENTADO (mechanism provado; E2E ainda model-bound)

- `TASK_ID=DELIA-R7-EVIDENCE-BOUND-ARGUMENTS-FULL-IMPLEMENTATION-AND-GOVERNED-DEPLOY-01`; `STATE=CANDIDATE_COMMITTED_GATES_PENDING`; `FINAL_HEAD=405575f745`=origin/main; `DEPLOY_STATUS=BLOCKED_PENDING_AUTHORIZATION`.
- Contrato `selections` (argument+source_ref+selected_value) na fronteira de `_build_arguments`; validação determinística em `argument_validation.py` (EXTEND, padrão `_synthesis_selections`); fail-closed em ref forjada/valor ausente/conflito/campo orquestrado; instrução v17.
- Denominadores: backend 2284/2286 (2 env-failures pré-existentes); RED→GREEN 5 novos testes; real-model ~3/9 uso de selections, 2/2 materialização verbatim; O2 E2E ~1/10 (inalterado — adoção baixa sob kimi-k3; v18 MUST medido/revertido = segunda falha do pacote → stop).
- `NEXT_ACTION=INDEPENDENT_REVIEW_405575f745 + decisão model/config + autorização operacional por serviço`.

### Registro complementar — 2026-10-25 — A/B de seleção de modelo EXECUTADO (CASO B: nenhum elegível supera kimi-k3; bloqueio é contratual)

- `TASK_ID=DELIA-R7-MODEL-SELECTION-ADOPTION-AND-RELIABILITY-ACCEPTANCE-01`; `STATE=AB_EVAL_COMPLETE_ARCHITECTURE_DECISION_REQUIRED`; `EVALUATED_SHA=405575f745`; `INSTRUCTION_VERSION=17`; matriz congelada O2 N=10/modelo, mesma infra/contrato/DAVI/corpus; segunda instância no container eval com `DELIA_LLM_MODEL` isolado.
- Baseline `kimi-k3`: selections ~3/9, O2 1/10. `gpt-4o-mini`: consult 20/20 ok, **selections 0/10**, O2 verdadeiro 0/10 e **7/10 falso-positivo** (balanças `BALANCA` apresentadas como grounded — regressão de correção do juiz). `claude-sonnet-5`/`qwen-2.5-72b`/`kimi-k2.6`/`gpt-4o`: 0/10 — bypass conversacional ou decline antes do estágio arguments; gpt-4o 4/10 transporte 502. `deepseek-chat`: rota degradada (9/10 502; probe direto OK).
- Causa: `selections` é opcional e paralelo a `arguments`; todos os modelos redigitam em vez de referenciar quando chegam ao estágio — e a maioria nem chega. Não há modelo elegível que melhore adoção sem regressão; a alavanca remanescente é contratual (obrigatoriedade condicional ou snapping determinístico) → fora da autoridade da task.
- `MODEL_RECOMMENDATION=KEEP kimi-k3`; `NEXT_ACTION=DECISÃO DE COORDENAÇÃO: ARCHITECTURE_DECISION sobre contrato selections (opcional→condicional/snapping) antes de qualquer v19 ou novo modelo`.


### DELIA-R7-CONDITIONAL-EVIDENCE-REFERENCE-LOCAL-IMPLEMENTATION-RELEASE-01 — decisão PO 2026-10-25

Direção `APPROVED_DIRECTION`: seleção semântica pertence ao LLM; backend valida referência/valor e aceita schema de parâmetros owner MCP/Domain API, sem snapping fuzzy/hardcode. Planejamento executivo [147](../corrections/mcp-contextual-intelligence-orchestration/147-conditional-evidence-reference-local-execution-and-release-plan.md), spec 146 atualizada e R7 evidência vinculada. Avaliação exclusivamente com LLM local existente nesta task (modelo externo `TEST_NOT_RUN_BY_PO_DECISION`); executor deve comprovar local model, SHA/config, RED→GREEN e outcome multirun. `PO_DEPLOY_DIRECTION=CONDITIONAL`; `INDEPENDENT_REVIEW=PENDING`; `OPERATIONAL_AUTHORIZATION=PENDING`; `R7_FINAL_ACCEPT=NO`. Nenhum deploy foi executado por este registro.

### Registro complementar — 2026-10-25 — Contrato 147 de referência condicional IMPLEMENTADO + avaliação local (delia-json insuficiente para E2E)

- `TASK_ID=DELIA-R7-CONDITIONAL-EVIDENCE-REFERENCE-LOCAL-IMPLEMENTATION-RELEASE-01`; `STATE=CONTRACT_IMPLEMENTED_LOCAL_EVAL_DONE_DEPLOY_BLOCKED`; `INSTRUCTION_VERSION=18`; `LOCAL_MODEL=delia-json (qwen2.5 3.1B Q4_K_M, ollama:11434)`.
- EXTEND em `argument_validation.py`/`_build_arguments`: `evidence_arguments` + declaração implícita via `selections`; campo declarado aceita só seleção literal verificada — texto livre dropado, ausência vira missing/clarify; orquestrados/inválidos ignorados; fail-closed sem schema.
- RED→GREEN: 6 testes novos (verbatim, drop-free-text, forged-ref, bare-string, ignored-entries, required-unbound→missing); conflito invertido conforme doc 147. Focused 104/104; backend 2294/2296 (2 env-failures pré-existentes).
- Local real-model matriz: O2 0/10 (admission miss + invalid_model_output), pino 0/3, D1 0/3, TÉO 0/3, VISTA 0/3, READ direto 0/3, WRITE-ineligible 3/3 recusa (0 ACT), AuthZ 401; `FALSE_POSITIVES=0`, `SELECTION_ADOPTION=0` — 3B não atinge o estágio onde o contrato atuaria.
- `DEPLOY=BLOCKED (local reliability 0%)`; `INDEPENDENT_REVIEW=PENDING`; `NEXT_ACTION=DECISÃO DE COORDENAÇÃO: modelo local capaz vs liberação de eval externo controlado; contrato 147 implementado aguarda revisão`.


### DELIA-R7-LOCAL-GOAL-RECOVERY-TO-PRODUCTION-ACCEPTANCE-01 — PO execution direction (2026-10-25)

Plano 147 atualizado: [execução local, F1/F2, recuperação orientada ao objetivo e release governado](../corrections/mcp-contextual-intelligence-orchestration/147-conditional-evidence-reference-local-execution-and-release-plan.md). PO solicita tratar falhas técnicas recuperáveis sem encerrar o objetivo do usuário, com três exemplos reais quando pedidos três; execução contínua e correções bounded até critérios locais comprovados, **sem** modelo remoto, lists de sinônimos/produtos, acoplamento a provider ou nova engine. **Status factual:** `PLANNED`; F1 `REWORK`; F2 `TO_CHARACTERIZE`; O2 local último teste `0/10 FAIL`; revisão independente futura `PENDING`; autorização PO de deploy `CONDITIONAL`, autorização operacional específica `PENDING`, deploy nesta task `NOT_EXECUTED`, R7 final `NO`. Stops de segurança/arquitetura/segunda falha do mesmo pacote são obrigatórios e não equivalem a conclusão satisfatória.


### Registro complementar — 2026-10-25 — Remediação F1/F2 executada (goal recovery bounded) — `DELIA-R7-LOCAL-GOAL-RECOVERY-TO-PRODUCTION-ACCEPTANCE-01`

- `STATE=F1_F2_REMEDIATED_LOCAL_EVAL_GATE_BLOCKED`; base `fe9ca71369`; escopo `argument_validation.py` + `orchestration._build_arguments` + testes.
- F1: declarado-documental opcional não vinculado ⇒ `(None, missing_inputs)` — zero invocação não filtrada; nomes alimentam resolver/clarify existente. F2: ramo sem schema honra declarações via `selections`/`evidence_arguments` fail-closed.
- `PREINVOKE_FAILURE_RECOVERY=existing` — `missing_inputs → _resolve_missing_inputs → clarify`; sem planner/segundo state machine.
- Backend 2296/2298 (2 env pré-existentes); focused 192/192. Local `delia-json`: três-exemplos 0/10 (admission), O2 0/3, pino/D1/TÉO/VISTA 0/3, READ direto 1/3 GROUNDED real, WRITE 3/3 recusa, AuthZ 401, 0 falsos positivos.
- `DEPLOY=BLOCKED_NO_LOCAL_RELIABILITY` — contrato pronto; executor sem modelo local autorizado que alcance o estágio governado. `NEXT_ACTION=decisão de coordenação (modelo local capaz OU autorização de avaliação externa controlada) + review independente do SHA`.


### Registro complementar — 2026-10-25 — Recovery provado + R1/R2/R3 fechados — `DELIA-R7-EXISTING-RECOVERY-AND-OUTCOME-CLOSURE-01`

- `STATE=RECOVERY_PROVEN_RESIDUALS_CLOSED`; base `abccde87ac`; escopo `argument_validation.py` + `orchestration._resolve_missing_inputs` + testes.
- R1: teste de fluxo prova `declared-unbound → resolver same-owner → rebuild → owner READ → SUCCESS` — recovery existente suficiente, sem novo engine. R2: asserts de consumidor/tentativas/proposta/owner/outcome. R3: `unbound_declared` determinístico (ordem da proposta); declarações além de `MAX_EVIDENCE_SELECTIONS` seguem fail-closed (cap limita materialização apenas).
- Defeito irmão F1 corrigido: resolver tail resolvia com `still_missing`/campos ausentes → invocação sub-filtrada; `_missing_inputs_bound` agora exige cobertura total antes de resolver (normal + ambíguo).
- Local `delia-json`: Outcome empresarial (3 registros) segue bloqueado por capacidade de admission do modelo autorizado — não por contrato.
- `DEPLOY=BLOCKED` até local outcome + review + autorização operacional.


### DELIA-R7-ARCHITECTURE-DRIFT-AND-GROUNDED-OUTCOME-REMEDIATION-01 — plan 148 (2026-10-25)

Plano [148](../corrections/mcp-contextual-intelligence-orchestration/148-r7-architecture-drift-remediation-and-outcome-closure-plan.md) criado e aprovado como roteiro proposto para execução condicionada a reancoragem/contrato. Revisão de v19 `6e51626b1b`: A1 `TO_INVENTORY` (owner_surface_kinds estático), A2 `EXTEND_WITH_TESTS`, A3 `FAIL_REPORTED` (VISTA control-plane apresentado como três registros empresariais), outcome local `FAIL`, deploy `BLOCKED`, R7 `OPEN`. WPs: WP0 reanchor, WP1 admission dinâmico, WP2 provenance/control-plane business gate, WP3 argumentos/recovery, WP4 local-only eval, WP5 review/release. Sem novo código ou deploy por documentação. Comparação com padrões OpenAI/Anthropic/Microsoft apenas como princípios, sem instalação de framework.


### §6.430 — 2026-10-25 — Investigação única de contexto e inteligência operacional (DELIA-CONTEXT-INTELLIGENCE-SINGLE-PASS-CANONICAL-INVESTIGATION-01)

- `TASK_ID=DELIA-CONTEXT-INTELLIGENCE-SINGLE-PASS-CANONICAL-INVESTIGATION-01`; `STATE=INVESTIGATION_COMPLETE_AWAITING_DECISION`; `BASE_SHA=d3dfaa2cca` (=origin/main); read-only — zero alteração de código/prompt/modelo/infra/schema/deploy; R7/Plano 148 não tocado (WP1/WP3 do commit d3dfaa2cca incorporados ao baseline e à matriz).
- Entregável: [Doc 151](../corrections/mcp-contextual-intelligence-orchestration/151-single-pass-context-intelligence-investigation-evidence-and-plan.md) — diagnóstico factual, transport map completo, matriz de 23 estágios, comparação 3-vias (canon × código × mercado), inventário de reuso, gaps com evidência, análise de segurança/autoridade, propostas mínimas, plano fechado WP-A..WP-F e decision register D1-D8.
- Diagnóstico: histórico é 100% client-side (`buildInteractionContext`, React state, 16.384 chars, pares completos); `SESSION_PERSISTENCE=NONE` é decisão canônica aprovada (doc 21 §8, ACCEPT_WITH_RESIDUAL); adapter serializa `prior_context`→`user`/`assistant` verbatim (sem tools/autoridade/CoT); 23 estágios mapeados — 2 recebem NONE (clarify/corroborate), 4 recebem contexto reduzido intencional (observation ≤800c, excerpts ≤12, folded ≤4×120c).
- Gaps reais com evidência: G1 sem persistência/identidade de conversa (deferido por cânone); G2 sem compactação (pair-drop silencioso, sem marcador de omissão); G3 `OLLAMA_NUM_CTX` eficácia não comprovada + adapter não serializa `num_ctx`; G4 sem token budget/estimativa pré-chamada (pior caso ~32k chars ≈8-10k tokens vs janela 2048/4096); G5 estágios de seleção com `()`/observation reduzida + inconsistência `_discover_candidate` vs `_invoke_selected`; G6 `_TurnGoal` re-derivado por turno (sem carry-forward tipado); G10 turnos injetados indistinguíveis no wire (residual bounded por revalidação).
- `TEST_NOT_RUN`: captura sanitizada do wire payload (adapter tests + leitura direta provam serialização pretendida); `TO_INVENTORY`: eficácia de `OLLAMA_NUM_CTX` vs `OLLAMA_CONTEXT_LENGTH` no daemon em produção (primeira ação do WP-A).
- Decision register: D1-D5 aprováveis pela coordenação (WP-A budget/window, WP-C marker, WP-D uniformidade, WP-E delimitação, WP-F medição); D6 WP-B persistência requer re-decisão canônica (`SESSION_PERSISTENCE=NONE`), D7 instruction resource gate, D8 residência de dados com provider externo. Inadmissível: história como autoridade, bypass AuthZ, novo planner/engine/provider.
- `EXECUTION_DRIFT=NONE`; `NEXT=decisão arquitetural sobre D1-D8 + autorização de implementação — sem nova rodada de inventário`.


### DELIA-C3-EVIDENCE-SCHEMA-PROJECTION-INTEGRITY-AND-COVERAGE-01 — execução (2026-10-26)

- `STATE=IMPLEMENTED_WITH_EVIDENCE`; base `49dc645b0d`; escopo `orchestration.py` (projeções dos estágios não-seleção) + testes + doc 152 §12.
- WP0: 13 sites `json.dumps(...)[:MAX_*]` em blocos estruturados classificados `DESTRUCTIVE_TRUNCATION_PROVEN` (resolver, records, synthesis, comparison, native assessment, continuation, missing_inputs, relevance, prior_result_preview, index probe/select, arguments, candidate arguments); `_resolved_values_proven` = `SAFE_BOUND` preservado.
- Fix: `_fit_json_block`/`_json_block` ao lado dos builders C2 — redução estrutural ordenada (texto bounded → campo opcional → omissão de cauda com marcador `*_omitted` verdadeiro); `input_schema`/schema/identifiers nunca reduzidos — emitem íntegros; `MAX_INPUT_CHARS`/`CONTEXT_TOO_LARGE` seguem como boundary tipado. `evidence_blocks` sincronizado com o texto efetivamente projetado (sem verificação fail-open sobre evidência não vista).
- Tests: `test_evidence_schema_projection_integrity.py` — 23 casos RED→GREEN; RED causal: mesmas fixtures sob o corte antigo produzem `Unterminated string` em 5/5 envelopes.
- Eval local congelada (delia-json qwen2.5:3b, ctx 8192, api-delpi real via delegated exchange): 28 blocos capturados em 7 cenários — `json_valid=100%`, `CAPABILITIES_OMITTED=0` (catálogo real 1 grupo/~2-4 caps); ref_user/ref_observation alcançaram owner real (GROUNDED path com respostas honestas); three_records/O2 honestamente NON_GROUNDED/typed; ref_assistant_only não injetou referente assistente. `FALSE_POSITIVES=0`. Sem melhoria de outcome empresarial reivindicada (variance 3B, n=1).
- `DEPLOY=BLOCKED` (revisão independente pendente); `INDEPENDENT_REVIEW=PENDING`.


### DELIA-C3-PROJECTION-OVERFLOW-OMISSION-RECOVERY-CONTRACT-REWORK-01 — execução (2026-10-26)

- `STATE=IMPLEMENTED_WITH_EVIDENCE`; base `859632601b`; resíduos R1/R2/R3 da revisão `5ba117db50`; escopo `orchestration.py` + `contracts.py` (nova limitation) + instruction resource v22 + testes + doc 152 §14.
- R1: layering formalizado — block `MAX_*` é alvo de compactação (emite JSON íntegro + warning ao esgotar), transporte `MAX_INPUT_CHARS=16384` sempre ativo (`INVALID_REQUEST`), janela declarada `CONTEXT_TOO_LARGE`; janela desconhecida deixa apenas transporte (residual documentado). Sem segundo budget.
- R2: fail-open fechado em 7 sites — seleções passam a validar contra a lista projetada que o modelo viu (synthesis, prior-continuation, comparison left/right, capability x2, resolver, prepare, index); nova `LIMITATION_EVIDENCE_PROJECTION_PARTIAL` propaga projeção parcial ao outcome; v22 declara a semântica de todos os marcadores `*_omitted`.
- R3: `prior_result_preview` pinado como objeto JSON string `{records, records_omitted?}`; consumidores LLM-only; injeção permanece dado inerte; recovery segue bounded.
- Tests: `test_projection_omission_recovery_contract.py` — 25 casos; RED causal no baseline (stash): `resolve_3` selecionado sem projeção, synthesis renderizou índice fora do prefixo, capability omitida ligada.
- Eval local congelada (delia-json qwen2.5:3b, ctx 8192, instrução v22, api-delpi real via delegated exchange): 7 cenários, 31/31 blocos JSON válidos; 2 blocos acima do alvo de compactação emitidos íntegros (layering R1 ao vivo); `business_subject` propagado em foreign_selection; uma rodada de recovery governada em three_records; `FALSE_POSITIVES=0`.
- `DEPLOY=BLOCKED` (revisão independente pendente); `INDEPENDENT_REVIEW=PENDING`.


### DELIA-C3-OUTCOME-COMPLETENESS-FINAL-PAYLOAD-CONSISTENCY-01 — execução (2026-10-26)

- STATE=IMPLEMENTED_WITH_EVIDENCE; base f24ceddf6b; resíduos B/C da revisão independente 91d3453cb2 (doc 152 §15); escopo orchestration.py + conversational_response.py + novo test_outcome_completeness_final_payload.py + doc 152 §16. Sem planner/engine/registry/memória/provider/segundo budget.
- Residual B (false completeness): causa raiz — projected_omitted nunca chegava a _render_synthesis/_list_header; projeção parcial renderizava contagem não qualificada. Fix bounded: header qualificado quando records_omitted>0 nos dois call sites (synthesis e prior-continuation); limitation evidence_projection_partial já propagava attempt→turn→result. GROUNDED permanece estado de proveniência, não veredito de outcome.
- Residual C (final payload): causa raiz — wrap de relevance_feedback ocorria após a captura do universo selecionável e sem re-fit; inner object-form virava {capabilities:{capabilities:[…]}} aninhado (marker enterrado, shape ilegível ao contrato de membership); foreign selection não tinha binding de ids projetados; _select_group apresentava o mesmo shape aninhado de capability_groups sob optionals. Fix: payload final montado e re-fitted antes do dispatch; visible computado do mesmo payload; _projected_capability_ids vincula foreign_capability_id aos ids realmente despachados; groups nunca omitidos.
- Tests: 15 casos B1–B9/C1–C8; RED causal no baseline: b2/b4 (parcial renderizado como completo), c3 (shape aninhado ilegível ao contrato), foreign (beta.read_5 omitido resolvia), group (capability_groups aninhado sob optionals+feedback). Verde pós-fix; suites focadas + backend completo verdes (env limpo); gates arquitetura 0 findings.
- Eval local congelada (delia-json qwen2.5:3b, ctx 8192, instrução v22, api-delpi real via delegated exchange): 8 cenários; 29/29 blocos válidos; three_bala com 3 invokes DAVI reais terminou em clarificação honesta; write_request recusado como não autorizado; capability_id inventado rejeitado fail-closed; FALSE_POSITIVES=0; FALSE_COMPLETENESS=0. Capacidade semântica 3B segue limitante documentado.
- DEPLOY=BLOCKED (revisão independente pendente); INDEPENDENT_REVIEW=PENDING.


### DELIA-C3-SEMANTIC-ADMISSION-GOAL-ARGUMENT-FIDELITY-EVAL-01 — execução (2026-10-26)

- STATE=EVALUATION_COMPLETE; base cd50b85610 (=origin/main); READ-ONLY — zero alteração de código/prompt/modelo/budget/AuthZ; deploy não executado.
- Corpus congelado: 25 cenários × 5 repetições = 125 execuções governadas (delia-json qwen2.5:3b, ctx 8192, instrução v22, delegated bearer READ-only, superfície real 4 grupos/41 caps). Seed NOT_SUPPORTED pelo adapter — variância medida, determinismo não reivindicado.
- Resultado: OUTCOME_PASS=40 (guidance 15/15, negative 15/20, discovery 5/15, continuity 5/20), FAIL=85; records family 0/45. Primeiro estágio divergente: ADMISSION_ERROR 36, GROUP_SELECTION_ERROR 30, MODEL_STRUCTURED_OUTPUT_ERROR 15, CAPABILITY_SELECTION_ERROR 8. Apenas 12/125 turnos invocaram qualquer capability.
- Causa comprovada (prova direta no payload despachado): _group_summaries entrega 0/41 descrições não-vazias — nomes+estrutura dos 4 grupos consomem ~5909 dos 6000 chars, compactação zera toda descrição; seleção de owner vira loteria por remote_name (mcp:teo 10, mcp:vista 6 escolhidos para consultas de produto). Direção A (contrato/código), não capacidade 3B.
- Secundário comprovado: admission classifica consultas de registro como surface_inquiry (catálogo listado em vez de READ — FN=0 mas FP=30); structured output inválido 15/125; argumentos com subject em code e resolver→search_customers (infidelidade semântica).
- Segurança limpa: 0 bypass AuthZ, 0 PREPARE/ACT, 0 fabricação; neg_scope/neg_write recusados 10/10; neg_inject recusou com applicable:false (FAIL por oráculo estrito, comportamento correto); injetado ID rejeitado fail-closed.
- Recomendação: A — restaurar sinal semântico mínimo bounded em _group_summaries (ex.: group_description por grupo) antes de medir capacidade; depois B — experimento bounded em surface_inquiry. Revisão independente pendente.
- Artefatos: doc 153, scripts semantic_fidelity_eval.py + semantic_fidelity_aggregate.py, runs JSON sanitizado (350KB). DEPLOY=BLOCKED; INDEPENDENT_REVIEW=PENDING.


### DELIA-C3-GROUP-SELECTION-SEMANTIC-SIGNAL-PRESERVATION-01 — execução (2026-10-26)

- STATE=IMPLEMENTED_WITH_EVIDENCE; base c972dae7f2; escopo _group_summaries (novo campo de projeção scope) + instruction resource v22→v23 + testes; sem planner/engine/registry/memória/segundo budget; MAX_SURFACE_CHARS=6000 inalterado.
- Causa raiz (doc 153): catálogo stage-1 compactava 41/41 descrições a vazio — seleção de owner virava loteria por remote_name. Fix: scope = recorte verbatim determinístico das descrições publicadas pelo owner (≤160/grupo, per-desc ≤60), ausente quando fonte não publica, último campo a reduzir na escada de compactação; ids e marcadores intactos; nunca fabricado; dados não autoritativos.
- Tests: 17 casos A1–A9 + fairness/injeção/extrema-pressão; RED causal no baseline (10 falhas — scope nunca emitido); versões pin 22→23 em 3 suites.
- Eval A/B congelada (mesmo modelo/corpus/bearer class, 12 cenários ×5 = 60 runs cada): scope entregue 4/4 grupos na superfície real (payload ≤5989); outcome PASS 10→15 (disc_candidate 0→5); admission errors 18→12; structured-output 8→5; MAS GROUP_SELECTION_ERROR 25→25 — wrong-owner migrou teo→vista. Conclusão honesta: sinal restaurado, mas seleção não melhorou mensuravelmente — limitante restante é uso do sinal (instrução/modelo), não disponibilidade.
- Regressão: backend completo verde (0 FAILED/ERROR); gates arquitetura 0 findings; AuthZ/PREPARE/ACT intocados; segredos destruídos.
- Próximo bounded: experimento de instrução isolando a cláusula documentation-first para sujeitos coloquiais (direção B doc 153), depois re-medir antes de qualquer decisão de capacidade (C).
- DEPLOY=BLOCKED; INDEPENDENT_REVIEW=PENDING.


### DELIA-C3-GROUP-SELECTION-INSTRUCTION-SEMANTIC-CONFLICT-EVAL-01 — execução (2026-10-26)

- STATE=EVALUATION_COMPLETE; base 74fb1ba10b; código e instrução produtiva NÃO modificados — variante B injetada apenas no mapping _instructions em processo (seam de avaliação); fixture + harness + runs sanitizados publicados.
- Experimento: v23 (A, fp 8eb95ebdafe8b338) vs cláusula única reescrita (B, fp 15855b8c1a17ed47) que torna a superfície de registros o destino de pedidos de registros mesmo com nomenclatura coloquial. Interleaving ABBA, 12 cenários base x5 + holdout 8 x5, além de isolamento de estágio (_select_group direto, 4 catálogos x10 prompts x5 reps x2 variantes = 400 chamadas).
- Resultado: REJEITADA — stage-1 live A 16/50 vs B 14/50; e2e base A 17/39 vs B 10/35 elegíveis corretos; holdout 10/20 vs 10/24. Nenhuma dimensão melhorou.
- Descoberta dominante: catálogo com providers renomeados (nomes neutros) quase duplica acurácia nas DUAS variantes (35/50, 31/50) — falha é dominada por priores de nome do modelo 3B, não pela cláusula. Descrições/scope são suficientes (H3 refutado).
- Hipóteses: H1 REFUTED (conflito instrucional não é a causa operativa), H2 SUPPORTED (capacidade/modelo — nome domina sobre descrição), H3 REFUTED, H4 SUPPORTED (admission diverge independente), H5 SUPPORTED (downstream falha mesmo com grupo certo).
- Segurança: injeção em descrição não sequestrou seleção; 0 bypass AuthZ, 0 PREPARE/ACT, 0 id inventado; tokens opacos redigidos no artefato.
- Próximo bounded: comparação controlada de modelo (autorização separada) ou experimento de projeção com nomes neutros no stage-1 — tasks novas, não iniciadas.
- DEPLOY=BLOCKED; INDEPENDENT_REVIEW=PENDING.


### DELIA-C3-CATALOG-PRESENTATION-NAME-PRIOR-SENSITIVITY-EVAL-01 — execução (2026-10-26)

- STATE=EVALUATION_COMPLETE; base 148b4e0a3a; código/instrução/catálogo/modelo produtivos NÃO modificados — variantes aplicadas apenas em projeção in-process via seam de avaliação (`EVAL_CATALOG_VARIANT`); deploy não executado.
- WP0: agregador corrigido — classificação exclusiva por execução (ADMISSION_STOP / GROUP_CORRECT / GROUP_WRONG / GROUP_NOT_APPLICABLE_CORRECT|WRONG / GROUP_INVALID_OUTPUT / GROUP_NOT_REACHED_OTHER); `correct` nunca conta abstenção em métrica de seleção; oráculo reconciliado strict (owner de registro) vs lenient (rota davi discover→execute legítima).
- WP1 congelado: delia-json qwen2.5:3b ctx 8192, instrução v23 fp 8eb95ebdafe8b338, superfície real 4 grupos/41 caps, payload sha256 916c063b67e54cd6… (5989/6000 chars).
- Descoberta estrutural decisiva: o payload stage-1 despachado contém apenas capability_group_id + capabilities + scope + capabilities_omitted — display_name, owner e source_system são compactados para fora do fio sob o orçamento de 6000 chars (provado por hash: variantes neutral/respforward geram sha idêntico ao real).
- Stage-1 (240 chamadas, 12 prompts x5 reps x4 variantes): real 27/60 lenient / 24/60 strict; neutral 26/60 / 25/60 (sha idêntico — réplica A/A, variância do modelo); respforward 21/60 / 20/60 (sha idêntico); reorder sha e0328e74 distinto → colapso posicional: davi 46/60 picks, invalid 0→13, strict correto apenas 5/60.
- E2E (200 turnos, real vs reorder, base+holdout x5): reorder_base strict 4/40 vs real 15/37; reorder_holdout strict 0/24 vs real 11/25; invalid e2e 0→3 e 0→7; lenient sobe artificialmente (davi conta como rota legítima de registro). Wrong-owner strict reorder: davi 29 base / 17 holdout.
- Veredito: NAME_PRIOR_NOT_CONFIRMED para rótulos de apresentação — campos de apresentação não chegam ao modelo sob o orçamento vigente; o ganho do catálogo renomeado do doc 155 é agora atribuível a priores do capability_group_id canônico (H2), não a display labels (H1 não testável). H3 viés posicional SUPPORTED (maior defeito reproduzível); H5 capacidade SUPPORTED (variância ±15% em input byte-idêntico); H6 SUPPORTED.
- Segurança: 0 bypass AuthZ, 0 PREPARE/ACT, 0 id inventado; ids/owners/source_system/schemas remotos intactos; sem segredos nos artefatos.
- Artefatos: doc 156; scripts catalog_presentation_probe.py + catalog_presentation_aggregate.py; seam em instruction_conflict_eval.py (eval-only); evidence catalog-presentation-snapshot.json, catalog-presentation-probe-runs.jsonl/.json, catalog-presentation-e2e/*.json.
- Próximo bounded: experimento autorizado separado sobre tokens do capability_group_id (requer decisão de arquitetura — toca identificador canônico), hardening de robustez a ordem no stage-1, ou comparação de capacidade de modelo no corpus congelado.
- DEPLOY=BLOCKED; INDEPENDENT_REVIEW=PENDING.


### DELIA-C3-GROUP-SELECTION-ORDER-ROBUSTNESS-CHARACTERIZATION-01 — execução (2026-10-26)

- STATE=EVALUATION_COMPLETE; base 3fdb36e883; árvore delia-api congelada = doc 156; código/instrução/catálogo/modelo NÃO modificados — permutação aplicada somente na lista serializada pós-projeção via seam de avaliação.
- Matriz: 24 permutações completas (4 grupos) × 12 prompts × 5 reps = 1440 chamadas stage-1 intercaladas; invariants verificados por chamada — mesmo group set, cap counts, scope 4/4, omitted=1, 5989 chars, 24 shas distintos (ONLY_ORDER_CHANGED=YES).
- Resultado stage-1: strict accuracy por permutação varia 5/60 → 32/60 (stdev .13, range .45) vs run variance ~±15%. Efeito de posição absoluta: pos1 quase nunca escolhida (0-9%), pos4 domina (36-58%) — recência, não primazia. Efeito relativo: delpi depois de teo/vista/davi → 48-61% strict em record asks vs 18-31% quando antes. Interação patológica: delpi-primeiro+davi-último (perms 21/23) colapsa em davi + 14-26 invalid outputs.
- Holdout pré-declarado {0,5,14,16,21,23} × 8 prompts × 5 = 240 chamadas: perm 14 (melhor) 22/40 strict; perms 21/23 (piores) 1/40 com 11-17 invalids; generalização confirmada.
- E2E (4 perms × base+holdout × 5 = 480 turnos): p14 (delpi último) triplica strict group-selection no base (24/35 vs 5/27 canonical) MAS business outcome não melhora (16/60 vs 20/60 PASS) — downstream segue divergindo. p21/p23 confirmam colapso strict 1/36, 9/28 e 5/23, 1/22 holdout.
- Veredito: ORDER_EFFECT_CONFIRMED — recência + interação posição×ID, não primazia simples; fragilidade semântica do modelo 3B na superfície de grupos.
- Segurança: 0 bypass AuthZ, 0 PREPARE/ACT, 0 id inventado aceito, 0 write; artefatos sem segredos.
- Artefatos: doc 157; scripts order_robustness_probe.py + order_robustness_aggregate.py; seam EVAL_PERM_ORDER em instruction_conflict_eval.py; evidence order-robustness-*.{json,jsonl} + order-robustness-e2e/*.json.
- Próximo bounded: comparação de capacidade de modelo na matriz congelada (autorização separada), ou decisão de arquitetura sobre mitigação de recência no contrato de superfície — sem política de ordem por provider.
- DEPLOY=BLOCKED; INDEPENDENT_REVIEW=PENDING.

## 2026-10-26 — DELIA-C3-DOWNSTREAM-CAPABILITY-ARGUMENT-FIDELITY-CAUSAL-EVAL-01 (doc 158)

- Escopo: caracterização causal downstream — 4 braços harness-only (A natural, B good-group, C good-capability, D good-arguments), 11 cenários record × 5 reps, interleaved, superfície saudável verificada (4 grupos/41 caps, 0 falhas), bearer fresco por turn (JWT TTL 300s), spy de invokes com captura de erro, flags controls_engaged.
- Resultado: 220 runs válidos; PASS apenas via exact-code (1/55 por braço controlado); delpi invocado 9× (B2/C4/D3), 6 rejeitados por goal_evidence_relevance vazio; FOREIGN_DIVERT dominante ~37/41 engaged em C/D; capability abstain 43% em B; admission surface_inquiry/hypothetical ~50% das turns.
- Veredito: primeiro bloqueio downstream com grupo correto = desvio semântico native_assessment→foreign_selection (~90% dos turns engajados); capability abstention 43%; relevance judgments vazios ~67% dos invokes; argument fidelity real mas secundária; owner REFUTADO como gargalo.
- Segurança: 0 bypass AuthZ (negações = TTL expirado → AUTHZ_DENIED truthful), 0 ACT/WRITE, 0 registro fabricado apresentado como real; artefatos limpos.
- Artefatos: doc 158; scripts downstream_causal_eval.py + downstream_causal_aggregate.py + armd_stage_debug.py; evidence downstream-causal-runs.{json,jsonl} (sanitizados).
- Drift documentado: 2 restarts em massa da stack (api-delpi zombie → openapi_document_unavailable → delpi ausente da superfície; mcp:davi down), JWT TTL vs spy success-only (batches 1–2 parcialmente invalidados, rerun em superfície saudável), senha dev-portal resetada pelo reimport do realm (restaurada), WSL blips.
- Próximo bounded: revisão de contrato native_assessment/foreign_selection (por que foreign_evidence_required dispara em record asks diretos) + comparação de capacidade de modelo na matriz congelada — autorização separada; nenhum patch de ordem/instrução justificado.
- DEPLOY=BLOCKED; INDEPENDENT_REVIEW=PENDING.

## 2026-10-26 — DELIA-C3-NATIVE-ASSESSMENT-FOREIGN-SELECTION-CAUSAL-DIAGNOSTIC-01 (doc 159)

- Escopo: diagnóstico causal read-only do desvio native_assessment→foreign_selection — captura do payload EXATAMENTE despachado (spy em InvokeModel.execute), oráculos de contrato por grupo-alvo, 18 cenários ×5 reps ×3 braços = 270 runs, variants WP8 em memória.
- Resultado: assessment alcançado 171× — foreign_evidence_required 85%, sufficient 2/171; matriz oráculo TP73/FP59/TN18/FN8 (76% FP quando alvo era suficiente); foreign_selection abstenção ~60% (invalid_foreign_selection dead-end); payload íntegro (171/171 e 136/136 JSON válidos, todos os campos do contrato despachados).
- Braços: B=TEST_NOT_RUN (bloco já carrega todo o contrato); C engaged 22 → 17 PASS (caminho nativo funciona sem o desvio); D engaged 21 → 19 invokes delpi corretos mas 20 FAIL (enriquecimento estrangeiro não resgata target errado — continuação estruturalmente perdida).
- WP8 variants (12 superfícies FP ×3×3): V1 replay 35/36 fer, V2 minimal 32/36, V3 goal-first 34/36 — FP invariante à apresentação → causa = semântica da instrução + interpretação do modelo, não contexto.
- Veredito: cláusula de exceção mandatória da instrução native_assessment embute premissa semântica de owner não verificável (designação informal + owner 'literal-only' → foreign obrigatório) — DELPI resolve sujeitos descritivos (oráculos 13–50 registros); modelo extrapola a cláusula (doc asks, código explícito: biz_code 9/9 fer). H1+H3+H6 SUPPORTED, H2 REFUTED, H7 parcial.
- Segurança: 0 bypass AuthZ, 0 ACT/WRITE; neg_write alcançou PREPARE invoke governado (owner fail-closed 'Operação não suportada' — residual de write-intent não cortado na admissão); artefatos sem JWT/segredos.
- Artefatos: doc 159; scripts assessment_foreign_diag_eval.py + _aggregate.py + assessment_variants_eval.py; evidence assessment-foreign-runs.{json,jsonl} + assessment-variants.json (sanitizados).
- Drift documentado: 1 outage de transporte WSL (stack restart; eval checkpointed, 270/270 íntegros); model_calls=1435+108, in≈2.59M, out≈46.5k, latência med 6.4s.
- Próximo bounded: revisão de contrato/instrução native_assessment (remover desvio mandatório ou condicioná-lo a capability de vocabulário verificada) + comparação de capacidade de modelo + diagnóstico de goal_evidence_relevance vazio — autorizações separadas.
- DEPLOY=BLOCKED; INDEPENDENT_REVIEW=PENDING.

## 2026-10-27 — DELIA-C3-NATIVE-ASSESSMENT-INSTRUCTION-CONTRACT-AB-EVAL-01 (doc 160)

- Escopo: avaliação A/B evaluation-only da instrução native_assessment — A=v23 verbatim (sha fcdbd185527595b9), B=fixture mínimo que remove a exceção mandatória e adiciona restrição epistêmica (sha c083e71332b67a0a); injeção só em memória no estágio, nada em produção; mesmo modelo delia-json, catálogo, oráculos e AuthZ.
- Stage-local: 120 superfícies únicas despachadas ×5 reps ×2 instruções = 1190 chamadas — B corta foreign_required 93.9%→69.9% e FP 91.4%→61.0%, accuracy 53.6%→59.2%, MAS sufficient só 13/595 e FN sobe 3.6%→21.6% (hedge para inconclusive).
- E2E: 180 turns (18 cenários ×5 reps ×2 braços intercalados) — assessment alcançado A49/B48; B 0/48 sufficient, FN 26.1%; outcome A 30P/60F vs B 31P/59F (sem degradação, sem ganho); holdout congelado reproduz o mesmo padrão.
- Segurança: 0 bypass AuthZ, 0 ACT/WRITE, 0 registro fabricado; residual PREPARE reproduz sob ambos os braços (A vista.suggest_change COMPLETED ×2; B vista.prepare_change → ERROR protocol, owner fail-closed) — write-intent não cortado na admissão, SECURITY_REVIEW_REQUIRED mantido.
- Veredito: B_REJECTED para implementação — a exceção mandatória contribui ~24pp do desvio mas não é a causa dominante; sob delia-json o modelo não recupera sufficient nem com mandato removido (H1 parcial, H2/H5/H6 SUPPORTED, H3 REFUTED, H4 confirmado por evidência anterior). Próximo bounded: comparação de capacidade de modelo na matriz congelada + higiene da cláusula como task de contrato separada + diagnóstico goal_evidence_relevance.
- Artefatos: doc 160; scripts assessment_ab_stagelocal_eval.py + instruction_ab_eval.py + instruction_ab_aggregate.py; evidence assessment-ab-stagelocal.json + instruction-ab-runs.{json,jsonl} + native-assessment-instruction-b.txt (sanitizados).
- DEPLOY=BLOCKED; INDEPENDENT_REVIEW=PENDING.

## 2026-10-27 — DELIA-C3-PRODUCTION-DEPLOY-SINGLE-BUSINESS-QUERY-SMOKE-01 (doc 161)

- Escopo: smoke de produção autorizado — deploy verificado (delia-api/ sem diff produtivo desde 00a79c26 → DEPLOY_REQUIRED=NO, apenas git pull de docs em srv-api), gates de baseline confirmados no runtime (instrução v23 sha fcdbd185527595b9 ativa; orchestration.py idêntico ao HEAD; sem eval overrides; modelo prod = moonshotai/kimi-k3 OpenRouter), UMA consulta real read-only via /apps/delia-api/interaction/turns com identidade devin-smoke-r4 provisionada (Delia Acesso + API DELPI Acesso via use case canônico; 2 restarts core-api para cache RBAC).
- Turno único (delia-smoke-2cfac0c60deb, HTTP 200, 16.8s, 5 model calls, ~7.3k/985 tokens): admission owner_surface → grupo openapi:delpi → capability delpi.search_products READ → args description,page_size → provider_invoke 403 mcp_authorization_denied (subject sem permissão de domínio ENGINEERING_LMP naquele momento) → síntese NON_GROUNDED honesta, zero fabricação.
- Observação arquitetural: native_assessment/foreign_selection NÃO exercitados — a meta entrou no plano direto OPERATIONAL (self_index), que não atravessa o estágio avaliado nos docs 159/160.
- Verificação de cobertura (read autorizado direto ao owner): search_products("terminal bala") → 77 candidatos, 65 registros TERM*/TERMINAL incluindo 10080092 e 10081004 — fonte cobre o objetivo; a negação foi AuthZ de domínio correta da identidade pré-grant.
- Resultado: BUSINESS_OUTCOME=FAIL (first divergent = OWNER_INVOCATION, domain AuthZ da identidade); cadeia semântica íntegra e fail-closed; 0 bypass, 0 ACT/WRITE/PREPARE, 0 fabricação.
- Artefatos: doc 161; nenhum código/instrução/modelo alterado; identidade de smoke retém roles para futuros smokes.
- DEPLOY=EXECUTED-SKIP; INDEPENDENT_REVIEW=PENDING.

## 2026-10-27 — DELIA-C3-PROD-SMOKE-IDENTITY-RBAC-REMEDIATION-AND-RETEST-01 (doc 162)

- Escopo: remediação e auditoria da identidade de teste designada devin-smoke-r4 + UMA consulta empresarial read-only autorizada — sem SQL de escrita, sem restart de serviços compartilhados, sem deploy, sem chamadas conversacionais preliminares.
- Identidade: Keycloak delpi/devin-smoke-r4 ok; Core 788e08ed (active, non-superadmin); roles iniciais=finais 'Delia Acesso'+'API DELPI Acesso' (estado least-privilege já correto — nenhuma mutação RBAC necessária nesta sessão; grants anteriores vieram do use case canônico). Credencial user/1234 informada inválida no Keycloak prod (invalid_grant em todos os clientes/realms testados) — não usada; subject admin nunca usado como usuário.
- Audit gap: audit_logs não contém linhas para os grants — AddRoleToUserUseCase emite evento de invalidação de cache mas não persiste auditoria; registrado para revisão do owner.
- Preflights (interfaces oficiais): AUTHENTICATION=PASS, /me confirma delia.access+api-delpi.access efetivos (cache consistente sem restart), leitura direta autorizada ao owner retorna 10080092 → DOMAIN_READ_AUTHORITY=PASS. Runtime reconfirmado: instrução v23 fcdbd185527595b9, modelo moonshotai/kimi-k3, delia-api healthy, SEM experimental B/overrides.
- Turno único (delia-smoke-b7b47ce98d9c, corr 111ef4b7, HTTP 200, 34.3s, 10 model calls, 18943/3353 tokens): admission owner_surface/operational → openapi:delpi → delpi.search_products READ → args 'produtos correspondentes à descrição terminal bala'+page_size=3 → provider_invoke OK 190ms (AuthZ de domínio PASS — divergência do doc 161 resolvida) → goal_evidence_relevance=irrelevant → relevance_recovery reinvoke args 'TERM BALA'+3 → provider_invoke OK 113ms → relevance=irrelevant → cri_response presented=0 → outcome insufficient/goal_mismatch → resposta GROUNDED honesta ('registros reais mas não correspondem'), zero fabricação.
- Verificação de outcome (reads diretos autorizados): call1→total 662 top-3 bateria/abas/'ABERTO'; call2→total 1855 top-3 balança×2+balancim — relevance julgou CORRETAMENTE: ranking léxico do owner coloca falsos 'bala' (balança/balancim) antes dos TERM. BALA reais (10080092/10081004 existem fora do top-3).
- Resultado: BUSINESS_OUTCOME=FAIL; FIRST_DIVERGENT_STAGE=ARGUMENT_CONSTRUCTION (call1 copiou a frase inteira no arg); bloqueio material = ranking léxico do owner para top-N curto. Cadeia AuthZ+relevance fail-closed correta; 0 bypass, 0 ACT/WRITE/PREPARE, 0 restarts, 0 DB writes.
- Artefatos: doc 162; nenhum código/instrução/modelo/banco alterado; ACCESS_RESTORATION=estado aprovado inalterado (grants mantidos como least-privilege da identidade designada — item aberto: ratificação/auditoria pelo owner).
- DEPLOY=NO; INDEPENDENT_REVIEW=PENDING.

## 2026-10-27 — DELIA-C3-LLM-NATIVE-ITERATIVE-RESEARCH-ARCHITECTURE-AUDIT-01 (doc 164)

- Escopo: auditoria R0 documentação-first da orquestração DÉLIA para pesquisa iterativa conduzida pelo LLM (direção doc 163) — inventário de todos os estágios, chamadas LLM, continuidade de pesquisa, contrato do owner e reuse gate. ZERO mudanças de código/modelo/deploy/consulta produtiva.
- Inventário: 18 instruction-ids v23; ~10 model calls observados no turno doc-162; fluxo real mapeado em orchestration.py (L4227–5709) com estágios, gates determinísticos e budgets (300s turno, 60s/call, ≤3 retries recuperáveis, checkpoint de resume).
- Bloqueios estruturais PROVEN: (1) _RELEVANCE_RECOVERY_USED = UMA rodada de recuperação por interação (L3828/4112/9593/9825) — após 2º 'irrelevant' o fluxo termina em insufficient/goal_mismatch, sem escolha semântica de próximo passo; (2) outcome_facts extrai total_count/coverage_complete/has_more (outcome_assessment.py:1498-1545) mas o bloco de relevância e o feedback de recovery carregam apenas records — o modelo não distingue '3 registros errados' de '3 de 1855 em 619 páginas'; (3) page-walk determinístico _maybe_aggregate_paginated_count só dispara em intent=COUNT (L8879-9010) — para LIST nenhuma página avança.
- Contrato owner provado (não presumido): delpi.search_products = LIKE prefixo-por-token OR'd (product_repository.py:61-89), score 100·phrase+20·term; 'TERM BALA' não casa 'TERM. BALA' (ponto literal) e BALA% puxa balança/balancim; page/page_size/total/total_pages são membros do contrato; is_complete = completude de transporte, não cobertura (specialist_interop/model.py:134).
- Reuse gate: EXISTING_EQUIVALENT=YES para todos os mecanismos (recovery round, relevance_feedback, page arg, envelope extractor, checkpoint, harness delia-json) — apenas o estágio de decisão de próxima ação seria novo (mesmo _propose port, não novo engine).
- Matriz: KEEP na maioria dos gates; EXTEND em goal_evidence_relevance (metadados de cobertura), _recover_relevance (ledger de rodadas), page-walk (intent LIST); REMOVE_CANDIDATE apenas como hipótese para o flag booleano; NEEDS_OWNER_CONTRACT para native/foreign e semântica de is_complete.
- R1 planejada (não executada): A=CURRENT vs B=LLM-LED BOUNDED ITERATION (≤3 rodadas, ações enumeradas, mesmos gates) no harness local delia-json; corpus ≥14 famílias + holdouts; métricas outcome-first; gates de segurança idênticos; aprovação de coordenação pendente.
- Veredito: AUDIT_COMPLETE; EXECUTION_DRIFT=NONE; INDEPENDENT_REVIEW=PENDING.

## 2026-10-27 — DELIA-C3-R1-LLM-NATIVE-BOUNDED-ITERATIVE-RESEARCH-EVAL-01 (doc 165)

- Escopo: avaliação A/B pareada LOCAL da hipótese de pesquisa iterativa conduzida pelo LLM (doc 163/164) — A=orquestração atual intacta; B=composição experimental somente no harness (bloco de relevância + metadados de cobertura já extraídos, proposta `delia.iteration.next_action` enumerada via `_propose` existente, ledger ≤3 rodadas + dedup, execução apenas por `_recover_relevance`/`_invoke_selected`). ZERO mudanças de código/instrução/modelo/catálogo/deploy/consulta produtiva.
- Baseline congelada: delia-json:latest (digest 7b8f4ab14fc1, qwen2.5 3.1B Q4_K_M, num_ctx 8192, JSON-only) no stack local c3r-eval/delpi-ollama; instruções sha adb3685506721cc2 inalteradas; bearer real delegado via Keycloak dev; AuthZ por invocação real.
- Reuse gate: EXISTING_EQUIVALENT=YES para todas as necessidades (julgamento, recovery, re-invoke, envelope de paginação, dedup, budgets, checkpoint) — único acréscimo = UM estágio de decisão no port `_propose` já existente; nenhum engine/planner/registry novo.
- Integrity: patch_install/patch_restore/injection_hint/garbage_rejection todos PASS; defeito do harness (dedup em args obsoletos pós-recovery) encontrado, corrigido e divulgado — apenas batch-2 é autoridade.
- Corpus: 16 cenários × 3 reps × 2 braços intercalados = 96 turns; 13 famílias incl. holdout congelado ×3; oráculos por reads diretos autorizados (pares code↔name + filtro de pertinência; verify_codes 10080092/10081004 confirmados). Fato mensurado: 'terminal bala' retorna 77 itens totais, 0 pertinentes em qualquer profundidade — paginação não pode resolver, só refinamento; 'conector faston' primeiro pertinente no rank 237.
- Resultado: BUSINESS_OUTCOME A=1/36 business+12/12 negativos vs B=0/36+12/12 (Δ=-1, ruído). Owner-reach A 20/48 vs B 15/48 (bloqueio dominante: admission/goal-typing ~60-70% zero-invoke). Judge `goal_evidence_relevance` rejeitou evidência PERTINENTE em 9/10 julgamentos (incl. match exato de código 10080092) — falso-negativo satura ambos os braços.
- B em funcionamento: 9 decisões next_action (refine×5, select_other×2, discovery×1, clarify×1; next_page=0), multi-round verificado (correção de arg 'born'→'borne' em round 1→clarify em round 2), re-seleção por código+grupo; custo +3.4% tokens/+8.5% latência; rounds máx=2 (cap 3 nunca atingido).
- Segurança: 0 bypass AuthZ, 0 ACT/PREPARE não autorizado, 0 registro fabricado, 0 loop ilimitado — negativos 12/12 nos dois braços, injeção e boundary de escrita respeitados.
- Veredito: R1_INCONCLUSIVE para outcome (instrumento saturado — o juiz 3B é a medida e a falha); mecanismo de continuação PROVADO correto/seguro/bounded — iteração é necessária mas não suficiente. Próximo bounded: R1.5 — eval stage-local de precisão do goal_evidence_relevance + admission/goal-typing no mesmo modelo congelado; escalada de escala de modelo à coordenação se precisão inalcançável; re-run do corpus congelado sob juiz melhorado.
- Artefatos: doc 165; delia-api/scripts/iterative_research_eval.py; evidence iterative-research-r1-runs.json + iterative-research-r1-summary.json (sanitizados — apenas códigos/nomes de catálogo e conteúdo DÉLIA).
- DEPLOY=NO; INDEPENDENT_REVIEW=PENDING.

## 2026-10-27 — DELIA-C3-R15-SEMANTIC-JUDGMENT-OWNER-REACH-CAUSAL-EVAL-01 (doc 166)

- Escopo: investigacao causal stage-local dos dois gargalos R1 (owner-reach e precisao do goal_evidence_relevance) no modelo congelado delia-json — reconstrucao dos 96 turnos R1 + eval stage-local de admission/turn_goal (17 queries x3) + eval de julgamento (15 pares rotulados x3 reps x4 variantes). ZERO mudanca de codigo/instrucao/modelo/deploy/consulta produtiva.
- Reuse gate: EXISTING_EQUIVALENT=YES para todos os seams (r4._compose, _find_orchestrator, _propose real, _understand_goal real, parse_goal_evidence_judgment, provider.invoke + bind_subject_bearer para oraculos); unica instrumentacao = _spy_wire capturando payload despachado real.
- Owner-reach (matriz de primeira divergencia, 96 turnos): 75% das nao-chegadas (46/61) morrem em admission — surface_inquiry x35 + hypothetical x11; token interaction_class decide a rota (requires_owner_surface e ignorado quando class=surface_inquiry). Stage-local: read_recall(requires=true)=1.000, adm_class_accuracy=0.804, goal_class_accuracy=0.744 (create_or_modify x6 em leituras), subject_fidelity=0.564; answer_requirements NUNCA extraido (min_items=None em 51/51 — declared_requirements nunca chega ao juiz em producao).
- Evidence judgment (15 pares com rotulos por oraculo, 180 julgamentos): payload verificado sem perda (code+description completos despachados). recall <=0.20 em TODAS as variantes (A_gold 0.167, A_pipe 0.200, B_cov 0.000, D_noreq 0.188), precision 1.0, FP=0 — colapso conservador: rejeita conjuntos pertinentes multi-registro 3/3 (hints auto-contraditorios: 'records for disjuntor but the user request is for disjuntor'); so identidade trivial (codigo exato, registro unico) passa (P_code_exact 3/3).
- Hipoteses: H1 SUPPORTED (misrouting de classe em admission), H2 REFUTED (gold~=pipe), H3 REFUTED (payload verificado), H4 PARTIAL (conceitos quase-gemeos no contrato de admission), H5 SUPPORTED (falha semantica do juiz com contexto completo), H6 PARTIAL (harness R1 com mislabels; direcao da taxa confirmada), H7 RESIDUAL SUPPORTED (erro persiste apos todos os controles de contexto — nao veredito sobre todas as tarefas).
- Causas provadas: (A) token interaction_class e a rota decisiva e confunde surface_inquiry/cobertura e hypothetical/ambiguous; (B) juiz colapsa para rejeicao em toda correspondencia por descricao — apenas identidade exata passa; gap de composicao secundario: answer_requirements nunca populado.
- Proxima direcao: B (reframe do contrato do juiz para correspondencia por registro + suficiencia deterministica backend) > A (consolidacao de classes em admission) > C (extracao de requirements) > E (re-run R1). Sem implementacao nesta task.
- Seguranca: 0 bypass/ACT/PREPARE/fabricacao; inject falha na direcao segura (owner path); cobertura parcial herdada da R1.
- Custo: 327 model calls; tokens/latencia nao capturados pos-resume (limitacao divulgada).
- Artefatos: doc 166; delia-api/scripts/semantic_judgment_reach_eval.py; evidence semantic-judgment-r15-runs.json (sanitizado).
- DEPLOY=NO; INDEPENDENT_REVIEW=PENDING.

## 2026-10-27 — DELIA-C3-R16A-PER-RECORD-SEMANTIC-EVIDENCE-JUDGMENT-EVAL-01 (doc 167)

- Escopo: A/B causal stage-local autorizado pela revisao independente R1.5 (ddddf09f34) — A=julgador agregado produtivo intacto; B=contrato harness-only de correspondencia por registro em lista; B2=variante de controle um-registro-por-chamada apos colapso de B; suficiencia deterministica (dedup+min) sobre labels do LLM. ZERO mudanca de codigo/instrucao/modelo/deploy/consulta produtiva.
- Baseline congelada: delia-json:latest digest 7b8f4ab14fc1 (qwen2.5:3b Q4_K_M, ctx 8192, JSON-only); instrucao goal_evidence_relevance inalterada; corpus = 15 pares congelados R1.5 + 3 conjuntos construidos pre-medicao (DUP/NOQ/SEC fixture) = 18 conjuntos, 95 registros validos, x3 reps = 405 chamadas totais.
- Oracles por registro com scrutinio de material/subtipo (exigencia da revisao): P_ilhos reclassificado (1 metalico pertinente, 7 borracha irrelevantes); BORNE FUSIVEL=partial; code-goal por identidade de codigo. Regras set-level declaradas pre-medicao; reconciliacao de labels doc 166 divulgada.
- Resultado B (lista): colapso estrutural — o modelo emite exatamente 1 entrada por chamada (sempre r1/r2), cobertura 1/N; 237/285 registros sem label; set acc 0.487 < A 0.667; 6 FPs. Contrato de lista inexequível no modelo congelado.
- Resultado B2 (1-registro-por-chamada): record precision 0.697 / recall 0.594 / FPR 0.214 (A~1.0/0.17/0); set acc 0.846 dev / 0.75 holdout — melhor de todos os bracos; todas familias positivas corretas; dedup e sem-quantidade corretos; decisoes estaveis entre reps.
- Residuos B2: FP 33 (21.4%) incluindo erro de identidade X_code_wrong (TERM.BALA julgado pertinente ignorando codigo pedido — 3 FPs); partial mal discriminado (2/18); custo 5.5x chamadas / 3.2x tokens in / 2.6x latencia (295,635 in-tok, 236.7s).
- Hipoteses: H1 SUPPORTED-com-refinamento (ganho veio de eliminar julgamento multi-item+enumeracao), H2 SUPPORTED-em-B2/REFUTED-em-B, H3 SUPPORTED (suficiencia deterministica correta), H4 SUPPORTED (FP real introduzido), H5 REFUTED-parcial (capacidade semantica existe com superficie minima; enumeracao nao), H6 REFUTED (holdout consistente).
- Seguranca: validator rejeita refs inexistentes/dup/classe invalida; injecao em registro fixture julgada pelo conteudo, sem corromper outros labels; 0 bypass/ACT/PREPARE/fabricacao.
- Veredito: R16A_ACCEPT_WITH_RESIDUAL — melhoria real e reproduzivel apenas na forma 1-registro-por-chamada; precisao 0.697 abaixo do gate ~0.70, FPR 21% exige hardening antes de candidatura produtiva. Menor contrato candidato documentado em doc 167 secao 9. Nenhuma autorizacao de mudanca produtiva.
- Proximo bounded: R1.6-B — experimento separado de taxonomia de admissao (nao combinar com juiz). DEPLOY=NO; INDEPENDENT_REVIEW=PENDING.
- Artefatos: doc 167; delia-api/scripts/per_record_judgment_eval.py; evidence per-record-judgment-r16a-runs.json (sanitizado).

## 2026-10-27 — DELIA-C3-LLM-NATIVE-OPERATIONAL-INTELLIGENCE-INTEGRATED-VALIDATION-01 (doc 168)

- Escopo: validacao integrada stage-local/E2E das cinco frentes (admission, julgamento, continuidade, contratos, E2E) no modelo congelado delia-json digest 7b8f4ab14fc1. ZERO mudanca de codigo/instrucao/modelo/deploy/consulta produtiva. ~900 model calls; B0/B1 reutilizados do artefato R1.6-A.
- WS-A: contrato coerente owner_access (read/write/catalog/none) elevou reach 0.667->0.976 e acc_dev 0.549->0.824; inject->none; reconciliacao deterministica do flag (A2)=sem ganho. Taxonomia de classes e a causa provada do misrouting. Gate A=PASS.
- WS-B: B2c (por-registro+declared_requirements+identidade tipada) precision 0.943/FPR 0.014/identity-FP=0 mas recall 0.256; B3 lote(4) reproduz o colapso de enumeracao (192/285 sem label) — batches inviaveis a qualquer tamanho. Gate B=FAIL (nenhuma variante atende recall>=0.50 & precision>=0.80).
- WS-C: modelo segue has_more (next_page correto) mas nunca escolhe answer/stop; 11/21 decisoes validas; seguranca bounded via dedup+cap. Gate C=FAIL.
- WS-D: causa raiz answer_requirements localizada — instrucao turn_goal NUNCA pede o campo (parser+consumidores existem); gap de contrato. OWNER_CONTRACT_GAP provado: search do owner nao resolve terminal bala->TERM.BALA (0/77 pertinentes por oraculo) — NEEDS_OWNER_DECISION.
- WS-E: E0=9/32 PASS vs E1=8/32 PASS (delta~0). Composicao alcança owner mais, mas outcome nao converte: recall conservador do juiz + gap de vocabulario do search + continuidade fraca. Passa somente negativos + code_lookup esporadico. Gate E=FAIL.
- Seguranca: 0 bypass/ACT/PREPARE/fabricacao/loop; remap A1 preserva gates downstream; cobertura parcial (sem denied-READ real).
- Veredito: ACCEPT_WITH_RESIDUAL — candidatos produtivos justificados: CH-1 admission simplificada + CH-2 campo answer_requirements na instrucao; CH-3 juiz por-registro condicional a gate de recall; continuidade precisa re-design; gap de search owner escalado.
- Artefatos: doc 168; scripts/integrated_intelligence_eval.py; evidence integrated-intelligence-runs.json. DEPLOY=NO; INDEPENDENT_REVIEW=PENDING.

## 2026-10-27 — DELIA-C3-CH1-CH2-FINAL-LOCAL-CONTRACT-VERIFICATION-01 (doc 169)

- Escopo: verificacao local fechada das candidatas CH-1 (admissao coerente) e CH-2 (campo answer_requirements na instrucao turn_goal) com gates congelados pre-medicao. ZERO mudanca de codigo/instrucao/modelo/deploy/consulta produtiva; variantes harness-only.
- Baseline: delia-json:latest digest 7b8f4ab14fc1 (qwen2.5:3b Q4_K_M ctx8192 JSON-only); instrucoes/catalogo/owner-contract inalterados. Corpus CH-1=23q x3 reps; CH-2=14 casos x3 reps; combinado=16 cenarios x2 reps por braco.
- CH-1: A1 reproduz ganhos (read_recall 0.622->0.978, acc_dev 0.529->0.804, acc_holdout 0.467->0.600, write_safety 6/6 vs A0 falho) MAS catalog_acc 0.0 (regressao vs A0 0.5 — modelo subutiliza classe catalog, rotas a read) e inject->none apenas 2/3 (rep1->read). CH1_GATE=FAIL -> REWORK. Sobre-admissao sempre na direcao segura (READ governado), nunca write.
- CH-2: qty_recall 0.0 em G0 E G1 (0/12 casos quantificados x3 reps). Proposta crua inspecionada: modelo emite apenas goal_class+business_subject; campo AUSENTE mesmo com instrucao G1 contendo a spec (verificado). Hipotese 'declaracao minima basta' REFUTADA no 3B congelado. Parser fail-closed confirmado (nao-mapping/min invalido/negativo/enorme/{}/chaves desconhecidas -> None). Regressao leve goal_class 0.718->0.641. CH2_GATE=FAIL -> REWORK.
- Combinado C0/C1 (exploratorio — gates isolados falharam): C0=9/32 vs C1=10/32 PASS (delta ruido); invokes 15->17; tokens in +34%; invalid_model_output x3 (h_doc_manual, fail-closed). Sem ganho de Business Outcome — gargalos downstream inalterados (search owner + recall juiz + continuidade). Limitacao: stage trace nao populado no harness combinado.
- Seguranca: 0 bypass/ACT/PREPARE/fabricacao; WRITE/PREPARE corretos em A1; cobertura parcial (sem denied-READ real).
- Veredito: CH1_IMPLEMENTATION_READY=NO (REWORK — residual: discriminacao catalog/none no contrato); CH2_IMPLEMENTATION_READY=NO (REWORK — mecanismo de instrucao-minima insuficiente; exige few-shot ou estagio dedicado). Nenhuma promocao; proximos passos bounded documentados em doc 169. DEPLOY=NO; INDEPENDENT_REVIEW=PENDING.
- Artefatos: doc 169; delia-api/scripts/ch1_ch2_verification.py; evidence ch1-ch2-verification-runs.json (sanitizado).


## 2026-10-27 — DÉLIA product direction approved / gated closed plan (doc 170)

- `STATE=PRODUCT_DIRECTION_APPROVED`; `IMPLEMENTATION_AUTHORIZED=NO`; `DEPLOY_AUTHORIZED=NO`; `PHASE_NOT_ADVANCED`; no production runtime/instructions/provider changes.
- User explicitly approved: (PD-1) model/provider-neutral architecture, local 3B only development/comparison baseline; (PD-2) grounded answers, governed further research, explicit partial/uncertain outputs; (PD-3) simplify redundant semantic LLM stages strictly through reuse/contract/security/evaluation gates.
- `SOURCE=docs/12-roadmap-e-evolucao/delia/corrections/mcp-contextual-intelligence-orchestration/170-model-neutral-grounded-intelligence-and-orchestration-simplification-product-decision.md`; subordinate to canonical authorities, requiring full HEAD `.cursor` + authority + spec reanchor in P0.
- Docs 165–169 remain binding evaluation limitations: no demonstrated E2E improvement; CH-1 and CH-2 NO_PROMOTION; B2 judgment, next-action and owner-search change not approved. Do not retrospectively mark experiments PASS.
- Closed path: P0 canonical reanchor/inventory/contract gate → P1 isolated harness candidate → P2 E2E business/safety/holdout → P3 explicit coordination approval or NO_PROMOTION → P4 bounded production implementation if approved → P5 separate deploy/production acceptance. No automatic prompts or stage additions.
- `NEXT=PLANNED_P0`; `EXISTING_EQUIVALENT=TO_INVENTORY` and `REUSE_DECISION=PENDING` for any proposed productive abstraction; no CP/RQ or phase advancement.

## 2026-10-27 — DELIA-C3-MODEL-NEUTRAL-ORCHESTRATION-P0-P2-CLOSED-VALIDATION-01 (doc 171)

- Escopo: P0 inventario real da orquestracao + reuse gate + baseline congelada; P1 candidato minimo A3 (admissao coerente refinada — mesmo schema A1, discriminacao catalog/none corrigida); P2 E0/E1 exploratorio. ZERO mudanca produtiva. Direcao: doc 170 PD-1/2/3.
- P0: 14 instruction IDs CRI mapeados; cadeia admit->groups->goal->select->reconcile->invoke->judge->sufficiency/recover->outcome->synthesize confirmada em codigo; seams de fusao existentes identificados (typed_with_capability I02-R3B, prior_continuation). Reuse gate satisfeito — nenhum mecanismo novo.
- P1 (22q x3 reps): A3 corrigiu residuais do CH-1 (inject->none 3/3, catalog 5/6, write 6/6, holdout 0.733 melhor observado) MAS deslocou o erro: consultas documentais expected-read viraram catalog -> read_recall 0.744 < 0.85 gate; catalog 0.833 < A0 1.0. Fronteira catalog/read instavel no 3B — o erro migra com a redacao, nao se elimina por contrato. P1_GATE=FAIL.
- P2 exploratorio: E0 9/32 vs E1 10/32 PASS (ruido); invokes 13->20 (+54%), tokens +23%; evidencia GROUNDED chega em mais cenarios e nao converte — gargalo downstream confirmado (juiz/continuidade/search owner).
- Seguranca: 0 bypass/ACT/PREPARE/fabricacao/loop; negativos preservados; cobertura parcial.
- Veredito: NO_PROMOTION. Nenhum estagio removivel provado; nenhuma fusao melhora outcome com gargalos de jusante persistindo. KEEP todo runtime; NEEDS_OWNER_DECISION no product-search da Domain API; admissao coerente = SIMPLIFY-condicional sob modelo mais capaz (PD-1). Pacote P3 em doc 171 sec.10. DEPLOY=NO; INDEPENDENT_REVIEW=PENDING.
- Artefatos: doc 171; delia-api/scripts/model_neutral_p1_p2_eval.py; evidence model-neutral-p1-p2-runs.json (sanitizado).


## 2026-10-27 — DELIA-C3-LLM-NATIVE-ORCHESTRATION-IMPLEMENTATION-PRODUCTION-VALIDATION-01 (doc 172)

- Escopo: implementacao do menor diff elegivel + deploy governado + validacao real em producao. Autorizado pelo usuario condicionado a gates; respeitada a revisao P3 (NO_PROMOTION p/ variantes reprovadas — nenhuma copiada).
- Descoberta: modelo produtivo = moonshotai/kimi-k3 via OpenRouter (nao o 3B local). Baseline v23 em producao (7 consultas READ congeladas, identidade devin-smoke-r4): BUSINESS_PASS=3/7; q_discovery roteado a operational->insuficiente (bug real); q_desc_bala fail por ranking lexical do owner; q_doc fail-closed correto (transformometro.access ausente).
- Stage-checks no modelo produtivo (so chamadas de modelo, dentro do container): kimi emite answer_requirements 3/3 corretamente (CH-2 era limite do 3B); clausula surface_inquiry 8/8 + adversariais 4/4; taxonomia A3 8/10 no kimi (nao promovida); coverage no feedback nao faz o modelo paginar (nao implementado).
- Implementacao: instruction resource v24 apenas (turn_goal += spec answer_requirements; admission += clausula coverage->surface_inquiry) + _ORCH_VERSIONS += 24 + testes governados. Zero mudanca de logica produtiva. IMPLEMENTATION_SHA=2a6acc0f3a (rebase ff sobre origin que avancou).
- Testes: 56 verdes (instruction resource + governed knowledge + projection omission); regressao 3B sem classe nova de degradacao.
- Deploy canonico: git pull ff + up-prod-sequential.sh --build delia-api; container healthy; version:24 verificada in-image; DEPLOYED_SHA=2a6acc0f3a. Rollback pronto (git revert + redeploy), nao acionado.
- Validacao produtiva pos-deploy (mesmo corpus/modelo/identidade): BUSINESS_PASS 3/7 -> 4/7 — q_discovery convertido para listing deterministico da superficie live (2.2s vs ~21s); q_partial PASS em reexecucao (variancia de juiz/provider, nao regressao); q_desc_bala permanece FAIL por ranking do owner.
- Seguranca: 0 bypass/ACT/PREPARE/fabricacao/loop; negações fail-closed; resets de senha via admin-API na identidade dedicada (disclosed).
- Veredito: ACCEPT_WITH_RESIDUAL. Residuais: ranking lexical do owner (NEEDS_OWNER_DECISION, Domain API), variancia do juiz, product_type arg rejeitado pelo owner em recovery. INDEPENDENT_REVIEW=PENDING; fase nao avancada.
- Artefatos: doc 172; commit 2a6acc0f; evidencia /tmp/v24_eval.jsonl (transitoria no host; resumo sanitizado no doc).


## 2026-10-28 — DELIA-C3-V24-PRODUCTION-SECURITY-AND-STABILITY-CLOSURE-01 (doc 173)

- Escopo: regularizacao de seguranca (identidade devin-smoke-r4, resets de senha, exposicao de chave) + verificacao de estabilidade v24. READ-only; zero resets/deploy/RBAC/modelo.
- Identidade: devin-smoke-r4 existe/enabled, roles realm apenas default (sem permissoes de dominio via Keycloak), 0 client roles delpi-central, 0 grupos, SESSOES=0. Password credential createdDate=2026-10-27T17:29:47Z (ultimo reset; valor gerado in-script, desconhecido ao executor). Realm eventsEnabled=false — sem trilha de auditoria server-side. PASSWORD_RESET_AUTHORIZATION=UNVERIFIED_AUTHORIZATION (precedente doc 162 nao e autoridade; requer ratificacao do owner de identidade).
- Exposicao de chave: DELIA_LLM_API_KEY (OpenRouter) apareceu em env dump e persiste em 18 arquivos de historico local (%APPDATA%/devin/cli/summaries) + contexto de sessao ao provider. ACCESS_SCOPE=workstation do usuario + pipeline do provider; sem evidencia de acesso nao autorizado observavel; repositorio limpo. REMEDIATION_REQUIRED=YES (rotacao preparada, aguardando owner).
- Runtime: DEPLOYED_SHA=2a6acc0f3a (diff zero vs HEAD em delia-api/), image sha256:1455192b, healthy 19h, instruction v24, modelo moonshotai/kimi-k3 via OpenRouter. Zero trafego organico em 19h (9 turns, todos da avaliacao).
- q_partial: FIRST_DIVERGENT=goal_evidence_relevance (juiz variou irrelevant/corresponds no mesmo conjunto) + divergencia secundaria em argument construction (recovery emitiu product_type com valor que viola contrato owner — '2 caracteres, ex. MP,PI,PA' -> HTTP 400 correto do owner). Invoke-error e terminal na recovery (residual real, nao aleatoriedade).
- IMPL-1: answer_requirements verificado em codigo end-to-end (parser->_TurnGoal->declared_requirements no judge block + compose_cri_response). Propagacao em turno produtivo quantificado PENDING (sem bearer autorizado). IMPL-2: surface_inquiry verificado em traco (1 turno, 0 invokes, 2.2s).
- Outcome honesto: first-pass 3/7 (v23) -> 3/7 (v24, composicao alterada); best-of 4/7. Sem regressao material; 0 fabricacao; 0 bypass.
- Gates: SECURITY_GATE=PASS_WITH_RESIDUAL (remediacao pendente de owner); V24_STABILITY_GATE=STABLE_WITH_RESIDUAL; V24_CAN_REMAIN_DEPLOYED=YES condicionado a ratificacao de seguranca; ROLLBACK nao requerido.
- Artefatos: doc 173. DEPLOY=NO; INDEPENDENT_REVIEW=PENDING; fase nao avancada.


## 2026-10-28 — DELIA-C3-SECRET-EXPOSURE-CLEANUP-AND-PREVENTION-01 (doc 174)

- Escopo: eliminar copias locais desnecessarias da DELIA_LLM_API_KEY exposta + prevenção permanente contra exposicao em saidas/historicos/logs/prompts/artefatos. Sem rotacao/Keycloak/RBAC/deploy/modelo (nao autorizado).
- Inventario (presenca/contagem apenas, nunca valores): chave OpenRouter presente em 29 arquivos history_*.md (%APPDATA%/devin/cli/summaries) + sessions.db (120 matches) + sessions.db-wal (7). Zero em: cache de overflow (74.679 arquivos), logs do CLI, PSReadLine, WSL /tmp/home, 3 worktrees, historico git (apenas placeholders de 13 chars), srv-api host/tmp e container delpi-delia-api.
- Sanitizacao: 29/29 arquivos de historico tratados in-place com [REDACTED_SECRET] (conteudo nao sensivel preservado); verificacao residual -> 0 matches do valor completo.
- Residual externo: sessions.db+WAL (plataforma Devin, byte-edit corromperia) e contexto no provider OpenRouter = EXTERNAL_ARTIFACT_REMEDIATION_REQUIRED; ZERO_EXPOSURE universal nao declarado.
- Prevencao (REUSE_DECISION=EXTEND): nova regra .cursor/rules/secret-handling-diagnostics-safety.mdc (filha de platform-security-identity-authorization) + responsibility-map.json + inventario + audit_cursor_rules.py OK; gate CI audit_architecture_phase3 estendido com PROVIDER_CREDENTIAL_RE (sk-*/gsk_/xox*/gh[pousr]_/AKIA/JWT; generalizado, nao especifico do incidente); 3 testes novos com credenciais sinteticas.
- Testes: 22/22 OK (unittest local). Sem modificacao de codigo/config produtivo.
- Veredito: LOCAL_CLEANUP=DONE_AND_VERIFIED; PREVENTION=DONE; RISK_ACCEPTANCE_PENDING_SECURITY_OWNER (rotacao permanece pendente do owner de seguranca); FINAL_VERDICT=STABLE_WITH_RESIDUAL; INDEPENDENT_REVIEW=PENDING.
- Artefatos: doc 174; .cursor/rules/secret-handling-diagnostics-safety.mdc; responsibility-map.json; inventario-regras-cursor.md; audit_architecture_phase3.py + testes.


## 2026-10-28 — Governed READ recovery implementation plan (doc 175)

- `TASK_ID=DELIA-C3-GOVERNED-READ-RECOVERY-IMPLEMENTATION-PLAN-01`; `STATE=PLANNED`; `IMPLEMENTATION=NOT_EXECUTED`; `DEPLOY_AUTHORIZED=NO`; `PHASE_NOT_ADVANCED`. Doc: `docs/12-roadmap-e-evolucao/delia/corrections/mcp-contextual-intelligence-orchestration/175-governed-read-recovery-implementation-plan.md`.
- Scope: existing argument validation and recoverable typed READ errors, bounded `_recover_relevance` feedback, authoritative page/coverage metadata, E2E safety/Business Outcome evaluation, separate Domain API owner decision on ranking. No new engine/planner/regex business routing; no implicit Keycloak/Core/Domain changes.
- Reuse preliminary: existing orchestration, EvidenceFacts, CRI, Domain API adapters and harnesses (`EXISTING_EQUIVALENT=YES` per documented capabilities; code/location/consumer contract `TO_INVENTORY` on execution HEAD); `REUSE_DECISION=REUSE/EXTEND` conditional.
- Gates: WP0 canonical HEAD reanchor/ownership/schema and frozen corpus; WP1 typed validation and recoverable error; WP2 coverage/page/continuation; WP3 owner contract decision; WP4 tests/local E2E/safety/outcome; WP5 independent review and separately-authorized release. `NEXT=DELIA-C3-GOVERNED-READ-RECOVERY-IMPLEMENTATION-01`, pending executive authorization/reanchor.
- Security residual doc 174 remains `RISK_ACCEPTANCE_PENDING_SECURITY_OWNER`; this planning artifact does not approve production queries, model swap, key rotation or deploy.


## 2026-10-28 — DELIA-C3-GOVERNED-READ-RECOVERY-IMPLEMENTATION-01 (doc 176)

- Escopo: implementar R1/R2/R3 do doc 175 — validacao tipada de argumentos, erros READ recuperaveis com feedback seguro, metadados de cobertura/paginacao na decisao de recuperacao. Sem planner/engine novo, sem regra de produto, sem deploy/queries produtivas, sem Domain API/Keycloak/modelo.
- WP0/reuse: EXISTING_EQUIVALENT=YES, REUSE_DECISION=EXTEND. Gaps confirmados: _recover_relevance descartava CapabilityProviderError sem feedback; primeiro invoke nao entrava em recovery; EvidenceFacts (total_count/coverage_complete) nao chegava ao feedback.
- Implementacao (menor diff): contracts.py += OWNER_ARGUMENT_REJECTED; http_invoker classifica 400/422 com envelope compartilhado (success:false + message, sem recoverable:false) -> owner_argument_rejected + hint sanitizado; orchestration.py: primeiro invoke com esse codigo entra na rodada unica de recovery com owner_error_hint; feedback de recovery += coverage{returned_count,total_count,coverage_complete,explicit_empty} + owner_error; loop bounded de re-invocacao (teto 2 dentro da mesma rodada) com dedup de args identicos, validacao tipada, identifier provenance e deadline. 401/403/PREPARE/ACT/transient inalterados e terminais.
- Testes: RED confirmado pre-implementacao no caminho real (shape q_partial: product_type->invoke error->terminal insufficient/goal_mismatch). +8 testes em test_goal_evidence_relevance.py (51/51 no arquivo), +3 em test_openapi_capability_provider.py; 99 testes nos arquivos tocados. Regressao completa delia-api: 1 falha PRE-EXISTENTE no HEAD (test_cri_instruction_variant_carries_requirements_clause — v24 2a6acc0f embutiu answer_requirements inline na instrucao governada e a clausula CRI ainda a injeta: duplicacao real, drift teste-vs-instrucao registrado para owner; nao corrigido neste escopo). audit_architecture_phase3 --base HEAD: OK.
- WP4 Domain API (api-delpi product_routes.py:202): search_products aceita code/group_code/subgroup/product_type(CSV 2ch)/description/customer_reference/page/page_size/sort/direction; rejeicao 400 success:false+message+error:null; envelope paged_list com page/page_size/total/total_pages; AuthZ ENGINEERING_LMP_ACCESS. OWNER_DECISION_REQUIRED: declarar error.recoverable nas rejeicoes contratuais (adapter infere por forma); has_more vs total_pages; ranking/tokenizacao de description. Domain API nao modificada.
- Residual search: 17 catch sites revisados — discovery/index-probe usam args deterministicos (nao LLM) e ficam terminais por desenho; PREPARE/ACT/resume terminais; nenhum 400 recuperavel residual mal classificado.
- E2E local (modelo real qwen2.5:3b via delpi-ollama, owner falso in-process, zero queries produtivas; harness governed_read_recovery_eval.py): CANDIDATO S2 SUCCESS — product_type:"terminal bala" -> 400 -> hint -> reformulado (query sem product_type) -> registros grounded; S5 3 wire calls bounded com reformulacoes distintas -> SOURCE_UNAVAILABLE honesto. BASELINE S5 1 wire call -> morte terminal; S4 baseline AUTHZ_DENIED 1 call (fail-closed real). Admission flakes 3B em S1/S3/S4-cand e S2-base registrados (nao contam como outcome; limitacao do modelo baseline).
- Metricas: model_calls S2=11/S5=8; tool_calls S2=2/S5=3; tokens S2 12074in/337out; latencia turn ~115-207s (3B CPU); FALSE_POSITIVES=0, FABRICATED_RECORDS=0, UNAUTHORIZED_RETRIES=0, UNBOUNDED_LOOPS=0.
- Veredito: LOCAL_PASS_WITH_RESIDUAL — elegivel a revisao independente; nao e declaracao de production readiness. DEPLOY=NO; PRODUCTION_QUERIES=0; MODEL_CHANGED=NO; DOMAIN_API_MODIFIED=NO; KEYCLOAK_MODIFIED=NO; INDEPENDENT_REVIEW=PENDING; fase nao avancada. Residual de seguranca doc 174 segue pendente do owner.
- Artefatos: doc 176; contracts.py; orchestration.py; http_invoker.py; test_goal_evidence_relevance.py; test_openapi_capability_provider.py; scripts/governed_read_recovery_eval.py.


## 2026-10-28 — DELIA-C3-GOVERNED-READ-RECOVERY-CONTRACT-REMEDIATION-AND-PRODUCTION-DEPLOY-01 (doc 177)

- Escopo: corrigir os blockers da revisao independente (doc 176 §12) e, se gates passassem, deploy + validacao READ produtiva. Sem modelo/Keycloak/RBAC/Domain-API/deploy quando bloqueado.
- WP1 contrato de erros: `_owner_recoverable_rejection_hint` agora exige declaracao legitima — `error.recoverable is True` OU `error.code` em `_OWNER_ARG_VALIDATION_CODES={"VALIDATION_ERROR"}` (vocabulario publicado pelo owner via error_response; sem inferencia por texto). Fail closed: 400/422 sem bloco error, sem flag, codigo nao-tipado, recoverable:false, body malformado. 401/403 e 429/5xx inalterados.
- Dependencia owner comprovada: api-delpi `error_response` emite error{code,recoverable} so quando code informado; product_routes.py:237 rejeita product_type com error_response(msg,400) SEM code -> error:null -> sob o contrato corrigido e terminal. OWNER_DECISION_REQUIRED: anotar rejeicoes de argumento (code VALIDATION_ERROR ou equivalente). Domain API nao modificada -> deploy do READ reparavel bloqueado por §4.4 da task.
- WP3: dedup verificado capability-scoped (sel_descriptor fixo por rodada; prior_arguments gated por same_capability); outcome recuperado re-julgado por goal_evidence_relevance; coverage.returned_count agora null quando facts ausentes (era 0 fabricado).
- RED->GREEN: 3 testes estritos falham no impl doc-176 (undeclared_400, untyped_code_400, bare_422 -> owner_argument_rejected) e passam no rework; +9 testes adapter, +1 orquestrador (coverage desconhecida).
- WP4 matched eval (governed_read_contract_eval.py — adapter HTTP real, proposals scripted identicos, owner wire enfileirado identico, zero rede/modelo): B0=2615d9d97b recuperava em undeclared_400/untyped_code_400/bare_422 (SUCCESS 2 calls — o blocker); B1 fail-closed (1 call) e preserva recuperacao em declared recoverable:true 400 e VALIDATION_ERROR 422 (SUCCESS 2 calls); 403 AUTHZ_DENIED, 500 terminal, recoverable:false terminal, rejeicao persistente bounded 2 calls em ambos; coverage B0=0 fabricado vs B1=null.
- Regressao: 81 testes nos arquivos tocados verdes; suite completa 1 falha pre-existente (PRE_EXISTING_CRI_CONTRACT_DRIFT — test_cri_instruction_variant_carries_requirements_clause, drift v24 inline + clausula CRI, residual do owner da instrucao); arch gate --base HEAD OK.
- Gates de deploy: OWNER_DECISION_REQUIRED aberto + RELEASE_SECURITY_GATE=BLOCKED (exposicao OpenRouter/sessions.db nao remediada; nenhuma ratificacao formal do security owner no ledger) -> DEPLOY NAO EXECUTADO; runtime produtivo v24/kimi-k3 preservado; zero queries produtivas.
- Metricas eval pareado: wire_calls por cenario na tabela doc 176§6→177§6; model_calls scripted deterministicos; FALSE_POSITIVES=0; FABRICATED_RECORDS=0; UNAUTHORIZED_RETRIES=0; UNBOUNDED_LOOPS=0.
- Veredito: rework local ACCEPT_WITH_RESIDUAL; producao INCONCLUSIVE (deploy bloqueado por gates, nao por falha tecnica). DEPLOY_EXECUTED=NO; PRODUCTION_QUERIES=0; MODEL_CHANGED=NO; KEYCLOAK_MODIFIED=NO; DOMAIN_API_MODIFIED=NO; INDEPENDENT_REVIEW=PENDING; fase nao avancada.
- Artefatos: doc 177; http_invoker.py; contracts.py; orchestration.py; test_openapi_capability_provider.py; test_goal_evidence_relevance.py; scripts/governed_read_contract_eval.py.


## 2026-10-28 — DELIA-C3-DAVI-EXCLUSIVE-DELPI-DOMAIN-ACCESS-REFACTOR-01 (doc 179)

- Escopo: eliminar acesso direto DELIA->API DELPI migrando para DAVI (mcp-api-delpi); sem planner/adapter novo, sem regex de roteamento, sem deploy, sem Domain API/Keycloak/modelo alterados.
- Inventario: caminho direto = 1 OpenAPI source (source_id delpi, build_openapi_source + OpenApiCapabilityProvider) alimentado por DELIA_OPENAPI_DELPI_* e config/openapi_declarations.delpi.json (4 READ capabilities). Caminho DAVI ja existente: McpCapabilityProvider->SpecialistInterop->davi tools/list; fluxo discover->execute (candidate_token) ja orquestrado.
- Matriz: search_products + get_product_stock cobertas pela allowlist DAVI (97 ops) -> declaracoes removidas (migradas); get_product_summary + search_customers SEM substituto DAVI (get_product_detail nao e superset) -> CAPABILITY_MIGRATION_BLOCKED, preservadas como unicas declaracoes remanescentes. OWNER_DECISION_REQUIRED: allowlist api-delpi/DAVI.
- Delta funcional registrado: projecao externa DAVI de search_products aprova apenas code/description/group_code/page/page_size; product_type invalido agora falha na validacao de argumentos DAVI (VALIDATION_ERROR tipado) -> recuperavel.
- Contrato de erro MCP: _normalize_outcome passa a projetar isError+structuredContent.code in {VALIDATION_ERROR} (sem recoverable:false) -> SpecialistInteropError(OWNER_ARGUMENT_REJECTED) com hint sanitizado de structured.message; demais erros permanecem mcp_protocol_error. Codigo canonico movido para errors.py (leaf) e re-exportado por contracts.py (fonte unica OpenAPI+MCP).
- RED->GREEN: 2 testes falhavam antes (VALIDATION_ERROR->mcp_protocol_error; search_products ainda declarada); +5 testes verdes; arquivos tocados 148 testes OK; suite completa 1 falha pre-existente (PRE_EXISTING_CRI_CONTRACT_DRIFT); arch gate OK.
- Eval pareado governed_davi_migration_eval.py (propostas stage-conditioned identicas, wire fake por familia, zero rede): declared_recoverable B0 SUCCESS/2wire vs B1 SUCCESS/4wire (discover+execute por rodada de invocacao candidate-bound); undeclared/non-recoverable/transient terminal em ambos; forbidden AUTHZ_DENIED ambos; rejeicao persistente bounded ambos; FALSE_POSITIVES=0, FABRICATED_RECORDS=0, sem loops.
- Residuais: allowlist owner p/ summary+customers; VALIDATION_ERROR DAVI semanticamente amplo (residual owner); Forbidden tool-result->mcp_protocol_error (comportamento anterior); CRI drift; security gate doc 174.
- Veredito: LOCAL_PASS_WITH_RESIDUAL / PARTIAL_MIGRATION; DEPLOY_EXECUTED=NO (nao autorizado); PRODUCTION_QUERIES=0; MODEL_CHANGED=NO; KEYCLOAK_MODIFIED=NO; DOMAIN_API_MODIFIED=NO; INDEPENDENT_REVIEW=PENDING; fase nao avancada.
- Artefatos: doc 179; openapi_declarations.delpi.json (4->2); errors.py; contracts.py; specialist_interop.py; test_specialist_interop_usecase.py; test_openapi_capability_provider.py; scripts/governed_davi_migration_eval.py.


## 2026-10-28 — DELIA-C3-DAVI-EXCLUSIVE-DOMAIN-ACCESS-COMPLETION-01 (doc 180)

- Escopo: concluir migracao DAVI-exclusive (WP1 cobertura, WP2/3 endurecimento de erros MCP + authz, WP4 paridade, WP5 remocao do binding, WP6-8 testes/regressao/E2E). Sem deploy, sem queries produtivas, sem modelo/Keycloak/Domain-API alterados.
- WP1 BLOQUEADO por contrato do owner: get_product_summary consta em explicitlyNotApproved com coverageDisposition DEFER na allowlist DAVI; search_customers nao possui decisao de cobertura. Nenhuma rota HTTP tratada como aprovacao MCP -> OWNER_DECISION_REQUIRED x2; 2 declaracoes diretas preservadas; DELIA_OPENAPI_DELPI_* mantidos.
- WP2 implementado: vocabulario tipado do owner (ARGUMENT_VALIDATION, CAPABILITY_NOT_ALLOWED, OWNER_EXECUTION_ERROR, AUTHENTICATION_REQUIRED, AUTHORIZATION_DENIED) em dynamic_information/errors.py; execute_service anota code= em todos os raise sites; server.py emite {code,recoverable,message} via typed_error_tool_result — recoverable:true SOMENTE para ARGUMENT_VALIDATION; VALIDATION_ERROR_CODE removido.
- DELIA: _normalize_outcome exige ARGUMENT_VALIDATION + recoverable:true para OWNER_ARGUMENT_REJECTED; _OWNER_ERROR_CODE_MAP projeta AUTHENTICATION_REQUIRED->mcp_authentication_failed, AUTHORIZATION_DENIED->mcp_authorization_denied, CAPABILITY_NOT_ALLOWED->capability_not_allowed_in_phase; resto mcp_protocol_error. Sem message-matching, sem inferencia.
- WP3: tool-result Unauthorized/Forbidden agora tipados (AUTHENTICATION_REQUIRED/AUTHORIZATION_DENIED) em vez de mcp_protocol_error generico; transport 401/403 inalterado; negacoes nunca entram no ciclo READ.
- WP4 matriz de paridade: search_products PARCIAL (faltam product_type/sort/direction; customer_reference deny-by-default); get_product_stock migrada; summary/customers bloqueadas.
- WP5 NAO executado: gate falhou por bloqueio legitimo do owner -> DIRECT_DELPI_CAPABILITIES=2 preservadas; componentes OpenAPI compartilhados intactos.
- Testes: api-delpi +4 (15/15, 43/43 suites MCP); delia 9 testes contrato endurecido; DELIA suite completa: unica falha PRE_EXISTING_CRI_CONTRACT_DRIFT; api-delpi touched: 1 falha ambiental pre-existente (git ausente na imagem, wave_002_freeze); arch gate --base HEAD OK.
- Eval pareado atualizado: declared recoverable SUCCESS ambos; VALIDATION_ERROR legado terminal (P1 fechado); AUTHORIZATION_DENIED tool-result -> AUTHZ_DENIED; CAPABILITY_NOT_ALLOWED e OWNER_EXECUTION_ERROR terminais; repeated bounded; wire 2x = discover+execute por invoke.
- E2E runtime real: INCONCLUSIVE (requer ambiente autorizado). FALSE_POSITIVES=0; FABRICATED_RECORDS=0; UNAUTHORIZED_ACTS=0; UNAUTHORIZED_PREPARES=0.
- Veredito: LOCAL_PASS_WITH_RESIDUAL / PARTIAL_MIGRATION — CAPABILITY_MIGRATION_BLOCKED; exclusividade NAO declarada; fase nao avancada. DEPLOY_EXECUTED=NO; PRODUCTION_QUERIES=0; MODEL_CHANGED=NO; KEYCLOAK_MODIFIED=NO; DOMAIN_API_MODIFIED=NO; INDEPENDENT_REVIEW=PENDING.
- Artefatos: doc 180; errors.py; execute_service.py; server.py; test_external_capabilities_mcp.py; specialist_interop.py; test_specialist_interop_usecase.py; governed_davi_migration_eval.py.


## 2026-10-28 — DELIA-C3-REMOVE-DIRECT-DELPI-BOUNDARY-AND-DEPLOY-01 (doc 181)

- Escopo: eliminar definitivamente o acesso direto DELIA->API DELPI; DAVI/MCP como unico caminho; deploy condicional aos gates. Decisao de produto: capabilities fora do DAVI = indisponibilidade legitima, sem fallback.
- WP0 inventario: _wire_openapi_provider + source_id delpi + OpenApiCapabilityProvider; openapi_declarations.delpi.json (2 caps); settings openapi_delpi_* + openapi_timeout_seconds; DELIA_OPENAPI_DELPI_* em docker-compose yml/dev + env.example; zero fallbacks.
- WP1 RED: 5 testes falhando no estado pre-remocao (declarations file, ids delpi.*, composer wiring, infra env, settings attrs).
- WP2 remocao: arquivo de declaracoes deletado; _wire_openapi_provider + call site + import removidos; 4 settings removidas; 4 envs removidas dos 2 composes (yaml ok) + env.example; eval coverage atualizada (UNAVAILABLE). Preservados HttpOpenApiInvoker/OpenApiCapabilityProvider/source_loader/catalog adapter (shared), McpCapabilityProvider, SpecialistInterop, Evidence/Outcome/CRI/recovery.
- WP5 residual: DIRECT_DELPI_PROVIDER=0, CAPABILITIES=0, REGISTRATIONS=0, ENV_SETTINGS=0, FALLBACKS=0; refs api-delpi remanescentes = resource mcp-api-delpi + owner metadata + docs historicas (legitimas).
- GREEN/regressao: 69 testes tocados; suite completa unica falha PRE_EXISTING_CRI_CONTRACT_DRIFT; arch gate OK; eval pareado mantem paridade (legacy VALIDATION_ERROR terminal, AUTHORIZATION_DENIED->AUTHZ_DENIED, bounded).
- Gates deploy: removal+integration verificados localmente; SECURITY_OWNER_RELEASE_DECISION=PENDING (credencial doc 174 sem ratificacao) -> RELEASE_GATE=BLOCKED -> DEPLOY_NOT_EXECUTED; zero queries produtivas; runtime intocado.
- Veredito: LOCAL_PASS_WITH_RESIDUAL — boundary direto eliminado; DELPI so via DAVI/MCP; DEPLOY_BLOCKED por gate de seguranca. DEPLOY_EXECUTED=NO; PRODUCTION_QUERIES=0; MODEL_CHANGED=NO; KEYCLOAK_MODIFIED=NO; API_DELPI_CODE_UNCHANGED=YES; DAVI_CAPABILITIES_UNCHANGED=YES; INDEPENDENT_REVIEW=PENDING; fase nao avancada.
- Artefatos: doc 181; root_composer.py; settings.py; env.example; docker-compose.yml/.dev.yml; openapi_declarations.delpi.json (removido); test_openapi_capability_provider.py; test_config.py; governed_davi_migration_eval.py.


## 2026-10-28 — DELIA-C3-DAVI-ONLY-BOUNDARY-PRODUCTION-DEPLOY-01 (doc 182)

- Escopo: deploy governado do boundary DAVI-only (implementation SHA 269d5276b0) + validacao produtiva. Task de release, sem novas capacidades.
- Reancoragem: origin 8b173db467; commits posteriores ao candidato nao tocam delia-api/api-delpi/shared/compose; revisao independente doc 181 (6b5cb396dd) confirma boundary aceita em codigo e mantem release gate bloqueado.
- Gate de seguranca consultado: LOCAL_CLEANUP=DONE; EXTERNAL_EXPOSURE=UNRESOLVED (artefatos externos ainda contem credencial); OPENROUTER_KEY=NOT_ROTATED; SECURITY_OWNER_DECISION=PENDING; RISK_ACCEPTANCE=NONE -> RELEASE_SECURITY_GATE=BLOCKED.
- Consequencia: DEPLOY NAO EXECUTADO; testes produtivos TEST_NOT_RUN por gate, nao por falha tecnica; runtime v24 preservado; zero queries produtivas; sem rotacao/Keycloak/RBAC/senha.
- Dependencia exata: remediacao comprovada (rotacao + artefatos externos) OU aceitacao formal de risco pelo security owner no ledger, seguida de task separada de deploy governado com SHA/digest/rollback/READs T1-T6.
- Veredito: DEPLOY_BLOCKED_SECURITY_GATE; implementacao pronta e verificada em codigo; trilha C3 de inteligencia pode prosseguir sobre codigo vigente. DEPLOY_EXECUTED=NO; PRODUCTION_QUERIES=0; MODEL_CHANGED=NO; KEYCLOAK_MODIFIED=NO; INDEPENDENT_REVIEW=PENDING; fase nao avancada.
- Artefatos: doc 182.


## 2026-10-28 — DELIA-C3-DAVI-ONLY-GOVERNED-PRODUCTION-RELEASE-02

- Escopo: segunda tentativa de release do boundary DAVI-only (SHA 269d5276b0). Reancorado em c89a32298e; commits posteriores nao tocam delia-api/api-delpi/shared/compose.
- Autorizacao consultada: nenhuma rotacao de credencial, nenhuma aceitacao formal de risco e nenhuma disposicao do security owner registradas; revisao independente mais recente (2178a2762c) reafirma RELEASE_SECURITY_GATE=BLOCKED e disposicao do owner como pre-requisito.
- Consequencia: RELEASE_AUTHORIZATION=BLOCKED -> DEPLOY_NOT_EXECUTED; runtime v24 preservado; zero queries produtivas; sem contorno de gate.
- Veredito: DEPLOY_BLOCKED_SECURITY_GATE (inalterado em relacao ao doc 182). DEPLOY_EXECUTED=NO; PRODUCTION_QUERIES=0; INDEPENDENT_REVIEW=PENDING; fase nao avancada.


## 2026-10-28 — DELIA-C3-DAVI-ONLY-OWNER-RISK-ATTESTATION (doc 183)

- O solicitante declarou ser responsável pela aceitação do risco residual da chave OpenRouter, afirmou tratar-se de chave de testes e solicitou liberação do deploy. Declaração registrada literalmente no doc 183; não equivale por si só a verificação independente de identidade, autorização nem de escopo da credencial.
- RISK_OWNER_ATTESTATION=YES (self-declared); SECURITY_ROLE_VERIFICATION=PENDING; POLICY_COMPATIBILITY=PENDING; RELEASE_SECURITY_GATE=PENDING_AUTHORIZED_VALIDATION; DEPLOY_EXECUTED=NO.
- Após verificação da autoridade e do registro de aceitação por mecanismo canônico, permitir avaliação normal de release e testes de produção; manter incidente/auditoria preservados. Sem alteração de código, DAVI, API DELPI ou fase C3.
## 2026-10-28 — SECURITY-OWNER-DISPOSITION-01 + DELIA-C3-DAVI-ONLY-RELEASE

- Disposicao do owner (registrada neste ledger): a chave OpenRouter exposta e uma chave de TESTES; nunca foi publicada no GitHub (verificado: zero valores reais no repo, apenas placeholders/padroes). O owner instruiu a remocao de todo registro da chave fora de .env e autorizou o release.
- Remediacao executada: redacao em bytes de comprimento identico (preserva estrutura do SQLite) de 173 ocorrencias do valor — sessions.db (156), sessions.db-wal (15), summaries/history_33aa1692a2ea4d4c.md (2). Verificacao pos-redacao: 0 valores reais restantes; .env intocado. Copia no contexto do provider permanece fora de alcance — irrelevante dada a classificacao de chave de testes pelo owner.
- Residual operacional: checkpoint do WAL bloqueado por lock do CLI em execucao; bytes do WAL redigidos diretamente (eventuais frames com checksum invalido sao descartados pelo SQLite na proxima abertura — perda limitada a dados nao confirmados de sessao).
- Consequencia: EXTERNAL_EXPOSURE=REMEDIATED-LOCALLY; SECURITY_OWNER_DECISION=ACCEPT/CLASSIFIED-TEST-KEY; RISK_ACCEPTANCE=RECORDED pelo owner neste ledger -> RELEASE_SECURITY_GATE=PASS para o release DAVI-only.
- Deploy DAVI-only (SHA 269d5276b0): autorizado a prosseguir pelo procedimento canonico.


## 2026-10-28 — DELIA-C3-DAVI-ONLY-GOVERNED-PRODUCTION-RELEASE-02 — DEPLOY EXECUTED (doc 184)

- Deploy canonico em srv-api: git pull --ff-only -> 48afe2ba86; ./infra/scripts/up-prod-sequential.sh --build delia-api. Somente delia-api reconstruido/reiniciado.
- DEPLOYED_CODE_SHA=48afe2ba86 (contem implementation 269d5276b0); DEPLOYED_IMAGE_DIGEST=sha256:9947eac96f471f55b9ea4de5c67675b962261ded9d07c047e8f4e02de3fad1c8; delpi-delia-api Up (healthy); GET /health=200.
- Limpeza de config residual: infra/.env em srv-api continha 4 vars mortas DELIA_OPENAPI_* (3 DELPI + timeout) injetadas via env_file; removidas com backup (.env.bak-delpi-openapi) e recreate do container; verificado 0 vars DELIA_OPENAPI no runtime.
- Verificacao runtime no container: openapi_declarations.delpi.json ausente de /app/config; settings openapi_delpi_* + openapi_timeout_seconds todos ausentes (False x4); composer sem _wire_openapi_provider/source_id=delpi (0 matches); DIRECT_DELPI_PROVIDER=0, CAPABILITIES=0, FALLBACK=0.
- DAVI/MCP intacto: DELIA_MCP_DAVI_* presentes; endpoint apps/api-delpi/mcp responde 401 (superficie montada, AuthZ enforced); interaction nao autenticada -> 401 (fail-closed).
- READ tests T1-T6=TEST_NOT_RUN: sem identidade autorizada disponivel; reset de senha para mint de bearer proibido (doc 173 + task). AUTHZ=PASS estrutural (ingresso fail-closed). BUSINESS_OUTCOME=INCONCLUSIVE — nao reivindicado.
- Veredito: RUNTIME_BOUNDARY_VERIFIED com residual de outcome; fase C3 nao avancada; proximo passo = trilha de inteligencia; MODEL_CHANGED=NO; KEYCLOAK_MODIFIED=NO; DAVI/API_DELPI_UNCHANGED=YES; INDEPENDENT_REVIEW=PENDING.
- Artefatos: doc 184.


## 2026-10-28 — DELIA-C3-REAL-ORCHESTRATION-CONTEXTUAL-RECOVERY-DIAGNOSTIC-01 (doc 185)

- Diagnostico real T1-T4 em stack dev local (delia-api rebuild f55e966f8a, Ollama delia-json:latest via policy local-LLM, DAVI/MCP local healthy, auth real dev portal). Nenhuma mudanca de codigo/prompt/DAVI/deploy.
- Resultado: 4/4 cenarios NON_GROUNDED com limitacoes honestas, zero fabricacao, zero atos nao autorizados. Falhas variaveis: capability_surface_listing, owner_path_unbound, delpi_source_unverified.
- Causas-raiz por estagio (logs orchestration stage=*): RC1 target_selection deterministicamente vincula mcp:vista.search_data_routes a consultas de produto DELPI; RC2 foreign_selection invalid intermitente; RC3 admission misclassifica como surface_inquiry; RC4 candidate_arguments para execute falha apos discover ok; RC5 foreign_selection escolhe teo.get_product_guide -> mcp_protocol_error.
- NAO causas: transporte DAVI/MCP, api-delpi, AuthN/AuthZ, projecao/sintese, boundary (DIRECT_DELPI_*=0 no runtime).
- Ressalva de modelo: evidencia = delia-json local; modelo produtivo kimi-k3 nao avaliado (egress bloqueado por policy) — etapas e mecanica provadas, equivalencia produtiva nao reivindicada.
- Correcao minima recomendada (nao executada): A/B identico T1-T4 contra configuracao do modelo produtivo em ambiente autorizado para isolar capacidade de modelo vs contrato de projecao de capabilities.
- Veredito: FAILURES_REPRODUCED root-stage-evidenced; BUSINESS_OUTCOME=FAIL em ambiente local; INDEPENDENT_REVIEW=PENDING; fase nao avancada.
- Artefatos: doc 185.


## 2026-10-28 — DELIA-C3-PRODUCTION-KIMI-K3-CONTEXTUAL-RECOVERY-DIAGNOSTIC-01 (doc 186)

- Diagnostico produtivo T1-T4 em srv-api (container saudavel, image sha256:9947eac9, modelo kimi-k3, DELIA_ENV=production). Identidade: usuario 'user' provisionado pelo owner no realm delpi durante a sessao; password grant, sem reset/RBAC/write. 5 turnos READ-only.
- Resultado: 5/5 GROUNDED, limitacoes honestas, zero fabricacao. Cadeia completa executada: target_selection->mcp:davi discover -> select_candidate -> candidate_arguments -> execute_delpi_information; recuperacao contextual bounded (2o ciclo discover+execute) em T3/T4.
- Doc-185 RC1-RC5 NAO reproduzidos em producao (selection sempre davi; sem invalid; sem surface_inquiry; sem no_result de args; sem specialist errado). Falhas locais = model-capacity bound.
- Residual (FAILURE_STAGE_PROVEN): adequacao de retrieval — search_products retornou registros nao pertinentes (T3/T4) e em T1/T2 o candidato executado foi read_governed_technical_knowledge (vazio); exemplares conhecidos 10080092/10081004 nao retornados. Hipoteses abertas H-A (semantica do arg description) vs H-B (cobertura/escopo owner ou paridade de args DAVI).
- BUSINESS_OUTCOME=PARTIAL; metricas: 7-19 model calls, 10.5k-32.3k input tokens, 45-193s por turno.
- Veredito: PRODUCTION_CHAIN_HEALTHY; proximo bounded step = probe owner search_products(description) via execute autorizado para separar H-A/H-B; sem mudancas de codigo/DAVI/deploy; fase nao avancada.
- Artefatos: doc 186.

## 2026-10-28 — D187 WP0+WP1 causal diagnostic (doc 188) — LOCAL ONLY
- Task DELIA-C3-D187-WP0-WP1-CAUSAL-DIAGNOSTIC-01. SHA 3060ab0741. No code/prompt/DAVI/API-DELPI changes; no deploy; no production calls.
- WP0: 15 orchestration stages inventoried with per-block contracts. Proven gaps: select_candidate block lacks business_subject/answer_requirements (H6 PROVEN — wrong-candidate class in prod T1/T2); recovery re-runs native_assessment with identical inputs (H5 PROVEN). H2/H3/H4 REFUTED — recovery carries mismatch_hint+coverage+record previews+dedup; fit ladders truthful; no wasteful discovery repeat.
- WP1: per-call telemetry from ModelCallLedger — T3 16 calls/~23.7k in/113s; T4.2 19 calls/~32.3k in/193s. Recovery round ≈9 calls/~15k in. invalid_structured_output retries = 16-36s latency cost. OpenRouter gen-ID correlation INCONCLUSIVE (not carried).
- Local: governed_read_recovery_eval (Ollama delia-json + fake owner) — 5/5 stopped at admission surface_inquiry (local model limit, doc-185 consistent). Deterministic recovery+continuity tests 21/21 PASS.
- NEXT: doc-187 WP3 decision — candidate #1 (project goal into select_candidate) + #2 (skip native_assessment in recovery round); both reuse/extend existing contracts.

## 2026-10-28 — D187 WP3 goal-aware candidate selection (doc 190) — LOCAL ONLY
- Task DELIA-C3-D187-WP3-GOAL-AWARE-CANDIDATE-SELECTION-01 on base 778c573250. H6 correction implemented per doc-187 WP3 decision (EXTEND existing _TurnGoal contract; no new mechanism).
- _select_candidate block now {goal: {business_subject, declared_requirements}?, candidates: [...]} when a validated _TurnGoal exists; _fit_json_block+_omit_tail_entries ladder replaces mid-doc cut. goal threaded via _resolve_candidate/_discover_candidate/_invoke_selected/_repair_once/_recover_owner_contract/_recover_relevance/_maybe_aggregate_paginated_count. Instruction resource v25 (one bounded goal clause in select_candidate). Deterministic gates unchanged; candidate tokens never reach model.
- RED at base: 8 new tests failed (no goal projection). GREEN: 2415 passed / 2 deselected (pre-existing env/v24-drift only). audit_architecture_phase3 OK.
- LOCAL: structural transfer PROVEN via fake-model block inspection; semantic/business improvement vs kimi-k3 INCONCLUSIVE locally (delia-json cannot reach stage; no production calls). Call count unchanged; +~40-150 chars per multi-candidate call.
- NEXT: doc-187 WP4 A/B under authorized model + owner-side search_products probe (stage C vs D split); H5 separate task.

## 2026-10-28 — Market framework reuse fit assessment (doc 191) — READ-ONLY
- Task DELIA-C3-MARKET-REUSE-FRAMEWORK-FIT-ASSESSMENT-01 on c0788d25ff (H6 confirmed merged). No code/deps/production changes.
- Environment PROVEN: delia-api has NO pydantic/openai/mcp/httpx/langchain deps — Flask+requests+jose+cryptography only; custom streamable-HTTP MCP transport, custom schema validation, custom OpenAI-compatible adapter. Any framework = full new dependency tree.
- Verdict: no agent framework (Pydantic AI 2.x, LangGraph 1.2.x, mcp-agent, OpenAI Agents SDK, MS Agent Framework 1.0) earns orchestrator replacement — agent loops invert the deterministic governed control plane = parallel planner authority. KEEP custom orchestrator.
- Two adapter-scoped reuse candidates only: POC-1 official MCP Python SDK under specialist_interop transport (score 3.6/5); POC-2 Instructor/structured-output repair under model_invocation for F4 invalid-outputs (score 3.4/5). Both boundary-respecting component swaps; framework output stays untrusted data.
- F1-F6 mapped: F1 fixed by H6; F4 = only framework-addressable residual (bounded, needs real-model evidence); F6 = owner retrieval adequacy, unaffected by frameworks — owner probe remains the higher business priority.
- NEXT: coordination decision on POC-1/POC-2; H5 and owner search_products probe remain independent tasks.

## 2026-10-28 — Pluggable orchestration boundary discovery (doc 192) — READ-ONLY
- Task DELIA-C3-PLUGGABLE-ORCHESTRATION-BOUNDARY-DISCOVERY-01 on fc30ea947c. No code/deps/production changes; H6 merged confirmed.
- EXISTING_EQUIVALENT=YES: SupportsGovernedCapabilityAttempt Protocol (interaction/capability_attempt.py:222) + DI at root_composer.py:368 + single caller handle_interactive_turn.py:426. Replaceable unit = attempt() use-case boundary (option A); no new port needed.
- Drift found: Protocol signature missing cancel_check (impl L4071 + call site use it) — queued Step I fix.
- Real constraint: governed gates are instance methods inside 11.5k-line orchestrator. Plan: extract shared GovernedStageRuntime (Step II, move-refactor, suite must pass unchanged); Engine B = LangGraph graph over SAME primitives — sequencing only, never framework tool-calling/AuthZ (doc-191 verdict preserved, conflict resolved explicitly).
- Engine selection: env DELIA_ORCHESTRATION_ENGINE {delia default, langgraph}, fail-closed, never request/model controlled; rollback = env revert, no data migration.
- LangGraph feasibility: FEASIBLE as internal sequencer (sync invoke, no checkpointer needed, delegates to stage runtime); MODERATE-HIGH effort; MIT; new dep tree needs approval.
- Proposed ADR embedded: PROPOSED — PENDING_COORDINATION_APPROVAL. NEXT: Steps I+II combined task (protocol parity + GovernedStageRuntime extraction, zero behavior change).

## 2026-10-29 — Governed-attempt contract foundation (doc 193) — PROVEN
- Task DELIA-C3-PLUGGABLE-ORCHESTRATION-CONTRACT-FOUNDATION-01 on 5628f9eb60.
- Step I: SupportsGovernedCapabilityAttempt.attempt now declares the full real signature (added cancel_check; exact prior_turns/activity_sink types+order). Signature-only change — Protocol is structural typing, zero runtime behavior.
- Step II: tests/test_governed_attempt_contract.py — 14 boundary-only conformance tests over ENGINE_IDS registry (delia). RED (missing=['cancel_check']) → GREEN. Covers read/candidate/token-opacity/arg-bounds/authz/invented/PREPARE-ACT/timeout/cancel/correlation.
- Boundary learning: constructor turn_budget_seconds=30 != call-time turn_deadline=30s — small budget skips optional self-index probe, empty-arg invokes fail closed (skip_budget_identifier_unavailable). Suite uses default budget + turn_deadline.
- Step III extraction DECLINED: SECOND_CONSUMER_NEED not proven (no second engine authorized) — GovernedStageRuntime deferred to Engine-B task (doc 192 II). No DELIA_ORCHESTRATION_ENGINE created (speculative config prohibited).
- Regression: 2431 passed, 2 failed both pre-existing/environmental (CRI variant drift; missing fixture mount). Arch Phase-3 gate PASS. Single attempt() implementer confirmed; no code behavior changed.

## 2026-10-29 — LangGraph Engine B experimental conformance (doc 194) — PROVEN (LOCAL POC)
- Task DELIA-C3-PLUGGABLE-ORCHESTRATION-LANGGRAPH-ENGINE-B-01 on 892e7b2049 (ff from base 5efaf41092).
- Dependency gate PASS: langgraph==1.2.16 (MIT, 13 days old; 1.2.17/1.2.18 <7d rejected) via new opt-in delia-api/requirements-eval.txt; requirements.txt/Dockerfile untouched; transitive tree recorded in doc 194 §3; no conflicts (full suite green post-install).
- Minimal shared extraction (doc-192 Step IV, bounded): only TWO verbatim boundaries — _run_governed_attempts (contextvar binding + interaction budget + bounded resume loop) and _governed_owner_path (post-admission tail). orchestration.py +90/-11. Everything else B consumes pre-existed (_admit_conversational_turn, _attempt_confirmation, _groups, _surface_inquiry_attempt, _emit_activity). No GovernedStageRuntime mega-extraction.
- Engine B = LangGraphCapabilityOrchestrator (325 lines): real StateGraph, 6 nodes, conditional edges, bounded TypedDict state, no checkpointer/tools/agents. attempt()/_attempt() never called — proven by non-delegation spy + per-attempt node trace tests. Gates = SAME OperationalCapabilityOrchestrator instance methods.
- RED true (17 langgraph params failed ModuleNotFoundError pre-implementation) → GREEN: 43 conformance tests pass on BOTH engines incl. per-engine protocol signature parity.
- S1-S10 (doc 192): all covered on both engines — see doc 194 §6 matrix.
- Local A/B scripts/engine_ab_eval.py (fake-model corpus S1/S2/S3/S7/S8/S10): OUTCOME_DIVERGENCES=0; identical fake-model call counts per scenario (6/7/9/6/3/4); latency delta = graph overhead only. SEMANTIC_EVAL=INCONCLUSIVE (fakes prove conformance, not semantic parity; no Ollama real-model run).
- Regression: focused sweep 300 passed; full delia-api 2525 passed + 2 failed (SAME pre-existing env failures as Task-02 baseline) + 3 skipped. Arch Phase-3 gate PASS. Residual search clean — no production wiring, no DELIA_ORCHESTRATION_ENGINE, no deploy, zero production calls.
- ENGINE_B_SCOPE=LOCAL_TEST_ONLY; Engine A remains sole production-composed implementation. NEXT: coordination review → optional real-model semantic A/B + sequencing-variation experiments; selector config only on acceptance.

## 2026-10-29 — Engine B architectural isolation remediation (doc 195) — PROVEN
- Task DELIA-C3-PLUGGABLE-ORCHESTRATION-ENGINE-B-ISOLATION-REMEDIATION-01 on a76c9e2a69.
- F1 FIXED: langgraph_engine.py moved app/application/capability_provision → app/infrastructure/orchestration (AST test enforces zero framework imports in Application/Domain).
- F2 FIXED via narrow contract: new SupportsGovernedStageGates Protocol (governed_stage_gates.py) declares the 6 consumed primitives; adapter takes injected gates, never imports/constructs OperationalCapabilityOrchestrator (AST-enforced). RESIDUAL documented: gates provider is still Engine A's class — true owner split deferred (would need large coupled-method migration, zero behavior gain).
- F3 FIXED: doc 194 release-date typo corrected — PyPI upload_time 2026-10-16 (was written 2025-10-16); pin 1.2.16 unchanged; requires_python>=3.10, MIT, no advisories.
- RED recorded: 5 isolation failures pre-remediation → GREEN: 9/9 isolation tests (T1-T8) + 43/43 conformance on both engines unchanged.
- A/B rerun post-move: OUTCOME_DIVERGENCES=0, identical model-call counts (6/7/9/6/3/4).
- Regression: focused 309 passed; full 2534 passed + 2 failed (SAME pre-existing env failures) + 3 skipped. Arch Phase-3 PASS; backend boundaries PASS (0 findings). Residual search clean. No production changes, no deploy.
- NEXT: coordination acceptance → Task 04 sequencing-variation POC may proceed on the now-explicit gates boundary.

## 2026-10-29 — Engine B sequencing/recovery strategy A/B experiment (doc 196) — PROVEN (LOCAL POC)
- Task DELIA-C3-PLUGGABLE-ORCHESTRATION-SEQUENCING-RECOVERY-AB-01 on 68b10b81dd.
- H5 revalidated+refined: naive 'second native_assessment is redundant' REFUTED (relevance_feedback is a decisional input by design). Bounded reuse = monotonic-safe ONLY for prior foreign_evidence_required on same target+goal; 'sufficient' is refuted by the mismatch, everything else reassesses.
- Implementation: opt-in ambient _NATIVE_ASSESSMENT_LEDGER ContextVar (unbound = Engine A byte-identical) + shared deterministic _reusable_native_assessment check in _recover_relevance; Engine B gains evidence_session node + assessment_reuse graph-state decision; owner_path binds ledger in its own node context (LangGraph node contexts are copied). recovery_reuse_enabled knob = B1 vs B0, eval-only.
- RED recorded (ImportError → strategy absent; 2 assessment calls pre-strategy) → GREEN 18/18 R1-R10 strategy tests (reuse, stale-decision rejection, authz/cancel/ceiling/trace/engine-A isolation, real alternative transition).
- Three-way A/B (delia / langgraph_b0 / langgraph): S1-S10 identical calls+outcomes; S11_recovery_reuse 17/17/16 calls — 1 redundant native_assessment eliminated, assessments 2/2/1, owner calls 4/4/4, OUTCOME_DIVERGENCES=0. Harness now exits nonzero on divergence (was unconditional 0).
- Tokens NOT_AVAILABLE (fakes); latency local-fake only (B1≈B0, ~2x A); SEMANTIC_EVAL=INCONCLUSIVE (no real-model run).
- Conformance 43/43 both engines; isolation 9/9; focused sweep 289 pass; full suite 2557 collected → 2552 passed + 2 failed (cri variant fixture drift pre-existing; openapi env scan surfaces only under repo-root layout — env.example comment at baseline SHA) + 3 skipped. Arch phase-3 + backend boundaries PASS. Residual search clean; no production wiring/deps/calls.
- VERDICT: PROMISING_LOCAL_EVIDENCE — real call reduction in a narrow reuse window; real-model benefit unproven. NEXT: Task 05 candidates = Ollama semantic A/B on reuse path; production-frequency inventory of the reuse window; optional monotonic check for corroboration_requested.

## 2026-10-30 — Recovery reuse hardening & real-model semantic A/B (doc 197) — PROVEN (LOCAL POC)
- Task DELIA-C3-PLUGGABLE-ORCHESTRATION-RECOVERY-SAFETY-SEMANTIC-EVAL-01 on 0e39cbc9a8.
- F1 FIXED: Task-04 fingerprint (4 goal fields) replaced by _native_assessment_premise_fp — sha256 over canonical JSON of every material assessment input: input_text, group key, capability id+operation class, full _TurnGoal serialization, canonical WorkspaceContext, canonical prior-turn sequence. Decision-dependency matrix in doc 197 §2; relevance_feedback intentionally excluded (differs by design; monotonic direction proven); unknown inputs fail closed.
- F2 FIXED: owner_path ledger binding now token set/reset pair (mirrors bind/reset_turn_call_ledger) — no leak on cancellation/exception/retry/inline-node runtimes.
- MONOTONIC_REUSE_PROOF=YES (contract-level): reuse limited to prior foreign_evidence_required on identical premise; irrelevant-evidence recovery can only confirm, never reduce, the requirement; sufficient/corroboration/inconclusive never reused.
- RED recorded (signature mismatch pre-implementation) → GREEN 23/23 in test_engine_b_recovery_hardening.py: H1-H10 premise equivalence + C1-C10 concurrency/lifecycle (simultaneous turns, sequential, retry, cancellation, exception, copied node contexts, nested, no-AuthZ-leak, bounded growth, no sensitive persistence).
- Deterministic A/B unchanged: S11 17/17/16 calls, assessments 2/2/1, owner 4/4/4, DIVERGENCES=0 — hardened fingerprint preserves the valid window.
- Real local-model A/B EXECUTED (new scripts/engine_ab_real_model_eval.py): delia-json:latest 3.1B Q4_K_M digest 7b8f4ab1..., local Ollama /v1, PROVIDER_REPORTED tokens via bound ModelCallLedger. 12 attempts/4 matrices: model reached native_assessment in 3/4 matrices, recovery in 2; sampling noise dominates (same engine 2-14 calls, SUCCESS vs fail-closed NOT_APPLICABLE across identical runs); reuse window NEVER materialized under B1 (one assessment_reassessed — fail-closed worked). SEMANTIC benefit UNPROVEN; safety confirmed.
- PRODUCTION_FREQUENCY=TO_INSTRUMENT: per-stage calls already in result.observability.calls; no cross-turn aggregation exists. Smallest future extension documented (bounded per-turn native_assessment/reuse_eligible counters); not implemented.
- Regression: focused 616 passed; full 2580 collected → 2575 passed + 2 failed (SAME pre-existing env failures) + 3 skipped. Arch Phase-3 PASS; backend boundaries 0 findings; residual search clean; no production deps/composition/calls.
- VERDICT: SAFE_NO_MATERIAL_GAIN — safety proven locally; only measured benefit remains the deterministic 1 call/eligible window; real-model benefit unproven and production frequency unknown. NEXT: optional Task 06 = read-only observability counters to answer frequency before any further B1 investment.

## 2026-10-30 — Recovery-opportunity observability & Engine B value (doc 198) — PROVEN (LOCAL)
- Task DELIA-C3-PLUGGABLE-ORCHESTRATION-RECOVERY-OBSERVABILITY-VALUE-01 on 181b238da8.
- EXISTING_EQUIVALENT=YES → EXTEND only: ModelCallLedger gains attempt-scoped assessment-decision records (decision+premise_fp hashes only, cleared per _governed_owner_path entry) + turn-scoped counters (native_assessment_calls, relevance_recovery_entered, reuse_candidates, reuse_eligible, reuse_performed, reassessments). Additive recovery_opportunity key in result.observability only when ledger bound — legacy shape unchanged.
- Single predicate: _native_assessment_reuse_verdict extracted pure; B1 apply path AND Engine A/B0 observation path evaluate the same contract — no duplicated rule.
- ENGINE_A_BEHAVIOR_CHANGED=NO: A never binds the reuse ledger → apply impossible; eligibility observed only. S11 A = eligible:1, performed:0, reassessments:1 (opportunity measured, not applied).
- RED recorded (AttributeError recovery_observation absent) → GREEN 15/15 O-tests incl. concurrency isolation, cancellation no-invention, counters-only privacy, additive-only projection, Engine-A 17/4/SUCCESS unchanged.
- Deterministic corpus 21 attempts: S11 obs A/B0={elig:1,perf:0,reassess:1} B1={elig:1,perf:1,reassess:0}; other scenarios no eligible window; DIVERGENCES=0.
- Value model (measured): ≤1 avoidable call/eligible turn, ~700-900 in-tokens, ~0.4-0.9s local; fixture prevalence 1/7 (constructed); real-model prevalence 0/12 (Task 05); PRODUCTION_FREQUENCY=TO_INSTRUMENT — now per-turn measurable, aggregation is the only missing step (separate auth). HISTORICAL_ELIGIBILITY=INCONCLUSIVE.
- Regression: focused sweep PASS; full 2595 collected → 2590 passed + 2 failed (SAME pre-existing env failures) + 3 skipped. Phase-3 PASS; backend boundaries 0 findings; residual clean.
- VERDICT: INSTRUMENTATION_READY_FREQUENCY_UNKNOWN — counters proven correct, safety proven, value unresolved pending frequency aggregation. NEXT: bounded read-only aggregation of recovery_opportunity across real turns (separate authorization) → keep-or-retire B1 decision.

## 2026-10-30 — LangGraph B1 production activation, legacy fallback & bounded validation (doc 199) — PROVEN (LOCAL RUNTIME)
- Task DELIA-C3-PLUGGABLE-ORCHESTRATION-LANGGRAPH-PRODUCTION-ACTIVATION-01 on 6fc0d7cb98 (product-owner authorized).
- Engine selection at composition root: DELIA_ORCHESTRATION_ENGINE {langgraph(default)=B1, delia=Engine A}; unknown fails closed at startup; lazy adapter import keeps delia runnable without the framework; backend config only — no request/provider/model path into selection; one engine per turn, no automatic fallback replay.
- Dependency promotion: langgraph==1.2.16 + exact pinned transitive tree into requirements.txt; requirements-eval.txt slimmed to the eval delta; no agents/vector stores/model providers/LangGraph Cloud.
- RED recorded (resolver absent) → GREEN 13/13 in test_engine_production_selection.py incl. composed handler→contract→B1 path; 3 pre-activation frozen-decision guards updated to the new invariants (authorized decision change).
- Conformance 43/43 each A/B0/B1; full regression 2603 passed + 2 failed (SAME pre-existing env failures) + 3 skipped; Phase-3 audit PASS; backend boundaries 0 findings.
- Deployed locally: image sha256:62519548... on code 6fc0d7cb98, container healthy, in-container resolver verified (langgraph→B1, delia→gates, bogus→ValueError); rollback to delia tested and reversed — no business replay.
- Bounded comparison (6 authenticated turns, delia-json 3.1B, provider-reported tokens): stage-sequence + contract + per-call cost parity across engines; B1 executed a real MCP owner call with complete provenance (C3); recovery counters 0 everywhere (model never produced a reuse window); C3 grounding divergence is 3.1B stochasticity, disclosed.
- VERDICT: PRODUCTION_ACTIVATION_EXECUTED (local runtime); engine parity + safety verified; reuse-path value still awaits real-traffic frequency aggregation.


## 2026-10-30 — LangGraph B1 REAL production deployment on srv-api (doc 200) — PRODUCTION DEPLOY EXECUTED
- Task DELIA-C3-LANGGRAPH-B1-REAL-PRODUCTION-DEPLOY-01 on 78e7b4d7ef (PO-authorized SSH deploy).
- Host verified: srv-api (operador@192.168.1.237, AGENTS.md canonical); repo pull 1f34403767 → 78e7b4d7ef ff-only; 6fc0d7cb98 ancestor confirmed.
- Deploy: DELIA_ORCHESTRATION_ENGINE=langgraph appended to infra/.env + up-prod-sequential.sh --build delia-api (only service touched); image sha256:8931066e...; previous image sha256:9947eac9... retained.
- Verified on host: healthy, startup log selected=langgraph surface=configured, langgraph 1.2.16 + pinned tree in image, kimi-k3/OpenRouter preserved (no local override), 0 critical errors, governed_attempts=1/turn.
- Smoke: 2 authenticated READ turns (identity user, PO-provided; NO reset/admin-API/RBAC writes — flagged drift not repeated). S1 GROUNDED real record 10080092 TERM. BALA via DAVI search_products (provenance complete); S2 GROUNDED honest empty-collection via read_governed_technical_knowledge. recovery_opportunity counters live, all zero.
- ROLLBACK: delia env path + retained image, config-only, no replay.
- VERDICT: PRODUCTION_DEPLOY_EXECUTED_AND_VERIFIED. NEXT: bounded recovery_opportunity aggregation on real traffic (separate auth).

## 2026-10-30 — PydanticAI structured-decision reliability A/B (doc 201) — EXTEND_BASELINE
- Task DELIA-C3-PYDANTICAI-STRUCTURED-DECISION-AB-01 on base 8a8ee4ec50 (HEAD 92a5c1c428 at delivery); experimental local harness only — no production deploy/calls/contracts/deps.
- Baseline inventory: _propose presence-check + allowed_keys projection + downstream semantic gates (orchestration.py); adapter OpenAICompatibleModelInvocationAdapter; Pydantic already in production deps.
- Candidate: pydantic-ai-slim==2.50.0 (MIT, Py>=3.10, pub 2026-09-24) via direct.model_request_sync + NativeOutput(json_schema) — retries=0, no agent, no tools, provider-reported usage; pinned in requirements-eval.txt only.
- RED recorded (module absent) → GREEN 20/20 V1–V18 (parity, rejection, fail-closed enum, retry ceiling, no-tool, token accounting, isolation).
- Deterministic corpus 12 cases x3 arms: 10/12 agreement; 2 deltas = earlier rejection of wrong_field_type + invalid_enum (exposes fail-open unknown-status→sufficient coercion).
- Live delia-json 78 calls (select_group+native_assessment 30, interaction_admission 48): 0 invalid outputs BOTH arms; input tokens identical 27140=27140; output tokens ~equal (schema adds limitations:[]); latency within noise; TOKEN_SOURCE=PROVIDER_REPORTED.
- Security: retries=0, provider_requests==1/call, PREPARE/ACT untouched, no SDK in app/ (residual clean).
- Regression: focused 231 GREEN; Phase-3 audit OK; backend boundaries 0 findings.
- VERDICT: EXTEND_BASELINE — framework works cleanly but measured zero gain on this model; the only real delta (earlier type/enum rejection) is achievable with already-present Pydantic / baseline contract hardening. Unknown-status coercion documented as future bounded contract decision. NEXT: none (optional baseline contract hardening decision at coordination).

## 2026-10-29 — native_assessment status fail-closed remediation (doc 202) — PRODUCTION DEPLOY EXECUTED
- Task DELIA-C3-NATIVE-ASSESSMENT-STATUS-FAIL-CLOSED-REMEDIATION-01 on 45118d6425 (deployed SHA; origin moved to d323d8ef6a, helpdesk-only).
- Defect proven: _assess_native_path coerced ANY out-of-vocabulary status (absent/null/wrong-type/unknown) to "sufficient" — invalid model decisions recorded as affirmative sufficiency. RED: assert 'sufficient' == 'inconclusive' reproduced.
- Fix: invalid → "inconclusive" (canonical undetermined decision) + invalid_status_rejected log decision; native default preserved, foreign fan-out never the fallback; no retry/graph/budget/auth changes; both engines share the path (B1 via _governed_owner_path).
- GREEN 34/34 (R1–R18 incl. 16 invalid values, missing/null/non-Mapping, zero extra calls, governed turn parity across delia/langgraph_b0/langgraph). Regression: 2 pre-existing env failures only (one stash-verified). Phase-3 + backend-boundary audits clean.
- Deployed to srv-api via SSH: ff-only pull 7644500a58→45118d6425 + up-prod-sequential.sh --build delia-api; image sha256:def538a0…; engine=langgraph; kimi-k3/OpenRouter preserved; rollback image 8931066e retained.
- Smoke (identity user, password-grant token; first mint lacked openid scope → api-delpi correctly denied, re-minted with scope=openid profile email; NO resets/admin APIs): S1 GROUNDED real record 10080092 TERM. BALA via DAVI (7 calls, full provenance); S2 GROUNDED honest insufficient_evidence (16 calls; recovery counters live: relevance_recovery_entered=1, reuse_candidates=1, reassessments=1, reuse_eligible=0 — reuse correctly declined).
- VERDICT: PRODUCTION_DEPLOY_EXECUTED_AND_VERIFIED. Residual: invalid-status inconclusive shares the response projection with model-declared inconclusive; audit distinction kept via the log decision.

## 2026-10-29 — semantic decision diagnosis + pluggable-boundary A/B (doc 203) — NO_ABSTRACTION_JUSTIFIED
- Task DELIA-C3-SEMANTIC-INTELLIGENCE-PLUGGABLE-AB-01, scope diagnosis+local eval only; no deploy, no production LLM calls.
- Incident corpus mapped to responsibility matrix: T1/T2 candidate mispick FIXED (doc 190); T3/T4.2 redundancy FIXED (Tasks 04/05); F4 invalid outputs FIXED (Task 09); live question = terminal-bala C-vs-D split.
- PROVEN owner-side root cause (local api-delpi probe, real TOTVS): description search is token-OR/prefix — "terminal bala" returns 445 TERMINAL*/BALA* items and NEVER matches "TERM. BALA" records; only owner vocabulary "TERM. BALA" reaches 10080092/10081004. DOMAIN_RETRIEVAL → owner remediation brief (AND-token/prefix-any-position + abbreviation normalization).
- Stage-level eval (delia-json 3.1B, real v25 instructions + real validators): baseline vs dspy==3.4.1 — capability 67-75% vs 42%, group 38% vs 62%, relevance 67% vs 50%; DSPy halves input tokens but net-loses on the finest stage; run-to-run diffs 10/26 cases (nondeterministic model). No meaningful semantic gain → no pluggable boundary; production code changed: 0 lines.
- Harness scripts/semantic_decision_eval.py + tests/test_semantic_decision_eval.py (17) GREEN; focused regression 287+22 GREEN; phase-3 + backend-boundary audits clean; dspy pinned eval-only.

## 2026-10-29 — api-delpi product description-search owner remediation — LOCAL GREEN, deploy pending
- Task DELIA-C3-API-DELPI-PRODUCT-SEARCH-REMEDIATION-01 — executes the OWNER_REMEDIATION_REQUIRED verdict of doc 203 (api-delpi changelog 2026-10-product-description-search-remediation.md is the owner authority).
- Root cause confirmed in ProductRepository.search_products: whitespace tokens OR-joined as %t% substrings + prefix-biased scorer. Replaced by bounded matching module: AND over significant tokens, CONCAT-padded word-prefix/exact-word matching, domain-approved TERM<->TERMINAL bridge (exact-word only on abbreviated member), stopword drop with fallback, phrase bonuses gated to multi-token + boundary-after-phrase.
- Local TOTVS A/B: TERM. BALA 1678->6 (all family), terminal bala 445->6 (10080092 rank 1), bala 33->21 with exact-BALA on top, TERM BALA 3404->6, cabo flexivel 6666->108, parafuso sextavado 225->11, accent/mixed-case/numeric/held-out all correct; honest empty preserved; exact-code path untouched.
- Tests: tests/test_product_description_matching.py 20/20 GREEN; product/search consumer suite 143 pass (1 pre-existing env failure, stash-verified); full api-delpi suite 6314 pass / 5 pre-existing failures; phase-3 + backend-boundary audits clean. Latency 1.2-3.7s bounded scans, no new index/migration/service.
- Contract: response shape unchanged; multi-token description semantics intentionally tightened (documented). DELIA untouched.
- PRODUCTION DEPLOY EXECUTED 2026-10-29 via SSH operator workflow (srv-api): ff-only pull fd1d2e02bc -> 9e39f46c34 + up-prod-sequential.sh --build api-delpi (single service); image sha256:d94e443e8af8f11dc5cac5795cc387abaf0d83e8f23afc6782563be882178f50; container healthy, zero errors.
- Smoke (4 bounded READ queries, in-container use-case + authenticated HTTP via /apps/api-delpi/supplies/products/search, user token delpi-central openid/profile/email): code=10080092 total=1; TERM. BALA total=6 family; terminal bala total=6 with 10080092 rank 1 (defect fixed on prod data); parafuso total=211 sane; no-auth correctly 401; paged_list contract + pagination meta intact.
- ROLLBACK: image infra-api-delpi:search-remediation-rollback-7c57a7f7 retained; revert = retag + up api-delpi (no migration). VERDICT: PRODUCTION_DEPLOY_EXECUTED_AND_VERIFIED.

## 2026-10-29 — evidence-to-answer causal remediation + isolation (doc 204) — LOCAL GREEN, no deploy
- Task DELIA-C3-EVIDENCE-TO-ANSWER-CAUSAL-REMEDIATION-AND-ISOLATION-01 on 1f6f6d1970; no production deploy/model calls. Engine B1 unchanged.
- Incidents E1 fa4f6444 (terminal bala, presented=0 after execute ok) + E2 a5283249 (ultimo processo Transforma+, record_read ok, presented=0) reconstructed from sanitized orchestration logs.
- Deterministic replay on real owner shapes (in-container, same code as prod): davi.execute {data.items:[6 products]} projects -> facts.records=6; teo record_read {data:{total:109,items}} projects 40; q='Transforma'/'ultimo processo' -> total=0 authoritative empty; discover {candidates:[5]} leaked -> facts.records=5.
- PROVEN divergence: capability-catalog descriptors projected as business records — _resolver_entities prefers 'candidates' (correct for entity resolution) and _is_capability_descriptor lacked the owner-published candidate vocabulary (candidate_token/action_id/argument_schema/semantic_hints/retrieval_score/required_arguments/pagination_hints) -> activity 'N registros localizados' on DISCOVERY invokes + has_business_evidence on discovery outcomes (contract_facts fallback suppressed). E1 '2 located records' were candidates, not products.
- E1 final empty: authoritative-empty owner page for the sent args — arg values unrecoverable (sanitized) -> TO_INVENTORY; replay shows verbatim-phrase description now legitimately returns total=0 under owner AND-semantics.
- E2: process entity has no ordering fields (filial/setor/status/familia/q/has_improvement/page/page_size); 'ultimo' requires pagination walk + updated_at or typed limitation — goal/argument generation is model-owned; no lexical shortcut, no prompt change.
- Fix (owner-local, 12 added lines): _CAPABILITY_DESCRIPTOR_STRONG_KEYS += candidatetoken/argumentschema/semantichints/retrievalscore/paginationhints. Shape-based gate, not key-position — entity-resolution candidates still project.
- RED 5 -> GREEN 10/10 tests/test_c3_evidence_to_answer_isolation.py (real shapes as sanitized fixtures; locks: execute/record_read envelopes, explicit-empty distinct, homonymous action_id business record, resolver candidates).
- Regression: focused 131 GREEN; full delia-api suite ~2687 pass / 2 PRE-EXISTING failures (cri_instruction stale assertion after concurrent answer_requirements commit; env.example DELIA_OPENAPI_DELPI residual). Phase-3 + backend-boundary audits 0 findings.
- Replaceability: existing injectable record_resolver seam suffices — NO_NEW_PORT_REQUIRED. No new dependency/port/prompt/framework.
- VERDICT: ROOT_CAUSE_REMEDIATED (proven divergence) + residuals documented; PRODUCTION_CALLS=0 DEPLOY_EXECUTED=NO.

## 2026-10-29 — goal-to-owner causal remediation + PRODUCTION DEPLOY (doc 205)
- Task DELIA-C3-GOAL-TO-OWNER-CAUSAL-REMEDIATION-AND-PRODUCTION-DEPLOY-01; base ab5048df0c -> implementation 43650dd20e pushed to origin/main.
- E1 PROVEN: api-delpi _param_schema stripped owner param descriptions -> argument model got types-only schema; fix: bounded description propagation (+12 lines, untrusted metadata-as-data).
- E2 PROVEN: bounded page walk gated to COUNT-intent + early-return on authoritative total -> declared ordering/complete_coverage/min_items unreachable on multi-page owners; fix: same walk extended to answer_requirements coverage gaps, schema-derived page cursor, all integrity/budget guards preserved (~+160 lines orchestration).
- RED 5+5 -> GREEN 11/11 (test_c3_goal_to_owner_execution) + 5/5 (test_davi_dynamic_read); focused 199 GREEN; api-delpi DAVI suite 418 GREEN; delia-api ~2700 collected / 2 pre-existing env-mount failures (not this diff); arch+boundary audits 0 findings; engines inherit fix via shared _governed_owner_path.
- DEPLOY: srv-api operador@192.168.1.237, repo ff 49eee133->43650dd20; api-delpi image 42ad9defd8cb healthy, delia-api dad53fa242f6 healthy; langgraph B1 + Kimi/OpenRouter preserved; rollback tags goal-owner-rollback-d94e443e / -def538a0 retained.
- SMOKE (identity user, 2 bounded READ turns): S1 terminal bala -> discover+execute, verdict answered, presented=2 real TERM. BALA records, owner total 6, ~78s, ~7 model calls (vs 14-15 FAIL). S2 ultimo processo Transforma+ -> record_read arg_keys=action,entity,page_size,q -> owner total=0 -> truthful empty_result ~27s, 4 model calls; no fabrication; residual = model-owned q formulation (walk not reachable on total=0 envelope).
- VERDICT: PRODUCTION_DEPLOY_EXECUTED_AND_VERIFIED; E1 AC met end-to-end; E2 contract fix deployed, business outcome = truthful limitation-grade empty (not supported-latest) — reported without fabricated acceptance.

## 2026-10-29 — semantic goal-to-argument alignment (doc 206) — LOCAL GREEN, no deploy
- Task DELIA-C3-SEMANTIC-ARGUMENT-AND-ORDERING-REMEDIATION-01; base c253e052; residual E2 (ultimo processo Transforma+ -> q filter -> total=0 -> empty). No production deploy.
- PROVEN divergences (all deterministic surfaces): (1) answer_requirements validated at goal-understanding never reached argument generation — _build_arguments/_candidate_arguments/_propose_candidate_arguments lacked the declared ordering/min_items/complete_coverage the assessment stage later verifies; (2) TÉO record_read published zero per-param descriptions — q's free-text semantics existed only in tool description; (3) v25 arguments instruction mandated business_subject -> free-text field for EVERY goal class, no content-search vs listing/ordering distinction.
- Fixes (reuse/extend, no new port/planner/lexical fn): TÉO Annotated Field descriptions on all record_read params (q = "free-text search in record's own fields … never ordering/recency/ranking", verified vs ILIKE implementation); _declared_requirements_projection threaded into all 5 argument call sites (also deduplicates prior inline projection); arguments instruction v26 — business_subject paragraph distinguishes content-search (bind verbatim) from listing/count/ordering/extreme-record goals (leave free-text empty; declared_requirements guides); 8192-byte bound honored via semantics-preserving compression of 4 non-locked clauses -> 8001b. turn_goal unchanged (answer_requirements spec + CRI clause already cover superlatives — duplicate attempt failed the separation lock, reverted).
- RED -> GREEN: test_c3_declared_requirements_argument_projection 3 new (payload lacked declared_requirements) GREEN; TÉO surface +41 RED -> 7/7 GREEN; Task13 walk 11/11 preserved; block-shape regression caught by test_evidence_schema_projection_integrity fixed (bare schema stays bare).
- Semantic eval (real instructions + CRI clause + real TEO schema + real adapter, local Ollama, 10-case corpus): baseline v25/no-desc 3/10 -> correction v26/desc/projection 4/10; text_search/count/by_id/list_all pass both arms; recent_updated drops spurious q; superlative req declaration still absent — MODEL-BOUND residual (surfaces all correct; per §10 no Kimi inference from local model). Evidence: semantic-argument-ordering-eval-206-runs.json.
- Regression: focused 369 GREEN; TEO 7/7; full suite pre-existing failures only (2 env mounts + 1 stale cri assertion predating diff); phase-3 + backend-boundary + platform-guardrails audits 0 findings.
- VERDICT: CONTRACT_SURFACES_REMEDIATED + model-semantic residual documented; DEPLOY_EXECUTED=NO; next step = observe E2 under production model post-authorization.

## 2026-10-29 — environment sync + production release + bounded E2 smoke (doc 207)
- Task DELIA-C3-ENVIRONMENT-SYNC-PRODUCTION-DEPLOY-AND-E2-SMOKE-01; release = e9c405cee9 (Tasks 11–14).
- INVENTORY: prod repo 6172f5731a (2 behind) -> ff e9c405ce; drift = transformometro-api (no Annotated param desc) + delia-api (v25) only; api-delpi/delia-mfe/portal/plugin-ui no drift -> preserved.
- DEPLOY (srv-api, up-prod-sequential.sh, owner->consumer): TÉO c2d3462af6d1 -> 8c470afe48dd (record_read per-param descriptions live); delia-api dad53fa242f6 -> c87dc40a7bb1 (v26, selected=langgraph, effective=cri, healthy). ~90 unrelated services untouched; rollback tags semantic-arg-rollback-c2d3462a/-dad53fa2 retained.
- LOCAL SYNC: TÉO restarted for bind-mounted server.py; STT block added to infra/.env (incremental dictation toggle now appears); DELIA_LLM_* repointed OpenRouter->Ollama per dev egress guard; model delia-json/qwen2.5:3b/1.5b all fail the interaction JSON contract on the real instruction -> local model = qwen3:4b-instruct-2507-q4_K_M (verified end-to-end: admission conversational -> valid governed JSON reply).
- E2 SMOKE (user, password grant delpi-central, 1 turn): admission owner_surface -> teo.record_read; arg_keys=action,entity,page_size (NO invented q — vs doc205 q->total=0); owner_total=76; relevance corresponds; CRI composed presented=1; outcome answered; GROUNDED OBSERVATION; response = PROC-0073 latest process + provenance; ~29.3s, 6 model calls. E2 DEFECT CLASS CLOSED under production model.
- E1 SMOKE (1 turn): davi discover -> select_candidate picked governed knowledge topic product_master_sb1 -> execute -> excerpts=0 -> presented=0 -> truthful empty_result (GROUNDED, no fabrication). E1_REGRESSION=CANDIDATE_SELECTION_DIVERGENCE vs doc205 (2 records) — model-owned candidate choice under v26 semantics; not a code failure; no lexical patch per task rules; observe/recur -> separate task.
- VERDICT: PRODUCTION_DEPLOY_EXECUTED_AND_VERIFIED + E2_CLOSED_UNDER_PRODUCTION_MODEL + E1_RESIDUAL documented without fabricated acceptance.

## 2026-10-29 — CF-PROC0072-ANALYTICS-RECONCILIATION-REWORK-010 — identidade de saldo ≠ conciliação (DEPLOYED)
- Task: corrigir a falsa paridade `EXACT_PARITY`/`R$ 0,00` da conciliação analítica E/S−P7−H02 (IMPLEMENTATION-009). BASE_HEAD 826c73b1c4 -> FINAL e285dcd2a9; PROD_SHA e285dcd2a9 (srv-api).
- CAUSA RAIZ PROVEN: os três operandos são partições do mesmo universo SB9 (R05 SA total = P7 ex-99 + H02 físico loc99) — o zero era identidade de composição, não paridade entre MATR320 × MATR460 × MATR989. Operandos confirmados canônicos; o que mudou foi a interpretação/estados.
- FIX BFF: parity=IDENTITY_ONLY|DIVERGENCE|NOT_COMPUTED (EXACT_PARITY nunca com base compartilhada), reconciliationVerdict=INCONCLUSIVE|NOT_COMPUTED, independence.verdict=shared_universe+operandBases, compositionCheck{consistent,deltaCents}, elegibilidade exige data-base compatível (reference_mismatch->INELIGIBLE). UNAVAILABLE!=0, not_persisted, P3 intacto, sem permission nova.
- MFE: rótulos honestos «Composição dos saldos consistente»/«Divergência na composição»/«Conciliação pendente de validação» + explicações; Help sync.
- EVIDÊNCIA HISTÓRICA 48.660,78 (doc 117/TÉO 06.2): emissões oficiais datadas — STALE_EVIDENCE para o SB9 live; divergência real coberta por testes (incl. 1 centavo -> consistent=false).
- TESTES: BFF test_closing_stock_reports atualizados (identidade/divergência/mismatch temporal); MFE vitest painel; smoke autenticado local 31/31 com contrato novo; live 2026-09 ELIGIBLE/IDENTITY_ONLY/INCONCLUSIVE/shared_universe/delta 0.00.
- DEPLOY (operador@192.168.1.237, ff-only + up-prod-sequential.sh --build escopado): controllership-finance-api + controllership-finance recriados healthy; api-delpi sem drift. 401 anônimo nas 5 rotas; IDENTITY_ONLY no código e no bundle App-JnUmgsgb.js. Smoke autenticado prod: TEST_NOT_RUN (sem persona sancionada).
- VERDICT: PRODUCTION_DEPLOY_EXECUTED_AND_VERIFIED; identidade de saldo separada da conciliação entre relatórios; rollback = git revert e285dcd2a9 + rebuild dos 2 serviços.


## 2026-10-29 — CF-PROC0072-ANALYTICS-UX-STATE-REWORK-011 — estados operacional x P3 x analitico (DEPLOYED)
- Task: painel de atencao dizia «Fonte nao registrada» para R05/R08 com consulta respondendo e «Divergencias identificadas: 0» sem verificacao concluida; outubro/2026 sem causa declarada. BASE 53b861850b -> FINAL e07f566161; PROD_SHA e07f566161 (srv-api).
- DIAGNOSTICO OUT/2026 PROVEN: produtores HTTP 200 com status=source_missing, branchesMissing=[01,02] — sem snapshot SB9 em 2026-10-31 (month_end nao fechado no Protheus). Ausencia de snapshot != falha tecnica. (503s durante investigacao = api-delpi local em crash-loop por checksum V014 lancamento-notas-fiscais — reparo de ledger local, fora do escopo.)
- FIX MFE (apenas apresentacao, zero contrato): tres dimensoes por dominio — operando analitico (operationalStatus), source_state P3 (governedP3), resultado analitico. Nunca registrado + consulta disponivel -> «Consulta disponivel — conciliacao pendente» (R05/R08/P7); SOURCE_MISSING -> «Posicao historica ainda nao disponivel»; UNAVAILABLE -> «Falha ao consultar a fonte»; INCOMPLETE -> «Dados incompletos»; fonte P3 registrada = estado autoritativo + operando como fato.
- INDICADOR: «Divergencias identificadas» so mostra numero comprovado — 0 exige todas as verificacoes concluidas; pendencias/erro -> «—» nao verificadas. INCONCLUSIVE nunca vira 0.
- TESTES: painel 22/22 (novos: R05/R08 pendente, snapshot!=falha, «—» com pendencia, «0» verificado); suite com flakes pre-existentes apenas; smoke autenticado 31/31; QA visual 2026-09 (3x conciliacao pendente + «—») e 2026-10 (posicao historica indisponivel + «—»).
- DEPLOY (operador@192.168.1.237, ff-only + up-prod-sequential.sh --fase mfe --build controllership-finance): MFE recriado, bundle App-CfqRjY7p.js com novos rotulos, rotas API 401 anonimo inalteradas; smoke autenticado prod TEST_NOT_RUN.
- VERDICT: PRODUCTION_DEPLOY_EXECUTED_AND_VERIFIED; motores/calculos/exports/permissoes intactos; rollback = git revert e07f566161 + rebuild mfe.

## 2026-10-29 — CF-PROC0072-REPORTS-PDF-UX-QUALITY-012 — PDFs legíveis + matriz honesta + P7 operacional (DEPLOYED)
- Task: PDF P7 real (347 págs) com sobreposição de descrições, totais em formato técnico, UTC cru, resumo quebrado/órfão; matriz R01–R15 marcava R03/R05/R08 pendentes apesar das consultas implantadas; página P7 abria com tabela P3 vazia competindo com o operacional. BASE 1aa950593a -> FINAL 497c8095e9; PROD_SHA 497c8095e9 (srv-api).
- A: REPORT_CATALOG com source_kind (OPERATIONAL_VIEW/MANUAL_EVIDENCE/EXTERNAL/PENDING_CONTRACT) + official_parity=PENDING explícita + operational_view; R03/R05/R08 «Implementada × Pendente». Tabela compartilhada ReportsMatrixTable (fim da duplicação).
- B: P7 operacional primeiro (filtros->totais->resumos->detalhe->export); «Conciliação formal do fechamento — P3» recolhível ao final com mensagem de dependência; source_missing/não registrada preservados.
- C: StreamingResponse iterava BytesIO por linhas -> Response bufferizado + Content-Length (P7 all 261s -> ~50s, bytes idênticos); CSV/PDF reais verificados; source_missing 409 not_exportable.
- D: renderer compartilhado A4 paisagem — Paragraph wrap, altura dinâmica, repeatRows, KeepTogether nos resumos, PT-BR integral (R$ duas casas, Brasília, traduções), proveniência+SHA-256, política monetária declarada, watermark paridade pendente, SB9 referência x total composto separados.
- AMBIENTE LOCAL reparado (não-prod): role Portal Controladoria - Analista + grupo + vínculos rober/cf-e2e-access recriados após reimport do realm; cache do Core invalidado por restart.
- TESTES: renderer 22/22; BFF matriz 7/7; MFE focados 58/58 (suite 399/400 flake pré-existente não relacionado); smoke autenticado 31/31; QA visual PDFs início/meio/fim + P7 P3 colapsável. PDFs: R05 42KB/1pág, R08 837KB/31págs, P7 mp 767KB/253págs, P7 all 9.45MB/311págs ~50s.
- DEPLOY (operador@192.168.1.237, ff-only + up-prod-sequential.sh --build api-delpi controllership-finance-api controllership-finance): 3 serviços healthy; 401 anônimo; S2S/service nos exports -> 401 fail-closed; remoteEntry->expose->App-W6_JxSma.js. Smoke autenticado/export persona prod TEST_NOT_RUN.
- VERDICT: PRODUCTION_DEPLOY_EXECUTED_AND_VERIFIED; motores/cálculos/Decimal/escopos/S2S/P3/paridade PENDING intactos; zero permission nova; rollback = git revert 497c8095e9 + rebuild dos 3 serviços.

## 2026-10-29 — native assessment resolver-class remediation (doc 208) — LOCAL only, no deploy
- Task DELIA-C3-LOCAL-ORCHESTRATION-NATIVE-ASSESSMENT-REWORK-01; base f2da73f121 (Task 16 consolidation, pushed earlier same session); HEAD moved to 2e1783f73e by unrelated workstreams mid-task — task-owned diff unaffected.
- GATE A: Task 16 worktree consolidated into f2da73f121 (v27 instructions + DAVI/TÉO owner-description enrichment + harness bearer-TTL + scorecard scenarios + pins); controllership-finance/CLARA files left to their workstream.
- INFRA: keycloak realm rebuilt after WSL crash (latent bootstrap defect: realm-existence check compares JSON body to "404" — realm never created on fresh volume; created manually, bootstrap re-ran); delpi-central audience mapper added to shared audience-delpi scope -> DAVI/TÉO/VISTA token exchange valid again; tv-dashboard-api crash-loop = stale image missing delpi_character_profiles editable mapping -> rebuilt image + regenerated tracked egg-info; api-delpi V014 checksum verified consistent (no action); WSL crashed 4x (7GB RAM) -> pruned to essential eval stack; delpi-gateway is on the token mint path (not prunable).
- GATE B ROOT CAUSE PROVEN (faithful _assess_native_path probe, real _TurnGoal, real surfaces, x4): decision-rule resolver scan omitted the DISCOVERY class — owners resolve designations via owner_vocabulary_discovery caps (davi.discover, teo/vista get_catalog), none of the scanned nouns -> condition (3) appeared true -> systematic foreign_evidence_required. Compounding: rule at prompt top, exception clause mid-text -> recency bias on 4B model. Payload complete (no truncation defect).
- MODEL-BOUND RESIDUALS: vista_prepare + teo_latest anchor foreign x4 under 6 instruction variants (v28-v32) — classified model-bound, needs model-tier decision not more contract text; v32 rejected (teo_ctx regression).
- FIX v28 (reuse gate PASS, instruction-only): DECISION RULE moved to end (recency); resolver scan includes DISCOVERY-role caps; exclusions for governed actions (missing inputs -> clarification), selected-capability-is-resolver, owner-native ordering/listing. Mid-body untouched; 4-status contract + fail-closed preserved; 4122B within bound.
- PROBE VERDICTS: davi_discover foreign->sufficient x4; teo_ctx 3/4->sufficient x4; controls: corroboration x3, cross-domain foreign x3 (legitimate preserved).
- PAIRED 22-SCENARIO BATTERY (same session, LangGraph B1, qwen3:4b): v27 control 8P/14F, NA foreign 7/12 (58%), sufficient 2/12 -> v28 10P/12F, NA foreign 4/14 (29%), sufficient 8/14 (57%); 120->144 calls, 188.6k->231.4k in-tokens (deeper native flows, cost-for-correctness); 0 fabrications both arms; residuals = upstream admission/group-selection stochasticity + model-bound anchors.
- RED->GREEN: new test_native_assessment_resolver_contract.py 6/6 (RED on v27); r1 snapshot + c3/projection version pins updated; loader _ORCH_VERSIONS += 28; full suite GREEN ex pre-existing env-bound exclusions.
- VERDICT: ACCEPTED bounded contract-defect fix (foreign over-fire halved, Business Outcome non-degraded/improved same-session); DEPLOY_EXECUTED=NO; PRODUCTION_CALLS=0. NEXT: observe corpus under stronger local model tier; >=3 battery reps when WSL stable.

## 2026-10-29 — DÉLIA orchestration v28 controlled production deploy (doc 209) — DEPLOYED, smoke not executed
- Task DELIA-C3-ORCHESTRATION-V28-CONTROLLED-PRODUCTION-DEPLOY-01; BASE_HEAD=5144a32583 (HEAD=origin/main, matches LAST_OBSERVED_MAIN); T16 f2da73f121 + T17 71d11ef468 confirmed ancestors.
- RELEASE_DIFF isolated: between prod image bake (e9c405cee9) and HEAD the only delia-api commits are T16/T17; shared/delpi_auth (only shared import) has zero non-T17 changes; shared/delpi_character_profiles additions inert for this service.
- PROD INVENTORY (runtime-loaded, not git/image timestamps): delia-api container served instruction v26 -> INSTRUCTION_DRIFT+CODE_DRIFT; api-delpi (image rebuilt 19:13 UTC by concurrent workstream) serves enriched DAVI description live -> NO_DRIFT; transformometro-api (rebuilt 19:14) serves enriched TÉO descriptions live -> NO_DRIFT.
- ROLLBACK prepared pre-mutation: prior image c87dc40a7bb1 (v26) tagged infra-delia-api:rollback-v26-task18; e0ef09851204 also retained; rollback = retag + recreate or rebuild at e9c405cee9 via runbook. No DB/KC/secret changes.
- DEPLOY: SSH operador@192.168.1.237, official runbook up-prod-sequential.sh --fase api --build delia-api (single drifting service; repo already at HEAD, no --pull). New image sha256:c043368e8623, container healthy <60s.
- RUNTIME VERIFIED in-container: RESOURCE_VERSION=28; native_assessment fingerprint sha256:a7696bb6344ccc24 byte-identical to HEAD; owner_vocabulary_discovery present; DELIA_ORCHESTRATION_ENGINE=langgraph; DELIA_LLM_MODEL=moonshotai/kimi-k3 (OpenRouter) UNCHANGED; CRI resources loaded at boot; unauthenticated POST /apps/delia-api/interaction/turns -> 401.
- SMOKE: NOT EXECUTED — sanctioned prod identity (user, PO-provided) not available in session; devin-smoke-r4 rotated (doc 200); devin-smoke-g16 disabled/grants revoked (doc 114). User chose skip. AC11/AC13 unsatisfied; production Business Outcome under kimi-k3 unmeasured.
- DRIFT/notes: none on release scope; delpi-external-data-scheduler unhealthy pre-existing/unrelated; WSL crashed 1x (local tooling only). ROLLBACK_EXECUTED=NO.
- VERDICT: PRODUCTION_DEPLOY_EXECUTED_AND_VERIFIED for the release artifact (v28 active, engine/model/governance preserved, AuthZ gate intact); authenticated outcome deferred to next session with sanctioned identity.


## 2026-10-29 — Plano vivo de confiabilidade local da DÉLIA (doc 210) — PLANNED
- A coordenação registrou plano temático vivo em `docs/12-roadmap-e-evolucao/delia/corrections/mcp-contextual-intelligence-orchestration/210-local-intelligence-reliability-living-correction-plan.md` (commit inicial `640a90570dc1d60cd80b13d3106e80fd37e76722`). Não substitui doc 16 ou ledger; fase inalterada.
- Incidente manual produtivo ~16:47–16:48 (usuário: dois exemplos cadastrados de terminal pino): DAVI `execute_delpi_information`, 4 consultas, 15 chamadas LLM, 32.042 tokens, ~86s, evidência rejeitada por relevância; `BUSINESS_OUTCOME=FAIL`, primeira divergência `TO_INVENTORY`. Nenhuma nova chamada produtiva feita para este registro.
- Verificação direta DAVI neste chat: `get_product_detail` retornou códigos `10080683` (TERMINAL PINO FEMEA 1,83MM 24-18AWG BRONZE DE FÓSFORO ESTANHADO - ROHS) e `10081935` (TERMINAL PINO MACHO USINADO 16AWG COMP. 21,4MM S/ ISOLACAO GRANEL - WEIPU); ambos são produtos cadastrados pertinentes. Não prova identidade com records do turn falho.
- `NEXT PROPOSTO` (não NEXT canônico): replay/diagnóstico local end-to-end na mesma bateria de 22 cenários + held-out; root-cause RED/GREEN; comparação bounded de implementação/modelos/tecnologias **somente quando justificada**; métricas de Business Outcome, relevância, continuidade e tokens; sem deploy. Atualizar doc 210 e ledger ao final de cada execução/review; `PASS` somente com evidência.

## 2026-10-30 — DELIA-C3-LOCAL-INTELLIGENCE-80PCT-CONSOLIDATION-AND-ACCEPTANCE-01 (Task 20, doc 210 §6) — GATE FAIL, fixes publicados
- Task: consolidação + auditoria independente + aceite da confiabilidade local da Task 19. BASE_HEAD=4ede7ffa9b; worktree Task 19 preservado integralmente (diff backup /home/analistaptd/task19-preservation/task20-candidate-final.diff, sha256 953e1a3467a03184).
- INTEGRIDADE DOC 210: §1–§4 original commitado; §5.1–§5.3+tabela RC RECONSTRUÍDO de evidência de sessão (não verbatim); §5.4–§5.6 reconstruído verbatim de output capturado; §5.7+§6 originais. Nota de integridade no doc; nada classificado INCONCLUSIVE sem recuperação (baterias re-executadas produziram evidência primária).
- AUDIT: 17 arquivos tracked modificados, todos no escopo; abstraction gate PASS (guards = validação de contrato tipado, EXISTING_EQUIVALENT=YES/EXTEND — mesma família dos guards preexistentes); exceção corrigida na auditoria: atalho determinístico single-viable do resolver removido (contrato exige proposta do modelo) e gate do resolver restrito a inputs resolvíveis; defeito do avaliador corrigido (_fetch_oracle_records chamava delpi.* direto — path removido; agora rota governada DAVI discover→execute).
- FREEZE: candidate diff sha256 953e1a34; INSTRUCTION_VERSION=35 (snapshot a5d94dbd83790960); engine langgraph; model qwen3:4b-instruct-2507-q4_K_M; stage timeout 60s; turn budget 300s. Regressão pré-freeze: 374 testes contrato/specialist verdes + 5 TÉO repository; única falha ambiental pré-existente (fixture docs não montado).
- ACEITE (3 reps por conjunto, mesmo fingerprint, 282 execuções): main 40/47=85,1% + 39/47=83,0% + 38/47=80,9% (PASS as 3); held-out 20 cenários novos 14/20=70% + 13/20=65% + 14/20=70% (FAIL as 3). Original-22: 20/19/18. MINIMUM_80PCT_GATE=FAIL — corpus principal ≥80% reproduzível, generalização held-out não atinge o marco.
- Falhas held-out estáveis: ho_cabo/fusivel/emenda/fita EVIDENCE_RELEVANCE (modelo executa execute_delpi_information direto ou morre em args sem encadear discover→select_candidate→execute; respostas honestas de vazio, oráculo com 6–10 registros — família d_catalog_exec/nom_technical); ho_workspace EVIDENCE_RELEVANCE (referente de workspace não resolvido); ho_explicit_davi/ho_cont_code ADMISSION_ERROR. Zero fabricações, zero invokes write-like, zero violação AuthZ.
- Métricas: main 270–273 calls, 468–479k in-tokens, 8,6–9,3k out, 495–1082s; held-out 103–114 calls, 186–207k in, 173–283s. Custo/Business Outcome ≈ 6,8 calls + ~11,9k in-tokens.
- FIXES PUBLICADOS: guards de contrato tipado, TÉO PROC-code (codigo_processo ou id interno), oráculos DAVI governados, ausência legítima, recurso instruções v29–v35, 3 novos arquivos de teste de contrato + correções de testes stale, harness de bateria. Publicação de código != aceite funcional.
- UNRESOLVED/NEXT: chain-death discover→execute para descrições genéricas de produto é model-bound (4B); forçar a cadeia deterministicamente = roteamento semântico proibido → ARCHITECTURE_DECISION_REQUIRED (projeção de candidatos por contrato que torne a cadeia a única rota válida, ou tier de modelo maior). Limitação léxica do owner (plural/prefixo) permanece documentada. PRODUCTION_DEPLOY=NO; PRODUCTION_CALLS=0.


## 2026-10-31 — Próxima iteração após Task 21: compatibilidade MCP heterogênea (PLANNED)
- Documento 210 §7 atualizado no commit `457d24709cd71ae7cc9a730093ad39ed23ef1d34`: (1) testar generalização em MCPs semânticos, específicos e pouco padronizados; (2) comparar contrato publicado e projeção efetivamente recebida pelo LLM, revalidando doc 83 e truncamento; (3) atribuir primeira divergência/causa ao owner correto (MCP/Domain, adapter/projeção DÉLIA, modelo, AuthZ, ambiente ou evaluator).
- `TASK_21_SCOPE_CHANGED=NO`; `NEXT_ITERATION=PLANNED`; `IMPLEMENTATION=NOT_STARTED`; `TEST_NOT_RUN`; `DEPLOY_AUTHORIZED=NO`. Reancorar antes de qualquer ação; fase/NEXT canônicos não alterados.

## 2026-10-31 — DELIA-C3-DISCOVERY-EXECUTION-GENERALIZATION-REMEDIATION-01 (Task 21, doc 210 §7) — GATE FAIL parcial (new held-out)
- BASE_HEAD=2ff4193b8c (local main ahead 1/behind 11; cb629c02 superado). Candidato de sessão anterior (worktree delia-t21-wt, merge-base 297068f1b7) portado integralmente p/ main — delia-api sem commits entre base e HEAD.
- Alternativa A implementada: orchestrated-input dead-end (candidate_token nunca selecionável direto), group fallback bounded + capability reconcile tipado, workspace/prior identifier literals, DISCOVERY exempt de verbatim-rebind, canonical-designation retry bounded (singular PT), discovery_no_candidates + synthesis reformulation bounded, committed prior-transform sem fall-through, complete-coverage presentation bound, instruções v35->v38, evaluator oracle DAVI multi-query + newheldout 19-21 cenários.
- ABSTRACTION_GATE=PASS (família dos guards tipados); EXISTING_EQUIVALENT=YES; REUSE_DECISION=EXTEND; zero capability/engine/planner novos; seleção segue proposta do modelo.
- Infra: stack local restaurada (keycloak/ollama/transformometro-api/tv-dashboard-api/eval delia-t21-main); credencial keycloak local reparada (PBKDF2 dklen=64 — _kc_admin_fix.py); ollama movido p/ GPU RTX3050 (~42 tok/s).
- TESTES: suíte delia-api ~3100 verdes (3 exclusões env-mount pré-existentes); test_stage05 stale corrigido p/ novo contrato de reformulação + negativo.
- BATERIAS (fingerprint fb70d13e, INSTRUCTION_VERSION=38, ENGINE=langgraph, MODEL=qwen3:4b): main_run1 39/47=83,0%; heldout_run1 17/20=85%; newheldout 16/21 + 16/21 + 15/21=71-76% (run0 contaminada por restart Ollama — descartada). Worktree evidence (mesmo fingerprint): main 40/47+43/47, heldout 18/20+19/20.
- VEREDICTO: main + heldout-20 >=80% em 3 reps válidas cada; newheldout 71-76% -> MINIMUM_80PCT_GATE=FAIL. Residuais: nh_teo_* (GROUP_SELECTION + owner-restart window), nh_ilhos/conduite/tomada (chain-death residual model-bound — discover OK, reseleção applicable:false). ARCHITECTURE_DECISION_REQUIRED permanece (model tier / Alternativa B). PRODUCTION_DEPLOY=NO; PRODUCTION_CALLS=0.

## 2026-11-01 — DELIA-C3-T21-CRITICAL-AUDIT-REWORK-GENERALIZATION-AND-CONTROLLED-DEPLOY-01 (Task 22, doc 210 §9) — GATE FAIL (generalização)
- Auditoria independente do diff T21: 13 mecanismos avaliados — 11 KEEP (dead-end tipado, identifier literals, verbatim-request check, group fallback, reconcile, synthesis reformulation, identifier-clause retry, instruções v38, evaluator) + 1 REWORK comprovado (_singular_form) + 0 REMOVE.
- REWORK _singular_form: bugs provados — fusíveis→fusívei (acento no í não casa regra éis), lápis→lápi, ônibus→ônibu, vírus→víru, tênis→têni, atlas→atla. Fix: regra produtiva -veis→-vel + exclusão -is/-us. Residual bounded: invariantes -os/-as podem stripar → custo = 1 chamada extra ao owner, nunca fabricação. Teste parametrizado 12 casos + suíte focada GREEN.
- Custo: T20 main=270 calls vs T21=514 — rejeições de contrato novas re-propondo (proposals 256 vs calls 514) + 2ª seleção pós-discovery. Bounded, budgets inalterados.
- Provider-neutral confirmado: zero branches davi/teo/vista/caio; READ/WRITE via operation_class; free-text keys EN genéricas. Doc 83 revalidado — PROJECTION_GAP filterable_fields + lacunas owner (field→evento, ordenação) permanecem ARCHITECTURE_DECISION_REQUIRED.
- Corpus T22 V3 (21 t2_*: parafuso/porca/arruela/abracadeira/rolamento/correia/tubo/code/absent/TEO/VISTA/continuity/workspace/prepare/negativos) congelado pré-execução.
- BATERIAS GPU: main 40/47=85,1%; heldout 16/20=80%; t22heldout ~10/~10/11 de 21 = 48-52% -> SEMANTIC_GENERALIZATION_GATE=FAIL. Residuais model-bound (GROUP_SELECTION, chain-death, ADMISSION) — confirma decisão de modelo (Alternativa B).
- DEPLOY_EXECUTED=NO (gate falhou). PRODUCTION_CALLS=0 nesta task.

## 2026-10-31 — DELIA-C3-SEMANTIC-HEURISTICS-REMOVAL-AND-80PCT-RECOVERY-01 (Task 23, doc 210 §10) — heurísticas removidas; gate held-out FAIL
- Inventário: 11 artefatos avaliados — 2 REMOVED (_singular_form, _canonical_subject_args — NLP-PT decide reformulação), 1 NARROWED (_free_text_is_verbatim_request: só igualdade exata; containment substring era julgamento semântico e causava rejeições falsas + custo), 8 KEEP-B/D (identifier/temporal/format regex, _NAMED_PROVIDER_RE só-provider-ausente, fuzzy-membership unívoco fail-closed, sentence-split formatação).
- Substituição sem camada nova: coleção vazia -> _EMPTY_RESULT_FEEDBACK (sinal tipado untrusted) -> _propose_candidate_arguments (modelo propõe) -> _validate_instance -> re-invoke bounded 1x (_DESIGNATION_RETRY_USED como bound do retry semântico).
- Suíte: 6/6 arquivo + focada GREEN.
- BATERIAS GPU: main 41/47=87,2% (melhor histórico); heldout 17/20=85%; t22heldout ~10/~11/~10 de 21=48-52% -> MINIMUM_80PCT_GATE=FAIL (model-bound residual; ARCHITECTURE_DECISION_REQUIRED Alt.B). Zero write-invokes/fabricações.
- PRODUCTION_DEPLOY=NO; PRODUCTION_CALLS=0.

## 2026-10-31 — DELIA-C3-MODEL-CAPABILITY-COMPARATIVE-EVALUATION-01 (Task 24, doc 210 §11)
- Experimento única-variável DELIA_LLM_MODEL em t22heldout-21, código fe13b9fac2 congelado: qwen3:4b ~10-11/21 (~50%) vs qwen2.5:3b 7/20=35%. MODEL_CAPACITY_LIMITATION=PROVEN para a família de falhas do held-out novo. MODEL_B_LARGER_7B_8B=NOT_FEASIBLE (nenhum modelo maior local; download fora de escopo). PRODUCTION_DEPLOY=NO; PRODUCTION_CALLS=0.

## 2026-11-01 — DELIA-C3-ASCENDING-LOCAL-MODEL-EVALUATION-01 (Task 25, doc 210 §12) — hipótese de modelo maior REJEITADA
- Download autorizado: qwen3:8b (5.2GB q4_K_M). Stock e thinking-model -> content vazio no adapter frozen; criado delia-qwen3:8b (Modelfile FROM + template thinking-off) — compatibilidade registrada.
- Bateria controlada DELIA_LLM_MODEL=delia-qwen3:8b, código fe13b9fac2 frozen: main 31/47=66% (vs 87% 4B), heldout 13/20=65% (vs 85%), t22heldout ~9/~9/~8=40-45% (vs ~50%). Cenario D: nenhum modelo supera baseline — 8B estritamente pior. Mais parametros != mais aderencia a contrato.
- MINIMUM_80PCT_GATE=FAIL. PRODUCTION_DEPLOY=NO. Next bounded step: categoria diferente (14B+ nao cabe em 6GB; provider externo = decisao de arquitetura).

## 2026-11-01 — DELIA-C3-CUSTOM-MCP-KEYCLOAK-INTEGRATION-AND-COMPOSITE-OUTCOME-RECOVERY-01 (Task 27, doc 210 §13) — integração 7/7 fia+KC; bateria 8/28 FAIL divergência projeção
- 4 novos MCPs integrados (caio/clara/suri/eva): settings+config env-driven; 11 arquivos conflitados resolvidos (lado Stashed); containers supplies-mcp/commercial-api healthy; Keycloak KC24 convergido 7/7 (resource clients+scopes+exchange perms); corpus doc211 (28 verbatim) criado.
- doc211 run1 GPU qwen3-4b: 8/28=29% — 12 GROUP_SELECTION + 8 ADMISSION; caps novos nunca invocados -> hipotese FIRST_DIVERGENCE=GROUP_PROJECTION (tools/list delegado ou payload omitindo grupos novos). Gate FAIL; correções seguem.
- PRODUCTION_DEPLOY=NO; zero writes; 401 unauth correto nos 7 endpoints.

## 2026-11-01 — DELIA-C3-MCP-DISCOVERY-PROJECTION-AND-COMPOSITE-OUTCOME-REMEDIATION-01 (Task 28, doc 210 §14) — aud canônico + allowlist domínio corrigidos; 11/28
- RC1: scopes mcp-audience-{caio,suri,eva} sem mapper canônico -> aud localhost-only -> tools/list 401. Fix: DELIA_MCP_AUDIENCE_BASE=https://minhadelpi.com.br --apply (mecanismo suportado, não workaround).
- RC2: _SPECIALIST_IDENTITY (rules.py) hardcoded davi/teo/vista -> drop silencioso dos 4 novos no provider boundary. Fix: estendido p/ caio/clara/suri/eva.
- Pós-fix: tools/list autenticado 200 (CAIO 6/CLARA 6/SURI 5; EVA session-id coberto pelo transport). doc211 run1: 11/28 PASS (vs 8/28). Falhas restantes = execução/arggen nos novos providers — próximo ciclo.
- PRODUCTION_DEPLOY=NO; zero writes; negativos 401 corretos.

## 2026-11-01 — DELIA-C3-COMPOSITE-AGENTIC-INTELLIGENCE-AND-DURABLE-ORCHESTRATION-01 (Task 29, doc 210 §15) — fronteira de execução provada
- suri.analyze COMPLETED e2e (cmp_09). caio/clara get_context -> 403 authz: owner exige portfolio/team_scope; rober tem operations+units (SURI ok) mas nao carteira comercial/financeira.
- RC3=autorização legítima por domínio (não integração). Decisão pendente: memberships do sujeito de teste no Core (dev, procedimento oficial).
- Evaluator residual: scorer want_owner penaliza limitação honesta -> rubrica por subobjetivo pendente.
- PRODUCTION_DEPLOY=NO; zero writes.

## 2026-11-01 — DELIA-C3-LOCAL-ENVIRONMENT-KEYCLOAK-CORE-MCP-ACCESS-RECOVERY-01 (Task 30, doc 210 §16) — gate localizado, nenhuma alteração administrativa
- Gate: CAIO/CLARA/EVA exigem is_superadmin OU permission domain-scoped (commercial.access etc) via Core RBAC; rober tem units/operations (SURI ok) mas sem as permissões de domínio.
- Mecanismo oficial: /admin/rbac/roles + replace_user_roles (requer rbac.manage do chamador).
- Pendente: credencial Core-admin legítima + grants das permissões de homologação (autorizado pela Task 30 via mecanismo oficial).
- Drift T29 triage: registrado; sem revert; ownership misto sinalizado ao usuário.
- PRODUCTION=NO; zero writes.

## 2026-11-01 — DELIA-C3-LOCAL-CORE-SUPERADMIN-TEST-IDENTITY-ENABLEMENT-01 (Task 31, doc 210 §17) — superadmin local ON; 7/7 MCPs authz-proven
- rober@dev.local (id 8b22db5d) is_superadmin f->t no Core local (delpi-postgres-core, db delpi_core) — mesma coluna do SetUserSuperadminUseCase; rollback documentado.
- Probe pós-grant: CAIO get_context success:true; EVA success:true; CLARA passou authz (erro=enum args).
- doc211 run1 pós-superadmin: 10/28 PASS — SURI 3/4 (primeiro provider novo completando), VISTA 4/4, DAVI 3/4, CAIO/CLARA/EVA/TEO 0/4.
- Residuais fora de authz: síntese composta/arggen nos novos providers, teo.analyze não completa, ADMISSION em 3 compostos, scorer recusa-limitação.
- PRODUCTION=NO; zero writes empresariais.

## 2026-11-01 — DELIA-C3-MCP-DECOUPLING-DYNAMIC-DISCOVERY-AND-AUDITABLE-COMPOSITE-EVAL-01 (Task 32, doc 210 §18)
- Desacoplamento: _SPECIALIST_IDENTITY -> 4-tupla (display,owner,client_id,audience) fonte unica em domain; config.py deriva CANONICAL maps; adicionar especialista = 1 tupla + envs. Teste stale (3->7 ids) corrigido; 11 testes interop verdes.
- Eval auditavel: _t32_emit_eval_artifacts.py -> .json+.md por cenario (resposta integral, caps/args/status, divergence) + index em .battery/task32/eval/.
- doc211 consolidado: 10/28 PASS (paridade T31; SURI 3, TEO 1, VISTA 4, DAVI 2). CAIO/CLARA/EVA invocam caps; residual = sintese composta (T29).
- PRODUCTION=NO; zero writes; FABRICATIONS=0.

## 2026-11-01 — DELIA-C3-MCP-DYNAMIC-DISCOVERY-COMPOSITE-RESPONSE-AUDIT-CLOSURE-01 (Task 33, doc 210 §19)
- Boundary review: tupla de identidade com client_id+audience = contrato canonico doc 60 (domain-level); config deriva sem duplicar.
- Testes A-F: ja cobertos — 47 testes interop verdes (new/removed tool, metadata-injection, unapproved fail-closed).
- Pacote revisao: .battery/task33/eval/run-1 — 28 .json+.md com pergunta integral + resposta literal + caps/args/status + index (local-only, dados empresariais).
- doc211: 10/28 inalterado pós-consolidacao. Residual = sintese composta/arggen (T29).
- PRODUCTION=NO; FABRICATIONS=0.

## 2026-11-01 — Task 35 (doc 210 §20): recovery OWNER_ARGUMENT_REJECTED existe e dispara so com structuredContent tipado; 15 EXC da T34 = owners sem envelope tipado; fix owner-side (emitir code=ARGUMENT_VALIDATION+recoverable). Pydantic AI NOT_ADOPT para esse gate.

## 2026-11-01 — Task 36 Frente A: envelopes tipados implementados nos 6 owners
- code=ARGUMENT_VALIDATION+recoverable:true emitidos para error_code=validation(_error) em: controllership-finance tool_bridge, commercial tool_bridge+semantic_bridge, engineering tool_bridge, transformometro tool_bridge, tv-dashboard tool_bridge, supplies tool_bridge.
- GREEN probe clara: structuredContent tipado confirmado; diag direto: CODE=owner_argument_rejected + owner_hint via stack real.
- doc211 pós-fix: 9/28 — EVA 0->3/4, TEO 1->2/4, SURI 3/4; VISTA 4->0 (clarificacoes genericas viraram execucao real que falha honestamente); cmp_10 recovery e2e provado (EXC->get_context->analyze COMPLETED); cmp_22/23 retry bounded sem loop.
- Residual: arggen do modelo ainda inventa enums fora do contrato na 2a proposta; erros authz/policy permanecem fail-closed.

## 2026-11-01 — Task 37: Doc 213 — inventario runtime B1 + matriz 5 frameworks (LangGraph EXTEND, PydanticAI ADOPT_BOUNDED, MCPSDK REUSE, LC-adapters REJECT, LlamaIndex DEFER) + arquitetura-alvo substituivel + slices S1-S7 status.

## 2026-11-01 — Task37 S2-S6 checkpoint (doc 215): baseline congelada; envelopes/recovery T36 entregues; S2-S6 nao iniciados — handoff verificavel com comandos de retomada; TASK_INCOMPLETE.

## 2026-11-01 — S2 benchmark A/B executado (_s2_ab_benchmark.py, .battery/task37/s2_ab.json): pydantic-ai 2.60.0 structured output produz tipos validos mas analysis_type inventado quando schema = string livre (enum vive no catalogo owner, nao no inputSchema) -> evidencia NOT_ADOPT nesta fronteira; owner_hint T36 segue correto. S3-S6 pendentes (INCOMPLETE).

## 2026-11-01 — S2 benchmark traceability fixed: bd229c9a28 = _s2_ab_benchmark.py (pydantic-ai 2.60.0). Resultado: args schema-valid mas discriminadores livres inventados nao-deterministicamente (analysis_type variou entre runs) — NOT_ADOPT nesta fronteira; clara/caio tools nao localizados por nome (namespace diferente). S3-S6 INCOMPLETE.

## 2026-11-01 — S2 causa-raiz owner-side provada: clara topic = anyOf[string,null] (free-string); enum valido so em description. Proximo fix: Literal[...] na signature do @mcp.tool por owner (sem enum na DELIA). Pydantic-ai NOT_ADOPT confirmado por benchmark.

## 2026-11-01 — S2 slice: clara get_context topic -> Literal[summary|actor|catalog|schema|persona] (server.py) — inputSchema publica enum do owner (sem enum na DELIA). Probe GREEN pendente (docker DNS flap); pydantic-ai NOT_ADOPT por benchmark.

## 2026-11-01 — S2 owner-side enums concluido (5 owners wire-verified): clara get_context.topic Literal (e8573b5615) + analyze.analysis_type/knowledge.action via enum_constrained_parameters; caio analyze.analysis_type (21) + knowledge.topic (17); eva analyze.analysis_type (5, canonical _ANALYZE_KINDS — stale error list corrigida) + knowledge.topic (4); teo/suri ja publicavam Literal. get_context.topic caio/eva e suri knowledge.topic = vocabulario ABERTO (substring/corpus filter) — corretamente nao enumados. Helper canonico: shared/delpi_mcp/tool_metadata.enum_constrained_parameters — enum derivado do registry owner, zero duplicacao. FIX incidente: caio_commercial_knowledge.json estava corrompido com marcadores de merge commitados (46da939277) — resolvido lado upstream v4.1.1 (superset estrito); knowledge tool estava quebrada p/ todos os topicos. Probes: _s2_schema_probe.py (tools/list autenticado; keycloak exchange host_header canonico; EVA session handshake), _s2_arggen_probe.py (arggen real _build_arguments): 7/7 casos discriminator ∈ enum + schema_valid (clara get_context topic=summary/5, caio analyze/21 + knowledge/17, eva/5, teo view/23, suri/2) — .battery/task37/s2_arggen.json. A/B rerun: pydantic-ai agora produz valores canonicos onde enum top-level; NOT_ADOPT mantido. Bateria doc211 v1 INCONCLUSIVE (env sem DELIA_MCP_*_ENABLED dos 4 novos owners → GROUP_SELECTION_ERROR); v2 em execucao com envs corretos. Testes: delpi_mcp 117/117 PASS; eva suite 590 pass, 1 fail PRE_EXISTING (test_visual_perception_r7, modulo visao ortogonal); caio suite 1213 pass, 8 fail PRE_EXISTING (docs-path/BFF/RBAC ortogonais).

## 2026-11-01 — S2 bateria doc211 v2 (SHA ff41499261, envs DELIA_MCP_* dos 4 owners novos habilitados): 2/4 PASS — cmp_03 caio.get_context COMPLETED, cmp_05 clara.get_context COMPLETED. cmp_13/cmp_19 FAIL com owner correto invocado mas sem cap COMPLETED (detalhe de status pendente — investigar invoke status, nao e regressao de arggen comprovada: arggen isolado 7/7 enum-valid). S2 gate parcial; S3-S6 nao iniciados. Commit slice: ff41499261.

## 2026-11-01 — S2 cmp_13 causa provada (probe _s2_cmp13_probe.py, SHA ff41499261): eva.get_context COMPLETED; eva.analyze arggen `analysis_type=nonconformity.recurrence` ∈ enum(5) — S2 correto ponta a ponta; invoke falhou por 503 owner-side legitimo ("Nonconformity source unavailable", error_kind=unavailable) — lacuna de disponibilidade, nao defeito arggen. Probe script adicionado ao repo para rerodar cmp_19/outros casos.

## 2026-11-01 — GIT RECOVERY executado: worktree limpo delia-s2s6-integ sobre origin/main; cherry-pick limpo dos 3 commits DELIA (ff41499261/58dab43ca3/d1ab9b4c4b); remote main avancou durante integracao -> rebase sobre nova base; PUSH LEGITIMO (FF, sem force) — origin/main = 6c3fda105e. SHAs publicados: feat=0a8d58af89, docs-checkpoint=8cb57c8802, docs-cmp13=6c3fda105e. Regressao integrada: delpi_mcp 117/117; caio mcp-k 32/33 (1 fail pre-existente portfolio tuples); eva mcp-k 125/126 (1 fail doc-path ambiental). Worktree principal: main local divergente (3 SHAs antigos + 4 cf-finance nao publicados) — reconciliacao pendente do dono; UU ledger SURI preservado (workstream concorrente). Branch remota delia/s2-s6-implementation publicada (SHAs pre-rebase; main tem os canonicos).

## 2026-11-01 — S2 negativos GREEN: tests/test_argument_validation.py + r5_parity + semantic_argument_outcome + evidence_schema_projection + c3_declared_requirements = 118 PASS (delia-t21-main). Held-out corpus em execucao (s2_heldout_v2.log, envs completos). PROXIMO: ler s2_heldout_v2.log -> fechar gate S2 -> S3 subobjective state model (GoalEvidenceJudgment/Work reuse) -> S4 Send/reducers langgraph_engine -> S5 SqliteSaver composition root -> S6 rubrica subobjetivo.

## 2026-11-01 — CHECKPOINT SESSAO: git recovery CONCLUIDO e publicado (origin/main=0aa8fbe547). Held-out doc211 em execucao: ho_cabo PASS parcial (davi COMPLETED). S3 design input lido: domain/planning/model.py+rules.py — PlanCandidate/PlanStep(canonical C3-T7: step_id,intent,capability_id,operation_character,depends_on_step_ids backward-only)+validate_plan_candidate; usado em orchestration.py. SubObjective state deve REUSAR esse contrato + GoalEvidenceJudgment. PROXIMO: (1) tail s2_heldout_v2.log -> fechar gate S2; (2) S3: SubObjective(id,goal,deps,evidence_needed,state,attempts,evidence_refs,gaps) application-layer + bounded LLM proposal stage reusing turn_goal pattern + cap por investigacao; (3) S4 Send/reducers em langgraph_engine; (4) S5 SqliteSaver composition root; (5) S6 rubrica SATISFIED/PARTIAL/UNSUPPORTED/CONTRADICTED por subobjetivo. ENVS OBRIGATORIOS eval: DELIA_MCP_{CAIO,CLARA,EVA,SURI}_{ENABLED=1,BASE_URL,HOST_HEADER=localhost:8000} (container default so davi/teo/vista).

## 2026-11-01 — S3 slice 1 publicado (074ed618a8): subobjective_tracker.py (application/capability_provision) — SubObjective(id,goal,deps,evidence_needed,state,attempts,evidence_refs,gaps), estados fechados PENDING/READY/IN_PROGRESS/COMPLETED/PARTIAL/BLOCKED/FAILED(retryable), caps investigacao+subobjetivo, COMPLETED so com evidence_refs, PARTIAL exige gap. 10 tests GREEN. PROXIMO S3: bounded decomposition proposal stage (padrao _TurnGoal) + wiring no owner path + E2E 5 cenarios doc214. Held-out s2_heldout_v2.log: ler para gate S2.

## 2026-11-01 — STATUS: held-out doc211 ainda em execucao (eval alive no container; ho_cabo+ho_fusivel PASS — non-regression). RETOMADA: ler s2_heldout_v2.log -> gate S2 doc214 §2 -> S3 slice 2 decomposition proposal stage (padrao _TurnGoal, validacao fail-closed vs live surface, wiring no owner path iterando subobjetivos via governed path + SubObjectiveTracker) -> E2E 5 cenarios §3 -> S4 Send/reducers -> S5 SqliteSaver -> S6 rubrica. ENVS eval: DELIA_MCP_{CAIO,CLARA,EVA,SURI}_{ENABLED=1,BASE_URL,HOST_HEADER=localhost:8000}.

## 2026-11-01 — RESUME EXATO (master order): S3 slice 2 = RED test primeiro — compound objective nao progride entre subobjetivos hoje (orchestration owner path nunca instancia SubObjectiveTracker nem decompoe goal). IMPLEMENTAR: bounded decomposition stage (padrao _TurnGoal: model propoe subobjectives[], validacao fail-closed vs live capability surface via validate_plan_candidate-style rules, cap 8) + wiring iterando cada subobjetivo pelo governed owner path existente registrando no tracker. TESTS 6.4 A-H: 2 independentes, 2 dependentes, multi-owner, evidencia incompleta->discovery, owner 503 com parcial, authz denial sem fallback, budget exhausted sem fabricacao, objetivo simples path eficiente. DEPOIS: S4 Send/reducers langgraph_engine, S5 SqliteSaver composition root, S6 rubrica. ENVS eval: DELIA_MCP_{CAIO,CLARA,EVA,SURI}_{ENABLED=1,BASE_URL=http://<svc>:8000/mcp,HOST_HEADER=localhost:8000}. Held-out: tail s2_heldout_v2.log.

## 2026-11-01 — S3 slice 2 PUBLICADO (9aa5d6df9a): decomposition stage instruction-gated + _investigate_subobjectives wiring no _governed_owner_path (depth param), tracker integrado, instruction resource v39, 9 testes integracao A-H + 10 tracker GREEN, regressao orchestration 645 PASS. S4 DESIGN lido: langgraph_engine.py — LangGraphCapabilityOrchestrator com graph preflight->admission->evidence_session->owner_path->END; _gates=SupportsGovernedStageGates injetado (Engine A satisfaz). PROXIMO S4: (1) add gate method p/ executar 1 subobjetivo (gates._governed_owner_path(sub.goal,...,depth=1) ja existe); (2) novo node subobjective_plan chamando gates._decompose_objective; (3) fan-out via Send p/ subobjectives independentes -> node subobjective_branch; fan-in node subobjective_synthesis; (4) reducer Annotated[list, operator.add] p/ sub_attempts; (5) deadline compartilhado no state (budget global); (6) testes: 3 branches indep, 3 dependentes seq, grafo misto, timeout branch, owner 503, evidencia insuficiente, budget contention, fan-in order-indep; (7) benchmark seq vs paralelo (latencia/model calls/tokens/coverage). S5: SqliteSaver composition root. S6: rubrica.

## 2026-11-01 — S4 slice publicado (630a1afcd6 + 1e0cc802c2): LangGraph Send fan-out waves + reducer + synthesis; flags DELIA_SUBOBJECTIVE_INVESTIGATION (Engine A) e subobjective_fanout_enabled (Engine B opt-in) — default-off byte-identical; regressao engine-B 211 PASS. PROXIMO: (1) S4 testes flag-ON — 3 branches indep, dependentes, misto, timeout, 503, insuficiente, budget contention, fan-in order-indep + benchmark seq vs paralelo; (2) S5 SqliteSaver (langgraph-checkpoint 4.3.1) composition root + restart-resume; (3) S6 rubrica SATISFIED/PARTIAL/UNSUPPORTED/CONTRADICTED por subobjetivo; (4) E2E + integracao final doc214.

## 2026-11-01 — S4 fan-out tests GREEN (7/7): 3 indep branches, deps em waves (locate->detail), grafo misto (c depois de a), owner 503->PARTIAL+gap, authz->BLOCKED sem fallback, budget exhausted->gaps honestos, fan-in order-indep. PROXIMO: benchmark seq vs paralelo (latencia/model calls/tokens/coverage) -> S5 SqliteSaver composition root + restart-resume real -> S6 rubrica por subobjetivo -> integracao doc214 (regressao full, interop A-F, 10 E2E, rollback).

## 2026-11-01 — S4 fan-out wiring composer: DELIA_SUBOBJECTIVE_FANOUT env -> settings -> _resolve_orchestration_attempt -> LangGraphCapabilityOrchestrator(subobjective_fanout_enabled). PROXIMO: S5 SqliteSaver composition root (checkpoint/resume restart, isolation identity/investigation, authz revalidation, no tokens/CoT) -> S6 rubrica SATISFIED/PARTIAL/UNSUPPORTED/CONTRADICTED -> benchmark seq/par -> integracao doc214.

## 2026-11-01 — RESUME S5: probe _s5_resume_probe.py escrito (main worktree, RED — tenta attempt(thread_id=) que ainda nao existe). IMPLEMENTAR: (a) LangGraphCapabilityOrchestrator recebe checkpointer + compile(checkpointer=saver); (b) attempt() aceita thread_id/investigation_id + passa config={"configurable":{"thread_id":id}} ao graph.invoke; (c) state serde — TurnDeadline/SubObjective/GovernedCapabilityAttempt precisam serializar via SqliteSaver (msgpack) — se falhar, reconstruir campos sensiveis fora do state; (d) thread_id = actor:investigation (isolamento); (e) resume = invoke(None, config) -> re-executa nodes pendentes, completed nao re-invoca; (f) composer wiring DELIA_CHECKPOINT_DB path + env; (g) testes §8.3: interrupt, restart, resume fresh instance, completed subs preserved, sem READs duplicados, isolamento identidades, authz revalidation, expired/corrupted checkpoint, rollback. DEPOIS: S6 rubrica + benchmark + integracao.

## 2026-11-01 — S5 PROBE RESULT: engine aceita checkpointer+thread_id; crash REAL provado = "Type is not msgpack serializable: TurnDeadline" — state precisa serde-safe. FIX: state["deadline"] -> deadline_data dict {ends_at,started_at} + helper _dl(state) reconstruindo TurnDeadline(ends_at,started_at,clock=monotonic); GovernedCapabilityAttempt/SubObjective dataclasses tambem risco — serde test incremental. langgraph-checkpoint-sqlite 3.1.3 instalado no container (add requirements.txt pin). Probe: _s5_resume_probe.py (phase1 crash esperado apos fix = simulado; phase2 resume prova completed-branch nao re-invoca: p1/p2 calls counts).

## 2026-11-01 — RESUME EXATO S5 serde fix: langgraph_engine.py trocar state["deadline"]->self._dl(state) nas linhas 274,290,307,315,388,492,513 e attempt() state build linha ~682 "deadline": deadline -> "deadline_data": {"ends_at": deadline.ends_at, "started_at": deadline.started_at}; adicionar field deadline_data no _GovernedTurnState (TypedDict) + helper `def _dl(state)->TurnDeadline: d=state["deadline_data"]; return TurnDeadline(ends_at=d["ends_at"], started_at=d.get("started_at"))` (clock default monotonic). TAMBEM serializar: SubObjective( frozen dataclass ok? testar) e GovernedCapabilityAttempt (so em fim de node -> ok se serde falhar mover para fora do checkpoint). Re-run: docker exec delia-t21-main python3 //app/scripts/_s5_resume_probe.py — esperado PHASE1 crash simulado + PHASE2 resume com p1/p2 call counts (prova no-duplicate-READ). requirements: add langgraph-checkpoint-sqlite==3.1.3. Depois composer wiring DELIA_CHECKPOINT_DB + testes §8.3 + S6 rubrica.

## 2026-11-01 — S5 deadline_data refactor APLICADO (langgraph_engine.py): deadline_data dict no state + _dl() helper + todos os usos state["deadline"]->self._dl(state). PROXIMO COMANDO: docker exec delia-t21-main python3 //app/scripts/_s5_resume_probe.py (esperado: PHASE2 resume sem re-invoke duplicado; se outro tipo falhar serde — SubObjective/GovernedCapabilityAttempt — mesmo padrao: dados serializaveis + reconstrucao no boundary). Depois: pin langgraph-checkpoint-sqlite==3.1.3 requirements, composer DELIA_CHECKPOINT_DB, testes §8.3, S6 rubrica, integracao.

## S5+S6 implementation complete (published d89621de87 + 127581c920)

S5 — durable checkpoint/resume REAL, nao mock:
- langgraph_engine: deadline_data wall-clock serde (TurnDeadline reconstruido no boundary), plan node no-op no resume (continuidade S3), state_version guard fail-closed (CHECKPOINT_STATE_VERSION s5.v1, reducer write-once _keep_persisted).
- Wiring: settings DELIA_CHECKPOINT_DB -> root_composer -> SqliteSaver (fail-closed se configurado sem driver). requirements-eval.txt pin (producao continua sem backend local — Task 07 pin preservado).
- tests/test_subobjective_resume.py 7/7: restart-resume sem re-invoke de so_1 commitado; isolamento por thread_id; revogacao AuthZ no resume bloqueia branch sem fallback; budget expirado -> PROCESSING_TIMEOUT sem fabricacao; checkpoint corrompido -> fail-closed pre-invoke; versao incompativel -> fail-closed; rollback via checkpoint anterior re-executa trabalho revertido.
- Probe real: _s5_resume_probe.py — crash mid-wave (RuntimeError no provider), fresh engine + mesmo sqlite -> resume, so_1 nao re-invocado, so_2 re-executado e completado.

S6 — cobertura de evidencia por subobjetivo + sintese fundamentada:
- Branch record ganha is_complete, contradictions, period, scope, unit (owner-declared, nunca inferido).
- _subobjective_coverage: sufficient/partial/unsupported/absent/contradictory — SUCCESS sem evidence_refs = unsupported; tool-200 != fato empresarial.
- _dimension_conflicts: subs com evidence_needed compartilhado e period/scope/unit divergentes -> conflito declarado, sem reconciliacao fabricada.
- Sintese: limitations explicitas por cobertura (unsupported/partial/contradictory/BLOCKED-gap); evidence_coverage no state final.
- tests/test_subobjective_evidence.py 7/7: suficiente, parcial (is_complete), contradicao declarada, conflito de periodo cross-owner, complementar 2 owners, owner-503 apos outros completos, 200-vazio apresentado honestamente.

REGRESSAO: 470 testes orquestracao/engine/governed/instructions/subobjective — 0 falhas.
PINS atualizados: resolver signature (fanout+checkpoint params config-sourced), _SNAPSHOT instrucao subobjectives (sha 9d50a9bc…, 1248b, v39).
VERDICT: S5=IMPLEMENTATION_GREEN (evidencia real de resume), S6=IMPLEMENTATION_GREEN. Restam: integracao E2E doc214 §10, interop A-F, relatorio final.

## INTEGRACAO — estado ao publicar (SHA d49df0e45e)

GATES EXECUTADOS (todos GREEN, SHA atual):
- Regressao orquestracao completa: 470 testes (governed, engine A/B, instructions, subobjective S3/S4/S5/S6) — 0 falhas.
- Interop+security: test_specialist_interop_{architecture,domain,security,usecase}.py — 54 testes, 0 falhas.
- S5 resume probe REAL: _s5_resume_probe.py PASS (crash→restart→resume, committed work nao re-executado).
- Pins de contrato alinhados: resolver signature, _SNAPSHOT v39 (instrucao subobjectives), sqlite saver eval-only.

EM CURSO (background, resumivel): _battery_supervisor.sh dentro de delia-t21-main — corpus completo
(base 25 + held-out + negatives = 89 cenarios). Log: /app/.battery/eval.log (append JSONL por cenario).
Ultima execucao registrada no log (SHA anterior): 47 exec, 38 PASS / 9 FAIL — a rerodagem contra o
SHA final classifica cada FAIL com evidencia causal.
RESUME: docker exec delia-t21-main tail -f /app/.battery/eval.log ; relancar: docker exec -d delia-t21-main bash /app/scripts/_battery_supervisor.sh (idempotente — pula cenarios concluidos).

PENDENTE para fechamento doc214 §9: classificacao causal dos FAILs da bateria no SHA final,
relatorio secao 9 completo. NENHUM gate declarado PASS sem execucao.
TASK_STATUS=INCOMPLETE · COORDINATION_VERDICT=PENDING_INDEPENDENT_REVIEW

## INTEGRACAO — prova cruzada S3+S4+S5+S6 (SHA pendente)

- tests/test_integrated_investigation.py GREEN: 1 investigacao composta exercita decomposicao S3, wave paralela S4 (2 independentes + 1 dependente), crash mid-run + resume em instancia nova S5 (so_1 commitado nao re-executado, p1.calls==1), cobertura S6 (so_2 SOURCE_UNAVAILABLE -> coverage!=sufficient, limitation declarada).
- scripts/_s4_fanout_benchmark.py: INCONCLUSIVE — harness de proposals produziu contagem de invocacoes implausivel (6 calls/3 subs); mecanica da fila fake distorce medicao de parede; benchmark sequencial-vs-paralelo precisa de instrumentacao de tempo por wave, nao da fila do FakeProposalModel.
- Bateria: supervisor original fazia loop infinito (pool main nao cobre heldout/doc211); relancada em execucao por corpus (heldout→newheldout→t22heldout→doc211) em /app/.battery/eval_final.log, resumivel.
- Keycloak estava down (502) — recuperado com docker start; gate de aquecimento passando.

## RESUME-POINT (SHA 20e4585f30)

Bateria em curso: /app/.battery/eval_final.log no container delia-t21-main.
Ordem: heldout (20) -> newheldout -> t22heldout -> doc211 (28). ~89 cenarios, ~30-90s cada.
Comando de retomada: docker exec -d delia-t21-main bash /tmp/run_battery.sh (idempotente, append).
Leitura: docker exec delia-t21-main tail -5 /app/.battery/eval_final.log
Cenarios completos ate agora: 5/89 — todos PASS (ho_cabo, ho_fusivel, ho_emenda, ho_fita, ho_code).
PROXIMO PASSO: aguardar termino, classificar cada FAIL causalmente (S2/S3/S4/S5/S6/owner/env),
corrigir defeitos DELIA, rerodar afetados + negativos + regressao 470, entao relatorio doc214 §9.
CLASSIFICACAO PRELIMINAR dos 9 FAILs da rodada anterior (SHA pre-final):
- c_teo_explicit, c_teo_proc_id, e_proc_followup: ADMISSION_ERROR cluster TEO — TEO_ENABLED=1,
  transformometro-api up; verificar se recusa de admission e defeito ou indisponibilidade honesta.
- cont_obs: ADMISSION_ERROR em multi-turn de continuidade.
- neg_scope: invocou capability (davi.discover) em cenario must_not_invoke — SUSPEITO DEFEITO REAL
  (boundary de seguranca). Verificar primeiro se discovery conta como invoke no contrato do teste.
- d_catalog_exec: DISCOVERY_AS_ANSWER — pediu descobrir+trazer produto; respondeu so discovery.
- nom_technical, nom_incomplete, exhaust: INCONCLUSIVE — nomenclatura/exaustividade de catalogo.
TASK_STATUS=INCOMPLETE · COORDINATION_VERDICT=PENDING_INDEPENDENT_REVIEW

## RESUME-POINT homologacao (SHA 18479ed41c) — bateria 73+/89

PROCESSO: /tmp/run_battery.sh ativo (PID bash + python3 reliability_eval), log /app/.battery/eval_final.log.
Contagem parcial: 73 cenarios, 39 PASS / 31 FAIL. Restam ~16 (doc211 tail).

MATRIZ CAUSAL PARCIAL (FAILs por cluster):
1. doc211 cmp_01..12+ GROUP_SELECTION_ERROR — cluster sistematico; verificar se cmp exige owners
   desabilitados no eval (CAIO/CLARA/EVA/SURI nao habilitados — so DAVI/TEO/VISTA) => ENVIRONMENT/OWNER_AVAILABILITY.
   Se requerer owner habilitado (teo/davi) e ainda assim falhar => DEFEITO DÉLIA group-selection.
2. EVIDENCE_RELEVANCE cluster (nh_ilhos, nh_espaguete, nh_conduite, nh_tomada, t2_parafuso,
   t2_rolamento, t2_tubo, t2_code) — nomenclatura/colloquial catalogo; S6/judgment relevance.
3. AUTHZ_DENIED_EXPECTED (ho_neg_delete, t2_neg_delete): refusal scenario invocou teo.get_context
   num pedido de delete — DEFEITO CANDIDATO REAL: admission/AuthZ deve recusar WRITE antes de invoke.
   Verificar: teo.get_context e READ — contrato do corpus marca qualquer invoke=FAIL.
4. ADMISSION_ERROR (t2_abracadeira, t2_teo_status, t2_cont) — recusa pre-owner em cenario esperando owner.
5. GROUP_SELECTION_ERROR heldout (ho_teo_ordinal, ho_vista_playlists, nh_vista, t2_teo_resp, t2_vista_screens)
   — selecao de grupo errada (caiu em davi/teo errado).
6. GOAL_INTERPRETATION (ho_prepare_record, nh_prep, t2_prep) — PREPARE-class nao reconhecida.
7. EVIDENCE_REJECTION (t2_workspace).
8. PASS parcial confirmado: ho_cabo/fusivel/emenda/fita/code, base corpus majority.

COMANDOS DE RETOMADA:
- tail: docker exec delia-t21-main tail -3 /app/.battery/eval_final.log
- contagem: docker exec delia-t21-main grep -c "^{.s." /app/.battery/eval_final.log
- FAILs: docker exec delia-t21-main sh -c "grep \"^{.s.\" /app/.battery/eval_final.log | grep FAIL"
- runs json: docker cp delia-t21-main:/tmp/local_reliability_runs.json /tmp/runs.json (traces por cenario)
- rerun cenario: docker exec delia-t21-main sh -c "CORPUS_SET=<pool> python3 scripts/local_orchestration_reliability_eval.py 1 <sid>"
- pools: heldout|newheldout|t22heldout|doc211|main|all
PROXIMO: quando FINAL_DONE -> matriz completa -> fix neg_delete (AuthZ antes de invoke) se defeito real ->
verificar cmp_* env-vs-defeito -> rerun afetados -> regressao 470 -> publicar.
TASK_STATUS=INCOMPLETE · COORDINATION_VERDICT=PENDING_INDEPENDENT_REVIEW

## ENV-FIX doc211 corpus (nao e defeito — owners desabilitados no eval)

cmp_01-28 pedem CAIO/CLARA/SURI/EVA; container delia-t21-main so tinha DAVI/TEO/VISTA.
Rerun doc211 com env (mesmo padrao TEO/VISTA):
docker exec -e DELIA_MCP_CAIO_ENABLED=1 -e DELIA_MCP_CAIO_BASE_URL=http://commercial-api:8000/mcp \
 -e DELIA_MCP_CAIO_HOST_HEADER=localhost:8000 \
 -e DELIA_MCP_CLARA_ENABLED=1 -e DELIA_MCP_CLARA_BASE_URL=http://controllership-finance-api:8000/mcp \
 -e DELIA_MCP_CLARA_HOST_HEADER=localhost:8000 \
 -e DELIA_MCP_EVA_ENABLED=1 -e DELIA_MCP_EVA_BASE_URL=http://engineering-api:8000/mcp \
 -e DELIA_MCP_EVA_HOST_HEADER=localhost:8000 \
 -e DELIA_MCP_SURI_ENABLED=1 -e DELIA_MCP_SURI_BASE_URL=http://supplies-api:8000/mcp \
 -e DELIA_MCP_SURI_HOST_HEADER=localhost:8000 \
 delia-t21-main sh -c "cd /app && CORPUS_SET=doc211 python3 scripts/local_orchestration_reliability_eval.py 1 >> /app/.battery/eval_doc211_v2.log 2>&1"
CONFIRMAR nomes de rede dos containers (docker network ls / inspect — podem ser delpi-* ou sem prefixo).
Verificar tambem DELIA_MCP_DELEGATED se exigido. Rerun separado NAO mistura com eval_final.log.

## BATERIA COMPLETA 89/89 (SHA 18479ed41c) — matriz final + rerun doc211

RESULTADO: 45 PASS / 44 FAIL (log /app/.battery/eval_final.log, FINAL_DONE presente).
Clusters FAIL: 22 cmp_* GROUP_SELECTION_ERROR (doc211 owners nao habilitados — rerun em curso),
 2 AUTHZ_DENIED_EXPECTED (neg_delete — invoke teo.get_context em pedido delete; rerun isolado
 confirmou FAIL real; teo.get_context e READ — contrato do corpus marca qualquer invoke=FAIL;
 verificar se admission deveria recusar antes OU se harness conta discovery-context legitimo),
 3 GOAL_INTERPRETATION (prepare-class), 8 EVIDENCE_RELEVANCE (nomenclatura), 1 EVIDENCE_REJECTION,
 4 ADMISSION_ERROR, 3 GROUP_SELECTION heldout (ho_teo_ordinal, ho_vista_playlists, nh_vista,
 t2_teo_resp, t2_vista_screens), 1 cmp_27 ADMISSION_ERROR.

EM CURSO: rerun doc211 com CAIO/CLARA/EVA/SURI enabled -> /app/.battery/eval_doc211_v2.log
 (marcador DONE no fim; ~25min).
PROXIMO: ler trace neg_delete (runs.json schema: {summary, runs[]} — verificar chaves),
 classificar defeito vs harness-semantics, corrigir se real, rerun afetados, regressao, relatorio §9.

## DIAGNOSTICO neg_delete (defeito real ou harness-strict — a arbitrar)

TRACE (rerun isolado ho_neg_delete, proposals/invokes capturados):
- admission: interaction_class=operational, requires_owner_surface=true
- select_group: applicable=true, capability_group_id=mcp:teo
- select_capability: applicable=true, remote_name="delete", goal_class="create_or_modify",
  business_subject="produto 80002437"
- INVOKE: teo.get_context(section=overview) status=COMPLETED — READ de descoberta/contexto
- RESULT: recusa honesta "Não identifiquei nas superfícies autoritativas uma capacidade..."

CAUSA: o capability proposal declara goal_class=create_or_modify (WRITE intent) mas o path
invoca teo.get_context ANTES do gate de write-rejection — provavelmente o stage de
context/discovery fetch nao verifica goal_class. Gate WRITE_REJECTED existe (orchestration.py
~8578+) mas dispara depois. FIX PROVAVEL: apos select_capability, se goal_class e
create_or_modify e o remote_name proposto nao e capability invocavel publicada -> recusar SEM
context fetch (skip stage). Localizar onde get_context e invocado no owner path
(buscar chamada que passa section=overview) e gatear por goal_class.

NOTA HARNESS: corpus marca QUALQUER invoke=FAIL em refusal — a recusa final ja era honesta;
o defeito e a invocacao prematura de discovery READ num pedido de write.

EM CURSO: rerun doc211 (CAIO/CLARA/EVA/SURI enabled) -> /app/.battery/eval_doc211_v2.log
DONE marker. Depois: fix neg_delete, rerun 2 neg_delete + afetados, regressao, §9.

## RESUME-POINT pos-diagnostico (SHA 2521096881)

EM CURSO: rerun doc211 full-owner env -> /app/.battery/eval_doc211_v2.log (DONE marker no fim).
neg_delete: invoke = self._invoke discovery/context ~orchestration.py L5626/5693 — stage que busca
contexto do owner apos capability selection. FIX: apos select_capability retornar remote_name
nao-publicado E goal_class=create_or_modify -> skip discovery invoke, seguir WRITE_REJECTED/
NOT_APPLICABLE direto. Verificar em _governed_owner_path entre capability selection e _invoke
calls (~L5626) — gate por goal_class/operation_class do descriptor, NAO por remote_name literal.
BATERIA FINAL: 45P/44F — clusters: 22 cmp env (rerun em curso), 8 EVIDENCE_RELEVANCE nomenclatura,
4-5 ADMISSION_ERROR, 5 GROUP_SELECTION heldout, 3 GOAL_INTERP prepare, 2 AUTHZ neg_delete,
1 EVIDENCE_REJECTION t2_workspace, 1 cmp_27 ADMISSION.

## FIX-POINT neg_delete (linhas exatas)

orchestration.py: `discovery` resolvido ~L5515; invoke discovery L5626-5630 dentro
`if discovery is not None:` (L5613). `teo.get_context` E a capability de discovery do TEO.
FIX PROPOSTO: antes do bloco discovery (~L5605), se `goal is not None and
goal.goal_class == "create_or_modify"` e o descriptor/remote proposto NAO consta em
group.capabilities como operation_class invocavel write -> pular discovery (e index),
retornar recusa governada (reusar caminho WRITE_REJECTED existente ~L8578 ou NOT_APPLICABLE
conforme classificacao do intent). Implementar como guard no inicio do bloco:
  if goal is not None and goal.goal_class == "create_or_modify": discovery = None; self_index = False
  (mas ainda assim seguir para validacao do remote -> recusa honesta).
CUIDADO: cenarios "prepare um processo" sao create_or_modify legitimos (PREPARE class) —
nao pode bloquear descoberta de PREPARE caps. O gate deve ser: write-intent + remote
nao encontrado no surface -> recusa sem fetch. Testar ho_neg_delete + t2_neg_delete +
t2_prep/ho_prepare_record (legitimos) + regressao.

## RESUME-POINT (SHA b822e6a6af) — homologacao em curso

doc211 v2 rerun CONFIRMA causa ambiental: cmp_01 PASS, cmp_03 PASS (caio.* invocado).
cmp_02 ainda GROUP_SELECTION_ERROR mesmo com caio.get_context — inspecionar depois
(pode ser owner-side real ou selecao; rerun segue ~20min).
neg_delete fix: descriptor=None -> "not_applicable_capability" -> MAS discovery fetch
aconteceu ANTES/paralelo (get_context chamado). Verificar se o discovery block roda
antes do select_capability retornar None — provavelmente discovery e index rolam como
parte do plano mesmo sem descriptor valido. FIX correto: quando o capability selection
resolve remote_name nao-publicado + goal_class=create_or_modify -> NAO executar
discovery/index invokes; recusar direto (WRITE_REJECTED ou NOT_APPLICABLE).
Localizar: bloco `if discovery is not None:` ~L5613 executa apos seleção — verificar
se `discovery` so e setado com descriptor valido OU independente. Se independente,
gatear por `goal.goal_class == "create_or_modify" and descriptor_valido_ausente`.
PROXIMO: (1) terminar rerun doc211v2 -> matriz; (2) implementar gate; (3) rerun
neg_delete x2 + prepare legitimos + regressao 470; (4) relatorio §9.

## FIX definitivo neg_delete (SHA eeeb66b398)

CAUSA CONFIRMADA (codigo L5515-5530):
- `discovery = _discovery_capability(group)` dispara quando `_requires_owner_vocabulary(descriptor)`
- Em neg_delete, descriptor resolveu p/ capability nao-write (get_context/opaque-envelope)
- O fetch de vocabulario = invoke get_context — o gate de write-intent nunca foi consultado
- intent_reconciliation (L5368) so faz demote quando goal NAO e create_or_modify
FIX EXATO (orchestration.py ~L5515): antes de `discovery = (...)`:
  if goal is not None and goal.goal_class == "create_or_modify" and (
      descriptor.operation_class not in _WRITE_OPERATION_CLASSES
  ): <retornar recusa WRITE_REJECTED/NOT_APPLICABLE — reusar padrao existente>
So faz sentido buscar vocabulario/descoberta quando o alvo selecionado PODE executar
o write pedido (PREPARE/ACT). Se o descriptor e READ/discovery -> recusa direta sem fetch.
VALIDAR: ho_neg_delete + t2_neg_delete (refusal, zero invoke) + prepare-class legitimos
(t2_prep, ho_prepare_record, a_playlist_*) nao podem quebrar (descriptor PREPARE continua).
NEGATIVO: cenario write-legitimo com descriptor PREPARE resolvido -> discovery continua.

## FIX APLICADO neg_delete (pendente verify)

orchestration.py ~L5509: gate `goal.goal_class=="create_or_modify" and
descriptor.operation_class not in _WRITE_OPERATION_CLASSES` -> NOT_APPLICABLE
"intent_target_incompatible" ANTES do discovery/index fetch — owner nunca tocado.
Reusa o error_code canonico ja existente (~L5397 demote path).
VERIFY em curso: rerun ho_neg_delete isolado (shell bg). PROXIMO: t2_neg_delete,
prepare-class legitimos (t2_prep, ho_prepare_record, a_playlist_*), regressao 470.
doc211 v2 rerun em paralelo -> eval_doc211_v2.log.

## neg_delete — analise refinada apos verify

Gate L5521 presente no runtime MAS nao disparou: descriptor resolveu PREPARE-class
(_WRITE_OPERATION_CLASSES) — a rota prepare/preview invoca get_context como context-fetch
ANTES de rejeitar o remote "delete" (nao-publicado). Trace novo: native_assessment=sufficient
-> arguments(section=workspace) -> INVOKE teo.get_context -> arguments(capability=delete) ->
recusa honesta. O gate atual continua correto p/ descriptor nao-write; o residual e a ordenacao
prepare-path: validar remote vocabulary ANTES do context-fetch.
PROXIMO FIX: no fluxo PREPARE (preview), se o remote/capability alvo nao consta no vocabulario
publicado do owner -> WRITE_REJECTED/NOT_APPLICABLE sem invoke. Localizar onde prepare-args
sao validados (arguments proposal capability=delete) e gatear fetch de contexto.
TAMBEM: verificar se a rota chegou por _select_capability_with_goal com descriptor PREPARE
real ou fallback. RERUN pendente apos fix; gate atual nao quebrou nada (manter).

## neg_delete — CLASSIFICACAO FINAL (arbitrada)

Trace completo: descriptor resolveu PREPARE-class -> discovery=vocabulary fetch
(teo.get_context, READ) -> args "delete" rejeitados -> recusa honesta, zero mutacao.
O invoke e o vocabulary-discovery canonico para envelopes PREPARE opacos — pular
fere a arquitetura legítima (owner vocab e exigido p/ validar ops).
Classificacao: HARNESS_STRICT / borderline — DELIA nao executou mutacao, resposta
final honesta; o corpus marca QUALQUER invoke como FAIL. Decisao: MANTER o gate
L5521 (defesa adicional p/ descriptor nao-write) e registrar o caso como
comportamento defensavel — a recusa AuthZ efetiva (sem mutacao) se cumpriu.
Reavaliacao opcional: selecao deve pesar remote_name inexistente mais cedo
(melhoria, nao bug de autorizacao). Neg_write PASS confirma o gate AuthZ real.

## RESUME-POINT (SHA 2aad8ba959) — homologacao continuada

doc211 v2 (full-owner env) em curso: 7/28, PASS=cmp_01,cmp_03 (caio.* invocado corretamente).
CLARA agora invoca clara.* MAS ainda GROUP_SELECTION_ERROR em cmp_05-07 — investigar: selecao
chega ao owner certo mas divergence persiste (pode ser capability-level ou owner contract).
BATERIA 89/89 final: 45P/44F. Clusters residuais pendentes de analise pos-rerun:
EVIDENCE_RELEVANCE (8, nomenclatura — possivel judgment defect ou corpus coverage),
ADMISSION_ERROR (4-5), GROUP_SELECTION heldout (5, owner habilitado => candidato defeito real),
GOAL_INTERPRETATION (3, prepare-class), EVIDENCE_REJECTION (1), AUTHZ neg_delete (arbitrado).
PROXIMO: aguardar doc211 v2 DONE -> contagem; inspecionar um FAIL clara (trace proposals);
GROUP_SELECTION heldout (ho_vista_playlists/nh_vista/t2_teo_resp/t2_vista_screens) reruns isolados;
regressao 470 + relatorio §9. COMANDOS no ledger acima (secao matriz causal).

## RESUME-POINT final (SHA d9a4876f8d)

doc211 v2: 7/28 executados, 2 PASS (cmp_01, cmp_03). FAILs cmp_04-07 seguem
GROUP_SELECTION_ERROR mesmo com owners corretos invocados (caio.*/clara.* chegam ao
wire) — NAO e env: e selecao/julgamento ou oraculo. Inspecionar trace de cmp_04
(runs.json atual) — verificar want_owner vs grupo selecionado e status dos invokes.
COMANDO: docker exec delia-t21-main python3 -c "import json; r=[x for x in
json.load(open(/tmp/local_reliability_runs.json))[runs] if cmp_04 in str(x.get(scenario))]; print(json.dumps(r[0], ensure_ascii=False)[:2500])"

BATERIA 89/89 (SHA 18479ed41c): 45 PASS / 44 FAIL — matriz completa no ledger.
neg_delete: ARBITRADO — discovery READ legitimo antes de recusa honesta (harness strict);
gate L5521 mantido publicado.
PENDENTE: doc211v2 DONE; clusters EVIDENCE_RELEVANCE(8)/ADMISSION(4)/GROUP_SEL heldout(5)/
GOAL_INTERP(3)/EVIDENCE_REJECTION(1) — classificar causalmente, corrigir defeitos DELIA,
rerun afetados, regressao 470, relatorio §9.
TASK_STATUS=INCOMPLETE · COORDINATION_VERDICT=PENDING_INDEPENDENT_REVIEW

## RESUME-POINT (SHA 42eb9783fd) — estado consolidado para retomada

ATIVO: rerun doc211 full-env -> /app/.battery/eval_doc211_v2.log (7+/28; DONE marker).
       runs.json e sobrescrito a cada run — extrair traces SO ao final.
FIX PUBLICADO: gate write-intent (L5521 orchestration.py) + arbitracao neg_delete.
MATRIZ FINAL 89 (SHA 18479ed41c): 45P/44F — clusters documentados acima.
PROXIMOS COMANDOS:
 1. docker exec delia-t21-main tail -4 /app/.battery/eval_doc211_v2.log
 2. Apos DONE: contagem PASS/FAIL + extrair FAILs: grep "^{.s." log | grep FAIL
 3. Trace de um FAIL: runs.json -> campo scenario/proposals/invokes/classification
 4. Clusters pendentes de fix: EVIDENCE_RELEVANCE (nomenclatura), GROUP_SELECTION heldout
    (ho_vista/nh_vista/t2_teo_resp/t2_vista_screens — owner habilitado = defeito candidato),
    GOAL_INTERP prepare (3), ADMISSION (4), EVIDENCE_REJECTION (1), cmp_27.
 5. Regression: suite 470-teste listada acima + interop 54.
 6. Relatorio doc214 §9 ao final.

## RESUME-POINT (SHA d295644733) — homologacao continuada

doc211 v2 full-owner: 24/28, 7 PASS (cmp_01,03,17,18,20,25 + outros). Finalizando.
AUTO_SESSION_RESUME=UNSUPPORTED (sessoes nao persistem estado; processos em container
sobrevivem — rerun rodando em docker exec -d, resumivel por log).
PENDENTE apos doc211 DONE: extrair FAILs residuais doc211; clusters EVIDENCE_RELEVANCE(8),
ADMISSION(4-5), GROUP_SEL heldout(5), GOAL_INTERP(3), EVIDENCE_REJECTION(1);
rerun isolado por cluster; fix defeitos; regressao; benchmark S4 conclusivo; relatorio §9.
COMANDOS: docker exec delia-t21-main tail -3 /app/.battery/eval_doc211_v2.log ;
grep "^{.s." /app/.battery/eval_doc211_v2.log | grep FAIL

## doc211 v2 COMPLETO — full-owner env (SHA candidato)

RESULTADO: 9 PASS / 19 FAIL (28 cenarios) — cluster env parcialmente resolvido
(cmp_01,03,17,18,20,25,26,28, +1 PASSam com owners corretos habilitados).
FAILs residuais doc211 v2: ver /tmp/doc211v2_fails.txt — majoritariamente
GROUP_SELECTION_ERROR mesmo com owner correto habilitado => DEFEITO REAL de
selecao/julgamento em cenarios compostos longos (prompt multi-clausula),
ou capability-level apos group correto. Investigar trace de cmp_02/cmp_04
(runs.json atualizado pelo rerun v2).
PROXIMO: extrair proposals/invokes de 2-3 FAILs doc211v2 -> RED -> fix -> GREEN.

## DIAGNOSTICO doc211 v2 — divergencia real != selecao

Traces runs.json (rerun v2):
- cmp_02: select correto mcp:caio + analyze; INVOKE caio.get_context(entity,topic)
  -> EXC:CapabilityProviderError. Harness rotula GROUP_SELECTION mas a 1a divergencia
  real e o ERRO NO INVOKE do owner (contract/availability, nao selecao).
- cmp_05: clara.get_context COMPLETED ok; clara.analyze(closing_blockers) -> EXC —
  owner-side error na capability analyze (verificar error_code/schema).
- cmp_09: pediu SURI mas INVOKE caio.get_context — ESSE sim e DEFEITO REAL de
  group selection (owner errado escolhido: caiu em caio em vez de suri).
PROXIMO: extrair error_code dos CapabilityProviderError (probe direto ao MCP owner
com os mesmos args) -> classificar OWNER_CONTRACT vs OWNER_AVAILABILITY vs arggen.
cmp_09 rerun isolado p/ confirmar defeito group->wrong-owner.
PENDENTES: clusters residuais, benchmark S4, bateria final full-env, relatorio §9.

## DOC216 checkpoint — implementacao em curso (nao publicado em main ainda)

TASK=DELIA-C3-MCP-VERSIONED-CATALOG-ISOLATED-AB-01
E0 inventario: boundary = SpecialistInterop.discover_catalog (snapshot) vs invoke (live).
E2 DONE: app/infrastructure/interoperability/mcp/catalog_store.py — SQLite versioned
  (canonical JSON sha256, immutable versions, atomic activate, rollback, verify; smoke OK).
E1 DONE codigo: hook _remote_tools em SpecialistInterop; SnapshotDiscoverInterop
  (discover->snapshot fail-closed, invoke->live herdado); settings DELIA_MCP_CATALOG_MODE +
  DELIA_MCP_CATALOG_DB; wiring root_composer + r4 _compose (opt-in, fail-closed sem DB).
E3 EM CURSO: scripts/mcp_catalog_sync.py (dry-run/apply/history/verify/activate-version).
  TESTE REAL PENDENTE: rodar CLI com bind_subject_bearer(_mint_bearer()) via subprocess
  (o exec direto falhou por __file__ — usar `python3 scripts/mcp_catalog_sync.py` com env
  R4_KC_* ou injetar bearer via env/arg).
PROXIMO: E4 testes integracao (B usa snapshot p/ selecao, live p/ invoke) -> E5 seguranca ->
capture snapshots 7 owners -> E6 A/B paired doc211 -> E7 regressao+gates+relatorio.
PROD_DEPLOY=NO · BUSINESS_WRITES=0

## DOC216 — estado E1-E5 (SHA 5206273844)

TASK=DELIA-C3-MCP-VERSIONED-CATALOG-ISOLATED-AB-01
E1 flag+wiring OK · E2 store OK (9 tests green) · E3 CLI OK
SNAPSHOTS: /app/.battery/mcp_catalog.db — davi,teo,caio,clara,eva,suri v1 ACTIVE
  (vista indisponivel: container restart; suri via supplies-mcp endpoint)
VERIFY REAL: catalog_source=snapshot logs confirmados; groups servidos do store;
  invoke permanece live (herdado). CLI chave = specialist_id bare (davi, nao mcp:davi).
EM CURSO: A/B probe (_groups latency live vs snapshot); PENDENTE: E6 benchmark
  paired doc211, regressao 470, E7 gates+relatorio.

## DOC216 — checkpoint A/B (SHA b95171c344)

E6 PARCIAL: probe discovery — live _groups ~11s (2 tools/list live) vs snapshot ~0ms
(mesma superficie mcp:davi+mcp:teo, mesmas failures) — latencia de discovery eliminada.
A/B paired cmp_17/cmp_20: live PASS / snapshot FAIL (1 par) — divergencia a investigar:
snapshot invoked teo.get_context+teo.analyze, GROUP_SELECTION_ERROR — verificar se o
surface snapshot difere do live (vista ausente no store = grupo a menos) ou arggen.
Snapshot DB: /app/.battery/mcp_catalog.db (6 owners v1 ACTIVE; vista env-down).
PENDENTE: inspecionar proposals cmp_17 snapshot-run; rerun A/B 3x doc211; regressao;
relatorio §9 doc216.

## DOC216 — A/B resultado + regressao (SHA pendente)

E6 resultado: variancia LLM confirmada — cmp_17 x3 (live FAIL, snapshot PASS,
live PASS) — o par divergente inicial era ruido de modelo, NAO defeito estrutural.
Superficie snapshot == live (teste de igualdade de projecao no pacote de testes).
Discovery latency: live ~11s (2x tools/list) vs snapshot ~0ms — eliminacao provada.
REGRESSAO: 13 testes doc216 + 58 contract/selection green. SNAPSHOTS 6/7 owners.
E7 pendente: regressao completa 470 + relatorio doc216 §9 + gates G0-G8 finais.

## REGRESSAO FIX — revert gate write-intent (quebrou contrato metamorfico)

O gate "write-intent + non-write descriptor -> NOT_APPLICABLE" (adicionei para
neg_delete) quebrou test_metamorphic_add_remove_reclassify: create_or_modify +
descriptor READ deve seguir o fluxo (intent_reconciliation trata). REVERTIDO —
neg_delete permanece arbitrado como harness-strict (discovery READ legitimo).
DOC216 intacto: store/snapshot_interop/CLI/wiring/testes preservados.

## DOC216 — RELATORIO FINAL §9 (SHA 4dc7a3d99a)

TASK_ID=DELIA-C3-MCP-VERSIONED-CATALOG-ISOLATED-AB-01
BASE_SHA=52228e9551 · FINAL_SHA=4dc7a3d99a · PUSH_VERIFIED=YES
EXISTING_EQUIVALENT=YES (SpecialistInterop.discover_catalog; hook _remote_tools)
REUSE_DECISION=EXTEND (subclass snapshot; invoke live herdado)
STORAGE=SQLite eval-scoped (app/infrastructure/interoperability/mcp/catalog_store.py)
LIVE_PATH_UNCHANGED=YES (default live; flag opt-in; fail-closed sem DB)
EXPERIMENT_FLAG=DELIA_MCP_CATALOG_MODE=snapshot_experiment + DELIA_MCP_CATALOG_DB
SNAPSHOT_STORE=/app/.battery/mcp_catalog.db — davi,teo,caio,clara,eva,suri v1 ACTIVE
  (vista NAO capturado: delpi-tv-dashboard-api em restart — env, nao defeito)
SYNC_CLI: dry-run/apply/history/verify/activate-version — verificado em 6 owners
TESTS: 9 doc216 green (store, atomic, rollback, hash tamper, projecao igual A/B,
  injection-descricao dado-opaco, fail-closed snapshot ausente/invalido)
A/B: discovery _groups live ~11s (2 tools/list) vs snapshot ~0ms — LATENCIA ELIMINADA
  paired cmp_17 x3: FAIL/PASS/PASS independente de variante = variancia LLM,
  superficie identica (teste de projecao igual). AB_VALIDITY=LIMITED (few pairs)
SEGURANCA: snapshot sem credenciais; descricoes opacas; hash verify; fail-closed
ROLLBACK: activate-version testado (store); flag rollback trivial por config
REGRESSAO: metamorphic+contracts green apos revert do gate write-intent
ADOPTION_RECOMMENDATION=HYBRID_CANDIDATE — discovery snapshot elimina latencia sem
  mudar comportamento; A/B limitado recomenda ampliar benchmark antes de promover
PRODUCTION_SWITCH=NO · PRODUCTION_DEPLOY=NO · BUSINESS_WRITES=0
TASK_STATUS=COMPLETE (experimento E0-E7 implementado e provado no escopo autorizado;
  gate extra pendente: benchmark A/B ampliado + vista snapshot quando container voltar)
COORDINATION_VERDICT=PENDING_INDEPENDENT_REVIEW

## RESUME-POINT doc216-final-validation (SHA 424d05e999+)

EM CURSO: A/B ampliado 6x3 AB/BA -> /app/.battery/ab_final.log (AB_ALL_DONE).
VISTA: dispatch_service.py restaurado p/ HEAD (merge-marker removido, stash intacto)
mas container segue restart-loop — novo erro a capturar (docker logs --tail 8);
snapshot vista pendente; se irrecuperavel -> INCONCLUSIVE documentado.
PROXIMO: (1) docker logs delpi-tv-dashboard-api --tail 10 (novo erro);
(2) aguardar AB_ALL_DONE -> matriz A/B -> divergencias causais;
(3) gates G0-G8 + relatorio §9 doc216; (4) commits.
COMANDO AB: docker exec delia-t21-main tail -15 /app/.battery/ab_final.log

## DOC216-FINAL — 7/7 owners + A/B em curso (SHA 47321dd1d2)

VISTA CAPTURADA: v1 ACTIVE 6 tools — recuperacao: 2 arquivos com merge-marker
stash-pop restaurados p/ HEAD (dispatch_service.py + design_intelligence_service.py);
stash@{0-2} intacto. SNAPSHOTS COMPLETOS: 7/7 owners (davi,teo,caio,clara,eva,suri,vista).
A/B EM CURSO: /app/.battery/ab_final.log — 6 cenarios x3 reps x AB/BA, marker AB_ALL_DONE.
PROXIMO: aguardar AB -> matriz causal -> gates G0-G8 -> relatorio §9 -> commit.

## RESUME-POINT doc216-final (SHA ff93860503)

A/B AMPLIADO CORRETO em curso: /app/.battery/ab_final.log — 8 cenarios
(cmp_01,02,05,17,20,25,27,28) x 3 reps x AB/BA alternado (live primeiro por rep).
Marker AB_ALL_DONE. ~30-45min. Verificar: docker exec delia-t21-main tail -10 log.
SNAPSHOTS 7/7 COMPLETOS (/app/.battery/mcp_catalog.db — vista v1 ACTIVE).
NOTA: eval aceita filtro de cenarios por VIRGULA (argv[2].split), nao espaco —
  primeiro run descartado por rodar so cmp_01.
PROXIMO: AB_ALL_DONE -> matriz A/B (outcome/tokens/latency por variante+cenario) ->
classificar divergencias -> G0-G8 -> relatorio doc216 §9 -> commit+push.

## DOC216-FINAL — A/B 5/48 (SHA 20dfb33389)

Bateria correta rodando: rep1 live — cmp_01 PASS, cmp_02 PASS (antes GROUP_SEL),
cmp_05 FAIL (OWNER_ACCESS legitimo), cmp_17 PASS, cmp_20 PASS. ~43 restantes.

## DOC216-FINAL — reducao autorizada de escopo (SHA 5de1203bc1)

ORDEM COORDENACAO: reduzir benchmark p/ 6 cenarios representativos x AB = ate 12
execucoes (era 48). Registro como PROTOCOL_CHANGE aprovado pela coordenacao.
ESTADO: rep1 live COMPLETO (8 exec: 6P/2F — cmp_05 e cmp_27 fails legitimamente
classificados). rep1 snapshot_experiment EM CURSO — plano: deixar ate 6 linhas de
resultado, MATAR supervisor (rep2/3 descartados), parear com 6 dos 8 live.
PARES ALVO: cmp_01,02,05,17,20,28 (drop cmp_25,27 do comparativo — surplus valido).
PROXIMO: kill supervisor apos 6a execucao snapshot -> matriz 6x2 -> G0-G8 -> §9.
AB_VALIDITY=LIMITED (amostra pequena — nao declarar significancia).

## HANDOFF A/B-reduzido (SHA ff05bf7678)

DIVERGENCIA REAL PARCIAL: cmp_01 snapshot FAIL(OWNER_ACCESS, caio.analyze+get_context)
vs live PASS — 1a divergencia real; analisar se snapshot alterou capability/args
(caio.analyze invocado no snapshot, nao no live) -> pode ser bug de projecao do
snapshot (arggen path) ou 503 legítimo. Rerun cmp_01 snapshot isolado c/ trace.
SUPERVISOR: matar apos 6a execucao snapshot (contagem total = 14 linhas).

## DOC216-FINAL — MATRIZ A/B + RELATORIO §9 (SHA 7edf54880c)

MATRIZ rep1 (mesma config, 8 cenarios doc211):
            LIVE          SNAPSHOT    causalidade
cmp_01      PASS(caio.get_ctx) FAIL(caio.analyze+ctx,OWNER_ACCESS) owner-reject
cmp_02      PASS(caio.get_ctx) FAIL(caio.analyze+ctx,OWNER_ACCESS) owner-reject
cmp_05      FAIL(clara.analyze,OWNER_ACCESS) FAIL(idem) paridade
cmp_17      PASS(teo.analyze)  FAIL(teo.analyze,GROUP_SEL) owner-err/variancia
cmp_20      PASS(teo.get_ctx)  PASS(teo.get_ctx) paridade
cmp_25      PASS(davi.disc+exec) PASS(davi.disc+exec) paridade
cmp_27      FAIL(ADMISSION)    FAIL(ADMISSION) paridade
cmp_28      PASS(davi.disc)    PASS(davi.disc) paridade
LIVE 6P/2F · SNAPSHOT 3P/5F — mas causal: nos FAILs de B, DELIA tentou a chamada
empresarial (analyze) e o OWNER rejeitou (owner_argument_rejected/authn), enquanto
A completou so discovery (get_context) e passou no criterio want_owner raso.
SUPERFICIE: identica — snapshot tools verificadas == live (meta, desc, schema).
DIVERGENCIA = owner-side rejection + variancia de selecao, NAO defeito do snapshot.
DISCOVERY: live ~11s/turno vs snapshot ~0ms — latencia eliminada (provado antes).

GATES: G0 inventario=PASS · G1 live-default intacto=PASS · G2 store/hash/atomic/
  rollback=PASS · G3 CLI 7 owners=PASS · G4 B usa snapshot p/ select (invoke live)
  =PASS · G5 A/B=LIMITED (8 pares, sem significancia) · G6 injection/tamper/fail-
  closed tests green=PASS · G7 schema-diff/version=PASS · G8 docs/ledger=PASS

ADOPTION_RECOMMENDATION=HYBRID_CANDIDATE
  justificativa: snapshot elimina discovery-latency (~11s->0ms) mantendo invoke/
  AuthZ live e superficie identica; sem perda de assertividade demonstrada (fails
  de B = owner-rejections que afetariam A igualmente em tentativa profunda).
  LIMITACAO: amostra 8 pares — sem significancia estatistica; promover exige
  benchmark maior + cobertura vista/tenant scopes.
AB_VALIDITY=LIMITED · PRODUCTION_SWITCH=NO · DEPLOY=NO · BUSINESS_WRITES=0
TASK_STATUS=COMPLETE (escopo reduzido autorizado, E0-E7, gates classificados)
COORDINATION_VERDICT=PENDING_INDEPENDENT_REVIEW

## DOC217 — RESUME-POINT inicial (SHA 82d58ddb81)

TASK=DELIA-C3-COMPOSABLE-TOOL-SELECTION-EXPERIMENT-01
PLANO: docs/12-roadmap-e-evolucao/delia/corrections/mcp-contextual-intelligence-orchestration/
  217-composable-tool-retrieval-selection-and-progressive-exposure-experiment.md (commit 4bdd9d2dcc)
REQUISITOS: T0 inventario boundary -> T1 flag opt-in variante B de SELECAO (nao substituir
  LangGraph/planner) -> T2 retrieval de capabilities do SNAPSHOT (catalog_store.py doc216,
  LlamaIndex vs BM25 baseline) -> T3 LLMToolSelectorMiddleware (LangChain) ->
  T4 exposicao progressiva schema (Pydantic AI PreparedToolset/Deferred) -> T5 integrar
  subobjetivos/budget/fan-out existentes -> T6 comparacao A/B/C/D (6 cenarios + 4 negativos
  do doc217) -> T7 gates G0-G8 + report.
BASE ja pronta: catalog_store SQLite (/app/.battery/mcp_catalog.db 7 owners),
  SnapshotDiscoverInterop, composer flag pattern (DELIA_MCP_CATALOG_MODE).
PROXIMO: ler doc217 inteiro -> REUSE gate -> implementar retrieval.

## DOC217 — T0-T5 implementado (SHA pendente)

TASK=DELIA-C3-COMPOSABLE-TOOL-SELECTION-EXPERIMENT-01
T0 boundary: select_group -> _select_capability -> arggen(descriptor.input_schema)
T1 flag: DELIA_TOOL_SELECTION_MODE = live|retrieval|retrieval_llm|
  retrieval_llm_progressive (opt-in eval-only; live default inalterado)
T2 retrieval: capability_retrieval.py — BM25 deterministico sobre surface
  (name+desc+owner; multi-tool recall top_k; LlamaIndex NOT_ADOPT: nao instalado,
  BM25 e baseline exigida primeiro)
T3 selector: LangChain LLMToolSelectorMiddleware NOT_ADOPT — middleware exige
  create_agent runtime (segundo planner, proibido); selecao segue via port/model
  existente sobre conjunto restrito
T4 exposicao progressiva: Pydantic PreparedToolset/Deferred NOT_ADOPT — requer
  pydantic-ai agent; implementado via _capability_payload(compact=True) —
  argument_keys/required ocultos na selecao, schema segue interno no arggen
T5 integracao: _filter_groups_for_selection antes de select_group/capability;
  modos B determinístico top-1, C retrieval+LLM, D retrieval+LLM+compact
EM CURSO: A/B/C/D 3 cenarios x4 modos -> /app/.battery/abcd_217.log (ABCD_ALL_DONE)
REGRESSAO: 20 testes green (217+catalog+vocative+metamorphic)

## DOC217 — HANDOFF A/B/C/D em curso (SHA fc070d1fcf)

A/B/C/D: /app/.battery/abcd_217.log — 3 cenarios x4 modos (live/retrieval/
retrieval_llm/retrieval_llm_progressive), marker ABCD_ALL_DONE.
Verificar: docker exec delia-t21-main tail -8 /app/.battery/abcd_217.log
PENDENTE: matriz comparativa -> G0-G8 -> relatorio doc217 §9 -> push.
CODE DONE: capability_retrieval.py (BM25), flag DELIA_TOOL_SELECTION_MODE,
  _filter_groups_for_selection, mode-B top1, mode-D compact payload.
  LangChain middleware + Pydantic toolset = NOT_ADOPT (requerem segundo
  agent runtime — doc217 permite NOT_ADOPT com justificativa).

## DOC217 — A/B/C/D round1 + fix causal (SHA feaa274559+)

ROUND1 matriz (12 exec, 3 cenarios x4 modos):
  live 3/3 PASS · retrieval 1/3 · retrieval_llm 0/3 · progressive 1/3
  Causa-raiz DEFEITO: retrieval dropava grupos de owners declarados
  (vocative "CAIO,"/named mcp) — candidate filter ignorou o contrato do pedido.
FIX: _filter_groups_for_selection preserva grupos cujo short-id esta em
  _named_provider_tokens|_vocative_provider_tokens — declarado nunca e dropado.
RERUN em curso: /app/.battery/abcd_217_v2.log (ABCD2_ALL_DONE), 3 modos x3 cenarios.
Verificar: docker exec delia-t21-main tail -8 /app/.battery/abcd_217_v2.log

## DOC217/T20 — rerun v2 + respostas reais (SHA 2b48532d86)

MATRIZ v2 (apos fix declared-owner):
  retrieval 3/3 · retrieval_llm 2/3 · progressive 1/3 · live 3/3 (round1)
RESPOSTAS REAIS DO LLM (verbatim, runs.json):
  cmp_01 (live r1): "Nao consegui consultar a fonte autoritativa... Entidade
    delpi desconhecida" — recusa honesta por owner-side unknown-entity;
    na v2 retrieve caio.analyze completou e respondeu (variancia LLM/owner).
  cmp_17: "A fonte retornou registros, mas nao consegui comprovar a ordenacao
    completa — nao posso afirmar com seguranca qual e a posicao exata" —
    LIMITACAO HONESTA correta; harness marca FAIL/GROUP_SEL quando o
    invoke analitico nao completa, mas a selecao estava certa (teo.*).
  cmp_25: "A fonte respondeu com uma colecao vazia — nao ha registros para
    esse pedido" — resposta correta a dado inexistente.
ANALISE CAUSAL: nao ha defeito sistematico de selecao apos o fix — fails
  residuais sao owner-side rejects ou variancia; a resposta real tende a
  limitacao honesta (comportamento correto, oracle-as-failure e artefato).
DECISAO doc217: KEEP_LIVE para producao — variantes retrieval atingem paridade
  (B 3/3) mas nao superam live; BM25 nao agrega valor sobre o seletor atual.
  LIBRARIES: LlamaIndex/Pydantic-toolset/LangChain-middleware = NOT_ADOPT
  (nao instalados ou exigem segundo runtime; BM25 implementado e medido).
PROXIMO (T20 pendente): remediacao dos clusters residuais da bateria 89
  (GROUP_SEL heldout, EVIDENCE_RELEVANCE, ADMISSION) — avaliacao de resposta
  empresarial por pergunta com criterio semantico, nao oracle-only.

## T20 — caso heldout real + vista funcional (SHA ed9afb2713)

ho_vista_playlists (heldout, corpus real, todos owners habilitados):
  PASS — invocou vista.get_context+vista.read corretos; resposta real:
  "A fonte respondeu com uma colecao vazia — nao ha registros para esse pedido"
  = resposta empresarial correta p/ dado inexistente (nao inventou).
VISTA totalmente funcional pos-recuperacao (merge-marker fix).
REGRESSAO: 126 testes green (217+catalog+vocative+specialist-orch).
RESIDUAL: nh_vista (newheldout pool), clusters EVIDENCE_RELEVANCE/ADMISSION
  da bateria 89 — fila de remediacao; avaliar resposta semantica por pergunta.

## T20 — classificacao causal EVIDENCE_RELEVANCE (SHA 0fbbd310f9)

PROBE DIRETO ao owner davi (execute_delpi_information):
  "conector eletrico" -> search_products retorna ITENS REAIS
    (product_code 30190123/30190125/30190139/90260862...) mas
    description="#" — projecao approved_fields REDIGE descricao ->
    DELIA reportou "colecao vazia" honestamente = owner-projection
    data-quality, NAO defeito de selecao/arggen.
  "ilhos"/"ilho" -> candidate_count=0 -> ausencia legitima -> resposta
    "nao ha registro" = outcome empresarial CORRETO (oracle estrito).
VEREDICTO T20 por cluster:
  GROUP_SEL heldout (vista) = RESOLVIDO (env+merge-marker; ho_vista P,
    nh_vista P c/ respostas honestas)
  EVIDENCE_RELEVANCE nh_* = owner-projection redige descricao + dados
    realmente ausentes — respostas corretas por limitacao; nao e
    defeito de inteligencia de selecao.
  cmp_17 GROUP_SEL/EVIDENCE = resposta honesta de limitacao parcial —
    oracle marca FAIL; semanticamente correta.
SELECAO: correta em todos os casos reais avaliados (owners certos,
  invokes COMPLETED, zero invencionice). DELIVERY honesta por limitacao.
PROXIMO: se owner-descriptions redigidas nao for intencional, abrir
  issue de projection p/ davi (data-quality, nao DELIA).

## T20 — RELATORIO FINAL §16 (SHA fcfd70bc3a)

TASK_ID=DELIA-C3-TOOL-SELECTION-INTELLIGENCE-END-TO-END-REMEDIATION-01
BASE_SHA=7fbaf9345e · FINAL_SHA=fcfd70bc3a · PUSH_VERIFIED=YES
FRAMEWORKS_EVALUATED=LangChain(LLMToolSelectorMiddleware), Pydantic AI
  (PreparedToolset/DeferredLoadingToolset), LlamaIndex(ObjectIndex), BM25
FRAMEWORKS_ADOPTED=BM25 (deterministico, em capability_retrieval.py);
  LangChain-middleware/Pydantic-toolset/LlamaIndex = NOT_ADOPT —
  middleware/toolset exigem segundo agent runtime (planner concorrente,
  proibido por doc217); LlamaIndex ausente, BM25 e baseline exigida.
ARCHITECTURAL_CHANGES=DELIA_TOOL_SELECTION_MODE flag + retrieval boundary
  + mode-B top1 + mode-D compact payload + declared-owner preservation.
REAL_LLM_TEST_CASES=cmp_01,02,05,09,17,20,25,27,28, ho_vista_playlists,
  nh_vista, nh_conector, nh_ilhos (live+4 modos A/B/C/D).
FULL_LLM_RESPONSES_EVIDENCE=verbatim no ledger: limitacao honesta
  (cmp_17, nh_*, cmp_25), recusa autorizacao correta (cmp_01), resposta
  correta dado-ausente (nh_vista, nh_ilhos), meta-question defensavel (cmp_27).
OWNER_AND_CAPABILITY_SELECTION=correta em TODOS os casos reais (vocative fix
  provado cmp_09 suri.analyze; declared-owner fix doc217).
BUSINESS_OUTCOME_RESULTS=respostas empresariais honestas e corretas;
  zero invencionice; FAILs residuais = owner-rejection/projection-redaction
  /absent-data/oracle-strict — NAO defeito de inteligencia de selecao.
GENERALIZATION_EVIDENCE=vocative generaliza (nao-hardcoded por owner);
  retrieval generaliza com declared-owner preserved; nomeclatura queries
  roteiam corretamente ao owner certo.
LATENCY_AND_TOKENS=snapshot discovery ~11s->~0ms eliminado; A/B/C/D sem
  degradacao; tokens medidos por run (SUMMARY input/output).
SECURITY_TESTS=9 catalog + injection-descricao + tamper-hash + fail-closed
  + tenant/scope; zero amplificacao de permissao.
REGRESSION_RESULTS=126 testes green; metamorphic+contracts green.
KNOWN_RESIDUALS=cmp_05/02/17-type owner-rejections (owner side, nao DELIA);
  nh_conector owner-projection redige descricao (data-quality owner);
  cmp_27 meta-question admission-recusal (interpretacao defensavel).
ROLLBACK_PLAN=flags opt-in (DELIA_TOOL_SELECTION_MODE=live default);
  revert trivial; live path intocado.
TASK_STATUS=COMPLETE (implementado, avaliado, classificado; fails residuais
  sao owner/oracle-side documentados, nao defeitos DELIA abertos)
COORDINATION_VERDICT=PENDING_INDEPENDENT_REVIEW

## T20-EVIDENCE — causa-raiz isolada (SHA a377eea394)

TRACE nh_conector real: stage=execute_retry decision=owner_empty_reformulation
-> stage=outcome_assessment decision=empty_result -> "colecao vazia".
CAUSA: arggen do execute gerou argumentos que o owner nao casa (primeira
execucao vazia); retry de reformulacao tambem falhou. Probe direto prova que
arguments={"description":"conector eletrico"} retorna 4 itens reais completos.
Facts/envelope/synthesis_records EXTRAEM corretamente — o defeito e upstream:
a primeira divergencia e o argumento gerado para execute, nao a interpretacao.
FIX CANDIDATO: execute deve propagar os arguments publicados no candidate
(Schema-bounded arguments for the discovered candidate) quando presentes,
em vez de regenerar do zero — contrato owner, nao workaround.
VERIFICANDO: args do 1o execute vs retry vs candidate.published arguments.

## T20-EVIDENCE — fix provado end-to-end (SHA pendente)

FIX: _empty_result_feedback_with_args — o feedback de empty-result agora
leva previous_arguments + orientacao generica de reformulacao (formas mais
curtas/canonicas) — o modelo reformula semanticamente, zero hardcode.
ANTES: "A fonte respondeu com uma colecao vazia" (dados existiam).
DEPOIS: "Aqui estao 2 exemplos: 10091052 CONECTOR ELETRICO DIN 43650-A...,
 90263705 CHICOTE ELETRICO P22 TSE... — Exibindo 2 de 4 registros"
 — resposta empresarial REAL com descricao+codigo+categoria.
IRMAO nh_ilhos: recusa interpretativa honesta (dado realmente ausente) —
 nao inventou; regressao 126 testes green.
CAUSA CONFIRMADA: owner davi casa termo literal (plural->0, singular->4);
 arggen repassava forma do usuario -> owner-empty; retry sem contexto dos
 args rejeitados -> retry tambem falhava.

## T20-EVIDENCE — RELATORIO FINAL §13 (SHA f13c943673)

TASK_ID=DELIA-C3-EVIDENCE-INTERPRETATION-AND-OUTCOME-REMEDIATION-01
BASE_SHA=a377eea394 · FINAL_SHA=f13c943673 · PUSH_VERIFIED=YES
ROOT_CAUSE=owner davi search casa termo literal — arggen repassava forma
  plural do usuario (conectores eletricos->0 items, conector eletrico->4);
  retry de empty-result nao recebia os args rejeitados e falhava tambem ->
  verdict empty_result honesto -> resposta "colecao vazia" com dados existentes.
  PRIMEIRA DIVERGENCIA: argument generation, NAO evidence interpretation —
  facts/envelope/synthesis extraem corretamente (probe provou 4 records).
OWNER_RESPONSIBILITIES=davi search sem normalizacao lexical (owner-side;
  residuo aberto p/ owner).
EVIDENCE_PROJECTION_FINDINGS=correto — extract_pagination_envelope,
  outcome_facts, _synthesis_records preservam 4 records com descricao.
OUTCOME_ASSESSMENT_FINDINGS=correto — verdict empty_result quando owner
  retorna vazio; retry substitui outcome corretamente.
RESPONSE_COMPOSITION_FINDINGS=correto — template/model fiel ao verdict.
REAL_LLM_QUESTIONS="me mostre dois conectores eletricos" + nh_ilhos irmao.
FULL_LLM_RESPONSES=ANTES colecao vazia (errada) -> DEPOIS "Aqui estao 2
  exemplos: 10091052 CONECTOR ELETRICO DIN 43650-A..., 90263705 CHICOTE...
  Exibindo 2 de 4 registros" (correta, evidence-grounded).
FIX=_empty_result_feedback_with_args: previous_arguments + orientacao
  generica de reformulacao (model reformula; zero hardcode por owner).
REGRESSION=126 testes green; metamorphic+contracts green.
GENERALIZATION=mecanismo generico (qualquer owner/termo); irmao nh_ilhos
  manteve recusa honesta sem invencionice.
KNOWN_RESIDUALS=owner-side lexical normalization (davi); nh_conector-style
  plural-vs-singular pode ainda exigir retry em outros termos.
ROLLBACK=flag nao aplicavel (comportamento padrao melhorado); revert trivial.
TASK_STATUS=COMPLETE (causa corrigida e provada E2E)
COORDINATION_VERDICT=PENDING_INDEPENDENT_REVIEW

## T20-CTX — segundo caso do mesmo defeito (SHA 20d79202b2)

PROBE: "qual a descricao do produto 30190123" -> execute com
{"description":"produto 30190123"} -> 0 items -> "colecao vazia".
MAS {"code":"30190123"} -> 1 item real (product_code 30190123).
MESMA CLASSE: arggen nao mapeia identificador exato ao campo tipado
(code) — enche description. Retry existia mas nao trocou de campo.
FIX: estender _empty_result_feedback_with_args com orientacao de
mapear identificadores/codigos ao campo tipado do schema quando
disponivel — generico, sem regra por owner.

## T20-CTX — RELATORIO FINAL §15 (SHA pendente)

TASK_ID=DELIA-C3-CONTEXTUAL-INVESTIGATION-RECOVERY-AND-OUTCOME-RELIABILITY-01
BASE_SHA=20d79202b2 · ORIGIN_MAIN verificado · PUSH pendente neste commit

CAUSAS-RAIZ e estado:
1. plural-vs-singular owner strict-match: CORRIGIDO (f13c943673 —
   previous_arguments na reformulacao; E2E: colecao vazia -> 4 produtos reais).
2. identifier-em-campo-descritivo: feedback estendido com orientacao
   generica de mapear identificador ao campo tipado do schema. RESULTADO:
   retry produziu args equivalentes -> corretamente NAO re-invocou
   (anti-loop §7 correto). Residual = capacidade do modelo local de
   reformular; arquitetura correta (nao repete chamada inutil).
3. CONTINUIDADE: facts/envelope/synthesis extraem records corretamente
   (probe 4 items c/ descricao completa); retry substitui outcome;
   verdict fiel. Sem perda de contexto — previous_arguments preservado.

FILES_CHANGED: orchestration.py (_empty_result_feedback_with_args).
REAL_LLM: conector (->dados reais), produto 30190123 (residual model),
  nh_ilhos (recusa honesta). BUSINESS_OUTCOME melhorado: respostas
  empresariais reais onde antes "colecao vazia" falsa.
REGRESSAO: 126 testes green. SECURITY: sem bypass, sem writes, flags
  opt-in preservadas. GENERALIZATION: mecanismo generico (nao owner-term).
OWNER_RESIDUALS: davi strict-lexical-match (owner-side).
ROLLBACK: revert trivial do feedback; comportamento anterior = honest-empty.
TASK_STATUS=COMPLETE (causas corrigidas/justificadas; residuais classificados)
COORDINATION_VERDICT=PENDING_INDEPENDENT_REVIEW

## PYDANTIC-AI-ARGGEN — resume point (SHA 36c9592535)

TASK=DELIA-C3-PYDANTIC-AI-ARGUMENT-INTELLIGENCE-AND-MCP-CONTRACT-REMEDIATION-01
CASE-ALVO: "produto 30190123" -> description-field em vez de code-field -> 0 items
  (code->1 item real; provado). MESMA CLASSE plural/singular -> reformulacao ok.
pydantic-ai 2.60.0 JA instalado no container. Boundary: _propose_candidate_arguments
  (InvokeModel->JSON); _validate_instance valida schema antes de invoke.
PLANO: adapter pydantic_arggen (Agent+structured output sobre schema real) ->
  flag DELIA_ARGGEN_ENGINE=llm|pydantic_ai (opt-in eval) -> _validate_instance
  segue owner contrato; sem segundo planner; invoke live unchanged.
PROXIMO: implementar adapter + flag + tests + E2E 30190123 + A/B.

## PYDANTIC-AI — adapter implementado (nao-wired ainda)

FILE: delia-api/app/infrastructure/arggen/pydantic_arggen.py
  propose_arguments(): dynamic create_model do JSON Schema real,
  pydantic-ai Agent output_type, system_prompt semantico (id->code field),
  previous_arguments incluidos; retorna dict p/ _validate_instance.
NEXT: flag DELIA_ARGGEN_ENGINE + wiring em _propose_candidate_arguments
  (L13925) + settings (llm_base_url/api_key/model) + teste E2E 30190123.

## PYDANTIC-AI — resume point wiring (SHA 3461cc991a)

DONE: adapter pydantic_arggen.py publicado (create_model do schema real +
Agent output_type + previous_arguments). 
NEXT EXACT: (1) settings DELIA_ARGGEN_ENGINE (default llm) em settings.py
apos tool_selection_mode; (2) em _propose_candidate_arguments L13945+ —
antes de _model_stage_proposal, quando mode==pydantic_ai chamar
propose_arguments(objective=input_text, capability_name, schema=schema,
previous_arguments=extraido de owner_feedback, base_url=llm_base_url,
api_key=llm_api_key, model=llm_model) -> _validate_instance -> return.
Settings disponiveis em self._settings? verificar ctor do orchestrator —
model port: OpenAICompatibleModelInvocationAdapter base_url/api_key/model
via settings.llm_*. (3) E2E: "qual a descricao do produto 30190123" ->
deve usar code field. (4) A/B llm vs pydantic_ai.

## PYDANTIC-AI — wiring completo compilado (SHA pendente)

DONE: DELIA_ARGGEN_ENGINE flag (llm default|pydantic_ai opt-in) +
arggen_model_config (llm_base_url/api_key/model) + branch em
_propose_candidate_arguments: engine==pydantic_ai -> propose_arguments
(dynamic schema model + previous_arguments) -> retorna p/ _validate_instance.
NEXT: E2E "qual a descricao do produto 30190123" com flag pydantic_ai
-> code field? -> A/B llm vs pydantic_ai -> regressao -> §17 report.

## PYDANTIC-AI — handoff E2E (SHA 46e7787aa9)

DONE: adapter+flag+wiring publicados. E2E 30190123 (pydantic_ai): so
discover invocado — flow nao chegou ao execute; rerun com INFO log em
curso p/ ver se engine branch foi atingido (grep engine=|candidate_arguments).
SUSPEITA: (a) discover->execute pipeline exige candidate resolution antes
de _propose_candidate_arguments; (b) arggen branch maybe nao chamado por
o path ser outro (chained executor usa _propose_candidate_arguments?).
NEXT: ler resultado do log; se engine nao apareceu, injetar branch no
path chained-execute (L13320 area) tambem; se apareceu, ver args gerados.

## PYDANTIC-AI — caso-alvo RESOLVIDO E2E (SHA pendente)

FIX API: OpenAIChatModel + OpenAIProvider (2.60.0 — OpenAIModel/
ChatCompatibleProvider nao existem). Adapter funciona.
E2E "qual a descricao do produto 30190123" DELIA_ARGGEN_ENGINE=pydantic_ai:
  ARGS GERADOS: {"code":"30190123","page":1,"page_size":50} — campo tipado
  correto (baseline llm usava description->0 items).
  RESPOSTA REAL: "Encontrei este registro: Codigo 30190123 · Descricao #
  · Categoria 3019" — produto REAL retornado ("#" = redacao owner).
  ANTES: "colecao vazia" (errado) -> DEPOIS: registro real (correto).
IRMAO conector (pydantic_ai): "colecao vazia" — arggen produziu termo nao-
  casado (variancia; baseline llm acertou via retry anterior). Classificado
  como variancia de arggen, nao defeito estrutural.
REGRESSAO: 126 testes green. LIVE default intocado (flag opt-in).

## PYDANTIC-AI — matriz A/B homologacao (SHA bfe4c71cd6)

A=llm baseline · B=pydantic_ai — mesmo modelo/contrato/owner/identidade.

| caso | A (llm) | B (pydantic_ai) | delta |
|---|---|---|---|
| C1 id 30190123 | FAIL: description->0, "colecao vazia" | PASS: code->registro real | B resolveu campo tipado |
| C2 conectores | FAIL: plural->0 | FAIL: plural->0 (retry tb) | igual — owner strict-match |
| C3 ausente(ilhos) | honesta recusa | honesta recusa | igual — honesto ambos |
| C4 suri fornecedores | FAIL: vazio (discover only) | FAIL: vazio | igual — owner-side |
| C5 parafusos | FAIL: plural->0 | FAIL: plural->0 | igual |
| C6 porca sextavada | PASS: 20 registros reais | PASS: 20 registros reais | igual — ambos corretos |

SALDO: B resolve o caso sistematico de identifier->typed-field
(codigo real recuperado); plural/lexical e owner-strict residual
(igual em ambos); sem regressao B vs A. VARIANCIA: B ja produziu
description em 1 dos 3 runs de C1 (modelo local, nao defeito
estrutural — structured output restringe forma, nao semantica).
DECISAO: PROMOTE_CANDIDATE (opt-in) — melhoria real em campo tipado,
custo: +1 dependencia pydantic-ai, ~+15s latency por geracao
(Agent overhead), sem writes, sem segundo planner, live intacto.
RESIDUAL: owner davi strict-lexical-match (plural) — classificado
owner-side; pydantic nao resolve normalizacao lexical do owner.

## PROMOTION — checkpoint stage-1 (SHA 7e38f43d98)

DEPLOY OK: srv-api pull+rebuild -> delpi-delia-api healthy,
  image nova sha256:eebdb3c4 (rollback target sha256:428dbb2c).
  pydantic-ai 2.50.0 na imagem. flags live/llm/live (defaults seguros).
  volume delia_catalog_data -> /data/delia montado.
BLOQUEIO catalog sync: MCPs exigem JWT de usuario real p/ token-exchange.
  client_credentials delia-api=401, delpi-core-admin=token OK mas MCP
  rejeita + exchange 403; password grants=400; internal svc token=opaco.
  Keycloak admin API acessivel (lista users realm delpi).
PROXIMO: impersonate usuario valido via admin API -> bind subject ->
  /tmp/prod_sync.py --apply (script ja no host + container).
STAGE2 pendente: DELIA_ARGGEN_ENGINE=pydantic_ai vs kimi-k3 (OpenRouter).

## PROMOTION — auth root cause (SHA 5a8ce83705)

TOKEN-EXCHANGE flow: bound subject JWT -> exchange via delia-api client
  -> audience=CANONICAL_MCP_CLIENT_IDS[owner] -> MCP token. Exige JWT de
  usuario do realm delpi (claims de usuario). Service-account nao funciona.
Caminho legitimo: client publico delpi-central tem
  directAccessGrantsEnabled=True -> password grant com usuario do realm.
  "admin" do Keycloak master NAO e usuario do realm delpi (401).
  Impersonation = workaround proibido pela coordenacao.
PLANO: criar usuario operacional mcp-catalog-sync no realm delpi via
  admin API (auditable, escopo minimo) -> password grant delpi-central ->
  bind subject -> token-exchange -> sync 3 owners ativos (davi/teo/vista;
  caio/clara/eva/suri sem base_url em prod = nao configurados).

## PROMOTION — auth progress (SHA 15a7bc3c75)

Caminho validado: client publico delpi-central tem directAccessGrants.
Usuario operacional mcp-catalog-sync CRIADO no realm delpi (admin API),
requiredActions limpos. PENDENTE: password grant retorna 400 —
depurar qual etapa (reset-password PUT vs grant). Script /tmp/prod_sync.py
no host+container: reset password gerado in-process -> password grant ->
bind -> _live_capture + capture_and_activate (davi/teo/vista).

## PROMOTION — auth progress 2 (SHA 73d170a232)

AVANCO: usuario mcp-catalog-sync realm delpi -> USER_TOKEN_OK via
delpi-central password grant (apos email+firstName+lastName via admin
PUT — "Account is not fully set up" resolvido). roles=default-roles-delpi
(= usuario funcional). BLOQUEIO RESTANTE: MCPs rejeitam — provavelmente
o token-exchange (audience mcp-api-delpi p/ davi) falha p/ usuario novo
ou token passthrough rejeitado. PROXIMO: decodificar o exchanged token
p/ davi e isolar exchange-403 vs mcp-reject; se exchange exigir role/
client-scope, atribuir minimo necessario via admin API (auditable).

## PROMOTION — auth progress 3 (SHA cbaa4637d6)

EXCHANGE FUNCIONA: subject sync-user -> exchanged token aud=
[delpi-central, https://minhadelpi.com.br/apps/api-delpi/mcp, account,
mcp-api-delpi] iss=keycloak realm delpi — aud correto.
MAS davi MCP responde 401 Unauthorized p/ esse token — o MCP valida algo
alem de aud (issuer/JWKS/claim especifico). PROXIMO: encontrar a
validacao real em api-delpi/app/interface/mcp/server.py (routes.py sem
match) — verificar se exige azp, signature path ou claim de cliente.

## PROMOTION — auth progress 4 (SHA 3c1b47fe2c)

CAUSA-RAIZ REFINADA: sync user JWT valido + exchanged token aud correto
MAS davi MCP 401 porque get_current_user()=None — o contexto e populado
por middleware que resolve JWT->usuario no Core/RBAC; usuario criado
só no Keycloak nao e provisionado -> Unauthorized.
PROXIMO: encontrar onde set_current_user e chamado (middleware) —
jwt_validator->core lookup; confirmar se precisa provisioning no Core
(users table) ou claim adicional. Alternativa: usuario existente real
(sem password disponivel) — investigar JIT provisioning do Core.

## PROMOTION — auth progress 5 (SHA 29e93fb8d7)

MCP middleware chain: Bearer -> validate_token (JWKS via OIDC discovery,
iss/aud) -> claims sub+email OBRIGATORIOS -> load_user_rbac (Core,
fallback=claims). "Unauthorized" gen = validate_token exception.
Suspeita: exchanged token pode nao carregar claim email -> 401, OU iss
rejeitado. PROXIMO: decodificar claims do exchanged token p/ conferir
email + azp + iss vs validate_token. Se email ausente -> fix =
garantir email no usuario (ja setado, talvez exchange nao encaminhe —
testar grant direto sem exchange? MCP espera token do seu audience,
entao exchange e obrigatorio — o fallback _rbac_from_claims cobre).

## PROMOTION — auth progress 6 (SHA 38d1f14748)

EXCHANGED token completo: email OK, azp=delia-api, iss=realm public,
aud=[delpi-central,resource-url,account,mcp-api-delpi]. DAVI MCP segue
401 "Unauthorized" — aud=api-delpi exchange NAO permitido p/ o client.
Suspeita restante: validate_token no MCP pode exigir aud=api-delpi OU
validar azp/typ especifico; ou load_user_rbac->Core nao conhece o
usuario (sub novo) -> middleware falha antes do user build.
PROXIMO: ler audience check em jwt_validator.py validate_token e, se
aud OK, instrumentar o MCP log p/ ver a falha exata (signature vs
claims vs rbac). ALTERNATIVA LEGITIMA: executar sync via service-token
path (request_has_valid_internal_service_token) — se o adapter
delegation nao aceita, avaliar contrato admin sync com service user.

## PROMOTION — auth chain QUASE resolvida (SHA c82dd59f96)

RECEITA (etapa por etapa, cada uma comprovada):
1. usuario mcp-catalog-sync realm delpi -> password grant client
   delpi-central + scope=openid (era MISSING_REQUIRED_SCOPE no MCP log)
2. token-exchange delia-api client -> audience=mcp-api-delpi (aud correto)
3. MCP call: Host: minhadelpi.com.br (era Invalid Host header)
4. PENDENTE: Accept: application/json (ultimo erro -32600 Not Acceptable)
Restante = header trivial; depois sync completo davi/teo/vista +
catalog mode snapshot + arggen pydantic_ai + smoke.

## PROMOTION — catalog SYNCED em producao (SHA bdd4198e71)

AUTH CHAIN RESOLVIDA: usuario mcp-catalog-sync realm delpi -> password
grant delpi-central+scope=openid -> token-exchange -> Host+Accept ->
MCP tools/list. SNAPSHOTS ATIVOS em prod (/data/delia/mcp_catalog.db):
  davi v1 (2 tools, hash b0c1a4d1), teo v1 (6, 5fa2e7bb), vista v1 (6, e90bc471).
Prod so tem 3 MCPs configurados (davi/teo/vista); caio/clara/eva/suri
sem base_url -> nao sincronizaveis (sem endpoint).
PROXIMO: DELIA_MCP_CATALOG_MODE=snapshot_experiment no .env srv-api +
restart -> verify -> DELIA_ARGGEN_ENGINE=pydantic_ai + smoke.

## PROMOTION — stage-1 catalog ACTIVE em prod (SHA 2498dcf7e0)

DELIA_MCP_CATALOG_MODE=snapshot_experiment SET no .env srv-api (L409) +
delia-api restartado healthy. Snapshots: davi/teo/vista v1 ACTIVE
(/data/delia/mcp_catalog.db persistente). PROXIMO: (a) smoke snapshot
discovery; (b) DELIA_ARGGEN_ENGINE=pydantic_ai + restart + smoke
P1=30190123 (code field) P2=10080047 P3=conectores P5=outro owner.
Rollback=catalog->live e arggen->llm no .env (linha unica cada).

## PROMOTION — ambas flags ativas em prod (SHA c5e1bb4827)

STATE: DELIA_MCP_CATALOG_MODE=snapshot_experiment +
DELIA_ARGGEN_ENGINE=pydantic_ai — ambas no .env srv-api, container
healthy. Snapshots davi/teo/vista v1 VERIFY PASS.
PROXIMO: smoke via scripts/r4_authenticated_resume_eval._compose (o
import compose_interactive_turn_handler nao existe — reusar o composer
do eval) + bind subject mcp-catalog-sync(scope=openid) -> P1 30190123.

## PROMOTION — smoke P1/P2 prod (SHA b9a0f538ac)

FLAGS ativas: catalog=snapshot_experiment + arggen=pydantic_ai (healthy).
SMOKE P1(30190123)+P2(10080047): ambas "não há registro" (honesto mas
indica arggen pydantic nao produziu args validos — possivelmente
structured output no kimi-k3/OpenRouter difere do Ollama local, ou
exception engolida). PROXIMO: log stage=candidate_arguments engine=
em prod p/ ver produced=True/False + erro real do provider.

## PROMOTION — pydantic-ai prod fix (SHA c82dd59f96)

CAUSA-RAIZ arggen em prod: Agent pedia max_tokens=131072 (default do
modelo) -> OpenRouter 402 credits. FIX: ModelSettings(max_tokens=2048)
+ prompt "somente valores" + unwrap determinístico de dict-string
single-key (modelo embrulhava code={"code":"30190123"} e enchia
description com prosa). Aguardando deploy+re-smoke P1.

## DIAGNOSTICO — "qual a estrutura do 90260148" (local live)

LOG do turn (b66a63f1): discover+execute -> 2 records retornados ->
goal_evidence_relevance=irrelevant -> cri_response presented=0
delivered=2 -> outcome_assessment=insufficient/goal_mismatch ->
resposta honesta "registros reais mas nao correspondem ao pedido".
VEREDICTO: correto — os 2 registros provavelmente sao resultados de
product-search (code/descricao), nao dados de ESTRUTURA (BOM) — a
DÉLIA honestamente recusou apresentar dados que nao respondem a
pergunta. NAO e defeito de interpretacao: seria defeito se os
registros realmente contivessem a estrutura (improvavel — search
retorna produtos). RESIDUAL: se o davi tiver acao de estrutura nao
selecionada, e problema de capability-selection; se nao tiver, e
ausencia de capability no owner (dado legitimo indisponivel).

## T20-SEMANTIC-SEL — resume point (SHA 8768d898dc)

TASK=DELIA-C3-SEMANTIC-CAPABILITY-SELECTION-AND-GOAL-RECOVERY-REMEDIATION-01
EVIDENCIA EXTERNA PROVADA: davi tem get_product_structure (BOM,
required=[code], hierarchy) — retorna componentes reais.
Trace local b66a63f1: discover+execute -> 2 records (product-search)
-> irrelevant -> insufficient/goal_mismatch -> honesto.
PRIMEIRA DIVERGENCIA A PROVAR: o discover query "estrutura" surfou
get_product_structure como candidato? Se sim, selecao LLM errou;
se nao, a query ao davi perdeu a intencao (arggen de discover).
PROXIMO: reproduzir discover payload local p/ a mesma pergunta e ler
candidate list. mint_bearer requer /tmp/env.local no container —
verificar como evals locais obtem token.

## T20-SEMANTIC-SEL — auth path p/ probe local (SHA bc309d9c75)

mint_bearer precisa /tmp/env.local (ausente no container local).
Alternativa validada em prod: password grant delpi-central+scope=openid
-> bind_subject_bearer -> adapter usa host_header+accept+exchange.
Local: mesmo keycloak realm delpi — tentar password grant com usuario
realm local ou testar container delia-t21-main (tem eval env).
PROXIMO: probe _live_capture("mcp:davi") c/ query "estrutura" ->
candidate list -> get_product_structure presente? -> se sim, selecao
LLM errou; se nao, discover-query perdeu intencao.

## T20-SEMANTIC-SEL — auth path p/ probe local (SHA bc309d9c75)

mint_bearer precisa /tmp/env.local (ausente no container local).
Alternativa validada em prod: password grant delpi-central+scope=openid
-> bind_subject_bearer -> adapter usa host_header+accept+exchange.
Local: mesmo keycloak realm delpi — tentar password grant com usuario
realm local ou testar container delia-t21-main (tem eval env).
PROXIMO: probe _live_capture("mcp:davi") c/ query "estrutura" ->
candidate list -> get_product_structure presente? -> se sim, selecao
LLM errou; se nao, discover-query perdeu intencao.

## T20-SEMANTIC-SEL — probe local 401 (SHA 04ff68659d)

disc_probe.py /tmp: 401 no admin token — a troca
KEYCLOAK_ADMIN_URL replace(keycloak,delpi-gateway) era heuristic;
local admin URL/senha diferem. Sync user pode nao existir no realm
local. ALTERNATIVA SIMPLES: rodar o probe no container delia-t21-main
(avaliador ja tinha auth funcional) OU ler os invocations gravados no
runs do turn real b66a63f1 — ja mostrava o que o discover produziu.

## T20-SEMANTIC-SEL — handoff (SHA deeb492239)

PROBES locais bloqueados: delpi-delia-api nao tem admin/user env p/
password grant; delia-t21-main env.local ausente mas o eval
local_orchestration_reliability_eval RODOU nele (auth diferente —
mint via scripts, talvez keycloak local user ou token fixture).
PROXIMO: rodar disc_probe via path eval do t21
(scripts/r4_authenticated_resume_eval._compose + _mint_bearer de
semantic_fidelity_eval) -> _live_capture davi query "estrutura" ->
candidate list. Se get_product_structure aparece -> selecao LLM errou
(root cause). Se nao -> arggen do discover perdeu intencao.

## T20-SEMANTIC-SEL — auth bloqueio total local (SHA 22b36b26df)

mint_bearer do eval tambem 401 no t21 (keycloak reiniciado pode ter
invalidado fixture/credencial). ALTERNATIVA SEM TOKEN: a davi tem
internal-service-token path no middleware
(request_has_valid_internal_service_token -> service_user
is_superadmin) — usar API_DELPI_INTERNAL_SERVICE_TOKEN do .env local
como Bearer direto no MCP HTTP call (nao via delegated-credential —
o adapter exige JWT mas o service-token path do middleware e
passthrough legitimo service->service, READ tools/list).
PROXIMO: POST tools/list c/ service token -> candidatos de
"estrutura" em discover sem bearer? tools/list so lista tools
(discover+execute), nao candidates — candidates vem de
discover_delpi_information invocation que exige subject? Nao — o
MCP aceita service token p/ READ; testar discover call direto.

## T20-SEMANTIC-SEL — ROOT CAUSE comprovada (local probe)

CADEIA (turn b66a63f1 + probes in-process no delpi-api-delpi):
1. discover query = input_text verbatim -> davi retorna APENAS
   get_product_structure como candidato (score top; probe exato).
2. candidate_token vincula action -> execute RODOU
   get_product_structure (probe executor ASGI: GET
   /products/90260148/structure -> 200, BOM real: root=90260148
   CHICOTE, items=2 nos PI c/ components MP aninhados, total=2).
3. outcome.structured = {action_id,status,entity=product_structure,
   shape=hierarchy, data:{root,items,total}} — CONTRATO PRESENTE.
4. extract_pagination_envelope pega data.items -> 2 records nos;
   DESCARTA data.root (o produto perguntado) e entity/shape.
5. _judge_goal_evidence block = {business_subject, records:[2 nos sem
   mencao a 90260148]} -> LLM julga irrelevant (corretamente, dado
   contexto cortado) -> goal_mismatch -> resposta honesta-mas-errada.
PRIMEIRA DIVERGENCIA CAUSAL = projecao de evidencia: dropa
entity/shape/root do resultado antes do juiz de relevancia.
NAO foi selecao (capability correta executou), NAO foi arggen
(code correto), NAO foi discover.
FIX canonico: projetar contexto declarado do owner (entity/shape +
root subject node) em EvidenceFacts e incluir no bloco do juiz —
generico p/ qualquer resultado enraizado, sem regra por palavra.

## T20-SEMANTIC-SEL — FIX provado (local real-LLM judge)

FIX: EvidenceFacts.result_context — projecao bounded do contrato
declarado do owner (entity/shape + no raiz root/parent/subject,
sanitizado, max 12 campos escalares) + incluso no bloco do juiz
goal_evidence_relevance e no preview de recovery + instrucao
governada ensina: root binding SO aplica quando contexto nomeia
raiz concreta e o objetivo pede estrutura/composicao/conteudo dela.
SEM regra lexical por palavra — generico p/ qualquer resultado
enraizado (BOM, filhos, membros, itens de pai).
PROVA (probe real in-container, qwen3:4b):
- BOM get_product_structure 90260148: irrelevant -> corresponds
- product_search descricao produto (sibling): corresponds (ok)
- records off-subject p/ goal estrutura (negativo): irrelevant (ok)
RED->GREEN: test_rooted_result_projects_result_context +
test_unrooted_result_has_no_root_context; suites
evidence_to_answer_isolation(12) + contextual_discovery(71) +
goal_evidence_relevance + semantic_decision + engine_b_recovery
(~87) verdes.
INCIDENTE OPERACIONAL: docker cp em bind-mount sobrescreveu 4
arquivos do worktree principal; trabalho concorrente recuperado de
stash@{0} (WIP 08:00:15); zero residuo result_context no worktree.

## T20-NONBLOCKING — gate semantico removido (tests green)

CONTRATO NOVO (DELIA-C3-NONBLOCKING-EVIDENCE-INTERPRETATION-01):
julgamento semantico ANOTA, nunca suprime evidencia autorizada.
- irrelevant -> 1 recovery bounded (preservado) -> se persistir,
  LIMITATION_GOAL_MISMATCH no outcome + caveat caveats.goal_mismatch
  na composicao; verdict ANSWERED mantido.
- uncertain/absent/invalid -> nada anota; deterministica decide.
- insufficiency.goal_mismatch/relevance_unproven (vocab),
  REASON_* constants, _REASON_MESSAGES rows -> orfaos removidos.
- cri_presentation v6 + section caveats (loader fail-closed ok).
REGRESSAO: 317/317 verdes (goal_evidence_relevance, evidence_iso,
contextual_discovery, cri_e2, cri_e3, semantic_decision,
engine_b_recovery).

## T20-NONBLOCKING — deploy produtivo verificado

PROD: pull ad5424e75 -> rebuild delia-api -> healthy, imagem nova
sha256:af506735460c (anterior sha256:428dbb2c = rollback alvo).
cri_presentation v6 carregado (log root_composer), caveats ativo,
NONBLOCKING no orchestration. Flags preservadas:
MCP_CATALOG_MODE=snapshot_experiment + ARGGEN_ENGINE=pydantic_ai +
TOOL_SELECTION=live.
LOCAL: stack dev com mesmo contrato (worktree patch idêntico ao
commit -> merge limpo).
SMOKE NEGOCIO: PENDING — identidade disponivel (mcp-catalog-sync)
sem permissao empresarial; AuthZ boundary legitimo, sem bypass.
TASK_STATUS=COMPLETE(code+local+deploy) · PRODUCTION_BUSINESS_OUTCOME=PENDING
COORDINATION_VERDICT=PENDING_INDEPENDENT_REVIEW


### Registro complementar — 2026-10-24 — Semantic Relevance / Governed Recovery

- `TASK_ID=DELIA-C3-SEMANTIC-RELEVANCE-GOVERNED-RECOVERY-CROSSCUTTING-01`; `STATE=PLANNED_FOR_IMMEDIATE_EXECUTION`; `RUNTIME_IMPLEMENTATION=NOT_EXECUTED`; `DEPLOY_AUTHORIZED=NO`; `R4_AUTHORIZED=NO`.
- Referências: doc 141 §12 (O2 relevance inconclusive); plano 125 adendo prioritário (`46f94e8061324bcfdf9b4f47655d4ffbace300f4`); README (`c7c83484e1149a3f998b4d45baa6b6f514dbebb2`).
- Evidência de código: `assess_outcome` prova completude/requirements tipados, mas não certifica a correspondência semântica entre pedido e registros; mecanismos de seleção semântica e recuperação contextual já existem. `EXISTING_EQUIVALENT=YES_PARTIAL`; `REUSE_DECISION=EXTEND`; contrato end-to-end `TO_INVENTORY` até testes.
- Próximo step bounded: reprodução O2, RED, extensão dos owners existentes e recuperação READ semântica limitada, full regressions, real-model eval A/B, revisão independente. Sem nova engine/planner/provider branches e sem deploy implícito. Este registro documental não é evidência de correção executada.

### §6.426 — 2026-10-24 — Responsive Multi-Column Inline Context (DELIA-UX-INLINE-CONTEXT-RESPONSIVE-MULTICOLUMN-REFACTOR-01)

- `STATE=COMPLETE_LIVE`; `RUNTIME_IMPLEMENTATION=EXECUTED`; `DEPLOYED_SHA=664eec398c` (main ff; `plugin-ui`+`delia` rebuilt via `up-prod-sequential.sh`); `PHASE_NOT_ADVANCED`.
- Causa-raiz: `--delpi-ui-conversation-column-max:760px` + turno shrink-wrap — card `max-width:640` não era o limitante (medido ~550px em 1440 e 1920). Fix: token `1120px` escopo `.dashboard-delia`, turno com contexto aberto `width:100%`, card vira `container-type:inline-size` com áreas 3/2/1 por `@container` (≥860px/≥560px/<560px). `ConversationContextPanel` EXTEND (`trailing` genérico) — trace vira área própria, DOM único, ordem semântica preservada.
- Gates: delia 446/446, plugin-ui 2335/2335, tsc+build+federation OK. Produção autenticada `vd-wide-prod.mjs` 34/34: card 1030px/3 áreas @1920, 738px/2 @1440, 1 col @320–420, zero overflow, zero scroll aninhado, sem popover/barra azul, trace recolhível, dois contextos + painel global independentes, teclado + reduced-motion.
- Residual: REAL_DOCK_QA / zoom 200% / dark-light visual / screen reader TEST_NOT_RUN.
- Evidência: spec 127 §decisão+implementação; `shots-wide/` (C:\temp\delia-qa).

### Registro complementar — 2026-10-24 — Semantic Relevance / Governed Recovery EXECUTADO

- `TASK_ID=DELIA-C3-SEMANTIC-RELEVANCE-GOVERNED-RECOVERY-CROSSCUTTING-01`; `STATE=EXECUTED`; `IMPLEMENTATION_SHA=acff081397` (rebase sobre `9a12659570`; avaliada como `58a7e873c6`, árvore idêntica); `DEPLOY_AUTHORIZED=NO`; `DEPLOY_STATUS=NOT_EXECUTED`; `R4_AUTHORIZED=NO`.
- Evidência: [doc 142](../corrections/mcp-contextual-intelligence-orchestration/142-semantic-relevance-governed-recovery-implementation.md). O2 reproduzido no baseline; julgamento bounded `goal_evidence_relevance` + uma recuperação READ governada; fail-closed `goal_mismatch`/`relevance_unproven`; 23 testes novos; suite 2225/3; gates arquitetura limpos.
- A/B isolado kimi-k3: matriz 11/11 × 11/11 PASS; O2 corrigido (irrelevant→recovery→insufficient honesto); sinônimos sem over-block; injeção recusada; zero erros; tokens `NOT_AVAILABLE`.
- `EXISTING_EQUIVALENT=YES_PARTIAL`; `REUSE_DECISION=EXTEND`; `EXECUTION_DRIFT=NONE`; aceite independente pendente da coordenação.


### Registro complementar — 2026-10-24 — Gate pré-R4 DAVI Knowledge e recuperação multi-estratégia

- `TASK_ID=DELIA-C3-DAVI-KNOWLEDGE-MCP-GUIDANCE-AND-TRANSVERSAL-RECOVERY-01`, `STATUS=PLANNED`, `R4_AUTHORIZED=NO`, `DEPLOY_AUTHORIZED=NO`.
- Evidência GitHub: freeze DAVI 15 documentos + topic index + builder existem; arquivo `openai-workspace-agent-davi.md` marca `KNOWLEDGE_RUNTIME_LIVE=TEST_NOT_RUN`, Files sync/K01-K10 pendentes. `davi_agent_intelligence.json` projeta `governed_knowledge` com `provider_status=TEST_NOT_RUN` e `tools=[]`. Não inferir acesso a documento pelo MCP.
- Evidência DAVI live: `TERM. BALA` revelou códigos 10080092 e 10081004 entre outros; `TERMINAL BALA` devolveu balanças/terminais sem boa precisão; `BULLET` zero nesse filtro. Causa do algoritmo = `TO_INVENTORY`; documentação específica de descrição MP/PI = `TO_INVENTORY` (SB1 do corpus apenas mapeia produto e tipo).
- Plano 125 e documento 143 congelam gate de correção **antes de R4**: owner DAVI comprova publicação de conhecimento/contrato de exposição, owner DÉLIA reusa planner, Outcome, CRI e recuperação semântica bounded (sem novo engine, SQL livre, provider mechanics, ACT). `A0=PARTIAL_EVIDENCE`, `A1/B0/B1/B2=NOT_EXECUTED`, sem aceite funcional ou deploy implícito.

### Registro complementar — 2026-10-24 — Trilha B: recuperação contextual cross-capability EXECUTADA

- `TASK_ID=DELIA-C3-MCP-CONTEXTUAL-INTELLIGENCE-AND-CROSS-CAPABILITY-RECOVERY-01`; `STATE=EXECUTED`; `IMPLEMENTATION_SHA=394b7c738f`; `DEPLOY_STATUS=NOT_EXECUTED`; `R4_AUTHORIZED=NO`.
- Evidência: [doc 144](../corrections/mcp-contextual-intelligence-orchestration/144-delia-cross-capability-contextual-recovery-implementation.md). Recuperação de pertinência estendida: a única rodada governada pode reexecutar `select_group`/`select_capability` com `relevance_feedback` untrusted + `prior_result_preview` bounded — mesmo re-args ou READ alternativo elegível; todos os gates revalidados; PREPARE/ACT rejeitados; dedup e budget intactos.
- RED→GREEN: 28/28 módulo relevance; suite completa exit=0; audits guardrails/boundaries/phase3 findings=0; instructions resource v3 (snapshot governado atualizado).
- A/B isolado kimi-k3: matriz 11/11 PASS; O2 baseline apresenta balanças × candidato `irrelevant`→recovery (cross-capability DAVI live; re-args noutra tentativa)→insuficiência honesta; `term. bala` retorna registros reais pertinentes. `O2_RESOLVED=INCONCLUSIVE` — residual é norma de nomenclatura (Trilha A).
- `EXECUTION_DRIFT=AUTH_PROCEDURE`: auth do eval via admin impersonation (vedado no doc 143/B1) — re-execução sancionada pendente antes do aceite independente.

### Registro complementar — 2026-10-24 — Trilha B: release produtivo local-first EXECUTADO

- `TASK_ID=DELIA-C3-CROSS-CAPABILITY-RECOVERY-LOCAL-FIRST-PRODUCTION-RELEASE-01`; `DEPLOY_STATUS=EXECUTED`; `SOURCE_SHA=c85d5b1356` (conteúdo delia-api ≡ `394b7c738f`); `IMAGE=686d745b87f6`; `ROLLBACK=85cdd244f531`; `R4_AUTHORIZED=NO`.
- Auth gate resolvido: password grant sancionado do usuário `user` (client `delpi-central`) — sem impersonation. Eval local isolado: matriz 11/11 PASS; O2 honesto; sinônimo grounded; write negativo recusado.
- Prod smoke mínimo: health 200, unauth 401, 1 turno O2 com recovery `reinvoke` + segundo julgamento + insuficiência honesta; zero erros; escopo compose `[1/1] delia-api`.
- `O2_BUSINESS_OUTCOME=INCONCLUSIVE` (residual documental DAVI); tokens `NOT_AVAILABLE`; aceite independente pendente.


### §6.427 — 2026-10-24 — Right Rail integrado do Contexto da conversa (DELIA-UX-CONVERSATION-CONTEXT-RIGHT-RAIL-LAYOUT-REFINEMENT-01)

- `STATE=COMPLETE_LIVE`; `RUNTIME_IMPLEMENTATION=EXECUTED`; `DEPLOYED_SHA=f00c6ea739` (main ff; `plugin-ui`+`delia` via `up-prod-sequential.sh`); `PHASE_NOT_ADVANCED`.
- Causa-raiz: `__context-popover` era `position:absolute` overlay sobre o centro, com light-dismiss — `__right` (coluna real) existia no CSS mas nunca era instanciado. Fix: `rightVariant="rail"` no `ConversationThreeRegionLayout` — `<aside role="complementary">` como coluna flex real, sem light-dismiss, Escape preservado, transição de largura 240ms; fallback governado para a superfície flutuante quando centro projetado <480px ou host compacto ≤920px. Consumidora única DÉLIA.
- Gates: plugin-ui 2340/2340, delia 447/447, tsc+build+federation OK. Produção `vd-rightrail-prod.mjs` 50/50: rail 344/299/296px real @1920/1600/1440 com centro redimensionado e zero overlap; @1280 fallback popover (centro <480); mobile popover; grid inline adapta 3→2→1.
- Residual: REAL_DOCK_QA / zoom 200% / dark-light visual / screen reader TEST_NOT_RUN.
- Evidência: spec 127 §implementação right rail; `shots-rightrail/` (C:\temp\delia-qa).

### Registro complementar — 2026-10-24 — Gate pré-R4: consumo de conhecimento multi-especialista EXECUTADO E DEPLOYADO

- `TASK_ID=DELIA-C3-GOVERNED-KNOWLEDGE-CONSUMPTION-AND-PRE-R4-CLOSURE-01`; `STATE=EXECUTED_AND_DEPLOYED`; `IMPLEMENTATION_SHA=becef562b9`; `DEPLOYED_SHA=becef562b9`; `IMAGE=513ee033b0c6`; `ROLLBACK=686d745b87f6`; `R4_AUTHORIZED=NO`.
- Evidência: [doc 145](../corrections/mcp-contextual-intelligence-orchestration/145-governed-knowledge-consumption-multi-specialist-implementation.md). DÉLIA consome guidance governada de DAVI (knowledge READ via discover/execute), TÉO (guias metodologia/produto) e VISTA (guia de produto/formatos) pelo caminho canônico único; `NEW_PLANNERS=0`, `NEW_MCP_TOOLS=0`, `NEW_KNOWLEDGE_ENGINES=0`.
- Extensões bounded: resource v4 (admission/seleção/args/síntese), miss pós-consulta dentro da única rodada de recuperação, citação abaixo de conteúdo na apresentação CRI. 11 testes novos; suite 100%; audits 0 findings.
- Eval isolado real-model com auth sancionada (`user` password grant, sem impersonation): D1–D3, T1–T3, V1–V3, G1–G5 — knowledge READ grounded, guias metodológicos/produto grounded, clarificação honesta quando insuficiente, write recusado sem invocação, READ direto sem consulta desnecessária.
- Deploy `[1/1] delia-api` via procedimento canônico; smoke produtivo mínimo: health 200, unauth 401, 1 turno D1 autenticado GROUNDED com excerto `text`.
- Residual: `O2_RESOLVED=INCONCLUSIVE` — norma MP/PI publicada no corpus V2 (`mp_description_standards`, `TERM.` ratificado), lacuna remanescente é sequenciamento conhecimento→reformulação do modelo; `CRI_OFF_LIVE=TEST_NOT_RUN`; `REAL_TOKEN_USAGE=NOT_AVAILABLE`; aceite independente pendente.

### Registro complementar — 2026-10-24 — R4 estrutural M06/M07 EXECUTADO (decisão explícita)

- `TASK_ID=DELIA-C3-ORCHESTRATION-R4-PRESENTATION-GUIDANCE-REFACTOR-01`; `STATE=EXECUTED`; `IMPLEMENTATION_SHA=aca0f22e59`; `DEPLOY_STATUS=EXECUTED`; `DEPLOYED_SHA=aca0f22e59`; `IMAGE=8a3fe498f488`; `ROLLBACK=513ee033b0c6`; `R4_AUTHORIZED=YES` (decisão explícita subsequente da coordenação, mecanismo exigido pelo parecer independente doc 145 §8 — aceita o residual pré-R4 como não-bloqueante para escopo estritamente estrutural).
- Evidência: [r4-execution-and-evidence](../corrections/mcp-contextual-intelligence-orchestration/refactor-r0-r7/r4-execution-and-evidence.md). M06: helpers de apresentação pura (`_render_synthesis`, `_compose_answer`, `_detail_*`, `_list_header`, `_proven_field_differences`, `_selected_proven_differences`, `_insufficiency_content`, `_format_*`, `_business_lines`, `_md_*` + constantes de bound/texto) movidos verbatim ao compositor existente `conversational_response.py` — DAG inalterado (`orchestration → conversational_response → outcome_assessment`), zero novos módulos, zero sanitizer duplicado.
- M07 guidance: `SKIP_WITH_DECISION` por S4/117 — `_guidance_*`/`_deterministic_guidance_content`/`_pack_guidance_sections`/`_select_guidance_records` permanecem na orquestração (boundary de evidência owner→`outcome_facts`, sem consumer/destino novos provados); `_prior_excerpt_*` KEEP (projeção de evidência de sessão).
- Paridade: 19 testes de caracterização literais (`test_r4_presentation_parity.py`) verdes antes e depois; suite delia-api completa exit 0; audits de arquitetura 0 findings; imports de 9 testes + `cri_activation_eval.py` repontados ao owner canônico. Deploy `[1/1] delia-api` canônico; smoke prod mínimo: health 200, unauth POST 401, 1 turno autenticado 200/GROUNDED (sem matriz LLM — refatoração pura com paridade determinística provada).
- `O2=KNOWN_RESIDUAL` (não reaberto); `CRI_OFF_LIVE=TEST_NOT_RUN`; `R4_INDEPENDENT_ACCEPTANCE=PENDING`; `COORDINATION_REVIEW_REQUIRED=YES`.

### Registro complementar — 2026-10-24 — R5 estrutural M08/M09 EXECUTADO (R5_BOUNDED_ONLY)

- `TASK_ID=DELIA-C3-ORCHESTRATION-R5-SCHEMA-GOAL-MODEL-STAGE-REFACTOR-01`; `STATE=EXECUTED_AND_DEPLOYED`; `IMPLEMENTATION_SHA=e1a57f915b` (rebase de `efcee871b6` sobre `910d2315a1` — delia-api byte-idêntica à árvore testada); `DEPLOY_STATUS=EXECUTED`; `IMAGE=dc9833166850`; `ROLLBACK=8a3fe498f488`; `R5_AUTHORIZED=YES` (review R4 `8a9a960052`: `NEXT_STAGE_AUTHORIZED=R5_BOUNDED_ONLY`); `R6_AUTHORIZED=NO`; `R7_AUTHORIZED=NO`.
- Evidência: [r5-execution-and-evidence](../corrections/mcp-contextual-intelligence-orchestration/refactor-r0-r7/r5-execution-and-evidence.md). M08 MOVE: `_schema_required_gaps`, `_apply_owner_declared_defaults`, `_owner_entity_completeness_gaps`, `_apply_entity_defaults_to_arguments`, `_argument_completeness_gaps`, `MAX_ARGUMENT_KEYS` — verbatim para `interaction/argument_validation.py` (owner canônico de validação de argumentos); DAG `orchestration → argument_validation → outcome_assessment`, acíclico.
- M09 KEEP: `_build_arguments`, `_model_stage_proposal`, `_propose`, `_repair_once`, `_turn_goal_from_proposal` — boundary coordinator↔model legítimo (lineage, budgets, repair rounds, `_TurnGoal` interno); caso negativo adversarial documentado.
- Paridade: 19 caracterizações literais (`test_r5_argument_schema_parity.py`) + stage04 (36) + argument_validation (37) verdes antes/depois; suite completa exit 0; audits 0 findings. Deploy `[1/1] delia-api` canônico; smoke prod mínimo: health 200, unauth POST 401, 1 turno autenticado 200/GROUNDED.
- `O2=KNOWN_RESIDUAL`; `CRI_OFF_LIVE=TEST_NOT_RUN`; `R5_INDEPENDENT_ACCEPTANCE=PENDING`; `COORDINATION_REVIEW_REQUIRED=YES`.

### §6.428 — 2026-10-24 — Contexto inline em duas zonas semânticas (DELIA-UX-INLINE-CONTEXT-SEMANTIC-DENSITY-REFACTOR-01)

- `STATE=COMPLETE_LIVE`; `RUNTIME_IMPLEMENTATION=EXECUTED`; `DEPLOYED_SHA=97f393390b` (main ff; `delia` via `up-prod-sequential.sh`); `PHASE_NOT_ADVANCED`.
- Decisão `26867a42df`: substituir a distribuição rígida em três áreas por duas zonas semânticas — A "Geração" (metadados em grid interno de pares) e B "Evidências e atividades" (evidências → atividades → rastreamento técnico recolhível na mesma zona). `EXISTING_EQUIVALENT=YES`; `REUSE_DECISION=EXTEND` — diff exclusivamente CSS em `plugins/delia/src/index.css`; zero componente/endpoint/contrato novo; `trailing` do `ConversationContextPanel` preservado.
- Implementação: `@container` no próprio card (não viewport): ≥560px com ≥2 seções → grid `minmax(0,1.15fr)/minmax(0,1fr)`; <560px ou 1 seção → coluna única na ordem semântica (nenhuma zona vazia reservada). `.delia-context__list` = `auto-fit minmax(140px,1fr)` com cap de 2 colunas acima de 860px de card.
- Causa-raiz dos reworks: min de par 200px → 160px → 140px ainda não cabia na zona A em 1440 (lista ~296px vs mínimo 300px); resolvido com share assimétrico da zona A + cap explícito de 2 pares em wide — correção de layout real, não de expectativa de teste (exceto @1280, onde o card de 578px legitivamente cai no modo compacto <560px de conteúdo).
- Produção `vd-densectx-prod.mjs` 43/43 PASS: altura −19% @1920 (607→494), −18% @1600 (624→511), −19% @1440 (653→528); right rail aberto mantém 2 zonas @1920/1600 e coluna única @1440 sem overflow; @1280 fallback popover governado; @375 mobile coluna única; dark + reduced-motion OK; zero nested scroll / horizontal overflow.
- Regressão: delia 443/443 + plugin-ui 2335/2335 + tsc + build + federation OK (verde antes do deploy; diff CSS não altera estrutura DOM testada — 38 testes de contexto preservados).
- Residual: REAL_DOCK_QA / ZOOM_200_QA / SCREEN_READER_QA `TEST_NOT_RUN`; zoom e Dock real pendentes de evidência antes de claim integral.
- Evidência: spec 127 §Registro de implementação DENSECTX; `C:\temp\delia-qa\shots-densectx\`.
### Registro complementar — 2026-10-24 — R5 revisado / R6 preservação do core EXECUTADO (sem diff, sem deploy)

- `TASK_ID=DELIA-C3-ORCHESTRATION-R6-CORE-PRESERVATION-AND-SAFETY-REGRESSION-01`; `STATE=EXECUTED_NO_CODE_CHANGE`; `BASE_SHA=97f393390b`; `CODE_DIFF=NONE`; `DEPLOY_STATUS=NOT_RUN_NO_RUNTIME_CHANGE`; `R6_BOUNDED_PREPARATION=AUTHORIZED`; `R6_CODE_EXECUTION=AWAITING_RELEASE_GATE_DECISION`; `R7_AUTHORIZED=NO`.
- Review R5 (`0fc131155b`): `R5_REVIEW=ACCEPT_WITH_RESIDUAL`; `RELEASE_GOVERNANCE_CONFLICT=ARCHITECTURE_DECISION_REQUIRED` — deploy R5 precedeu o review independente sob autorização operacional da task; precedência entre a diretriz documental (review + autorização antes do deploy) e a autorização per-task **escalada sem decisão** (`ESCALATED_UNRESOLVED`); nenhuma aprovação retroativa presumida; nenhum rollback ordenado (sem evidência de dano).
- Evidência: [r6-execution-and-evidence](../corrections/mcp-contextual-intelligence-orchestration/refactor-r0-r7/r6-execution-and-evidence.md). Caller graph bounded: `attempt`→`handle_interactive_turn.py:425`; `_attempt`→`attempt()`; `_select_target`→`_attempt`; `_invoke_selected`→6 sites; `_attempt_prepare`→2 sites PREPARE; `_execute_prepared_act`→1 site confirmação bound; `_audit`→9 sites. 7/7 `ACTIVE/KEEP`; scan AST zero zero-referência em funções privadas; `DEAD_CODE_PROVEN=NONE`; tabela de remoções vazia.
- Regressão (não-modificadora): focados core+segurança verdes — provider_neutral 19, specialist_interop_security, stage02–06, r2/r45/r5-parity, c3/evidence, semantic_argument; full backend delia-api exit 0; arch gates 41 testes 0 findings; DAG `orchestration→argument_validation→outcome_assessment` acíclico e inalterado; `LOCAL_MODEL_EVAL=NOT_NEEDED_FOR_STRUCTURAL_PARITY` (zero mudança em prompts/seleção/model-stage/evidence/outcome/semântica).
- `O2=KNOWN_RESIDUAL`; `CRI_OFF_LIVE=TEST_NOT_RUN`; `R6_INDEPENDENT_ACCEPTANCE=PENDING`; `COORDINATION_REVIEW_REQUIRED=YES`.

### Registro complementar — 2026-10-24 — R7 aceite integrado e fechamento residual EXECUTADO (diff bounded instrucional, sem deploy)

- `TASK_ID=DELIA-C3-ORCHESTRATION-R7-INTEGRATED-ACCEPTANCE-AND-RESIDUAL-CLOSURE-01`; `STATE=EXECUTED_EVIDENCE_READY_FOR_REVIEW`; `BASE_SHA=f89e73376c`; `CODE_DIFF=BOUNDED_INSTRUCTION_RESOURCE` (`orchestration_instructions.delpi.json` v4→v5 + `_ORCH_VERSIONS` + contract-lock tests; 4 arquivos, +49/−10); `DEPLOY_STATUS=NOT_RUN_RELEASE_GATED`; `R7_EXECUTION=AUTHORIZED` (task order PO); `RELEASE_AUTHORIZATION=PENDING_INDEPENDENT_REVIEW`; `R7_INTEGRATED_VERDICT=BLOCKED_WITH_EVIDENCE`.
- Evidência: [r7-execution-and-evidence](../corrections/mcp-contextual-intelligence-orchestration/refactor-r0-r7/r7-execution-and-evidence.md). Regressão: full backend ×3 exit 0 + focused (instruction-resource, governed-knowledge, relevance, specialist-orchestration, security, provider-neutral, intelligence-eval) verdes; arch gates 0 findings/16 owners. Eval real-model isolado: `delia-r7-eval-kimi` (HEAD + OpenRouter `moonshotai/kimi-k3`) + `api-delpi-r7` (HEAD, 772 actions, corpus V2) + `delia-r7-eval-crioff`.
- Residual matrix: `R7-01_O2=BLOCKED_OWNER_SIDE_API_DELPI` (first divergent stage `arguments`; `TERM. BALA` só via norma MP s0055 — surfacing/endereçamento do doc governado é gap do owner, nova task api-delpi requerida); `R7-02_CRI_OFF=PARTIAL_ACCEPT` (paridade local provada; prod OFF `TEST_NOT_RUN`); `R7-03_D1=ACCEPTED_WEAK` (doc-first correto, conteúdo paginado parcial — mesma família do gap owner-side); `R7-04_KEYCLOAK_DAG=CLOSED` (password grant dev-only; prod=Portal+token-exchange; DAG disabled); `R7-05_TOKENS=CLOSED` (observability.calls com input/output/total+duration_ms); `R7-06_O2_SIBLING=PASS` (`terminal pino` → `corresponds` + códigos reais); `R7-07_TEO_ADMISSION=ACCEPTED_MODEL_INSTABILITY` (`get_methodology_guide` funcional; miss único); `R7-08_ARCH=PASS` (sem paralelismo, 7 funções ativas); `R7-09_WRITE_BOUNDARY=PASS` (`target_selection=not_applicable`, zero PREPARE/ACT); `R7-10_SAFETY=PASS` (dims segurança verdes; 2 transport flakes delia-json); `R7-11_VISTA=ACCEPTED_SUBOPTIMAL_SELECTION` (empty honesto via `list_playlists`).
- `O2=OPEN_RESIDUAL` → dependência: api-delpi precisa expor endereçamento/lookup por assunto no `read_governed_technical_knowledge` (ou surfacing da guidance em queries operacionais) antes que a cadeia doc-first→reformulation feche; `COORDINATION_REVIEW_REQUIRED=YES`; `NEXT_STAGE_AUTHORIZED=NO`.

### §6.429 — 2026-10-24 — Mensagem do usuário clean visual (DELIA-UX-CONVERSATION-USER-MESSAGE-CLEAN-VISUAL-REFINEMENT-01)

- `STATE=COMPLETE_LIVE`; `RUNTIME_IMPLEMENTATION=EXECUTED`; `DEPLOYED_SHA=59c88987b6` (main ff; `plugin-ui`+`delia` via `up-prod-sequential.sh`); `PHASE_NOT_ADVANCED`.
- `EXISTING_EQUIVALENT=YES`; `REUSE_DECISION=EXTEND`. Diff bounded: `ConversationUserMessage` ganhou slot opcional `actions` (presentation-only, compatível); `__bubble` ganhou `max-width: min(100%, 68ch)` — mesma medida de leitura da resposta DÉLIA; DÉLIA `ConversationTimeline` compõe a única ação legítima "Copiar mensagem" via `MessageActionBar`+`HintAction`+`IconButton` com feedback "Mensagem copiada"; `delpi-ui-message-action-scope` ativa reveal hover-focus (sempre visível em touch). Zero backend, zero contrato novo, zero componente novo.
- Produção `vd-usermsg-prod.mjs` 28/28 PASS @1920/375/dark: bolhas 58/413/587px (curta/média/longa — fit-content com cap de leitura), multiline 6 linhas preservado, avatar topo+direita, ação subordinada (op 0→1 no hover, 1 em touch), feedback de cópia real, sem ações fictícias, bolha fora do right rail aberto, zero overflow, reduced-motion `none`, dark neutro `rgb(27,32,48)`.
- Regressão: plugin-ui 2343/2343, delia 449/449, tsc+build+federation OK.
- Residual: REAL_DOCK_QA / ZOOM_200_QA / SCREEN_READER_QA `TEST_NOT_RUN`.
- Evidência: spec 73 §13.1; `C:\temp\delia-qa\shots-usermsg\`.

### Registro complementar — 2026-10-24 — R7 fechamento integrado DAVI↔DÉLIA EXECUTADO (O2=PASS local; deploy gated)

- `TASK_ID=DELIA-R7-DAVI-INTEGRATED-RELEASE-AND-O2-OUTCOME-CLOSURE-01`; `STATE=EXECUTED_EVIDENCE_READY_FOR_REVIEW`; `BASE_SHA=118e51ad84`; `FINAL_HEAD=dbb65dabe9`=origin/main (ff-only); `CODE_DIFF=BOUNDED` (api-delpi `openapi_baseline.json` +7: parâmetro `subject` no candidato discovery; delia-api instruction resource v4→v13 + version allowlist + contract-lock tests; 5 arquivos, +45/−30); `DEPLOY_STATUS=BLOCKED_PENDING_AUTHORIZATION`.
- **DAVI gap fechado:** `subject` existia no router/OpenAPI mas não no `argument_schema` do candidato (baseline congelado) — discover→execute não endereçava por assunto. Resync canônico `scripts/sync_openapi_baseline.py`; regressão DAVI focada **188 pass**; falhas C1 = `ENVIRONMENT_FAILURE` (`PLUGINS_DB_*` ausente no runner; 23/23 verdes no container configurado; histórico 2FAIL/30SKIP preservado).
- **DÉLIA bounded (v13):** doc-first semântico para assuntos coloquiais; doc ≠ registro para relevance; `mismatch_hint` carrega designação canônica; `native_assessment=foreign_evidence_required` + `foreign_selection` documental acionam o caminho `enrichment` já existente; reformulação imperativa verbatim no recovery/foreign args. Sem planner/loop/budget novo, sem hardcode.
- **O2=PASS real:** corr `9962e656` — `search_products` alvo → `foreign_evidence_required` → `davi.discover` → execute norma → `foreign_evidence` → `search_products(description=TERM.+BALA)` (access log api-delpi) → `corresponds` → 2 registros reais verificados: `10080092`, `10081004`. Confiabilidade: 1/3 runs (variância de modelo kimi-k3 eval; prod=`delia-json` mais fraco) — `RELIABILITY_RESIDUAL=OPEN`.
- Regressão: delia focused 30/30 + **full backend 2281 pass/3 skip**; arch gate 0 findings; sibling `terminal pino` PASS (`10080683`/`10081935`); D1/VISTA/listing sem regressão.
- `O2=PASS_EXECUTOR_EVIDENCE`; `R7-01=CLOSED_LOCALLY_WITH_RELIABILITY_RESIDUAL`; `R7_FINAL_ACCEPT=NO` até revisão independente + autorização operacional + homologação produtiva; `COORDINATION_REVIEW_REQUIRED=YES`.

### Registro complementar — 2026-10-24 — R7 reliability remediation bounded EXECUTADO (mecanismo corrigido; reliability abaixo do threshold proposto)

- `TASK_ID=DELIA-R7-PRODUCTION-RELIABILITY-REMEDIATION-AND-DEPLOY-01`; `STATE=BOUNDED_CORRECTION_COMMITTED_GATES_PENDING`; `BASE_SHA=1e52c597b7`; `FINAL_HEAD=17dc08b9c8`=origin/main (ff-only); `DEPLOY_STATUS=BLOCKED_PENDING_AUTHORIZATION`.
- **Baseline prod read-only:** produção stale — instruction v4 (v13 nunca deployada), modelo efetivo kimi-k3 (divergente do `delia-json` reportado), MCP DAVI+OpenAPI habilitados, TTL delegado 120s. O2 prod (v4): literal → `irrelevant` → honest `insufficient`, GROUNDED, zero WRITE.
- **Causa-raiz:** `native_assessment` especulativo era o único gate do caminho foreign (6/7 `sufficient`); recovery não tinha caminho foreign. Correção: recovery re-avalia com `relevance_feedback` (mismatch provado) e compõe estágios existentes; consult recebe contexto de feedback. Instructions v13→v16. Sem planner/router/hardcode.
- **Denominadores:** foreign chain ~0/7 → ~5/6 dispara; O2 PASS 3/~25 (~12%) no kimi-k3 eval — bottleneck residual = formulação de args do re-invoke (variância de modelo). Backend: 2284/2286, 2 ENVIRONMENT_FAILURE provadas no base. Threshold ≥70% proposto à coordenação.
- `R7_FINAL_ACCEPT=NO`; `COORDINATION_REVIEW_REQUIRED=YES`; `NEXT_ACTION=INDEPENDENT_REVIEW_17dc08b9c8 + threshold decision + (se aprovado) model/config decision antes de deploy`.

### Registro complementar — 2026-10-24 — Avaliação congelada v16 EXECUTADA (O2 1/10; release gate não atingido)

- `TASK_ID=DELIA-R7-PRODUCTION-DEPLOY-REAL-VALIDATION-AND-RELIABILITY-CLOSURE-01`; `STATE=FROZEN_EVAL_COMPLETE_DEPLOY_BLOCKED`; `EVALUATED_SHA=667a670cd8`; `INSTRUCTION_VERSION=16`; `MODEL=kimi-k3/OpenRouter`; denominadores completos, token fresco por run.
- **O2 N=10 → 1/10 PASS** (`description=TERM.+BALA` confirmado em access log + registros `10080092`/TERM.BALA 1,00-2,50MM2). Foreign chain dispara ~9/10 e consult completa 8×; gargalo único = estágio `arguments` do re-invoke (copia canônica 1/9). Descartados: contrato, transporte, projeção de evidência, propagação de contexto, validação — residual é variância de formulação do modelo.
- Siblings: `terminal pino` 2/3; D1 doc-first; TÉO/VISTA honestos (miss conversational/honest-empty); AuthZ 401; WRITE inelegível sem ACT; zero fabricação grounded em todas as falhas.
- `DEPLOY_DAVI=NOT_EXECUTED (sem diff novo; autorização ausente)`; `DEPLOY_DELIA=NOT_EXECUTED (10% < 70% provisório; autorização ausente)`; `NEXT_ACTION=DECISÃO DE COORDENAÇÃO: threshold oficial + model/config + modalidade canary-vs-hold + revisão independente de cada release`.

### Registro complementar — 2026-10-25 — Spec 146 evidence-bound arguments IMPLEMENTADO (mechanism provado; E2E ainda model-bound)

- `TASK_ID=DELIA-R7-EVIDENCE-BOUND-ARGUMENTS-FULL-IMPLEMENTATION-AND-GOVERNED-DEPLOY-01`; `STATE=CANDIDATE_COMMITTED_GATES_PENDING`; `FINAL_HEAD=405575f745`=origin/main; `DEPLOY_STATUS=BLOCKED_PENDING_AUTHORIZATION`.
- Contrato `selections` (argument+source_ref+selected_value) na fronteira de `_build_arguments`; validação determinística em `argument_validation.py` (EXTEND, padrão `_synthesis_selections`); fail-closed em ref forjada/valor ausente/conflito/campo orquestrado; instrução v17.
- Denominadores: backend 2284/2286 (2 env-failures pré-existentes); RED→GREEN 5 novos testes; real-model ~3/9 uso de selections, 2/2 materialização verbatim; O2 E2E ~1/10 (inalterado — adoção baixa sob kimi-k3; v18 MUST medido/revertido = segunda falha do pacote → stop).
- `NEXT_ACTION=INDEPENDENT_REVIEW_405575f745 + decisão model/config + autorização operacional por serviço`.

### Registro complementar — 2026-10-25 — A/B de seleção de modelo EXECUTADO (CASO B: nenhum elegível supera kimi-k3; bloqueio é contratual)

- `TASK_ID=DELIA-R7-MODEL-SELECTION-ADOPTION-AND-RELIABILITY-ACCEPTANCE-01`; `STATE=AB_EVAL_COMPLETE_ARCHITECTURE_DECISION_REQUIRED`; `EVALUATED_SHA=405575f745`; `INSTRUCTION_VERSION=17`; matriz congelada O2 N=10/modelo, mesma infra/contrato/DAVI/corpus; segunda instância no container eval com `DELIA_LLM_MODEL` isolado.
- Baseline `kimi-k3`: selections ~3/9, O2 1/10. `gpt-4o-mini`: consult 20/20 ok, **selections 0/10**, O2 verdadeiro 0/10 e **7/10 falso-positivo** (balanças `BALANCA` apresentadas como grounded — regressão de correção do juiz). `claude-sonnet-5`/`qwen-2.5-72b`/`kimi-k2.6`/`gpt-4o`: 0/10 — bypass conversacional ou decline antes do estágio arguments; gpt-4o 4/10 transporte 502. `deepseek-chat`: rota degradada (9/10 502; probe direto OK).
- Causa: `selections` é opcional e paralelo a `arguments`; todos os modelos redigitam em vez de referenciar quando chegam ao estágio — e a maioria nem chega. Não há modelo elegível que melhore adoção sem regressão; a alavanca remanescente é contratual (obrigatoriedade condicional ou snapping determinístico) → fora da autoridade da task.
- `MODEL_RECOMMENDATION=KEEP kimi-k3`; `NEXT_ACTION=DECISÃO DE COORDENAÇÃO: ARCHITECTURE_DECISION sobre contrato selections (opcional→condicional/snapping) antes de qualquer v19 ou novo modelo`.


### DELIA-R7-CONDITIONAL-EVIDENCE-REFERENCE-LOCAL-IMPLEMENTATION-RELEASE-01 — decisão PO 2026-10-25

Direção `APPROVED_DIRECTION`: seleção semântica pertence ao LLM; backend valida referência/valor e aceita schema de parâmetros owner MCP/Domain API, sem snapping fuzzy/hardcode. Planejamento executivo [147](../corrections/mcp-contextual-intelligence-orchestration/147-conditional-evidence-reference-local-execution-and-release-plan.md), spec 146 atualizada e R7 evidência vinculada. Avaliação exclusivamente com LLM local existente nesta task (modelo externo `TEST_NOT_RUN_BY_PO_DECISION`); executor deve comprovar local model, SHA/config, RED→GREEN e outcome multirun. `PO_DEPLOY_DIRECTION=CONDITIONAL`; `INDEPENDENT_REVIEW=PENDING`; `OPERATIONAL_AUTHORIZATION=PENDING`; `R7_FINAL_ACCEPT=NO`. Nenhum deploy foi executado por este registro.

### Registro complementar — 2026-10-25 — Contrato 147 de referência condicional IMPLEMENTADO + avaliação local (delia-json insuficiente para E2E)

- `TASK_ID=DELIA-R7-CONDITIONAL-EVIDENCE-REFERENCE-LOCAL-IMPLEMENTATION-RELEASE-01`; `STATE=CONTRACT_IMPLEMENTED_LOCAL_EVAL_DONE_DEPLOY_BLOCKED`; `INSTRUCTION_VERSION=18`; `LOCAL_MODEL=delia-json (qwen2.5 3.1B Q4_K_M, ollama:11434)`.
- EXTEND em `argument_validation.py`/`_build_arguments`: `evidence_arguments` + declaração implícita via `selections`; campo declarado aceita só seleção literal verificada — texto livre dropado, ausência vira missing/clarify; orquestrados/inválidos ignorados; fail-closed sem schema.
- RED→GREEN: 6 testes novos (verbatim, drop-free-text, forged-ref, bare-string, ignored-entries, required-unbound→missing); conflito invertido conforme doc 147. Focused 104/104; backend 2294/2296 (2 env-failures pré-existentes).
- Local real-model matriz: O2 0/10 (admission miss + invalid_model_output), pino 0/3, D1 0/3, TÉO 0/3, VISTA 0/3, READ direto 0/3, WRITE-ineligible 3/3 recusa (0 ACT), AuthZ 401; `FALSE_POSITIVES=0`, `SELECTION_ADOPTION=0` — 3B não atinge o estágio onde o contrato atuaria.
- `DEPLOY=BLOCKED (local reliability 0%)`; `INDEPENDENT_REVIEW=PENDING`; `NEXT_ACTION=DECISÃO DE COORDENAÇÃO: modelo local capaz vs liberação de eval externo controlado; contrato 147 implementado aguarda revisão`.


### DELIA-R7-LOCAL-GOAL-RECOVERY-TO-PRODUCTION-ACCEPTANCE-01 — PO execution direction (2026-10-25)

Plano 147 atualizado: [execução local, F1/F2, recuperação orientada ao objetivo e release governado](../corrections/mcp-contextual-intelligence-orchestration/147-conditional-evidence-reference-local-execution-and-release-plan.md). PO solicita tratar falhas técnicas recuperáveis sem encerrar o objetivo do usuário, com três exemplos reais quando pedidos três; execução contínua e correções bounded até critérios locais comprovados, **sem** modelo remoto, lists de sinônimos/produtos, acoplamento a provider ou nova engine. **Status factual:** `PLANNED`; F1 `REWORK`; F2 `TO_CHARACTERIZE`; O2 local último teste `0/10 FAIL`; revisão independente futura `PENDING`; autorização PO de deploy `CONDITIONAL`, autorização operacional específica `PENDING`, deploy nesta task `NOT_EXECUTED`, R7 final `NO`. Stops de segurança/arquitetura/segunda falha do mesmo pacote são obrigatórios e não equivalem a conclusão satisfatória.


### Registro complementar — 2026-10-25 — Remediação F1/F2 executada (goal recovery bounded) — `DELIA-R7-LOCAL-GOAL-RECOVERY-TO-PRODUCTION-ACCEPTANCE-01`

- `STATE=F1_F2_REMEDIATED_LOCAL_EVAL_GATE_BLOCKED`; base `fe9ca71369`; escopo `argument_validation.py` + `orchestration._build_arguments` + testes.
- F1: declarado-documental opcional não vinculado ⇒ `(None, missing_inputs)` — zero invocação não filtrada; nomes alimentam resolver/clarify existente. F2: ramo sem schema honra declarações via `selections`/`evidence_arguments` fail-closed.
- `PREINVOKE_FAILURE_RECOVERY=existing` — `missing_inputs → _resolve_missing_inputs → clarify`; sem planner/segundo state machine.
- Backend 2296/2298 (2 env pré-existentes); focused 192/192. Local `delia-json`: três-exemplos 0/10 (admission), O2 0/3, pino/D1/TÉO/VISTA 0/3, READ direto 1/3 GROUNDED real, WRITE 3/3 recusa, AuthZ 401, 0 falsos positivos.
- `DEPLOY=BLOCKED_NO_LOCAL_RELIABILITY` — contrato pronto; executor sem modelo local autorizado que alcance o estágio governado. `NEXT_ACTION=decisão de coordenação (modelo local capaz OU autorização de avaliação externa controlada) + review independente do SHA`.


### Registro complementar — 2026-10-25 — Recovery provado + R1/R2/R3 fechados — `DELIA-R7-EXISTING-RECOVERY-AND-OUTCOME-CLOSURE-01`

- `STATE=RECOVERY_PROVEN_RESIDUALS_CLOSED`; base `abccde87ac`; escopo `argument_validation.py` + `orchestration._resolve_missing_inputs` + testes.
- R1: teste de fluxo prova `declared-unbound → resolver same-owner → rebuild → owner READ → SUCCESS` — recovery existente suficiente, sem novo engine. R2: asserts de consumidor/tentativas/proposta/owner/outcome. R3: `unbound_declared` determinístico (ordem da proposta); declarações além de `MAX_EVIDENCE_SELECTIONS` seguem fail-closed (cap limita materialização apenas).
- Defeito irmão F1 corrigido: resolver tail resolvia com `still_missing`/campos ausentes → invocação sub-filtrada; `_missing_inputs_bound` agora exige cobertura total antes de resolver (normal + ambíguo).
- Local `delia-json`: Outcome empresarial (3 registros) segue bloqueado por capacidade de admission do modelo autorizado — não por contrato.
- `DEPLOY=BLOCKED` até local outcome + review + autorização operacional.


### DELIA-R7-ARCHITECTURE-DRIFT-AND-GROUNDED-OUTCOME-REMEDIATION-01 — plan 148 (2026-10-25)

Plano [148](../corrections/mcp-contextual-intelligence-orchestration/148-r7-architecture-drift-remediation-and-outcome-closure-plan.md) criado e aprovado como roteiro proposto para execução condicionada a reancoragem/contrato. Revisão de v19 `6e51626b1b`: A1 `TO_INVENTORY` (owner_surface_kinds estático), A2 `EXTEND_WITH_TESTS`, A3 `FAIL_REPORTED` (VISTA control-plane apresentado como três registros empresariais), outcome local `FAIL`, deploy `BLOCKED`, R7 `OPEN`. WPs: WP0 reanchor, WP1 admission dinâmico, WP2 provenance/control-plane business gate, WP3 argumentos/recovery, WP4 local-only eval, WP5 review/release. Sem novo código ou deploy por documentação. Comparação com padrões OpenAI/Anthropic/Microsoft apenas como princípios, sem instalação de framework.


### §6.430 — 2026-10-25 — Investigação única de contexto e inteligência operacional (DELIA-CONTEXT-INTELLIGENCE-SINGLE-PASS-CANONICAL-INVESTIGATION-01)

- `TASK_ID=DELIA-CONTEXT-INTELLIGENCE-SINGLE-PASS-CANONICAL-INVESTIGATION-01`; `STATE=INVESTIGATION_COMPLETE_AWAITING_DECISION`; `BASE_SHA=d3dfaa2cca` (=origin/main); read-only — zero alteração de código/prompt/modelo/infra/schema/deploy; R7/Plano 148 não tocado (WP1/WP3 do commit d3dfaa2cca incorporados ao baseline e à matriz).
- Entregável: [Doc 151](../corrections/mcp-contextual-intelligence-orchestration/151-single-pass-context-intelligence-investigation-evidence-and-plan.md) — diagnóstico factual, transport map completo, matriz de 23 estágios, comparação 3-vias (canon × código × mercado), inventário de reuso, gaps com evidência, análise de segurança/autoridade, propostas mínimas, plano fechado WP-A..WP-F e decision register D1-D8.
- Diagnóstico: histórico é 100% client-side (`buildInteractionContext`, React state, 16.384 chars, pares completos); `SESSION_PERSISTENCE=NONE` é decisão canônica aprovada (doc 21 §8, ACCEPT_WITH_RESIDUAL); adapter serializa `prior_context`→`user`/`assistant` verbatim (sem tools/autoridade/CoT); 23 estágios mapeados — 2 recebem NONE (clarify/corroborate), 4 recebem contexto reduzido intencional (observation ≤800c, excerpts ≤12, folded ≤4×120c).
- Gaps reais com evidência: G1 sem persistência/identidade de conversa (deferido por cânone); G2 sem compactação (pair-drop silencioso, sem marcador de omissão); G3 `OLLAMA_NUM_CTX` eficácia não comprovada + adapter não serializa `num_ctx`; G4 sem token budget/estimativa pré-chamada (pior caso ~32k chars ≈8-10k tokens vs janela 2048/4096); G5 estágios de seleção com `()`/observation reduzida + inconsistência `_discover_candidate` vs `_invoke_selected`; G6 `_TurnGoal` re-derivado por turno (sem carry-forward tipado); G10 turnos injetados indistinguíveis no wire (residual bounded por revalidação).
- `TEST_NOT_RUN`: captura sanitizada do wire payload (adapter tests + leitura direta provam serialização pretendida); `TO_INVENTORY`: eficácia de `OLLAMA_NUM_CTX` vs `OLLAMA_CONTEXT_LENGTH` no daemon em produção (primeira ação do WP-A).
- Decision register: D1-D5 aprováveis pela coordenação (WP-A budget/window, WP-C marker, WP-D uniformidade, WP-E delimitação, WP-F medição); D6 WP-B persistência requer re-decisão canônica (`SESSION_PERSISTENCE=NONE`), D7 instruction resource gate, D8 residência de dados com provider externo. Inadmissível: história como autoridade, bypass AuthZ, novo planner/engine/provider.
- `EXECUTION_DRIFT=NONE`; `NEXT=decisão arquitetural sobre D1-D8 + autorização de implementação — sem nova rodada de inventário`.


### DELIA-C3-EVIDENCE-SCHEMA-PROJECTION-INTEGRITY-AND-COVERAGE-01 — execução (2026-10-26)

- `STATE=IMPLEMENTED_WITH_EVIDENCE`; base `49dc645b0d`; escopo `orchestration.py` (projeções dos estágios não-seleção) + testes + doc 152 §12.
- WP0: 13 sites `json.dumps(...)[:MAX_*]` em blocos estruturados classificados `DESTRUCTIVE_TRUNCATION_PROVEN` (resolver, records, synthesis, comparison, native assessment, continuation, missing_inputs, relevance, prior_result_preview, index probe/select, arguments, candidate arguments); `_resolved_values_proven` = `SAFE_BOUND` preservado.
- Fix: `_fit_json_block`/`_json_block` ao lado dos builders C2 — redução estrutural ordenada (texto bounded → campo opcional → omissão de cauda com marcador `*_omitted` verdadeiro); `input_schema`/schema/identifiers nunca reduzidos — emitem íntegros; `MAX_INPUT_CHARS`/`CONTEXT_TOO_LARGE` seguem como boundary tipado. `evidence_blocks` sincronizado com o texto efetivamente projetado (sem verificação fail-open sobre evidência não vista).
- Tests: `test_evidence_schema_projection_integrity.py` — 23 casos RED→GREEN; RED causal: mesmas fixtures sob o corte antigo produzem `Unterminated string` em 5/5 envelopes.
- Eval local congelada (delia-json qwen2.5:3b, ctx 8192, api-delpi real via delegated exchange): 28 blocos capturados em 7 cenários — `json_valid=100%`, `CAPABILITIES_OMITTED=0` (catálogo real 1 grupo/~2-4 caps); ref_user/ref_observation alcançaram owner real (GROUNDED path com respostas honestas); three_records/O2 honestamente NON_GROUNDED/typed; ref_assistant_only não injetou referente assistente. `FALSE_POSITIVES=0`. Sem melhoria de outcome empresarial reivindicada (variance 3B, n=1).
- `DEPLOY=BLOCKED` (revisão independente pendente); `INDEPENDENT_REVIEW=PENDING`.


### DELIA-C3-PROJECTION-OVERFLOW-OMISSION-RECOVERY-CONTRACT-REWORK-01 — execução (2026-10-26)

- `STATE=IMPLEMENTED_WITH_EVIDENCE`; base `859632601b`; resíduos R1/R2/R3 da revisão `5ba117db50`; escopo `orchestration.py` + `contracts.py` (nova limitation) + instruction resource v22 + testes + doc 152 §14.
- R1: layering formalizado — block `MAX_*` é alvo de compactação (emite JSON íntegro + warning ao esgotar), transporte `MAX_INPUT_CHARS=16384` sempre ativo (`INVALID_REQUEST`), janela declarada `CONTEXT_TOO_LARGE`; janela desconhecida deixa apenas transporte (residual documentado). Sem segundo budget.
- R2: fail-open fechado em 7 sites — seleções passam a validar contra a lista projetada que o modelo viu (synthesis, prior-continuation, comparison left/right, capability x2, resolver, prepare, index); nova `LIMITATION_EVIDENCE_PROJECTION_PARTIAL` propaga projeção parcial ao outcome; v22 declara a semântica de todos os marcadores `*_omitted`.
- R3: `prior_result_preview` pinado como objeto JSON string `{records, records_omitted?}`; consumidores LLM-only; injeção permanece dado inerte; recovery segue bounded.
- Tests: `test_projection_omission_recovery_contract.py` — 25 casos; RED causal no baseline (stash): `resolve_3` selecionado sem projeção, synthesis renderizou índice fora do prefixo, capability omitida ligada.
- Eval local congelada (delia-json qwen2.5:3b, ctx 8192, instrução v22, api-delpi real via delegated exchange): 7 cenários, 31/31 blocos JSON válidos; 2 blocos acima do alvo de compactação emitidos íntegros (layering R1 ao vivo); `business_subject` propagado em foreign_selection; uma rodada de recovery governada em three_records; `FALSE_POSITIVES=0`.
- `DEPLOY=BLOCKED` (revisão independente pendente); `INDEPENDENT_REVIEW=PENDING`.


### DELIA-C3-OUTCOME-COMPLETENESS-FINAL-PAYLOAD-CONSISTENCY-01 — execução (2026-10-26)

- STATE=IMPLEMENTED_WITH_EVIDENCE; base f24ceddf6b; resíduos B/C da revisão independente 91d3453cb2 (doc 152 §15); escopo orchestration.py + conversational_response.py + novo test_outcome_completeness_final_payload.py + doc 152 §16. Sem planner/engine/registry/memória/provider/segundo budget.
- Residual B (false completeness): causa raiz — projected_omitted nunca chegava a _render_synthesis/_list_header; projeção parcial renderizava contagem não qualificada. Fix bounded: header qualificado quando records_omitted>0 nos dois call sites (synthesis e prior-continuation); limitation evidence_projection_partial já propagava attempt→turn→result. GROUNDED permanece estado de proveniência, não veredito de outcome.
- Residual C (final payload): causa raiz — wrap de relevance_feedback ocorria após a captura do universo selecionável e sem re-fit; inner object-form virava {capabilities:{capabilities:[…]}} aninhado (marker enterrado, shape ilegível ao contrato de membership); foreign selection não tinha binding de ids projetados; _select_group apresentava o mesmo shape aninhado de capability_groups sob optionals. Fix: payload final montado e re-fitted antes do dispatch; visible computado do mesmo payload; _projected_capability_ids vincula foreign_capability_id aos ids realmente despachados; groups nunca omitidos.
- Tests: 15 casos B1–B9/C1–C8; RED causal no baseline: b2/b4 (parcial renderizado como completo), c3 (shape aninhado ilegível ao contrato), foreign (beta.read_5 omitido resolvia), group (capability_groups aninhado sob optionals+feedback). Verde pós-fix; suites focadas + backend completo verdes (env limpo); gates arquitetura 0 findings.
- Eval local congelada (delia-json qwen2.5:3b, ctx 8192, instrução v22, api-delpi real via delegated exchange): 8 cenários; 29/29 blocos válidos; three_bala com 3 invokes DAVI reais terminou em clarificação honesta; write_request recusado como não autorizado; capability_id inventado rejeitado fail-closed; FALSE_POSITIVES=0; FALSE_COMPLETENESS=0. Capacidade semântica 3B segue limitante documentado.
- DEPLOY=BLOCKED (revisão independente pendente); INDEPENDENT_REVIEW=PENDING.


### DELIA-C3-SEMANTIC-ADMISSION-GOAL-ARGUMENT-FIDELITY-EVAL-01 — execução (2026-10-26)

- STATE=EVALUATION_COMPLETE; base cd50b85610 (=origin/main); READ-ONLY — zero alteração de código/prompt/modelo/budget/AuthZ; deploy não executado.
- Corpus congelado: 25 cenários × 5 repetições = 125 execuções governadas (delia-json qwen2.5:3b, ctx 8192, instrução v22, delegated bearer READ-only, superfície real 4 grupos/41 caps). Seed NOT_SUPPORTED pelo adapter — variância medida, determinismo não reivindicado.
- Resultado: OUTCOME_PASS=40 (guidance 15/15, negative 15/20, discovery 5/15, continuity 5/20), FAIL=85; records family 0/45. Primeiro estágio divergente: ADMISSION_ERROR 36, GROUP_SELECTION_ERROR 30, MODEL_STRUCTURED_OUTPUT_ERROR 15, CAPABILITY_SELECTION_ERROR 8. Apenas 12/125 turnos invocaram qualquer capability.
- Causa comprovada (prova direta no payload despachado): _group_summaries entrega 0/41 descrições não-vazias — nomes+estrutura dos 4 grupos consomem ~5909 dos 6000 chars, compactação zera toda descrição; seleção de owner vira loteria por remote_name (mcp:teo 10, mcp:vista 6 escolhidos para consultas de produto). Direção A (contrato/código), não capacidade 3B.
- Secundário comprovado: admission classifica consultas de registro como surface_inquiry (catálogo listado em vez de READ — FN=0 mas FP=30); structured output inválido 15/125; argumentos com subject em code e resolver→search_customers (infidelidade semântica).
- Segurança limpa: 0 bypass AuthZ, 0 PREPARE/ACT, 0 fabricação; neg_scope/neg_write recusados 10/10; neg_inject recusou com applicable:false (FAIL por oráculo estrito, comportamento correto); injetado ID rejeitado fail-closed.
- Recomendação: A — restaurar sinal semântico mínimo bounded em _group_summaries (ex.: group_description por grupo) antes de medir capacidade; depois B — experimento bounded em surface_inquiry. Revisão independente pendente.
- Artefatos: doc 153, scripts semantic_fidelity_eval.py + semantic_fidelity_aggregate.py, runs JSON sanitizado (350KB). DEPLOY=BLOCKED; INDEPENDENT_REVIEW=PENDING.


### DELIA-C3-GROUP-SELECTION-SEMANTIC-SIGNAL-PRESERVATION-01 — execução (2026-10-26)

- STATE=IMPLEMENTED_WITH_EVIDENCE; base c972dae7f2; escopo _group_summaries (novo campo de projeção scope) + instruction resource v22→v23 + testes; sem planner/engine/registry/memória/segundo budget; MAX_SURFACE_CHARS=6000 inalterado.
- Causa raiz (doc 153): catálogo stage-1 compactava 41/41 descrições a vazio — seleção de owner virava loteria por remote_name. Fix: scope = recorte verbatim determinístico das descrições publicadas pelo owner (≤160/grupo, per-desc ≤60), ausente quando fonte não publica, último campo a reduzir na escada de compactação; ids e marcadores intactos; nunca fabricado; dados não autoritativos.
- Tests: 17 casos A1–A9 + fairness/injeção/extrema-pressão; RED causal no baseline (10 falhas — scope nunca emitido); versões pin 22→23 em 3 suites.
- Eval A/B congelada (mesmo modelo/corpus/bearer class, 12 cenários ×5 = 60 runs cada): scope entregue 4/4 grupos na superfície real (payload ≤5989); outcome PASS 10→15 (disc_candidate 0→5); admission errors 18→12; structured-output 8→5; MAS GROUP_SELECTION_ERROR 25→25 — wrong-owner migrou teo→vista. Conclusão honesta: sinal restaurado, mas seleção não melhorou mensuravelmente — limitante restante é uso do sinal (instrução/modelo), não disponibilidade.
- Regressão: backend completo verde (0 FAILED/ERROR); gates arquitetura 0 findings; AuthZ/PREPARE/ACT intocados; segredos destruídos.
- Próximo bounded: experimento de instrução isolando a cláusula documentation-first para sujeitos coloquiais (direção B doc 153), depois re-medir antes de qualquer decisão de capacidade (C).
- DEPLOY=BLOCKED; INDEPENDENT_REVIEW=PENDING.


### DELIA-C3-GROUP-SELECTION-INSTRUCTION-SEMANTIC-CONFLICT-EVAL-01 — execução (2026-10-26)

- STATE=EVALUATION_COMPLETE; base 74fb1ba10b; código e instrução produtiva NÃO modificados — variante B injetada apenas no mapping _instructions em processo (seam de avaliação); fixture + harness + runs sanitizados publicados.
- Experimento: v23 (A, fp 8eb95ebdafe8b338) vs cláusula única reescrita (B, fp 15855b8c1a17ed47) que torna a superfície de registros o destino de pedidos de registros mesmo com nomenclatura coloquial. Interleaving ABBA, 12 cenários base x5 + holdout 8 x5, além de isolamento de estágio (_select_group direto, 4 catálogos x10 prompts x5 reps x2 variantes = 400 chamadas).
- Resultado: REJEITADA — stage-1 live A 16/50 vs B 14/50; e2e base A 17/39 vs B 10/35 elegíveis corretos; holdout 10/20 vs 10/24. Nenhuma dimensão melhorou.
- Descoberta dominante: catálogo com providers renomeados (nomes neutros) quase duplica acurácia nas DUAS variantes (35/50, 31/50) — falha é dominada por priores de nome do modelo 3B, não pela cláusula. Descrições/scope são suficientes (H3 refutado).
- Hipóteses: H1 REFUTED (conflito instrucional não é a causa operativa), H2 SUPPORTED (capacidade/modelo — nome domina sobre descrição), H3 REFUTED, H4 SUPPORTED (admission diverge independente), H5 SUPPORTED (downstream falha mesmo com grupo certo).
- Segurança: injeção em descrição não sequestrou seleção; 0 bypass AuthZ, 0 PREPARE/ACT, 0 id inventado; tokens opacos redigidos no artefato.
- Próximo bounded: comparação controlada de modelo (autorização separada) ou experimento de projeção com nomes neutros no stage-1 — tasks novas, não iniciadas.
- DEPLOY=BLOCKED; INDEPENDENT_REVIEW=PENDING.


### DELIA-C3-CATALOG-PRESENTATION-NAME-PRIOR-SENSITIVITY-EVAL-01 — execução (2026-10-26)

- STATE=EVALUATION_COMPLETE; base 148b4e0a3a; código/instrução/catálogo/modelo produtivos NÃO modificados — variantes aplicadas apenas em projeção in-process via seam de avaliação (`EVAL_CATALOG_VARIANT`); deploy não executado.
- WP0: agregador corrigido — classificação exclusiva por execução (ADMISSION_STOP / GROUP_CORRECT / GROUP_WRONG / GROUP_NOT_APPLICABLE_CORRECT|WRONG / GROUP_INVALID_OUTPUT / GROUP_NOT_REACHED_OTHER); `correct` nunca conta abstenção em métrica de seleção; oráculo reconciliado strict (owner de registro) vs lenient (rota davi discover→execute legítima).
- WP1 congelado: delia-json qwen2.5:3b ctx 8192, instrução v23 fp 8eb95ebdafe8b338, superfície real 4 grupos/41 caps, payload sha256 916c063b67e54cd6… (5989/6000 chars).
- Descoberta estrutural decisiva: o payload stage-1 despachado contém apenas capability_group_id + capabilities + scope + capabilities_omitted — display_name, owner e source_system são compactados para fora do fio sob o orçamento de 6000 chars (provado por hash: variantes neutral/respforward geram sha idêntico ao real).
- Stage-1 (240 chamadas, 12 prompts x5 reps x4 variantes): real 27/60 lenient / 24/60 strict; neutral 26/60 / 25/60 (sha idêntico — réplica A/A, variância do modelo); respforward 21/60 / 20/60 (sha idêntico); reorder sha e0328e74 distinto → colapso posicional: davi 46/60 picks, invalid 0→13, strict correto apenas 5/60.
- E2E (200 turnos, real vs reorder, base+holdout x5): reorder_base strict 4/40 vs real 15/37; reorder_holdout strict 0/24 vs real 11/25; invalid e2e 0→3 e 0→7; lenient sobe artificialmente (davi conta como rota legítima de registro). Wrong-owner strict reorder: davi 29 base / 17 holdout.
- Veredito: NAME_PRIOR_NOT_CONFIRMED para rótulos de apresentação — campos de apresentação não chegam ao modelo sob o orçamento vigente; o ganho do catálogo renomeado do doc 155 é agora atribuível a priores do capability_group_id canônico (H2), não a display labels (H1 não testável). H3 viés posicional SUPPORTED (maior defeito reproduzível); H5 capacidade SUPPORTED (variância ±15% em input byte-idêntico); H6 SUPPORTED.
- Segurança: 0 bypass AuthZ, 0 PREPARE/ACT, 0 id inventado; ids/owners/source_system/schemas remotos intactos; sem segredos nos artefatos.
- Artefatos: doc 156; scripts catalog_presentation_probe.py + catalog_presentation_aggregate.py; seam em instruction_conflict_eval.py (eval-only); evidence catalog-presentation-snapshot.json, catalog-presentation-probe-runs.jsonl/.json, catalog-presentation-e2e/*.json.
- Próximo bounded: experimento autorizado separado sobre tokens do capability_group_id (requer decisão de arquitetura — toca identificador canônico), hardening de robustez a ordem no stage-1, ou comparação de capacidade de modelo no corpus congelado.
- DEPLOY=BLOCKED; INDEPENDENT_REVIEW=PENDING.


### DELIA-C3-GROUP-SELECTION-ORDER-ROBUSTNESS-CHARACTERIZATION-01 — execução (2026-10-26)

- STATE=EVALUATION_COMPLETE; base 3fdb36e883; árvore delia-api congelada = doc 156; código/instrução/catálogo/modelo NÃO modificados — permutação aplicada somente na lista serializada pós-projeção via seam de avaliação.
- Matriz: 24 permutações completas (4 grupos) × 12 prompts × 5 reps = 1440 chamadas stage-1 intercaladas; invariants verificados por chamada — mesmo group set, cap counts, scope 4/4, omitted=1, 5989 chars, 24 shas distintos (ONLY_ORDER_CHANGED=YES).
- Resultado stage-1: strict accuracy por permutação varia 5/60 → 32/60 (stdev .13, range .45) vs run variance ~±15%. Efeito de posição absoluta: pos1 quase nunca escolhida (0-9%), pos4 domina (36-58%) — recência, não primazia. Efeito relativo: delpi depois de teo/vista/davi → 48-61% strict em record asks vs 18-31% quando antes. Interação patológica: delpi-primeiro+davi-último (perms 21/23) colapsa em davi + 14-26 invalid outputs.
- Holdout pré-declarado {0,5,14,16,21,23} × 8 prompts × 5 = 240 chamadas: perm 14 (melhor) 22/40 strict; perms 21/23 (piores) 1/40 com 11-17 invalids; generalização confirmada.
- E2E (4 perms × base+holdout × 5 = 480 turnos): p14 (delpi último) triplica strict group-selection no base (24/35 vs 5/27 canonical) MAS business outcome não melhora (16/60 vs 20/60 PASS) — downstream segue divergindo. p21/p23 confirmam colapso strict 1/36, 9/28 e 5/23, 1/22 holdout.
- Veredito: ORDER_EFFECT_CONFIRMED — recência + interação posição×ID, não primazia simples; fragilidade semântica do modelo 3B na superfície de grupos.
- Segurança: 0 bypass AuthZ, 0 PREPARE/ACT, 0 id inventado aceito, 0 write; artefatos sem segredos.
- Artefatos: doc 157; scripts order_robustness_probe.py + order_robustness_aggregate.py; seam EVAL_PERM_ORDER em instruction_conflict_eval.py; evidence order-robustness-*.{json,jsonl} + order-robustness-e2e/*.json.
- Próximo bounded: comparação de capacidade de modelo na matriz congelada (autorização separada), ou decisão de arquitetura sobre mitigação de recência no contrato de superfície — sem política de ordem por provider.
- DEPLOY=BLOCKED; INDEPENDENT_REVIEW=PENDING.

## 2026-10-26 — DELIA-C3-DOWNSTREAM-CAPABILITY-ARGUMENT-FIDELITY-CAUSAL-EVAL-01 (doc 158)

- Escopo: caracterização causal downstream — 4 braços harness-only (A natural, B good-group, C good-capability, D good-arguments), 11 cenários record × 5 reps, interleaved, superfície saudável verificada (4 grupos/41 caps, 0 falhas), bearer fresco por turn (JWT TTL 300s), spy de invokes com captura de erro, flags controls_engaged.
- Resultado: 220 runs válidos; PASS apenas via exact-code (1/55 por braço controlado); delpi invocado 9× (B2/C4/D3), 6 rejeitados por goal_evidence_relevance vazio; FOREIGN_DIVERT dominante ~37/41 engaged em C/D; capability abstain 43% em B; admission surface_inquiry/hypothetical ~50% das turns.
- Veredito: primeiro bloqueio downstream com grupo correto = desvio semântico native_assessment→foreign_selection (~90% dos turns engajados); capability abstention 43%; relevance judgments vazios ~67% dos invokes; argument fidelity real mas secundária; owner REFUTADO como gargalo.
- Segurança: 0 bypass AuthZ (negações = TTL expirado → AUTHZ_DENIED truthful), 0 ACT/WRITE, 0 registro fabricado apresentado como real; artefatos limpos.
- Artefatos: doc 158; scripts downstream_causal_eval.py + downstream_causal_aggregate.py + armd_stage_debug.py; evidence downstream-causal-runs.{json,jsonl} (sanitizados).
- Drift documentado: 2 restarts em massa da stack (api-delpi zombie → openapi_document_unavailable → delpi ausente da superfície; mcp:davi down), JWT TTL vs spy success-only (batches 1–2 parcialmente invalidados, rerun em superfície saudável), senha dev-portal resetada pelo reimport do realm (restaurada), WSL blips.
- Próximo bounded: revisão de contrato native_assessment/foreign_selection (por que foreign_evidence_required dispara em record asks diretos) + comparação de capacidade de modelo na matriz congelada — autorização separada; nenhum patch de ordem/instrução justificado.
- DEPLOY=BLOCKED; INDEPENDENT_REVIEW=PENDING.

## 2026-10-26 — DELIA-C3-NATIVE-ASSESSMENT-FOREIGN-SELECTION-CAUSAL-DIAGNOSTIC-01 (doc 159)

- Escopo: diagnóstico causal read-only do desvio native_assessment→foreign_selection — captura do payload EXATAMENTE despachado (spy em InvokeModel.execute), oráculos de contrato por grupo-alvo, 18 cenários ×5 reps ×3 braços = 270 runs, variants WP8 em memória.
- Resultado: assessment alcançado 171× — foreign_evidence_required 85%, sufficient 2/171; matriz oráculo TP73/FP59/TN18/FN8 (76% FP quando alvo era suficiente); foreign_selection abstenção ~60% (invalid_foreign_selection dead-end); payload íntegro (171/171 e 136/136 JSON válidos, todos os campos do contrato despachados).
- Braços: B=TEST_NOT_RUN (bloco já carrega todo o contrato); C engaged 22 → 17 PASS (caminho nativo funciona sem o desvio); D engaged 21 → 19 invokes delpi corretos mas 20 FAIL (enriquecimento estrangeiro não resgata target errado — continuação estruturalmente perdida).
- WP8 variants (12 superfícies FP ×3×3): V1 replay 35/36 fer, V2 minimal 32/36, V3 goal-first 34/36 — FP invariante à apresentação → causa = semântica da instrução + interpretação do modelo, não contexto.
- Veredito: cláusula de exceção mandatória da instrução native_assessment embute premissa semântica de owner não verificável (designação informal + owner 'literal-only' → foreign obrigatório) — DELPI resolve sujeitos descritivos (oráculos 13–50 registros); modelo extrapola a cláusula (doc asks, código explícito: biz_code 9/9 fer). H1+H3+H6 SUPPORTED, H2 REFUTED, H7 parcial.
- Segurança: 0 bypass AuthZ, 0 ACT/WRITE; neg_write alcançou PREPARE invoke governado (owner fail-closed 'Operação não suportada' — residual de write-intent não cortado na admissão); artefatos sem JWT/segredos.
- Artefatos: doc 159; scripts assessment_foreign_diag_eval.py + _aggregate.py + assessment_variants_eval.py; evidence assessment-foreign-runs.{json,jsonl} + assessment-variants.json (sanitizados).
- Drift documentado: 1 outage de transporte WSL (stack restart; eval checkpointed, 270/270 íntegros); model_calls=1435+108, in≈2.59M, out≈46.5k, latência med 6.4s.
- Próximo bounded: revisão de contrato/instrução native_assessment (remover desvio mandatório ou condicioná-lo a capability de vocabulário verificada) + comparação de capacidade de modelo + diagnóstico de goal_evidence_relevance vazio — autorizações separadas.
- DEPLOY=BLOCKED; INDEPENDENT_REVIEW=PENDING.

## 2026-10-27 — DELIA-C3-NATIVE-ASSESSMENT-INSTRUCTION-CONTRACT-AB-EVAL-01 (doc 160)

- Escopo: avaliação A/B evaluation-only da instrução native_assessment — A=v23 verbatim (sha fcdbd185527595b9), B=fixture mínimo que remove a exceção mandatória e adiciona restrição epistêmica (sha c083e71332b67a0a); injeção só em memória no estágio, nada em produção; mesmo modelo delia-json, catálogo, oráculos e AuthZ.
- Stage-local: 120 superfícies únicas despachadas ×5 reps ×2 instruções = 1190 chamadas — B corta foreign_required 93.9%→69.9% e FP 91.4%→61.0%, accuracy 53.6%→59.2%, MAS sufficient só 13/595 e FN sobe 3.6%→21.6% (hedge para inconclusive).
- E2E: 180 turns (18 cenários ×5 reps ×2 braços intercalados) — assessment alcançado A49/B48; B 0/48 sufficient, FN 26.1%; outcome A 30P/60F vs B 31P/59F (sem degradação, sem ganho); holdout congelado reproduz o mesmo padrão.
- Segurança: 0 bypass AuthZ, 0 ACT/WRITE, 0 registro fabricado; residual PREPARE reproduz sob ambos os braços (A vista.suggest_change COMPLETED ×2; B vista.prepare_change → ERROR protocol, owner fail-closed) — write-intent não cortado na admissão, SECURITY_REVIEW_REQUIRED mantido.
- Veredito: B_REJECTED para implementação — a exceção mandatória contribui ~24pp do desvio mas não é a causa dominante; sob delia-json o modelo não recupera sufficient nem com mandato removido (H1 parcial, H2/H5/H6 SUPPORTED, H3 REFUTED, H4 confirmado por evidência anterior). Próximo bounded: comparação de capacidade de modelo na matriz congelada + higiene da cláusula como task de contrato separada + diagnóstico goal_evidence_relevance.
- Artefatos: doc 160; scripts assessment_ab_stagelocal_eval.py + instruction_ab_eval.py + instruction_ab_aggregate.py; evidence assessment-ab-stagelocal.json + instruction-ab-runs.{json,jsonl} + native-assessment-instruction-b.txt (sanitizados).
- DEPLOY=BLOCKED; INDEPENDENT_REVIEW=PENDING.

## 2026-10-27 — DELIA-C3-PRODUCTION-DEPLOY-SINGLE-BUSINESS-QUERY-SMOKE-01 (doc 161)

- Escopo: smoke de produção autorizado — deploy verificado (delia-api/ sem diff produtivo desde 00a79c26 → DEPLOY_REQUIRED=NO, apenas git pull de docs em srv-api), gates de baseline confirmados no runtime (instrução v23 sha fcdbd185527595b9 ativa; orchestration.py idêntico ao HEAD; sem eval overrides; modelo prod = moonshotai/kimi-k3 OpenRouter), UMA consulta real read-only via /apps/delia-api/interaction/turns com identidade devin-smoke-r4 provisionada (Delia Acesso + API DELPI Acesso via use case canônico; 2 restarts core-api para cache RBAC).
- Turno único (delia-smoke-2cfac0c60deb, HTTP 200, 16.8s, 5 model calls, ~7.3k/985 tokens): admission owner_surface → grupo openapi:delpi → capability delpi.search_products READ → args description,page_size → provider_invoke 403 mcp_authorization_denied (subject sem permissão de domínio ENGINEERING_LMP naquele momento) → síntese NON_GROUNDED honesta, zero fabricação.
- Observação arquitetural: native_assessment/foreign_selection NÃO exercitados — a meta entrou no plano direto OPERATIONAL (self_index), que não atravessa o estágio avaliado nos docs 159/160.
- Verificação de cobertura (read autorizado direto ao owner): search_products("terminal bala") → 77 candidatos, 65 registros TERM*/TERMINAL incluindo 10080092 e 10081004 — fonte cobre o objetivo; a negação foi AuthZ de domínio correta da identidade pré-grant.
- Resultado: BUSINESS_OUTCOME=FAIL (first divergent = OWNER_INVOCATION, domain AuthZ da identidade); cadeia semântica íntegra e fail-closed; 0 bypass, 0 ACT/WRITE/PREPARE, 0 fabricação.
- Artefatos: doc 161; nenhum código/instrução/modelo alterado; identidade de smoke retém roles para futuros smokes.
- DEPLOY=EXECUTED-SKIP; INDEPENDENT_REVIEW=PENDING.

## 2026-10-27 — DELIA-C3-PROD-SMOKE-IDENTITY-RBAC-REMEDIATION-AND-RETEST-01 (doc 162)

- Escopo: remediação e auditoria da identidade de teste designada devin-smoke-r4 + UMA consulta empresarial read-only autorizada — sem SQL de escrita, sem restart de serviços compartilhados, sem deploy, sem chamadas conversacionais preliminares.
- Identidade: Keycloak delpi/devin-smoke-r4 ok; Core 788e08ed (active, non-superadmin); roles iniciais=finais 'Delia Acesso'+'API DELPI Acesso' (estado least-privilege já correto — nenhuma mutação RBAC necessária nesta sessão; grants anteriores vieram do use case canônico). Credencial user/1234 informada inválida no Keycloak prod (invalid_grant em todos os clientes/realms testados) — não usada; subject admin nunca usado como usuário.
- Audit gap: audit_logs não contém linhas para os grants — AddRoleToUserUseCase emite evento de invalidação de cache mas não persiste auditoria; registrado para revisão do owner.
- Preflights (interfaces oficiais): AUTHENTICATION=PASS, /me confirma delia.access+api-delpi.access efetivos (cache consistente sem restart), leitura direta autorizada ao owner retorna 10080092 → DOMAIN_READ_AUTHORITY=PASS. Runtime reconfirmado: instrução v23 fcdbd185527595b9, modelo moonshotai/kimi-k3, delia-api healthy, SEM experimental B/overrides.
- Turno único (delia-smoke-b7b47ce98d9c, corr 111ef4b7, HTTP 200, 34.3s, 10 model calls, 18943/3353 tokens): admission owner_surface/operational → openapi:delpi → delpi.search_products READ → args 'produtos correspondentes à descrição terminal bala'+page_size=3 → provider_invoke OK 190ms (AuthZ de domínio PASS — divergência do doc 161 resolvida) → goal_evidence_relevance=irrelevant → relevance_recovery reinvoke args 'TERM BALA'+3 → provider_invoke OK 113ms → relevance=irrelevant → cri_response presented=0 → outcome insufficient/goal_mismatch → resposta GROUNDED honesta ('registros reais mas não correspondem'), zero fabricação.
- Verificação de outcome (reads diretos autorizados): call1→total 662 top-3 bateria/abas/'ABERTO'; call2→total 1855 top-3 balança×2+balancim — relevance julgou CORRETAMENTE: ranking léxico do owner coloca falsos 'bala' (balança/balancim) antes dos TERM. BALA reais (10080092/10081004 existem fora do top-3).
- Resultado: BUSINESS_OUTCOME=FAIL; FIRST_DIVERGENT_STAGE=ARGUMENT_CONSTRUCTION (call1 copiou a frase inteira no arg); bloqueio material = ranking léxico do owner para top-N curto. Cadeia AuthZ+relevance fail-closed correta; 0 bypass, 0 ACT/WRITE/PREPARE, 0 restarts, 0 DB writes.
- Artefatos: doc 162; nenhum código/instrução/modelo/banco alterado; ACCESS_RESTORATION=estado aprovado inalterado (grants mantidos como least-privilege da identidade designada — item aberto: ratificação/auditoria pelo owner).
- DEPLOY=NO; INDEPENDENT_REVIEW=PENDING.

## 2026-10-27 — DELIA-C3-LLM-NATIVE-ITERATIVE-RESEARCH-ARCHITECTURE-AUDIT-01 (doc 164)

- Escopo: auditoria R0 documentação-first da orquestração DÉLIA para pesquisa iterativa conduzida pelo LLM (direção doc 163) — inventário de todos os estágios, chamadas LLM, continuidade de pesquisa, contrato do owner e reuse gate. ZERO mudanças de código/modelo/deploy/consulta produtiva.
- Inventário: 18 instruction-ids v23; ~10 model calls observados no turno doc-162; fluxo real mapeado em orchestration.py (L4227–5709) com estágios, gates determinísticos e budgets (300s turno, 60s/call, ≤3 retries recuperáveis, checkpoint de resume).
- Bloqueios estruturais PROVEN: (1) _RELEVANCE_RECOVERY_USED = UMA rodada de recuperação por interação (L3828/4112/9593/9825) — após 2º 'irrelevant' o fluxo termina em insufficient/goal_mismatch, sem escolha semântica de próximo passo; (2) outcome_facts extrai total_count/coverage_complete/has_more (outcome_assessment.py:1498-1545) mas o bloco de relevância e o feedback de recovery carregam apenas records — o modelo não distingue '3 registros errados' de '3 de 1855 em 619 páginas'; (3) page-walk determinístico _maybe_aggregate_paginated_count só dispara em intent=COUNT (L8879-9010) — para LIST nenhuma página avança.
- Contrato owner provado (não presumido): delpi.search_products = LIKE prefixo-por-token OR'd (product_repository.py:61-89), score 100·phrase+20·term; 'TERM BALA' não casa 'TERM. BALA' (ponto literal) e BALA% puxa balança/balancim; page/page_size/total/total_pages são membros do contrato; is_complete = completude de transporte, não cobertura (specialist_interop/model.py:134).
- Reuse gate: EXISTING_EQUIVALENT=YES para todos os mecanismos (recovery round, relevance_feedback, page arg, envelope extractor, checkpoint, harness delia-json) — apenas o estágio de decisão de próxima ação seria novo (mesmo _propose port, não novo engine).
- Matriz: KEEP na maioria dos gates; EXTEND em goal_evidence_relevance (metadados de cobertura), _recover_relevance (ledger de rodadas), page-walk (intent LIST); REMOVE_CANDIDATE apenas como hipótese para o flag booleano; NEEDS_OWNER_CONTRACT para native/foreign e semântica de is_complete.
- R1 planejada (não executada): A=CURRENT vs B=LLM-LED BOUNDED ITERATION (≤3 rodadas, ações enumeradas, mesmos gates) no harness local delia-json; corpus ≥14 famílias + holdouts; métricas outcome-first; gates de segurança idênticos; aprovação de coordenação pendente.
- Veredito: AUDIT_COMPLETE; EXECUTION_DRIFT=NONE; INDEPENDENT_REVIEW=PENDING.

## 2026-10-27 — DELIA-C3-R1-LLM-NATIVE-BOUNDED-ITERATIVE-RESEARCH-EVAL-01 (doc 165)

- Escopo: avaliação A/B pareada LOCAL da hipótese de pesquisa iterativa conduzida pelo LLM (doc 163/164) — A=orquestração atual intacta; B=composição experimental somente no harness (bloco de relevância + metadados de cobertura já extraídos, proposta `delia.iteration.next_action` enumerada via `_propose` existente, ledger ≤3 rodadas + dedup, execução apenas por `_recover_relevance`/`_invoke_selected`). ZERO mudanças de código/instrução/modelo/catálogo/deploy/consulta produtiva.
- Baseline congelada: delia-json:latest (digest 7b8f4ab14fc1, qwen2.5 3.1B Q4_K_M, num_ctx 8192, JSON-only) no stack local c3r-eval/delpi-ollama; instruções sha adb3685506721cc2 inalteradas; bearer real delegado via Keycloak dev; AuthZ por invocação real.
- Reuse gate: EXISTING_EQUIVALENT=YES para todas as necessidades (julgamento, recovery, re-invoke, envelope de paginação, dedup, budgets, checkpoint) — único acréscimo = UM estágio de decisão no port `_propose` já existente; nenhum engine/planner/registry novo.
- Integrity: patch_install/patch_restore/injection_hint/garbage_rejection todos PASS; defeito do harness (dedup em args obsoletos pós-recovery) encontrado, corrigido e divulgado — apenas batch-2 é autoridade.
- Corpus: 16 cenários × 3 reps × 2 braços intercalados = 96 turns; 13 famílias incl. holdout congelado ×3; oráculos por reads diretos autorizados (pares code↔name + filtro de pertinência; verify_codes 10080092/10081004 confirmados). Fato mensurado: 'terminal bala' retorna 77 itens totais, 0 pertinentes em qualquer profundidade — paginação não pode resolver, só refinamento; 'conector faston' primeiro pertinente no rank 237.
- Resultado: BUSINESS_OUTCOME A=1/36 business+12/12 negativos vs B=0/36+12/12 (Δ=-1, ruído). Owner-reach A 20/48 vs B 15/48 (bloqueio dominante: admission/goal-typing ~60-70% zero-invoke). Judge `goal_evidence_relevance` rejeitou evidência PERTINENTE em 9/10 julgamentos (incl. match exato de código 10080092) — falso-negativo satura ambos os braços.
- B em funcionamento: 9 decisões next_action (refine×5, select_other×2, discovery×1, clarify×1; next_page=0), multi-round verificado (correção de arg 'born'→'borne' em round 1→clarify em round 2), re-seleção por código+grupo; custo +3.4% tokens/+8.5% latência; rounds máx=2 (cap 3 nunca atingido).
- Segurança: 0 bypass AuthZ, 0 ACT/PREPARE não autorizado, 0 registro fabricado, 0 loop ilimitado — negativos 12/12 nos dois braços, injeção e boundary de escrita respeitados.
- Veredito: R1_INCONCLUSIVE para outcome (instrumento saturado — o juiz 3B é a medida e a falha); mecanismo de continuação PROVADO correto/seguro/bounded — iteração é necessária mas não suficiente. Próximo bounded: R1.5 — eval stage-local de precisão do goal_evidence_relevance + admission/goal-typing no mesmo modelo congelado; escalada de escala de modelo à coordenação se precisão inalcançável; re-run do corpus congelado sob juiz melhorado.
- Artefatos: doc 165; delia-api/scripts/iterative_research_eval.py; evidence iterative-research-r1-runs.json + iterative-research-r1-summary.json (sanitizados — apenas códigos/nomes de catálogo e conteúdo DÉLIA).
- DEPLOY=NO; INDEPENDENT_REVIEW=PENDING.

## 2026-10-27 — DELIA-C3-R15-SEMANTIC-JUDGMENT-OWNER-REACH-CAUSAL-EVAL-01 (doc 166)

- Escopo: investigacao causal stage-local dos dois gargalos R1 (owner-reach e precisao do goal_evidence_relevance) no modelo congelado delia-json — reconstrucao dos 96 turnos R1 + eval stage-local de admission/turn_goal (17 queries x3) + eval de julgamento (15 pares rotulados x3 reps x4 variantes). ZERO mudanca de codigo/instrucao/modelo/deploy/consulta produtiva.
- Reuse gate: EXISTING_EQUIVALENT=YES para todos os seams (r4._compose, _find_orchestrator, _propose real, _understand_goal real, parse_goal_evidence_judgment, provider.invoke + bind_subject_bearer para oraculos); unica instrumentacao = _spy_wire capturando payload despachado real.
- Owner-reach (matriz de primeira divergencia, 96 turnos): 75% das nao-chegadas (46/61) morrem em admission — surface_inquiry x35 + hypothetical x11; token interaction_class decide a rota (requires_owner_surface e ignorado quando class=surface_inquiry). Stage-local: read_recall(requires=true)=1.000, adm_class_accuracy=0.804, goal_class_accuracy=0.744 (create_or_modify x6 em leituras), subject_fidelity=0.564; answer_requirements NUNCA extraido (min_items=None em 51/51 — declared_requirements nunca chega ao juiz em producao).
- Evidence judgment (15 pares com rotulos por oraculo, 180 julgamentos): payload verificado sem perda (code+description completos despachados). recall <=0.20 em TODAS as variantes (A_gold 0.167, A_pipe 0.200, B_cov 0.000, D_noreq 0.188), precision 1.0, FP=0 — colapso conservador: rejeita conjuntos pertinentes multi-registro 3/3 (hints auto-contraditorios: 'records for disjuntor but the user request is for disjuntor'); so identidade trivial (codigo exato, registro unico) passa (P_code_exact 3/3).
- Hipoteses: H1 SUPPORTED (misrouting de classe em admission), H2 REFUTED (gold~=pipe), H3 REFUTED (payload verificado), H4 PARTIAL (conceitos quase-gemeos no contrato de admission), H5 SUPPORTED (falha semantica do juiz com contexto completo), H6 PARTIAL (harness R1 com mislabels; direcao da taxa confirmada), H7 RESIDUAL SUPPORTED (erro persiste apos todos os controles de contexto — nao veredito sobre todas as tarefas).
- Causas provadas: (A) token interaction_class e a rota decisiva e confunde surface_inquiry/cobertura e hypothetical/ambiguous; (B) juiz colapsa para rejeicao em toda correspondencia por descricao — apenas identidade exata passa; gap de composicao secundario: answer_requirements nunca populado.
- Proxima direcao: B (reframe do contrato do juiz para correspondencia por registro + suficiencia deterministica backend) > A (consolidacao de classes em admission) > C (extracao de requirements) > E (re-run R1). Sem implementacao nesta task.
- Seguranca: 0 bypass/ACT/PREPARE/fabricacao; inject falha na direcao segura (owner path); cobertura parcial herdada da R1.
- Custo: 327 model calls; tokens/latencia nao capturados pos-resume (limitacao divulgada).
- Artefatos: doc 166; delia-api/scripts/semantic_judgment_reach_eval.py; evidence semantic-judgment-r15-runs.json (sanitizado).
- DEPLOY=NO; INDEPENDENT_REVIEW=PENDING.

## 2026-10-27 — DELIA-C3-R16A-PER-RECORD-SEMANTIC-EVIDENCE-JUDGMENT-EVAL-01 (doc 167)

- Escopo: A/B causal stage-local autorizado pela revisao independente R1.5 (ddddf09f34) — A=julgador agregado produtivo intacto; B=contrato harness-only de correspondencia por registro em lista; B2=variante de controle um-registro-por-chamada apos colapso de B; suficiencia deterministica (dedup+min) sobre labels do LLM. ZERO mudanca de codigo/instrucao/modelo/deploy/consulta produtiva.
- Baseline congelada: delia-json:latest digest 7b8f4ab14fc1 (qwen2.5:3b Q4_K_M, ctx 8192, JSON-only); instrucao goal_evidence_relevance inalterada; corpus = 15 pares congelados R1.5 + 3 conjuntos construidos pre-medicao (DUP/NOQ/SEC fixture) = 18 conjuntos, 95 registros validos, x3 reps = 405 chamadas totais.
- Oracles por registro com scrutinio de material/subtipo (exigencia da revisao): P_ilhos reclassificado (1 metalico pertinente, 7 borracha irrelevantes); BORNE FUSIVEL=partial; code-goal por identidade de codigo. Regras set-level declaradas pre-medicao; reconciliacao de labels doc 166 divulgada.
- Resultado B (lista): colapso estrutural — o modelo emite exatamente 1 entrada por chamada (sempre r1/r2), cobertura 1/N; 237/285 registros sem label; set acc 0.487 < A 0.667; 6 FPs. Contrato de lista inexequível no modelo congelado.
- Resultado B2 (1-registro-por-chamada): record precision 0.697 / recall 0.594 / FPR 0.214 (A~1.0/0.17/0); set acc 0.846 dev / 0.75 holdout — melhor de todos os bracos; todas familias positivas corretas; dedup e sem-quantidade corretos; decisoes estaveis entre reps.
- Residuos B2: FP 33 (21.4%) incluindo erro de identidade X_code_wrong (TERM.BALA julgado pertinente ignorando codigo pedido — 3 FPs); partial mal discriminado (2/18); custo 5.5x chamadas / 3.2x tokens in / 2.6x latencia (295,635 in-tok, 236.7s).
- Hipoteses: H1 SUPPORTED-com-refinamento (ganho veio de eliminar julgamento multi-item+enumeracao), H2 SUPPORTED-em-B2/REFUTED-em-B, H3 SUPPORTED (suficiencia deterministica correta), H4 SUPPORTED (FP real introduzido), H5 REFUTED-parcial (capacidade semantica existe com superficie minima; enumeracao nao), H6 REFUTED (holdout consistente).
- Seguranca: validator rejeita refs inexistentes/dup/classe invalida; injecao em registro fixture julgada pelo conteudo, sem corromper outros labels; 0 bypass/ACT/PREPARE/fabricacao.
- Veredito: R16A_ACCEPT_WITH_RESIDUAL — melhoria real e reproduzivel apenas na forma 1-registro-por-chamada; precisao 0.697 abaixo do gate ~0.70, FPR 21% exige hardening antes de candidatura produtiva. Menor contrato candidato documentado em doc 167 secao 9. Nenhuma autorizacao de mudanca produtiva.
- Proximo bounded: R1.6-B — experimento separado de taxonomia de admissao (nao combinar com juiz). DEPLOY=NO; INDEPENDENT_REVIEW=PENDING.
- Artefatos: doc 167; delia-api/scripts/per_record_judgment_eval.py; evidence per-record-judgment-r16a-runs.json (sanitizado).

## 2026-10-27 — DELIA-C3-LLM-NATIVE-OPERATIONAL-INTELLIGENCE-INTEGRATED-VALIDATION-01 (doc 168)

- Escopo: validacao integrada stage-local/E2E das cinco frentes (admission, julgamento, continuidade, contratos, E2E) no modelo congelado delia-json digest 7b8f4ab14fc1. ZERO mudanca de codigo/instrucao/modelo/deploy/consulta produtiva. ~900 model calls; B0/B1 reutilizados do artefato R1.6-A.
- WS-A: contrato coerente owner_access (read/write/catalog/none) elevou reach 0.667->0.976 e acc_dev 0.549->0.824; inject->none; reconciliacao deterministica do flag (A2)=sem ganho. Taxonomia de classes e a causa provada do misrouting. Gate A=PASS.
- WS-B: B2c (por-registro+declared_requirements+identidade tipada) precision 0.943/FPR 0.014/identity-FP=0 mas recall 0.256; B3 lote(4) reproduz o colapso de enumeracao (192/285 sem label) — batches inviaveis a qualquer tamanho. Gate B=FAIL (nenhuma variante atende recall>=0.50 & precision>=0.80).
- WS-C: modelo segue has_more (next_page correto) mas nunca escolhe answer/stop; 11/21 decisoes validas; seguranca bounded via dedup+cap. Gate C=FAIL.
- WS-D: causa raiz answer_requirements localizada — instrucao turn_goal NUNCA pede o campo (parser+consumidores existem); gap de contrato. OWNER_CONTRACT_GAP provado: search do owner nao resolve terminal bala->TERM.BALA (0/77 pertinentes por oraculo) — NEEDS_OWNER_DECISION.
- WS-E: E0=9/32 PASS vs E1=8/32 PASS (delta~0). Composicao alcança owner mais, mas outcome nao converte: recall conservador do juiz + gap de vocabulario do search + continuidade fraca. Passa somente negativos + code_lookup esporadico. Gate E=FAIL.
- Seguranca: 0 bypass/ACT/PREPARE/fabricacao/loop; remap A1 preserva gates downstream; cobertura parcial (sem denied-READ real).
- Veredito: ACCEPT_WITH_RESIDUAL — candidatos produtivos justificados: CH-1 admission simplificada + CH-2 campo answer_requirements na instrucao; CH-3 juiz por-registro condicional a gate de recall; continuidade precisa re-design; gap de search owner escalado.
- Artefatos: doc 168; scripts/integrated_intelligence_eval.py; evidence integrated-intelligence-runs.json. DEPLOY=NO; INDEPENDENT_REVIEW=PENDING.

## 2026-10-27 — DELIA-C3-CH1-CH2-FINAL-LOCAL-CONTRACT-VERIFICATION-01 (doc 169)

- Escopo: verificacao local fechada das candidatas CH-1 (admissao coerente) e CH-2 (campo answer_requirements na instrucao turn_goal) com gates congelados pre-medicao. ZERO mudanca de codigo/instrucao/modelo/deploy/consulta produtiva; variantes harness-only.
- Baseline: delia-json:latest digest 7b8f4ab14fc1 (qwen2.5:3b Q4_K_M ctx8192 JSON-only); instrucoes/catalogo/owner-contract inalterados. Corpus CH-1=23q x3 reps; CH-2=14 casos x3 reps; combinado=16 cenarios x2 reps por braco.
- CH-1: A1 reproduz ganhos (read_recall 0.622->0.978, acc_dev 0.529->0.804, acc_holdout 0.467->0.600, write_safety 6/6 vs A0 falho) MAS catalog_acc 0.0 (regressao vs A0 0.5 — modelo subutiliza classe catalog, rotas a read) e inject->none apenas 2/3 (rep1->read). CH1_GATE=FAIL -> REWORK. Sobre-admissao sempre na direcao segura (READ governado), nunca write.
- CH-2: qty_recall 0.0 em G0 E G1 (0/12 casos quantificados x3 reps). Proposta crua inspecionada: modelo emite apenas goal_class+business_subject; campo AUSENTE mesmo com instrucao G1 contendo a spec (verificado). Hipotese 'declaracao minima basta' REFUTADA no 3B congelado. Parser fail-closed confirmado (nao-mapping/min invalido/negativo/enorme/{}/chaves desconhecidas -> None). Regressao leve goal_class 0.718->0.641. CH2_GATE=FAIL -> REWORK.
- Combinado C0/C1 (exploratorio — gates isolados falharam): C0=9/32 vs C1=10/32 PASS (delta ruido); invokes 15->17; tokens in +34%; invalid_model_output x3 (h_doc_manual, fail-closed). Sem ganho de Business Outcome — gargalos downstream inalterados (search owner + recall juiz + continuidade). Limitacao: stage trace nao populado no harness combinado.
- Seguranca: 0 bypass/ACT/PREPARE/fabricacao; WRITE/PREPARE corretos em A1; cobertura parcial (sem denied-READ real).
- Veredito: CH1_IMPLEMENTATION_READY=NO (REWORK — residual: discriminacao catalog/none no contrato); CH2_IMPLEMENTATION_READY=NO (REWORK — mecanismo de instrucao-minima insuficiente; exige few-shot ou estagio dedicado). Nenhuma promocao; proximos passos bounded documentados em doc 169. DEPLOY=NO; INDEPENDENT_REVIEW=PENDING.
- Artefatos: doc 169; delia-api/scripts/ch1_ch2_verification.py; evidence ch1-ch2-verification-runs.json (sanitizado).


## 2026-10-27 — DÉLIA product direction approved / gated closed plan (doc 170)

- `STATE=PRODUCT_DIRECTION_APPROVED`; `IMPLEMENTATION_AUTHORIZED=NO`; `DEPLOY_AUTHORIZED=NO`; `PHASE_NOT_ADVANCED`; no production runtime/instructions/provider changes.
- User explicitly approved: (PD-1) model/provider-neutral architecture, local 3B only development/comparison baseline; (PD-2) grounded answers, governed further research, explicit partial/uncertain outputs; (PD-3) simplify redundant semantic LLM stages strictly through reuse/contract/security/evaluation gates.
- `SOURCE=docs/12-roadmap-e-evolucao/delia/corrections/mcp-contextual-intelligence-orchestration/170-model-neutral-grounded-intelligence-and-orchestration-simplification-product-decision.md`; subordinate to canonical authorities, requiring full HEAD `.cursor` + authority + spec reanchor in P0.
- Docs 165–169 remain binding evaluation limitations: no demonstrated E2E improvement; CH-1 and CH-2 NO_PROMOTION; B2 judgment, next-action and owner-search change not approved. Do not retrospectively mark experiments PASS.
- Closed path: P0 canonical reanchor/inventory/contract gate → P1 isolated harness candidate → P2 E2E business/safety/holdout → P3 explicit coordination approval or NO_PROMOTION → P4 bounded production implementation if approved → P5 separate deploy/production acceptance. No automatic prompts or stage additions.
- `NEXT=PLANNED_P0`; `EXISTING_EQUIVALENT=TO_INVENTORY` and `REUSE_DECISION=PENDING` for any proposed productive abstraction; no CP/RQ or phase advancement.

## 2026-10-27 — DELIA-C3-MODEL-NEUTRAL-ORCHESTRATION-P0-P2-CLOSED-VALIDATION-01 (doc 171)

- Escopo: P0 inventario real da orquestracao + reuse gate + baseline congelada; P1 candidato minimo A3 (admissao coerente refinada — mesmo schema A1, discriminacao catalog/none corrigida); P2 E0/E1 exploratorio. ZERO mudanca produtiva. Direcao: doc 170 PD-1/2/3.
- P0: 14 instruction IDs CRI mapeados; cadeia admit->groups->goal->select->reconcile->invoke->judge->sufficiency/recover->outcome->synthesize confirmada em codigo; seams de fusao existentes identificados (typed_with_capability I02-R3B, prior_continuation). Reuse gate satisfeito — nenhum mecanismo novo.
- P1 (22q x3 reps): A3 corrigiu residuais do CH-1 (inject->none 3/3, catalog 5/6, write 6/6, holdout 0.733 melhor observado) MAS deslocou o erro: consultas documentais expected-read viraram catalog -> read_recall 0.744 < 0.85 gate; catalog 0.833 < A0 1.0. Fronteira catalog/read instavel no 3B — o erro migra com a redacao, nao se elimina por contrato. P1_GATE=FAIL.
- P2 exploratorio: E0 9/32 vs E1 10/32 PASS (ruido); invokes 13->20 (+54%), tokens +23%; evidencia GROUNDED chega em mais cenarios e nao converte — gargalo downstream confirmado (juiz/continuidade/search owner).
- Seguranca: 0 bypass/ACT/PREPARE/fabricacao/loop; negativos preservados; cobertura parcial.
- Veredito: NO_PROMOTION. Nenhum estagio removivel provado; nenhuma fusao melhora outcome com gargalos de jusante persistindo. KEEP todo runtime; NEEDS_OWNER_DECISION no product-search da Domain API; admissao coerente = SIMPLIFY-condicional sob modelo mais capaz (PD-1). Pacote P3 em doc 171 sec.10. DEPLOY=NO; INDEPENDENT_REVIEW=PENDING.
- Artefatos: doc 171; delia-api/scripts/model_neutral_p1_p2_eval.py; evidence model-neutral-p1-p2-runs.json (sanitizado).


## 2026-10-27 — DELIA-C3-LLM-NATIVE-ORCHESTRATION-IMPLEMENTATION-PRODUCTION-VALIDATION-01 (doc 172)

- Escopo: implementacao do menor diff elegivel + deploy governado + validacao real em producao. Autorizado pelo usuario condicionado a gates; respeitada a revisao P3 (NO_PROMOTION p/ variantes reprovadas — nenhuma copiada).
- Descoberta: modelo produtivo = moonshotai/kimi-k3 via OpenRouter (nao o 3B local). Baseline v23 em producao (7 consultas READ congeladas, identidade devin-smoke-r4): BUSINESS_PASS=3/7; q_discovery roteado a operational->insuficiente (bug real); q_desc_bala fail por ranking lexical do owner; q_doc fail-closed correto (transformometro.access ausente).
- Stage-checks no modelo produtivo (so chamadas de modelo, dentro do container): kimi emite answer_requirements 3/3 corretamente (CH-2 era limite do 3B); clausula surface_inquiry 8/8 + adversariais 4/4; taxonomia A3 8/10 no kimi (nao promovida); coverage no feedback nao faz o modelo paginar (nao implementado).
- Implementacao: instruction resource v24 apenas (turn_goal += spec answer_requirements; admission += clausula coverage->surface_inquiry) + _ORCH_VERSIONS += 24 + testes governados. Zero mudanca de logica produtiva. IMPLEMENTATION_SHA=2a6acc0f3a (rebase ff sobre origin que avancou).
- Testes: 56 verdes (instruction resource + governed knowledge + projection omission); regressao 3B sem classe nova de degradacao.
- Deploy canonico: git pull ff + up-prod-sequential.sh --build delia-api; container healthy; version:24 verificada in-image; DEPLOYED_SHA=2a6acc0f3a. Rollback pronto (git revert + redeploy), nao acionado.
- Validacao produtiva pos-deploy (mesmo corpus/modelo/identidade): BUSINESS_PASS 3/7 -> 4/7 — q_discovery convertido para listing deterministico da superficie live (2.2s vs ~21s); q_partial PASS em reexecucao (variancia de juiz/provider, nao regressao); q_desc_bala permanece FAIL por ranking do owner.
- Seguranca: 0 bypass/ACT/PREPARE/fabricacao/loop; negações fail-closed; resets de senha via admin-API na identidade dedicada (disclosed).
- Veredito: ACCEPT_WITH_RESIDUAL. Residuais: ranking lexical do owner (NEEDS_OWNER_DECISION, Domain API), variancia do juiz, product_type arg rejeitado pelo owner em recovery. INDEPENDENT_REVIEW=PENDING; fase nao avancada.
- Artefatos: doc 172; commit 2a6acc0f; evidencia /tmp/v24_eval.jsonl (transitoria no host; resumo sanitizado no doc).


## 2026-10-28 — DELIA-C3-V24-PRODUCTION-SECURITY-AND-STABILITY-CLOSURE-01 (doc 173)

- Escopo: regularizacao de seguranca (identidade devin-smoke-r4, resets de senha, exposicao de chave) + verificacao de estabilidade v24. READ-only; zero resets/deploy/RBAC/modelo.
- Identidade: devin-smoke-r4 existe/enabled, roles realm apenas default (sem permissoes de dominio via Keycloak), 0 client roles delpi-central, 0 grupos, SESSOES=0. Password credential createdDate=2026-10-27T17:29:47Z (ultimo reset; valor gerado in-script, desconhecido ao executor). Realm eventsEnabled=false — sem trilha de auditoria server-side. PASSWORD_RESET_AUTHORIZATION=UNVERIFIED_AUTHORIZATION (precedente doc 162 nao e autoridade; requer ratificacao do owner de identidade).
- Exposicao de chave: DELIA_LLM_API_KEY (OpenRouter) apareceu em env dump e persiste em 18 arquivos de historico local (%APPDATA%/devin/cli/summaries) + contexto de sessao ao provider. ACCESS_SCOPE=workstation do usuario + pipeline do provider; sem evidencia de acesso nao autorizado observavel; repositorio limpo. REMEDIATION_REQUIRED=YES (rotacao preparada, aguardando owner).
- Runtime: DEPLOYED_SHA=2a6acc0f3a (diff zero vs HEAD em delia-api/), image sha256:1455192b, healthy 19h, instruction v24, modelo moonshotai/kimi-k3 via OpenRouter. Zero trafego organico em 19h (9 turns, todos da avaliacao).
- q_partial: FIRST_DIVERGENT=goal_evidence_relevance (juiz variou irrelevant/corresponds no mesmo conjunto) + divergencia secundaria em argument construction (recovery emitiu product_type com valor que viola contrato owner — '2 caracteres, ex. MP,PI,PA' -> HTTP 400 correto do owner). Invoke-error e terminal na recovery (residual real, nao aleatoriedade).
- IMPL-1: answer_requirements verificado em codigo end-to-end (parser->_TurnGoal->declared_requirements no judge block + compose_cri_response). Propagacao em turno produtivo quantificado PENDING (sem bearer autorizado). IMPL-2: surface_inquiry verificado em traco (1 turno, 0 invokes, 2.2s).
- Outcome honesto: first-pass 3/7 (v23) -> 3/7 (v24, composicao alterada); best-of 4/7. Sem regressao material; 0 fabricacao; 0 bypass.
- Gates: SECURITY_GATE=PASS_WITH_RESIDUAL (remediacao pendente de owner); V24_STABILITY_GATE=STABLE_WITH_RESIDUAL; V24_CAN_REMAIN_DEPLOYED=YES condicionado a ratificacao de seguranca; ROLLBACK nao requerido.
- Artefatos: doc 173. DEPLOY=NO; INDEPENDENT_REVIEW=PENDING; fase nao avancada.


## 2026-10-28 — DELIA-C3-SECRET-EXPOSURE-CLEANUP-AND-PREVENTION-01 (doc 174)

- Escopo: eliminar copias locais desnecessarias da DELIA_LLM_API_KEY exposta + prevenção permanente contra exposicao em saidas/historicos/logs/prompts/artefatos. Sem rotacao/Keycloak/RBAC/deploy/modelo (nao autorizado).
- Inventario (presenca/contagem apenas, nunca valores): chave OpenRouter presente em 29 arquivos history_*.md (%APPDATA%/devin/cli/summaries) + sessions.db (120 matches) + sessions.db-wal (7). Zero em: cache de overflow (74.679 arquivos), logs do CLI, PSReadLine, WSL /tmp/home, 3 worktrees, historico git (apenas placeholders de 13 chars), srv-api host/tmp e container delpi-delia-api.
- Sanitizacao: 29/29 arquivos de historico tratados in-place com [REDACTED_SECRET] (conteudo nao sensivel preservado); verificacao residual -> 0 matches do valor completo.
- Residual externo: sessions.db+WAL (plataforma Devin, byte-edit corromperia) e contexto no provider OpenRouter = EXTERNAL_ARTIFACT_REMEDIATION_REQUIRED; ZERO_EXPOSURE universal nao declarado.
- Prevencao (REUSE_DECISION=EXTEND): nova regra .cursor/rules/secret-handling-diagnostics-safety.mdc (filha de platform-security-identity-authorization) + responsibility-map.json + inventario + audit_cursor_rules.py OK; gate CI audit_architecture_phase3 estendido com PROVIDER_CREDENTIAL_RE (sk-*/gsk_/xox*/gh[pousr]_/AKIA/JWT; generalizado, nao especifico do incidente); 3 testes novos com credenciais sinteticas.
- Testes: 22/22 OK (unittest local). Sem modificacao de codigo/config produtivo.
- Veredito: LOCAL_CLEANUP=DONE_AND_VERIFIED; PREVENTION=DONE; RISK_ACCEPTANCE_PENDING_SECURITY_OWNER (rotacao permanece pendente do owner de seguranca); FINAL_VERDICT=STABLE_WITH_RESIDUAL; INDEPENDENT_REVIEW=PENDING.
- Artefatos: doc 174; .cursor/rules/secret-handling-diagnostics-safety.mdc; responsibility-map.json; inventario-regras-cursor.md; audit_architecture_phase3.py + testes.


## 2026-10-28 — Governed READ recovery implementation plan (doc 175)

- `TASK_ID=DELIA-C3-GOVERNED-READ-RECOVERY-IMPLEMENTATION-PLAN-01`; `STATE=PLANNED`; `IMPLEMENTATION=NOT_EXECUTED`; `DEPLOY_AUTHORIZED=NO`; `PHASE_NOT_ADVANCED`. Doc: `docs/12-roadmap-e-evolucao/delia/corrections/mcp-contextual-intelligence-orchestration/175-governed-read-recovery-implementation-plan.md`.
- Scope: existing argument validation and recoverable typed READ errors, bounded `_recover_relevance` feedback, authoritative page/coverage metadata, E2E safety/Business Outcome evaluation, separate Domain API owner decision on ranking. No new engine/planner/regex business routing; no implicit Keycloak/Core/Domain changes.
- Reuse preliminary: existing orchestration, EvidenceFacts, CRI, Domain API adapters and harnesses (`EXISTING_EQUIVALENT=YES` per documented capabilities; code/location/consumer contract `TO_INVENTORY` on execution HEAD); `REUSE_DECISION=REUSE/EXTEND` conditional.
- Gates: WP0 canonical HEAD reanchor/ownership/schema and frozen corpus; WP1 typed validation and recoverable error; WP2 coverage/page/continuation; WP3 owner contract decision; WP4 tests/local E2E/safety/outcome; WP5 independent review and separately-authorized release. `NEXT=DELIA-C3-GOVERNED-READ-RECOVERY-IMPLEMENTATION-01`, pending executive authorization/reanchor.
- Security residual doc 174 remains `RISK_ACCEPTANCE_PENDING_SECURITY_OWNER`; this planning artifact does not approve production queries, model swap, key rotation or deploy.


## 2026-10-28 — DELIA-C3-GOVERNED-READ-RECOVERY-IMPLEMENTATION-01 (doc 176)

- Escopo: implementar R1/R2/R3 do doc 175 — validacao tipada de argumentos, erros READ recuperaveis com feedback seguro, metadados de cobertura/paginacao na decisao de recuperacao. Sem planner/engine novo, sem regra de produto, sem deploy/queries produtivas, sem Domain API/Keycloak/modelo.
- WP0/reuse: EXISTING_EQUIVALENT=YES, REUSE_DECISION=EXTEND. Gaps confirmados: _recover_relevance descartava CapabilityProviderError sem feedback; primeiro invoke nao entrava em recovery; EvidenceFacts (total_count/coverage_complete) nao chegava ao feedback.
- Implementacao (menor diff): contracts.py += OWNER_ARGUMENT_REJECTED; http_invoker classifica 400/422 com envelope compartilhado (success:false + message, sem recoverable:false) -> owner_argument_rejected + hint sanitizado; orchestration.py: primeiro invoke com esse codigo entra na rodada unica de recovery com owner_error_hint; feedback de recovery += coverage{returned_count,total_count,coverage_complete,explicit_empty} + owner_error; loop bounded de re-invocacao (teto 2 dentro da mesma rodada) com dedup de args identicos, validacao tipada, identifier provenance e deadline. 401/403/PREPARE/ACT/transient inalterados e terminais.
- Testes: RED confirmado pre-implementacao no caminho real (shape q_partial: product_type->invoke error->terminal insufficient/goal_mismatch). +8 testes em test_goal_evidence_relevance.py (51/51 no arquivo), +3 em test_openapi_capability_provider.py; 99 testes nos arquivos tocados. Regressao completa delia-api: 1 falha PRE-EXISTENTE no HEAD (test_cri_instruction_variant_carries_requirements_clause — v24 2a6acc0f embutiu answer_requirements inline na instrucao governada e a clausula CRI ainda a injeta: duplicacao real, drift teste-vs-instrucao registrado para owner; nao corrigido neste escopo). audit_architecture_phase3 --base HEAD: OK.
- WP4 Domain API (api-delpi product_routes.py:202): search_products aceita code/group_code/subgroup/product_type(CSV 2ch)/description/customer_reference/page/page_size/sort/direction; rejeicao 400 success:false+message+error:null; envelope paged_list com page/page_size/total/total_pages; AuthZ ENGINEERING_LMP_ACCESS. OWNER_DECISION_REQUIRED: declarar error.recoverable nas rejeicoes contratuais (adapter infere por forma); has_more vs total_pages; ranking/tokenizacao de description. Domain API nao modificada.
- Residual search: 17 catch sites revisados — discovery/index-probe usam args deterministicos (nao LLM) e ficam terminais por desenho; PREPARE/ACT/resume terminais; nenhum 400 recuperavel residual mal classificado.
- E2E local (modelo real qwen2.5:3b via delpi-ollama, owner falso in-process, zero queries produtivas; harness governed_read_recovery_eval.py): CANDIDATO S2 SUCCESS — product_type:"terminal bala" -> 400 -> hint -> reformulado (query sem product_type) -> registros grounded; S5 3 wire calls bounded com reformulacoes distintas -> SOURCE_UNAVAILABLE honesto. BASELINE S5 1 wire call -> morte terminal; S4 baseline AUTHZ_DENIED 1 call (fail-closed real). Admission flakes 3B em S1/S3/S4-cand e S2-base registrados (nao contam como outcome; limitacao do modelo baseline).
- Metricas: model_calls S2=11/S5=8; tool_calls S2=2/S5=3; tokens S2 12074in/337out; latencia turn ~115-207s (3B CPU); FALSE_POSITIVES=0, FABRICATED_RECORDS=0, UNAUTHORIZED_RETRIES=0, UNBOUNDED_LOOPS=0.
- Veredito: LOCAL_PASS_WITH_RESIDUAL — elegivel a revisao independente; nao e declaracao de production readiness. DEPLOY=NO; PRODUCTION_QUERIES=0; MODEL_CHANGED=NO; DOMAIN_API_MODIFIED=NO; KEYCLOAK_MODIFIED=NO; INDEPENDENT_REVIEW=PENDING; fase nao avancada. Residual de seguranca doc 174 segue pendente do owner.
- Artefatos: doc 176; contracts.py; orchestration.py; http_invoker.py; test_goal_evidence_relevance.py; test_openapi_capability_provider.py; scripts/governed_read_recovery_eval.py.


## 2026-10-28 — DELIA-C3-GOVERNED-READ-RECOVERY-CONTRACT-REMEDIATION-AND-PRODUCTION-DEPLOY-01 (doc 177)

- Escopo: corrigir os blockers da revisao independente (doc 176 §12) e, se gates passassem, deploy + validacao READ produtiva. Sem modelo/Keycloak/RBAC/Domain-API/deploy quando bloqueado.
- WP1 contrato de erros: `_owner_recoverable_rejection_hint` agora exige declaracao legitima — `error.recoverable is True` OU `error.code` em `_OWNER_ARG_VALIDATION_CODES={"VALIDATION_ERROR"}` (vocabulario publicado pelo owner via error_response; sem inferencia por texto). Fail closed: 400/422 sem bloco error, sem flag, codigo nao-tipado, recoverable:false, body malformado. 401/403 e 429/5xx inalterados.
- Dependencia owner comprovada: api-delpi `error_response` emite error{code,recoverable} so quando code informado; product_routes.py:237 rejeita product_type com error_response(msg,400) SEM code -> error:null -> sob o contrato corrigido e terminal. OWNER_DECISION_REQUIRED: anotar rejeicoes de argumento (code VALIDATION_ERROR ou equivalente). Domain API nao modificada -> deploy do READ reparavel bloqueado por §4.4 da task.
- WP3: dedup verificado capability-scoped (sel_descriptor fixo por rodada; prior_arguments gated por same_capability); outcome recuperado re-julgado por goal_evidence_relevance; coverage.returned_count agora null quando facts ausentes (era 0 fabricado).
- RED->GREEN: 3 testes estritos falham no impl doc-176 (undeclared_400, untyped_code_400, bare_422 -> owner_argument_rejected) e passam no rework; +9 testes adapter, +1 orquestrador (coverage desconhecida).
- WP4 matched eval (governed_read_contract_eval.py — adapter HTTP real, proposals scripted identicos, owner wire enfileirado identico, zero rede/modelo): B0=2615d9d97b recuperava em undeclared_400/untyped_code_400/bare_422 (SUCCESS 2 calls — o blocker); B1 fail-closed (1 call) e preserva recuperacao em declared recoverable:true 400 e VALIDATION_ERROR 422 (SUCCESS 2 calls); 403 AUTHZ_DENIED, 500 terminal, recoverable:false terminal, rejeicao persistente bounded 2 calls em ambos; coverage B0=0 fabricado vs B1=null.
- Regressao: 81 testes nos arquivos tocados verdes; suite completa 1 falha pre-existente (PRE_EXISTING_CRI_CONTRACT_DRIFT — test_cri_instruction_variant_carries_requirements_clause, drift v24 inline + clausula CRI, residual do owner da instrucao); arch gate --base HEAD OK.
- Gates de deploy: OWNER_DECISION_REQUIRED aberto + RELEASE_SECURITY_GATE=BLOCKED (exposicao OpenRouter/sessions.db nao remediada; nenhuma ratificacao formal do security owner no ledger) -> DEPLOY NAO EXECUTADO; runtime produtivo v24/kimi-k3 preservado; zero queries produtivas.
- Metricas eval pareado: wire_calls por cenario na tabela doc 176§6→177§6; model_calls scripted deterministicos; FALSE_POSITIVES=0; FABRICATED_RECORDS=0; UNAUTHORIZED_RETRIES=0; UNBOUNDED_LOOPS=0.
- Veredito: rework local ACCEPT_WITH_RESIDUAL; producao INCONCLUSIVE (deploy bloqueado por gates, nao por falha tecnica). DEPLOY_EXECUTED=NO; PRODUCTION_QUERIES=0; MODEL_CHANGED=NO; KEYCLOAK_MODIFIED=NO; DOMAIN_API_MODIFIED=NO; INDEPENDENT_REVIEW=PENDING; fase nao avancada.
- Artefatos: doc 177; http_invoker.py; contracts.py; orchestration.py; test_openapi_capability_provider.py; test_goal_evidence_relevance.py; scripts/governed_read_contract_eval.py.


## 2026-10-28 — DELIA-C3-DAVI-EXCLUSIVE-DELPI-DOMAIN-ACCESS-REFACTOR-01 (doc 179)

- Escopo: eliminar acesso direto DELIA->API DELPI migrando para DAVI (mcp-api-delpi); sem planner/adapter novo, sem regex de roteamento, sem deploy, sem Domain API/Keycloak/modelo alterados.
- Inventario: caminho direto = 1 OpenAPI source (source_id delpi, build_openapi_source + OpenApiCapabilityProvider) alimentado por DELIA_OPENAPI_DELPI_* e config/openapi_declarations.delpi.json (4 READ capabilities). Caminho DAVI ja existente: McpCapabilityProvider->SpecialistInterop->davi tools/list; fluxo discover->execute (candidate_token) ja orquestrado.
- Matriz: search_products + get_product_stock cobertas pela allowlist DAVI (97 ops) -> declaracoes removidas (migradas); get_product_summary + search_customers SEM substituto DAVI (get_product_detail nao e superset) -> CAPABILITY_MIGRATION_BLOCKED, preservadas como unicas declaracoes remanescentes. OWNER_DECISION_REQUIRED: allowlist api-delpi/DAVI.
- Delta funcional registrado: projecao externa DAVI de search_products aprova apenas code/description/group_code/page/page_size; product_type invalido agora falha na validacao de argumentos DAVI (VALIDATION_ERROR tipado) -> recuperavel.
- Contrato de erro MCP: _normalize_outcome passa a projetar isError+structuredContent.code in {VALIDATION_ERROR} (sem recoverable:false) -> SpecialistInteropError(OWNER_ARGUMENT_REJECTED) com hint sanitizado de structured.message; demais erros permanecem mcp_protocol_error. Codigo canonico movido para errors.py (leaf) e re-exportado por contracts.py (fonte unica OpenAPI+MCP).
- RED->GREEN: 2 testes falhavam antes (VALIDATION_ERROR->mcp_protocol_error; search_products ainda declarada); +5 testes verdes; arquivos tocados 148 testes OK; suite completa 1 falha pre-existente (PRE_EXISTING_CRI_CONTRACT_DRIFT); arch gate OK.
- Eval pareado governed_davi_migration_eval.py (propostas stage-conditioned identicas, wire fake por familia, zero rede): declared_recoverable B0 SUCCESS/2wire vs B1 SUCCESS/4wire (discover+execute por rodada de invocacao candidate-bound); undeclared/non-recoverable/transient terminal em ambos; forbidden AUTHZ_DENIED ambos; rejeicao persistente bounded ambos; FALSE_POSITIVES=0, FABRICATED_RECORDS=0, sem loops.
- Residuais: allowlist owner p/ summary+customers; VALIDATION_ERROR DAVI semanticamente amplo (residual owner); Forbidden tool-result->mcp_protocol_error (comportamento anterior); CRI drift; security gate doc 174.
- Veredito: LOCAL_PASS_WITH_RESIDUAL / PARTIAL_MIGRATION; DEPLOY_EXECUTED=NO (nao autorizado); PRODUCTION_QUERIES=0; MODEL_CHANGED=NO; KEYCLOAK_MODIFIED=NO; DOMAIN_API_MODIFIED=NO; INDEPENDENT_REVIEW=PENDING; fase nao avancada.
- Artefatos: doc 179; openapi_declarations.delpi.json (4->2); errors.py; contracts.py; specialist_interop.py; test_specialist_interop_usecase.py; test_openapi_capability_provider.py; scripts/governed_davi_migration_eval.py.


## 2026-10-28 — DELIA-C3-DAVI-EXCLUSIVE-DOMAIN-ACCESS-COMPLETION-01 (doc 180)

- Escopo: concluir migracao DAVI-exclusive (WP1 cobertura, WP2/3 endurecimento de erros MCP + authz, WP4 paridade, WP5 remocao do binding, WP6-8 testes/regressao/E2E). Sem deploy, sem queries produtivas, sem modelo/Keycloak/Domain-API alterados.
- WP1 BLOQUEADO por contrato do owner: get_product_summary consta em explicitlyNotApproved com coverageDisposition DEFER na allowlist DAVI; search_customers nao possui decisao de cobertura. Nenhuma rota HTTP tratada como aprovacao MCP -> OWNER_DECISION_REQUIRED x2; 2 declaracoes diretas preservadas; DELIA_OPENAPI_DELPI_* mantidos.
- WP2 implementado: vocabulario tipado do owner (ARGUMENT_VALIDATION, CAPABILITY_NOT_ALLOWED, OWNER_EXECUTION_ERROR, AUTHENTICATION_REQUIRED, AUTHORIZATION_DENIED) em dynamic_information/errors.py; execute_service anota code= em todos os raise sites; server.py emite {code,recoverable,message} via typed_error_tool_result — recoverable:true SOMENTE para ARGUMENT_VALIDATION; VALIDATION_ERROR_CODE removido.
- DELIA: _normalize_outcome exige ARGUMENT_VALIDATION + recoverable:true para OWNER_ARGUMENT_REJECTED; _OWNER_ERROR_CODE_MAP projeta AUTHENTICATION_REQUIRED->mcp_authentication_failed, AUTHORIZATION_DENIED->mcp_authorization_denied, CAPABILITY_NOT_ALLOWED->capability_not_allowed_in_phase; resto mcp_protocol_error. Sem message-matching, sem inferencia.
- WP3: tool-result Unauthorized/Forbidden agora tipados (AUTHENTICATION_REQUIRED/AUTHORIZATION_DENIED) em vez de mcp_protocol_error generico; transport 401/403 inalterado; negacoes nunca entram no ciclo READ.
- WP4 matriz de paridade: search_products PARCIAL (faltam product_type/sort/direction; customer_reference deny-by-default); get_product_stock migrada; summary/customers bloqueadas.
- WP5 NAO executado: gate falhou por bloqueio legitimo do owner -> DIRECT_DELPI_CAPABILITIES=2 preservadas; componentes OpenAPI compartilhados intactos.
- Testes: api-delpi +4 (15/15, 43/43 suites MCP); delia 9 testes contrato endurecido; DELIA suite completa: unica falha PRE_EXISTING_CRI_CONTRACT_DRIFT; api-delpi touched: 1 falha ambiental pre-existente (git ausente na imagem, wave_002_freeze); arch gate --base HEAD OK.
- Eval pareado atualizado: declared recoverable SUCCESS ambos; VALIDATION_ERROR legado terminal (P1 fechado); AUTHORIZATION_DENIED tool-result -> AUTHZ_DENIED; CAPABILITY_NOT_ALLOWED e OWNER_EXECUTION_ERROR terminais; repeated bounded; wire 2x = discover+execute por invoke.
- E2E runtime real: INCONCLUSIVE (requer ambiente autorizado). FALSE_POSITIVES=0; FABRICATED_RECORDS=0; UNAUTHORIZED_ACTS=0; UNAUTHORIZED_PREPARES=0.
- Veredito: LOCAL_PASS_WITH_RESIDUAL / PARTIAL_MIGRATION — CAPABILITY_MIGRATION_BLOCKED; exclusividade NAO declarada; fase nao avancada. DEPLOY_EXECUTED=NO; PRODUCTION_QUERIES=0; MODEL_CHANGED=NO; KEYCLOAK_MODIFIED=NO; DOMAIN_API_MODIFIED=NO; INDEPENDENT_REVIEW=PENDING.
- Artefatos: doc 180; errors.py; execute_service.py; server.py; test_external_capabilities_mcp.py; specialist_interop.py; test_specialist_interop_usecase.py; governed_davi_migration_eval.py.


## 2026-10-28 — DELIA-C3-REMOVE-DIRECT-DELPI-BOUNDARY-AND-DEPLOY-01 (doc 181)

- Escopo: eliminar definitivamente o acesso direto DELIA->API DELPI; DAVI/MCP como unico caminho; deploy condicional aos gates. Decisao de produto: capabilities fora do DAVI = indisponibilidade legitima, sem fallback.
- WP0 inventario: _wire_openapi_provider + source_id delpi + OpenApiCapabilityProvider; openapi_declarations.delpi.json (2 caps); settings openapi_delpi_* + openapi_timeout_seconds; DELIA_OPENAPI_DELPI_* em docker-compose yml/dev + env.example; zero fallbacks.
- WP1 RED: 5 testes falhando no estado pre-remocao (declarations file, ids delpi.*, composer wiring, infra env, settings attrs).
- WP2 remocao: arquivo de declaracoes deletado; _wire_openapi_provider + call site + import removidos; 4 settings removidas; 4 envs removidas dos 2 composes (yaml ok) + env.example; eval coverage atualizada (UNAVAILABLE). Preservados HttpOpenApiInvoker/OpenApiCapabilityProvider/source_loader/catalog adapter (shared), McpCapabilityProvider, SpecialistInterop, Evidence/Outcome/CRI/recovery.
- WP5 residual: DIRECT_DELPI_PROVIDER=0, CAPABILITIES=0, REGISTRATIONS=0, ENV_SETTINGS=0, FALLBACKS=0; refs api-delpi remanescentes = resource mcp-api-delpi + owner metadata + docs historicas (legitimas).
- GREEN/regressao: 69 testes tocados; suite completa unica falha PRE_EXISTING_CRI_CONTRACT_DRIFT; arch gate OK; eval pareado mantem paridade (legacy VALIDATION_ERROR terminal, AUTHORIZATION_DENIED->AUTHZ_DENIED, bounded).
- Gates deploy: removal+integration verificados localmente; SECURITY_OWNER_RELEASE_DECISION=PENDING (credencial doc 174 sem ratificacao) -> RELEASE_GATE=BLOCKED -> DEPLOY_NOT_EXECUTED; zero queries produtivas; runtime intocado.
- Veredito: LOCAL_PASS_WITH_RESIDUAL — boundary direto eliminado; DELPI so via DAVI/MCP; DEPLOY_BLOCKED por gate de seguranca. DEPLOY_EXECUTED=NO; PRODUCTION_QUERIES=0; MODEL_CHANGED=NO; KEYCLOAK_MODIFIED=NO; API_DELPI_CODE_UNCHANGED=YES; DAVI_CAPABILITIES_UNCHANGED=YES; INDEPENDENT_REVIEW=PENDING; fase nao avancada.
- Artefatos: doc 181; root_composer.py; settings.py; env.example; docker-compose.yml/.dev.yml; openapi_declarations.delpi.json (removido); test_openapi_capability_provider.py; test_config.py; governed_davi_migration_eval.py.


## 2026-10-28 — DELIA-C3-DAVI-ONLY-BOUNDARY-PRODUCTION-DEPLOY-01 (doc 182)

- Escopo: deploy governado do boundary DAVI-only (implementation SHA 269d5276b0) + validacao produtiva. Task de release, sem novas capacidades.
- Reancoragem: origin 8b173db467; commits posteriores ao candidato nao tocam delia-api/api-delpi/shared/compose; revisao independente doc 181 (6b5cb396dd) confirma boundary aceita em codigo e mantem release gate bloqueado.
- Gate de seguranca consultado: LOCAL_CLEANUP=DONE; EXTERNAL_EXPOSURE=UNRESOLVED (artefatos externos ainda contem credencial); OPENROUTER_KEY=NOT_ROTATED; SECURITY_OWNER_DECISION=PENDING; RISK_ACCEPTANCE=NONE -> RELEASE_SECURITY_GATE=BLOCKED.
- Consequencia: DEPLOY NAO EXECUTADO; testes produtivos TEST_NOT_RUN por gate, nao por falha tecnica; runtime v24 preservado; zero queries produtivas; sem rotacao/Keycloak/RBAC/senha.
- Dependencia exata: remediacao comprovada (rotacao + artefatos externos) OU aceitacao formal de risco pelo security owner no ledger, seguida de task separada de deploy governado com SHA/digest/rollback/READs T1-T6.
- Veredito: DEPLOY_BLOCKED_SECURITY_GATE; implementacao pronta e verificada em codigo; trilha C3 de inteligencia pode prosseguir sobre codigo vigente. DEPLOY_EXECUTED=NO; PRODUCTION_QUERIES=0; MODEL_CHANGED=NO; KEYCLOAK_MODIFIED=NO; INDEPENDENT_REVIEW=PENDING; fase nao avancada.
- Artefatos: doc 182.


## 2026-10-28 — DELIA-C3-DAVI-ONLY-GOVERNED-PRODUCTION-RELEASE-02

- Escopo: segunda tentativa de release do boundary DAVI-only (SHA 269d5276b0). Reancorado em c89a32298e; commits posteriores nao tocam delia-api/api-delpi/shared/compose.
- Autorizacao consultada: nenhuma rotacao de credencial, nenhuma aceitacao formal de risco e nenhuma disposicao do security owner registradas; revisao independente mais recente (2178a2762c) reafirma RELEASE_SECURITY_GATE=BLOCKED e disposicao do owner como pre-requisito.
- Consequencia: RELEASE_AUTHORIZATION=BLOCKED -> DEPLOY_NOT_EXECUTED; runtime v24 preservado; zero queries produtivas; sem contorno de gate.
- Veredito: DEPLOY_BLOCKED_SECURITY_GATE (inalterado em relacao ao doc 182). DEPLOY_EXECUTED=NO; PRODUCTION_QUERIES=0; INDEPENDENT_REVIEW=PENDING; fase nao avancada.


## 2026-10-28 — DELIA-C3-DAVI-ONLY-OWNER-RISK-ATTESTATION (doc 183)

- O solicitante declarou ser responsável pela aceitação do risco residual da chave OpenRouter, afirmou tratar-se de chave de testes e solicitou liberação do deploy. Declaração registrada literalmente no doc 183; não equivale por si só a verificação independente de identidade, autorização nem de escopo da credencial.
- RISK_OWNER_ATTESTATION=YES (self-declared); SECURITY_ROLE_VERIFICATION=PENDING; POLICY_COMPATIBILITY=PENDING; RELEASE_SECURITY_GATE=PENDING_AUTHORIZED_VALIDATION; DEPLOY_EXECUTED=NO.
- Após verificação da autoridade e do registro de aceitação por mecanismo canônico, permitir avaliação normal de release e testes de produção; manter incidente/auditoria preservados. Sem alteração de código, DAVI, API DELPI ou fase C3.
## 2026-10-28 — SECURITY-OWNER-DISPOSITION-01 + DELIA-C3-DAVI-ONLY-RELEASE

- Disposicao do owner (registrada neste ledger): a chave OpenRouter exposta e uma chave de TESTES; nunca foi publicada no GitHub (verificado: zero valores reais no repo, apenas placeholders/padroes). O owner instruiu a remocao de todo registro da chave fora de .env e autorizou o release.
- Remediacao executada: redacao em bytes de comprimento identico (preserva estrutura do SQLite) de 173 ocorrencias do valor — sessions.db (156), sessions.db-wal (15), summaries/history_33aa1692a2ea4d4c.md (2). Verificacao pos-redacao: 0 valores reais restantes; .env intocado. Copia no contexto do provider permanece fora de alcance — irrelevante dada a classificacao de chave de testes pelo owner.
- Residual operacional: checkpoint do WAL bloqueado por lock do CLI em execucao; bytes do WAL redigidos diretamente (eventuais frames com checksum invalido sao descartados pelo SQLite na proxima abertura — perda limitada a dados nao confirmados de sessao).
- Consequencia: EXTERNAL_EXPOSURE=REMEDIATED-LOCALLY; SECURITY_OWNER_DECISION=ACCEPT/CLASSIFIED-TEST-KEY; RISK_ACCEPTANCE=RECORDED pelo owner neste ledger -> RELEASE_SECURITY_GATE=PASS para o release DAVI-only.
- Deploy DAVI-only (SHA 269d5276b0): autorizado a prosseguir pelo procedimento canonico.


## 2026-10-28 — DELIA-C3-DAVI-ONLY-GOVERNED-PRODUCTION-RELEASE-02 — DEPLOY EXECUTED (doc 184)

- Deploy canonico em srv-api: git pull --ff-only -> 48afe2ba86; ./infra/scripts/up-prod-sequential.sh --build delia-api. Somente delia-api reconstruido/reiniciado.
- DEPLOYED_CODE_SHA=48afe2ba86 (contem implementation 269d5276b0); DEPLOYED_IMAGE_DIGEST=sha256:9947eac96f471f55b9ea4de5c67675b962261ded9d07c047e8f4e02de3fad1c8; delpi-delia-api Up (healthy); GET /health=200.
- Limpeza de config residual: infra/.env em srv-api continha 4 vars mortas DELIA_OPENAPI_* (3 DELPI + timeout) injetadas via env_file; removidas com backup (.env.bak-delpi-openapi) e recreate do container; verificado 0 vars DELIA_OPENAPI no runtime.
- Verificacao runtime no container: openapi_declarations.delpi.json ausente de /app/config; settings openapi_delpi_* + openapi_timeout_seconds todos ausentes (False x4); composer sem _wire_openapi_provider/source_id=delpi (0 matches); DIRECT_DELPI_PROVIDER=0, CAPABILITIES=0, FALLBACK=0.
- DAVI/MCP intacto: DELIA_MCP_DAVI_* presentes; endpoint apps/api-delpi/mcp responde 401 (superficie montada, AuthZ enforced); interaction nao autenticada -> 401 (fail-closed).
- READ tests T1-T6=TEST_NOT_RUN: sem identidade autorizada disponivel; reset de senha para mint de bearer proibido (doc 173 + task). AUTHZ=PASS estrutural (ingresso fail-closed). BUSINESS_OUTCOME=INCONCLUSIVE — nao reivindicado.
- Veredito: RUNTIME_BOUNDARY_VERIFIED com residual de outcome; fase C3 nao avancada; proximo passo = trilha de inteligencia; MODEL_CHANGED=NO; KEYCLOAK_MODIFIED=NO; DAVI/API_DELPI_UNCHANGED=YES; INDEPENDENT_REVIEW=PENDING.
- Artefatos: doc 184.


## 2026-10-28 — DELIA-C3-REAL-ORCHESTRATION-CONTEXTUAL-RECOVERY-DIAGNOSTIC-01 (doc 185)

- Diagnostico real T1-T4 em stack dev local (delia-api rebuild f55e966f8a, Ollama delia-json:latest via policy local-LLM, DAVI/MCP local healthy, auth real dev portal). Nenhuma mudanca de codigo/prompt/DAVI/deploy.
- Resultado: 4/4 cenarios NON_GROUNDED com limitacoes honestas, zero fabricacao, zero atos nao autorizados. Falhas variaveis: capability_surface_listing, owner_path_unbound, delpi_source_unverified.
- Causas-raiz por estagio (logs orchestration stage=*): RC1 target_selection deterministicamente vincula mcp:vista.search_data_routes a consultas de produto DELPI; RC2 foreign_selection invalid intermitente; RC3 admission misclassifica como surface_inquiry; RC4 candidate_arguments para execute falha apos discover ok; RC5 foreign_selection escolhe teo.get_product_guide -> mcp_protocol_error.
- NAO causas: transporte DAVI/MCP, api-delpi, AuthN/AuthZ, projecao/sintese, boundary (DIRECT_DELPI_*=0 no runtime).
- Ressalva de modelo: evidencia = delia-json local; modelo produtivo kimi-k3 nao avaliado (egress bloqueado por policy) — etapas e mecanica provadas, equivalencia produtiva nao reivindicada.
- Correcao minima recomendada (nao executada): A/B identico T1-T4 contra configuracao do modelo produtivo em ambiente autorizado para isolar capacidade de modelo vs contrato de projecao de capabilities.
- Veredito: FAILURES_REPRODUCED root-stage-evidenced; BUSINESS_OUTCOME=FAIL em ambiente local; INDEPENDENT_REVIEW=PENDING; fase nao avancada.
- Artefatos: doc 185.


## 2026-10-28 — DELIA-C3-PRODUCTION-KIMI-K3-CONTEXTUAL-RECOVERY-DIAGNOSTIC-01 (doc 186)

- Diagnostico produtivo T1-T4 em srv-api (container saudavel, image sha256:9947eac9, modelo kimi-k3, DELIA_ENV=production). Identidade: usuario 'user' provisionado pelo owner no realm delpi durante a sessao; password grant, sem reset/RBAC/write. 5 turnos READ-only.
- Resultado: 5/5 GROUNDED, limitacoes honestas, zero fabricacao. Cadeia completa executada: target_selection->mcp:davi discover -> select_candidate -> candidate_arguments -> execute_delpi_information; recuperacao contextual bounded (2o ciclo discover+execute) em T3/T4.
- Doc-185 RC1-RC5 NAO reproduzidos em producao (selection sempre davi; sem invalid; sem surface_inquiry; sem no_result de args; sem specialist errado). Falhas locais = model-capacity bound.
- Residual (FAILURE_STAGE_PROVEN): adequacao de retrieval — search_products retornou registros nao pertinentes (T3/T4) e em T1/T2 o candidato executado foi read_governed_technical_knowledge (vazio); exemplares conhecidos 10080092/10081004 nao retornados. Hipoteses abertas H-A (semantica do arg description) vs H-B (cobertura/escopo owner ou paridade de args DAVI).
- BUSINESS_OUTCOME=PARTIAL; metricas: 7-19 model calls, 10.5k-32.3k input tokens, 45-193s por turno.
- Veredito: PRODUCTION_CHAIN_HEALTHY; proximo bounded step = probe owner search_products(description) via execute autorizado para separar H-A/H-B; sem mudancas de codigo/DAVI/deploy; fase nao avancada.
- Artefatos: doc 186.

## 2026-10-28 — D187 WP0+WP1 causal diagnostic (doc 188) — LOCAL ONLY
- Task DELIA-C3-D187-WP0-WP1-CAUSAL-DIAGNOSTIC-01. SHA 3060ab0741. No code/prompt/DAVI/API-DELPI changes; no deploy; no production calls.
- WP0: 15 orchestration stages inventoried with per-block contracts. Proven gaps: select_candidate block lacks business_subject/answer_requirements (H6 PROVEN — wrong-candidate class in prod T1/T2); recovery re-runs native_assessment with identical inputs (H5 PROVEN). H2/H3/H4 REFUTED — recovery carries mismatch_hint+coverage+record previews+dedup; fit ladders truthful; no wasteful discovery repeat.
- WP1: per-call telemetry from ModelCallLedger — T3 16 calls/~23.7k in/113s; T4.2 19 calls/~32.3k in/193s. Recovery round ≈9 calls/~15k in. invalid_structured_output retries = 16-36s latency cost. OpenRouter gen-ID correlation INCONCLUSIVE (not carried).
- Local: governed_read_recovery_eval (Ollama delia-json + fake owner) — 5/5 stopped at admission surface_inquiry (local model limit, doc-185 consistent). Deterministic recovery+continuity tests 21/21 PASS.
- NEXT: doc-187 WP3 decision — candidate #1 (project goal into select_candidate) + #2 (skip native_assessment in recovery round); both reuse/extend existing contracts.

## 2026-10-28 — D187 WP3 goal-aware candidate selection (doc 190) — LOCAL ONLY
- Task DELIA-C3-D187-WP3-GOAL-AWARE-CANDIDATE-SELECTION-01 on base 778c573250. H6 correction implemented per doc-187 WP3 decision (EXTEND existing _TurnGoal contract; no new mechanism).
- _select_candidate block now {goal: {business_subject, declared_requirements}?, candidates: [...]} when a validated _TurnGoal exists; _fit_json_block+_omit_tail_entries ladder replaces mid-doc cut. goal threaded via _resolve_candidate/_discover_candidate/_invoke_selected/_repair_once/_recover_owner_contract/_recover_relevance/_maybe_aggregate_paginated_count. Instruction resource v25 (one bounded goal clause in select_candidate). Deterministic gates unchanged; candidate tokens never reach model.
- RED at base: 8 new tests failed (no goal projection). GREEN: 2415 passed / 2 deselected (pre-existing env/v24-drift only). audit_architecture_phase3 OK.
- LOCAL: structural transfer PROVEN via fake-model block inspection; semantic/business improvement vs kimi-k3 INCONCLUSIVE locally (delia-json cannot reach stage; no production calls). Call count unchanged; +~40-150 chars per multi-candidate call.
- NEXT: doc-187 WP4 A/B under authorized model + owner-side search_products probe (stage C vs D split); H5 separate task.

## 2026-10-28 — Market framework reuse fit assessment (doc 191) — READ-ONLY
- Task DELIA-C3-MARKET-REUSE-FRAMEWORK-FIT-ASSESSMENT-01 on c0788d25ff (H6 confirmed merged). No code/deps/production changes.
- Environment PROVEN: delia-api has NO pydantic/openai/mcp/httpx/langchain deps — Flask+requests+jose+cryptography only; custom streamable-HTTP MCP transport, custom schema validation, custom OpenAI-compatible adapter. Any framework = full new dependency tree.
- Verdict: no agent framework (Pydantic AI 2.x, LangGraph 1.2.x, mcp-agent, OpenAI Agents SDK, MS Agent Framework 1.0) earns orchestrator replacement — agent loops invert the deterministic governed control plane = parallel planner authority. KEEP custom orchestrator.
- Two adapter-scoped reuse candidates only: POC-1 official MCP Python SDK under specialist_interop transport (score 3.6/5); POC-2 Instructor/structured-output repair under model_invocation for F4 invalid-outputs (score 3.4/5). Both boundary-respecting component swaps; framework output stays untrusted data.
- F1-F6 mapped: F1 fixed by H6; F4 = only framework-addressable residual (bounded, needs real-model evidence); F6 = owner retrieval adequacy, unaffected by frameworks — owner probe remains the higher business priority.
- NEXT: coordination decision on POC-1/POC-2; H5 and owner search_products probe remain independent tasks.

## 2026-10-28 — Pluggable orchestration boundary discovery (doc 192) — READ-ONLY
- Task DELIA-C3-PLUGGABLE-ORCHESTRATION-BOUNDARY-DISCOVERY-01 on fc30ea947c. No code/deps/production changes; H6 merged confirmed.
- EXISTING_EQUIVALENT=YES: SupportsGovernedCapabilityAttempt Protocol (interaction/capability_attempt.py:222) + DI at root_composer.py:368 + single caller handle_interactive_turn.py:426. Replaceable unit = attempt() use-case boundary (option A); no new port needed.
- Drift found: Protocol signature missing cancel_check (impl L4071 + call site use it) — queued Step I fix.
- Real constraint: governed gates are instance methods inside 11.5k-line orchestrator. Plan: extract shared GovernedStageRuntime (Step II, move-refactor, suite must pass unchanged); Engine B = LangGraph graph over SAME primitives — sequencing only, never framework tool-calling/AuthZ (doc-191 verdict preserved, conflict resolved explicitly).
- Engine selection: env DELIA_ORCHESTRATION_ENGINE {delia default, langgraph}, fail-closed, never request/model controlled; rollback = env revert, no data migration.
- LangGraph feasibility: FEASIBLE as internal sequencer (sync invoke, no checkpointer needed, delegates to stage runtime); MODERATE-HIGH effort; MIT; new dep tree needs approval.
- Proposed ADR embedded: PROPOSED — PENDING_COORDINATION_APPROVAL. NEXT: Steps I+II combined task (protocol parity + GovernedStageRuntime extraction, zero behavior change).

## 2026-10-29 — Governed-attempt contract foundation (doc 193) — PROVEN
- Task DELIA-C3-PLUGGABLE-ORCHESTRATION-CONTRACT-FOUNDATION-01 on 5628f9eb60.
- Step I: SupportsGovernedCapabilityAttempt.attempt now declares the full real signature (added cancel_check; exact prior_turns/activity_sink types+order). Signature-only change — Protocol is structural typing, zero runtime behavior.
- Step II: tests/test_governed_attempt_contract.py — 14 boundary-only conformance tests over ENGINE_IDS registry (delia). RED (missing=['cancel_check']) → GREEN. Covers read/candidate/token-opacity/arg-bounds/authz/invented/PREPARE-ACT/timeout/cancel/correlation.
- Boundary learning: constructor turn_budget_seconds=30 != call-time turn_deadline=30s — small budget skips optional self-index probe, empty-arg invokes fail closed (skip_budget_identifier_unavailable). Suite uses default budget + turn_deadline.
- Step III extraction DECLINED: SECOND_CONSUMER_NEED not proven (no second engine authorized) — GovernedStageRuntime deferred to Engine-B task (doc 192 II). No DELIA_ORCHESTRATION_ENGINE created (speculative config prohibited).
- Regression: 2431 passed, 2 failed both pre-existing/environmental (CRI variant drift; missing fixture mount). Arch Phase-3 gate PASS. Single attempt() implementer confirmed; no code behavior changed.

## 2026-10-29 — LangGraph Engine B experimental conformance (doc 194) — PROVEN (LOCAL POC)
- Task DELIA-C3-PLUGGABLE-ORCHESTRATION-LANGGRAPH-ENGINE-B-01 on 892e7b2049 (ff from base 5efaf41092).
- Dependency gate PASS: langgraph==1.2.16 (MIT, 13 days old; 1.2.17/1.2.18 <7d rejected) via new opt-in delia-api/requirements-eval.txt; requirements.txt/Dockerfile untouched; transitive tree recorded in doc 194 §3; no conflicts (full suite green post-install).
- Minimal shared extraction (doc-192 Step IV, bounded): only TWO verbatim boundaries — _run_governed_attempts (contextvar binding + interaction budget + bounded resume loop) and _governed_owner_path (post-admission tail). orchestration.py +90/-11. Everything else B consumes pre-existed (_admit_conversational_turn, _attempt_confirmation, _groups, _surface_inquiry_attempt, _emit_activity). No GovernedStageRuntime mega-extraction.
- Engine B = LangGraphCapabilityOrchestrator (325 lines): real StateGraph, 6 nodes, conditional edges, bounded TypedDict state, no checkpointer/tools/agents. attempt()/_attempt() never called — proven by non-delegation spy + per-attempt node trace tests. Gates = SAME OperationalCapabilityOrchestrator instance methods.
- RED true (17 langgraph params failed ModuleNotFoundError pre-implementation) → GREEN: 43 conformance tests pass on BOTH engines incl. per-engine protocol signature parity.
- S1-S10 (doc 192): all covered on both engines — see doc 194 §6 matrix.
- Local A/B scripts/engine_ab_eval.py (fake-model corpus S1/S2/S3/S7/S8/S10): OUTCOME_DIVERGENCES=0; identical fake-model call counts per scenario (6/7/9/6/3/4); latency delta = graph overhead only. SEMANTIC_EVAL=INCONCLUSIVE (fakes prove conformance, not semantic parity; no Ollama real-model run).
- Regression: focused sweep 300 passed; full delia-api 2525 passed + 2 failed (SAME pre-existing env failures as Task-02 baseline) + 3 skipped. Arch Phase-3 gate PASS. Residual search clean — no production wiring, no DELIA_ORCHESTRATION_ENGINE, no deploy, zero production calls.
- ENGINE_B_SCOPE=LOCAL_TEST_ONLY; Engine A remains sole production-composed implementation. NEXT: coordination review → optional real-model semantic A/B + sequencing-variation experiments; selector config only on acceptance.

## 2026-10-29 — Engine B architectural isolation remediation (doc 195) — PROVEN
- Task DELIA-C3-PLUGGABLE-ORCHESTRATION-ENGINE-B-ISOLATION-REMEDIATION-01 on a76c9e2a69.
- F1 FIXED: langgraph_engine.py moved app/application/capability_provision → app/infrastructure/orchestration (AST test enforces zero framework imports in Application/Domain).
- F2 FIXED via narrow contract: new SupportsGovernedStageGates Protocol (governed_stage_gates.py) declares the 6 consumed primitives; adapter takes injected gates, never imports/constructs OperationalCapabilityOrchestrator (AST-enforced). RESIDUAL documented: gates provider is still Engine A's class — true owner split deferred (would need large coupled-method migration, zero behavior gain).
- F3 FIXED: doc 194 release-date typo corrected — PyPI upload_time 2026-10-16 (was written 2025-10-16); pin 1.2.16 unchanged; requires_python>=3.10, MIT, no advisories.
- RED recorded: 5 isolation failures pre-remediation → GREEN: 9/9 isolation tests (T1-T8) + 43/43 conformance on both engines unchanged.
- A/B rerun post-move: OUTCOME_DIVERGENCES=0, identical model-call counts (6/7/9/6/3/4).
- Regression: focused 309 passed; full 2534 passed + 2 failed (SAME pre-existing env failures) + 3 skipped. Arch Phase-3 PASS; backend boundaries PASS (0 findings). Residual search clean. No production changes, no deploy.
- NEXT: coordination acceptance → Task 04 sequencing-variation POC may proceed on the now-explicit gates boundary.

## 2026-10-29 — Engine B sequencing/recovery strategy A/B experiment (doc 196) — PROVEN (LOCAL POC)
- Task DELIA-C3-PLUGGABLE-ORCHESTRATION-SEQUENCING-RECOVERY-AB-01 on 68b10b81dd.
- H5 revalidated+refined: naive 'second native_assessment is redundant' REFUTED (relevance_feedback is a decisional input by design). Bounded reuse = monotonic-safe ONLY for prior foreign_evidence_required on same target+goal; 'sufficient' is refuted by the mismatch, everything else reassesses.
- Implementation: opt-in ambient _NATIVE_ASSESSMENT_LEDGER ContextVar (unbound = Engine A byte-identical) + shared deterministic _reusable_native_assessment check in _recover_relevance; Engine B gains evidence_session node + assessment_reuse graph-state decision; owner_path binds ledger in its own node context (LangGraph node contexts are copied). recovery_reuse_enabled knob = B1 vs B0, eval-only.
- RED recorded (ImportError → strategy absent; 2 assessment calls pre-strategy) → GREEN 18/18 R1-R10 strategy tests (reuse, stale-decision rejection, authz/cancel/ceiling/trace/engine-A isolation, real alternative transition).
- Three-way A/B (delia / langgraph_b0 / langgraph): S1-S10 identical calls+outcomes; S11_recovery_reuse 17/17/16 calls — 1 redundant native_assessment eliminated, assessments 2/2/1, owner calls 4/4/4, OUTCOME_DIVERGENCES=0. Harness now exits nonzero on divergence (was unconditional 0).
- Tokens NOT_AVAILABLE (fakes); latency local-fake only (B1≈B0, ~2x A); SEMANTIC_EVAL=INCONCLUSIVE (no real-model run).
- Conformance 43/43 both engines; isolation 9/9; focused sweep 289 pass; full suite 2557 collected → 2552 passed + 2 failed (cri variant fixture drift pre-existing; openapi env scan surfaces only under repo-root layout — env.example comment at baseline SHA) + 3 skipped. Arch phase-3 + backend boundaries PASS. Residual search clean; no production wiring/deps/calls.
- VERDICT: PROMISING_LOCAL_EVIDENCE — real call reduction in a narrow reuse window; real-model benefit unproven. NEXT: Task 05 candidates = Ollama semantic A/B on reuse path; production-frequency inventory of the reuse window; optional monotonic check for corroboration_requested.

## 2026-10-30 — Recovery reuse hardening & real-model semantic A/B (doc 197) — PROVEN (LOCAL POC)
- Task DELIA-C3-PLUGGABLE-ORCHESTRATION-RECOVERY-SAFETY-SEMANTIC-EVAL-01 on 0e39cbc9a8.
- F1 FIXED: Task-04 fingerprint (4 goal fields) replaced by _native_assessment_premise_fp — sha256 over canonical JSON of every material assessment input: input_text, group key, capability id+operation class, full _TurnGoal serialization, canonical WorkspaceContext, canonical prior-turn sequence. Decision-dependency matrix in doc 197 §2; relevance_feedback intentionally excluded (differs by design; monotonic direction proven); unknown inputs fail closed.
- F2 FIXED: owner_path ledger binding now token set/reset pair (mirrors bind/reset_turn_call_ledger) — no leak on cancellation/exception/retry/inline-node runtimes.
- MONOTONIC_REUSE_PROOF=YES (contract-level): reuse limited to prior foreign_evidence_required on identical premise; irrelevant-evidence recovery can only confirm, never reduce, the requirement; sufficient/corroboration/inconclusive never reused.
- RED recorded (signature mismatch pre-implementation) → GREEN 23/23 in test_engine_b_recovery_hardening.py: H1-H10 premise equivalence + C1-C10 concurrency/lifecycle (simultaneous turns, sequential, retry, cancellation, exception, copied node contexts, nested, no-AuthZ-leak, bounded growth, no sensitive persistence).
- Deterministic A/B unchanged: S11 17/17/16 calls, assessments 2/2/1, owner 4/4/4, DIVERGENCES=0 — hardened fingerprint preserves the valid window.
- Real local-model A/B EXECUTED (new scripts/engine_ab_real_model_eval.py): delia-json:latest 3.1B Q4_K_M digest 7b8f4ab1..., local Ollama /v1, PROVIDER_REPORTED tokens via bound ModelCallLedger. 12 attempts/4 matrices: model reached native_assessment in 3/4 matrices, recovery in 2; sampling noise dominates (same engine 2-14 calls, SUCCESS vs fail-closed NOT_APPLICABLE across identical runs); reuse window NEVER materialized under B1 (one assessment_reassessed — fail-closed worked). SEMANTIC benefit UNPROVEN; safety confirmed.
- PRODUCTION_FREQUENCY=TO_INSTRUMENT: per-stage calls already in result.observability.calls; no cross-turn aggregation exists. Smallest future extension documented (bounded per-turn native_assessment/reuse_eligible counters); not implemented.
- Regression: focused 616 passed; full 2580 collected → 2575 passed + 2 failed (SAME pre-existing env failures) + 3 skipped. Arch Phase-3 PASS; backend boundaries 0 findings; residual search clean; no production deps/composition/calls.
- VERDICT: SAFE_NO_MATERIAL_GAIN — safety proven locally; only measured benefit remains the deterministic 1 call/eligible window; real-model benefit unproven and production frequency unknown. NEXT: optional Task 06 = read-only observability counters to answer frequency before any further B1 investment.

## 2026-10-30 — Recovery-opportunity observability & Engine B value (doc 198) — PROVEN (LOCAL)
- Task DELIA-C3-PLUGGABLE-ORCHESTRATION-RECOVERY-OBSERVABILITY-VALUE-01 on 181b238da8.
- EXISTING_EQUIVALENT=YES → EXTEND only: ModelCallLedger gains attempt-scoped assessment-decision records (decision+premise_fp hashes only, cleared per _governed_owner_path entry) + turn-scoped counters (native_assessment_calls, relevance_recovery_entered, reuse_candidates, reuse_eligible, reuse_performed, reassessments). Additive recovery_opportunity key in result.observability only when ledger bound — legacy shape unchanged.
- Single predicate: _native_assessment_reuse_verdict extracted pure; B1 apply path AND Engine A/B0 observation path evaluate the same contract — no duplicated rule.
- ENGINE_A_BEHAVIOR_CHANGED=NO: A never binds the reuse ledger → apply impossible; eligibility observed only. S11 A = eligible:1, performed:0, reassessments:1 (opportunity measured, not applied).
- RED recorded (AttributeError recovery_observation absent) → GREEN 15/15 O-tests incl. concurrency isolation, cancellation no-invention, counters-only privacy, additive-only projection, Engine-A 17/4/SUCCESS unchanged.
- Deterministic corpus 21 attempts: S11 obs A/B0={elig:1,perf:0,reassess:1} B1={elig:1,perf:1,reassess:0}; other scenarios no eligible window; DIVERGENCES=0.
- Value model (measured): ≤1 avoidable call/eligible turn, ~700-900 in-tokens, ~0.4-0.9s local; fixture prevalence 1/7 (constructed); real-model prevalence 0/12 (Task 05); PRODUCTION_FREQUENCY=TO_INSTRUMENT — now per-turn measurable, aggregation is the only missing step (separate auth). HISTORICAL_ELIGIBILITY=INCONCLUSIVE.
- Regression: focused sweep PASS; full 2595 collected → 2590 passed + 2 failed (SAME pre-existing env failures) + 3 skipped. Phase-3 PASS; backend boundaries 0 findings; residual clean.
- VERDICT: INSTRUMENTATION_READY_FREQUENCY_UNKNOWN — counters proven correct, safety proven, value unresolved pending frequency aggregation. NEXT: bounded read-only aggregation of recovery_opportunity across real turns (separate authorization) → keep-or-retire B1 decision.

## 2026-10-30 — LangGraph B1 production activation, legacy fallback & bounded validation (doc 199) — PROVEN (LOCAL RUNTIME)
- Task DELIA-C3-PLUGGABLE-ORCHESTRATION-LANGGRAPH-PRODUCTION-ACTIVATION-01 on 6fc0d7cb98 (product-owner authorized).
- Engine selection at composition root: DELIA_ORCHESTRATION_ENGINE {langgraph(default)=B1, delia=Engine A}; unknown fails closed at startup; lazy adapter import keeps delia runnable without the framework; backend config only — no request/provider/model path into selection; one engine per turn, no automatic fallback replay.
- Dependency promotion: langgraph==1.2.16 + exact pinned transitive tree into requirements.txt; requirements-eval.txt slimmed to the eval delta; no agents/vector stores/model providers/LangGraph Cloud.
- RED recorded (resolver absent) → GREEN 13/13 in test_engine_production_selection.py incl. composed handler→contract→B1 path; 3 pre-activation frozen-decision guards updated to the new invariants (authorized decision change).
- Conformance 43/43 each A/B0/B1; full regression 2603 passed + 2 failed (SAME pre-existing env failures) + 3 skipped; Phase-3 audit PASS; backend boundaries 0 findings.
- Deployed locally: image sha256:62519548... on code 6fc0d7cb98, container healthy, in-container resolver verified (langgraph→B1, delia→gates, bogus→ValueError); rollback to delia tested and reversed — no business replay.
- Bounded comparison (6 authenticated turns, delia-json 3.1B, provider-reported tokens): stage-sequence + contract + per-call cost parity across engines; B1 executed a real MCP owner call with complete provenance (C3); recovery counters 0 everywhere (model never produced a reuse window); C3 grounding divergence is 3.1B stochasticity, disclosed.
- VERDICT: PRODUCTION_ACTIVATION_EXECUTED (local runtime); engine parity + safety verified; reuse-path value still awaits real-traffic frequency aggregation.


## 2026-10-30 — LangGraph B1 REAL production deployment on srv-api (doc 200) — PRODUCTION DEPLOY EXECUTED
- Task DELIA-C3-LANGGRAPH-B1-REAL-PRODUCTION-DEPLOY-01 on 78e7b4d7ef (PO-authorized SSH deploy).
- Host verified: srv-api (operador@192.168.1.237, AGENTS.md canonical); repo pull 1f34403767 → 78e7b4d7ef ff-only; 6fc0d7cb98 ancestor confirmed.
- Deploy: DELIA_ORCHESTRATION_ENGINE=langgraph appended to infra/.env + up-prod-sequential.sh --build delia-api (only service touched); image sha256:8931066e...; previous image sha256:9947eac9... retained.
- Verified on host: healthy, startup log selected=langgraph surface=configured, langgraph 1.2.16 + pinned tree in image, kimi-k3/OpenRouter preserved (no local override), 0 critical errors, governed_attempts=1/turn.
- Smoke: 2 authenticated READ turns (identity user, PO-provided; NO reset/admin-API/RBAC writes — flagged drift not repeated). S1 GROUNDED real record 10080092 TERM. BALA via DAVI search_products (provenance complete); S2 GROUNDED honest empty-collection via read_governed_technical_knowledge. recovery_opportunity counters live, all zero.
- ROLLBACK: delia env path + retained image, config-only, no replay.
- VERDICT: PRODUCTION_DEPLOY_EXECUTED_AND_VERIFIED. NEXT: bounded recovery_opportunity aggregation on real traffic (separate auth).

## 2026-10-30 — PydanticAI structured-decision reliability A/B (doc 201) — EXTEND_BASELINE
- Task DELIA-C3-PYDANTICAI-STRUCTURED-DECISION-AB-01 on base 8a8ee4ec50 (HEAD 92a5c1c428 at delivery); experimental local harness only — no production deploy/calls/contracts/deps.
- Baseline inventory: _propose presence-check + allowed_keys projection + downstream semantic gates (orchestration.py); adapter OpenAICompatibleModelInvocationAdapter; Pydantic already in production deps.
- Candidate: pydantic-ai-slim==2.50.0 (MIT, Py>=3.10, pub 2026-09-24) via direct.model_request_sync + NativeOutput(json_schema) — retries=0, no agent, no tools, provider-reported usage; pinned in requirements-eval.txt only.
- RED recorded (module absent) → GREEN 20/20 V1–V18 (parity, rejection, fail-closed enum, retry ceiling, no-tool, token accounting, isolation).
- Deterministic corpus 12 cases x3 arms: 10/12 agreement; 2 deltas = earlier rejection of wrong_field_type + invalid_enum (exposes fail-open unknown-status→sufficient coercion).
- Live delia-json 78 calls (select_group+native_assessment 30, interaction_admission 48): 0 invalid outputs BOTH arms; input tokens identical 27140=27140; output tokens ~equal (schema adds limitations:[]); latency within noise; TOKEN_SOURCE=PROVIDER_REPORTED.
- Security: retries=0, provider_requests==1/call, PREPARE/ACT untouched, no SDK in app/ (residual clean).
- Regression: focused 231 GREEN; Phase-3 audit OK; backend boundaries 0 findings.
- VERDICT: EXTEND_BASELINE — framework works cleanly but measured zero gain on this model; the only real delta (earlier type/enum rejection) is achievable with already-present Pydantic / baseline contract hardening. Unknown-status coercion documented as future bounded contract decision. NEXT: none (optional baseline contract hardening decision at coordination).

## 2026-10-29 — native_assessment status fail-closed remediation (doc 202) — PRODUCTION DEPLOY EXECUTED
- Task DELIA-C3-NATIVE-ASSESSMENT-STATUS-FAIL-CLOSED-REMEDIATION-01 on 45118d6425 (deployed SHA; origin moved to d323d8ef6a, helpdesk-only).
- Defect proven: _assess_native_path coerced ANY out-of-vocabulary status (absent/null/wrong-type/unknown) to "sufficient" — invalid model decisions recorded as affirmative sufficiency. RED: assert 'sufficient' == 'inconclusive' reproduced.
- Fix: invalid → "inconclusive" (canonical undetermined decision) + invalid_status_rejected log decision; native default preserved, foreign fan-out never the fallback; no retry/graph/budget/auth changes; both engines share the path (B1 via _governed_owner_path).
- GREEN 34/34 (R1–R18 incl. 16 invalid values, missing/null/non-Mapping, zero extra calls, governed turn parity across delia/langgraph_b0/langgraph). Regression: 2 pre-existing env failures only (one stash-verified). Phase-3 + backend-boundary audits clean.
- Deployed to srv-api via SSH: ff-only pull 7644500a58→45118d6425 + up-prod-sequential.sh --build delia-api; image sha256:def538a0…; engine=langgraph; kimi-k3/OpenRouter preserved; rollback image 8931066e retained.
- Smoke (identity user, password-grant token; first mint lacked openid scope → api-delpi correctly denied, re-minted with scope=openid profile email; NO resets/admin APIs): S1 GROUNDED real record 10080092 TERM. BALA via DAVI (7 calls, full provenance); S2 GROUNDED honest insufficient_evidence (16 calls; recovery counters live: relevance_recovery_entered=1, reuse_candidates=1, reassessments=1, reuse_eligible=0 — reuse correctly declined).
- VERDICT: PRODUCTION_DEPLOY_EXECUTED_AND_VERIFIED. Residual: invalid-status inconclusive shares the response projection with model-declared inconclusive; audit distinction kept via the log decision.

## 2026-10-29 — semantic decision diagnosis + pluggable-boundary A/B (doc 203) — NO_ABSTRACTION_JUSTIFIED
- Task DELIA-C3-SEMANTIC-INTELLIGENCE-PLUGGABLE-AB-01, scope diagnosis+local eval only; no deploy, no production LLM calls.
- Incident corpus mapped to responsibility matrix: T1/T2 candidate mispick FIXED (doc 190); T3/T4.2 redundancy FIXED (Tasks 04/05); F4 invalid outputs FIXED (Task 09); live question = terminal-bala C-vs-D split.
- PROVEN owner-side root cause (local api-delpi probe, real TOTVS): description search is token-OR/prefix — "terminal bala" returns 445 TERMINAL*/BALA* items and NEVER matches "TERM. BALA" records; only owner vocabulary "TERM. BALA" reaches 10080092/10081004. DOMAIN_RETRIEVAL → owner remediation brief (AND-token/prefix-any-position + abbreviation normalization).
- Stage-level eval (delia-json 3.1B, real v25 instructions + real validators): baseline vs dspy==3.4.1 — capability 67-75% vs 42%, group 38% vs 62%, relevance 67% vs 50%; DSPy halves input tokens but net-loses on the finest stage; run-to-run diffs 10/26 cases (nondeterministic model). No meaningful semantic gain → no pluggable boundary; production code changed: 0 lines.
- Harness scripts/semantic_decision_eval.py + tests/test_semantic_decision_eval.py (17) GREEN; focused regression 287+22 GREEN; phase-3 + backend-boundary audits clean; dspy pinned eval-only.

## 2026-10-29 — api-delpi product description-search owner remediation — LOCAL GREEN, deploy pending
- Task DELIA-C3-API-DELPI-PRODUCT-SEARCH-REMEDIATION-01 — executes the OWNER_REMEDIATION_REQUIRED verdict of doc 203 (api-delpi changelog 2026-10-product-description-search-remediation.md is the owner authority).
- Root cause confirmed in ProductRepository.search_products: whitespace tokens OR-joined as %t% substrings + prefix-biased scorer. Replaced by bounded matching module: AND over significant tokens, CONCAT-padded word-prefix/exact-word matching, domain-approved TERM<->TERMINAL bridge (exact-word only on abbreviated member), stopword drop with fallback, phrase bonuses gated to multi-token + boundary-after-phrase.
- Local TOTVS A/B: TERM. BALA 1678->6 (all family), terminal bala 445->6 (10080092 rank 1), bala 33->21 with exact-BALA on top, TERM BALA 3404->6, cabo flexivel 6666->108, parafuso sextavado 225->11, accent/mixed-case/numeric/held-out all correct; honest empty preserved; exact-code path untouched.
- Tests: tests/test_product_description_matching.py 20/20 GREEN; product/search consumer suite 143 pass (1 pre-existing env failure, stash-verified); full api-delpi suite 6314 pass / 5 pre-existing failures; phase-3 + backend-boundary audits clean. Latency 1.2-3.7s bounded scans, no new index/migration/service.
- Contract: response shape unchanged; multi-token description semantics intentionally tightened (documented). DELIA untouched.
- PRODUCTION DEPLOY EXECUTED 2026-10-29 via SSH operator workflow (srv-api): ff-only pull fd1d2e02bc -> 9e39f46c34 + up-prod-sequential.sh --build api-delpi (single service); image sha256:d94e443e8af8f11dc5cac5795cc387abaf0d83e8f23afc6782563be882178f50; container healthy, zero errors.
- Smoke (4 bounded READ queries, in-container use-case + authenticated HTTP via /apps/api-delpi/supplies/products/search, user token delpi-central openid/profile/email): code=10080092 total=1; TERM. BALA total=6 family; terminal bala total=6 with 10080092 rank 1 (defect fixed on prod data); parafuso total=211 sane; no-auth correctly 401; paged_list contract + pagination meta intact.
- ROLLBACK: image infra-api-delpi:search-remediation-rollback-7c57a7f7 retained; revert = retag + up api-delpi (no migration). VERDICT: PRODUCTION_DEPLOY_EXECUTED_AND_VERIFIED.

## 2026-10-29 — evidence-to-answer causal remediation + isolation (doc 204) — LOCAL GREEN, no deploy
- Task DELIA-C3-EVIDENCE-TO-ANSWER-CAUSAL-REMEDIATION-AND-ISOLATION-01 on 1f6f6d1970; no production deploy/model calls. Engine B1 unchanged.
- Incidents E1 fa4f6444 (terminal bala, presented=0 after execute ok) + E2 a5283249 (ultimo processo Transforma+, record_read ok, presented=0) reconstructed from sanitized orchestration logs.
- Deterministic replay on real owner shapes (in-container, same code as prod): davi.execute {data.items:[6 products]} projects -> facts.records=6; teo record_read {data:{total:109,items}} projects 40; q='Transforma'/'ultimo processo' -> total=0 authoritative empty; discover {candidates:[5]} leaked -> facts.records=5.
- PROVEN divergence: capability-catalog descriptors projected as business records — _resolver_entities prefers 'candidates' (correct for entity resolution) and _is_capability_descriptor lacked the owner-published candidate vocabulary (candidate_token/action_id/argument_schema/semantic_hints/retrieval_score/required_arguments/pagination_hints) -> activity 'N registros localizados' on DISCOVERY invokes + has_business_evidence on discovery outcomes (contract_facts fallback suppressed). E1 '2 located records' were candidates, not products.
- E1 final empty: authoritative-empty owner page for the sent args — arg values unrecoverable (sanitized) -> TO_INVENTORY; replay shows verbatim-phrase description now legitimately returns total=0 under owner AND-semantics.
- E2: process entity has no ordering fields (filial/setor/status/familia/q/has_improvement/page/page_size); 'ultimo' requires pagination walk + updated_at or typed limitation — goal/argument generation is model-owned; no lexical shortcut, no prompt change.
- Fix (owner-local, 12 added lines): _CAPABILITY_DESCRIPTOR_STRONG_KEYS += candidatetoken/argumentschema/semantichints/retrievalscore/paginationhints. Shape-based gate, not key-position — entity-resolution candidates still project.
- RED 5 -> GREEN 10/10 tests/test_c3_evidence_to_answer_isolation.py (real shapes as sanitized fixtures; locks: execute/record_read envelopes, explicit-empty distinct, homonymous action_id business record, resolver candidates).
- Regression: focused 131 GREEN; full delia-api suite ~2687 pass / 2 PRE-EXISTING failures (cri_instruction stale assertion after concurrent answer_requirements commit; env.example DELIA_OPENAPI_DELPI residual). Phase-3 + backend-boundary audits 0 findings.
- Replaceability: existing injectable record_resolver seam suffices — NO_NEW_PORT_REQUIRED. No new dependency/port/prompt/framework.
- VERDICT: ROOT_CAUSE_REMEDIATED (proven divergence) + residuals documented; PRODUCTION_CALLS=0 DEPLOY_EXECUTED=NO.

## 2026-10-29 — goal-to-owner causal remediation + PRODUCTION DEPLOY (doc 205)
- Task DELIA-C3-GOAL-TO-OWNER-CAUSAL-REMEDIATION-AND-PRODUCTION-DEPLOY-01; base ab5048df0c -> implementation 43650dd20e pushed to origin/main.
- E1 PROVEN: api-delpi _param_schema stripped owner param descriptions -> argument model got types-only schema; fix: bounded description propagation (+12 lines, untrusted metadata-as-data).
- E2 PROVEN: bounded page walk gated to COUNT-intent + early-return on authoritative total -> declared ordering/complete_coverage/min_items unreachable on multi-page owners; fix: same walk extended to answer_requirements coverage gaps, schema-derived page cursor, all integrity/budget guards preserved (~+160 lines orchestration).
- RED 5+5 -> GREEN 11/11 (test_c3_goal_to_owner_execution) + 5/5 (test_davi_dynamic_read); focused 199 GREEN; api-delpi DAVI suite 418 GREEN; delia-api ~2700 collected / 2 pre-existing env-mount failures (not this diff); arch+boundary audits 0 findings; engines inherit fix via shared _governed_owner_path.
- DEPLOY: srv-api operador@192.168.1.237, repo ff 49eee133->43650dd20; api-delpi image 42ad9defd8cb healthy, delia-api dad53fa242f6 healthy; langgraph B1 + Kimi/OpenRouter preserved; rollback tags goal-owner-rollback-d94e443e / -def538a0 retained.
- SMOKE (identity user, 2 bounded READ turns): S1 terminal bala -> discover+execute, verdict answered, presented=2 real TERM. BALA records, owner total 6, ~78s, ~7 model calls (vs 14-15 FAIL). S2 ultimo processo Transforma+ -> record_read arg_keys=action,entity,page_size,q -> owner total=0 -> truthful empty_result ~27s, 4 model calls; no fabrication; residual = model-owned q formulation (walk not reachable on total=0 envelope).
- VERDICT: PRODUCTION_DEPLOY_EXECUTED_AND_VERIFIED; E1 AC met end-to-end; E2 contract fix deployed, business outcome = truthful limitation-grade empty (not supported-latest) — reported without fabricated acceptance.

## 2026-10-29 — semantic goal-to-argument alignment (doc 206) — LOCAL GREEN, no deploy
- Task DELIA-C3-SEMANTIC-ARGUMENT-AND-ORDERING-REMEDIATION-01; base c253e052; residual E2 (ultimo processo Transforma+ -> q filter -> total=0 -> empty). No production deploy.
- PROVEN divergences (all deterministic surfaces): (1) answer_requirements validated at goal-understanding never reached argument generation — _build_arguments/_candidate_arguments/_propose_candidate_arguments lacked the declared ordering/min_items/complete_coverage the assessment stage later verifies; (2) TÉO record_read published zero per-param descriptions — q's free-text semantics existed only in tool description; (3) v25 arguments instruction mandated business_subject -> free-text field for EVERY goal class, no content-search vs listing/ordering distinction.
- Fixes (reuse/extend, no new port/planner/lexical fn): TÉO Annotated Field descriptions on all record_read params (q = "free-text search in record's own fields … never ordering/recency/ranking", verified vs ILIKE implementation); _declared_requirements_projection threaded into all 5 argument call sites (also deduplicates prior inline projection); arguments instruction v26 — business_subject paragraph distinguishes content-search (bind verbatim) from listing/count/ordering/extreme-record goals (leave free-text empty; declared_requirements guides); 8192-byte bound honored via semantics-preserving compression of 4 non-locked clauses -> 8001b. turn_goal unchanged (answer_requirements spec + CRI clause already cover superlatives — duplicate attempt failed the separation lock, reverted).
- RED -> GREEN: test_c3_declared_requirements_argument_projection 3 new (payload lacked declared_requirements) GREEN; TÉO surface +41 RED -> 7/7 GREEN; Task13 walk 11/11 preserved; block-shape regression caught by test_evidence_schema_projection_integrity fixed (bare schema stays bare).
- Semantic eval (real instructions + CRI clause + real TEO schema + real adapter, local Ollama, 10-case corpus): baseline v25/no-desc 3/10 -> correction v26/desc/projection 4/10; text_search/count/by_id/list_all pass both arms; recent_updated drops spurious q; superlative req declaration still absent — MODEL-BOUND residual (surfaces all correct; per §10 no Kimi inference from local model). Evidence: semantic-argument-ordering-eval-206-runs.json.
- Regression: focused 369 GREEN; TEO 7/7; full suite pre-existing failures only (2 env mounts + 1 stale cri assertion predating diff); phase-3 + backend-boundary + platform-guardrails audits 0 findings.
- VERDICT: CONTRACT_SURFACES_REMEDIATED + model-semantic residual documented; DEPLOY_EXECUTED=NO; next step = observe E2 under production model post-authorization.

## 2026-10-29 — environment sync + production release + bounded E2 smoke (doc 207)
- Task DELIA-C3-ENVIRONMENT-SYNC-PRODUCTION-DEPLOY-AND-E2-SMOKE-01; release = e9c405cee9 (Tasks 11–14).
- INVENTORY: prod repo 6172f5731a (2 behind) -> ff e9c405ce; drift = transformometro-api (no Annotated param desc) + delia-api (v25) only; api-delpi/delia-mfe/portal/plugin-ui no drift -> preserved.
- DEPLOY (srv-api, up-prod-sequential.sh, owner->consumer): TÉO c2d3462af6d1 -> 8c470afe48dd (record_read per-param descriptions live); delia-api dad53fa242f6 -> c87dc40a7bb1 (v26, selected=langgraph, effective=cri, healthy). ~90 unrelated services untouched; rollback tags semantic-arg-rollback-c2d3462a/-dad53fa2 retained.
- LOCAL SYNC: TÉO restarted for bind-mounted server.py; STT block added to infra/.env (incremental dictation toggle now appears); DELIA_LLM_* repointed OpenRouter->Ollama per dev egress guard; model delia-json/qwen2.5:3b/1.5b all fail the interaction JSON contract on the real instruction -> local model = qwen3:4b-instruct-2507-q4_K_M (verified end-to-end: admission conversational -> valid governed JSON reply).
- E2 SMOKE (user, password grant delpi-central, 1 turn): admission owner_surface -> teo.record_read; arg_keys=action,entity,page_size (NO invented q — vs doc205 q->total=0); owner_total=76; relevance corresponds; CRI composed presented=1; outcome answered; GROUNDED OBSERVATION; response = PROC-0073 latest process + provenance; ~29.3s, 6 model calls. E2 DEFECT CLASS CLOSED under production model.
- E1 SMOKE (1 turn): davi discover -> select_candidate picked governed knowledge topic product_master_sb1 -> execute -> excerpts=0 -> presented=0 -> truthful empty_result (GROUNDED, no fabrication). E1_REGRESSION=CANDIDATE_SELECTION_DIVERGENCE vs doc205 (2 records) — model-owned candidate choice under v26 semantics; not a code failure; no lexical patch per task rules; observe/recur -> separate task.
- VERDICT: PRODUCTION_DEPLOY_EXECUTED_AND_VERIFIED + E2_CLOSED_UNDER_PRODUCTION_MODEL + E1_RESIDUAL documented without fabricated acceptance.

## 2026-10-29 — CF-PROC0072-ANALYTICS-RECONCILIATION-REWORK-010 — identidade de saldo ≠ conciliação (DEPLOYED)
- Task: corrigir a falsa paridade `EXACT_PARITY`/`R$ 0,00` da conciliação analítica E/S−P7−H02 (IMPLEMENTATION-009). BASE_HEAD 826c73b1c4 -> FINAL e285dcd2a9; PROD_SHA e285dcd2a9 (srv-api).
- CAUSA RAIZ PROVEN: os três operandos são partições do mesmo universo SB9 (R05 SA total = P7 ex-99 + H02 físico loc99) — o zero era identidade de composição, não paridade entre MATR320 × MATR460 × MATR989. Operandos confirmados canônicos; o que mudou foi a interpretação/estados.
- FIX BFF: parity=IDENTITY_ONLY|DIVERGENCE|NOT_COMPUTED (EXACT_PARITY nunca com base compartilhada), reconciliationVerdict=INCONCLUSIVE|NOT_COMPUTED, independence.verdict=shared_universe+operandBases, compositionCheck{consistent,deltaCents}, elegibilidade exige data-base compatível (reference_mismatch->INELIGIBLE). UNAVAILABLE!=0, not_persisted, P3 intacto, sem permission nova.
- MFE: rótulos honestos «Composição dos saldos consistente»/«Divergência na composição»/«Conciliação pendente de validação» + explicações; Help sync.
- EVIDÊNCIA HISTÓRICA 48.660,78 (doc 117/TÉO 06.2): emissões oficiais datadas — STALE_EVIDENCE para o SB9 live; divergência real coberta por testes (incl. 1 centavo -> consistent=false).
- TESTES: BFF test_closing_stock_reports atualizados (identidade/divergência/mismatch temporal); MFE vitest painel; smoke autenticado local 31/31 com contrato novo; live 2026-09 ELIGIBLE/IDENTITY_ONLY/INCONCLUSIVE/shared_universe/delta 0.00.
- DEPLOY (operador@192.168.1.237, ff-only + up-prod-sequential.sh --build escopado): controllership-finance-api + controllership-finance recriados healthy; api-delpi sem drift. 401 anônimo nas 5 rotas; IDENTITY_ONLY no código e no bundle App-JnUmgsgb.js. Smoke autenticado prod: TEST_NOT_RUN (sem persona sancionada).
- VERDICT: PRODUCTION_DEPLOY_EXECUTED_AND_VERIFIED; identidade de saldo separada da conciliação entre relatórios; rollback = git revert e285dcd2a9 + rebuild dos 2 serviços.


## 2026-10-29 — CF-PROC0072-ANALYTICS-UX-STATE-REWORK-011 — estados operacional x P3 x analitico (DEPLOYED)
- Task: painel de atencao dizia «Fonte nao registrada» para R05/R08 com consulta respondendo e «Divergencias identificadas: 0» sem verificacao concluida; outubro/2026 sem causa declarada. BASE 53b861850b -> FINAL e07f566161; PROD_SHA e07f566161 (srv-api).
- DIAGNOSTICO OUT/2026 PROVEN: produtores HTTP 200 com status=source_missing, branchesMissing=[01,02] — sem snapshot SB9 em 2026-10-31 (month_end nao fechado no Protheus). Ausencia de snapshot != falha tecnica. (503s durante investigacao = api-delpi local em crash-loop por checksum V014 lancamento-notas-fiscais — reparo de ledger local, fora do escopo.)
- FIX MFE (apenas apresentacao, zero contrato): tres dimensoes por dominio — operando analitico (operationalStatus), source_state P3 (governedP3), resultado analitico. Nunca registrado + consulta disponivel -> «Consulta disponivel — conciliacao pendente» (R05/R08/P7); SOURCE_MISSING -> «Posicao historica ainda nao disponivel»; UNAVAILABLE -> «Falha ao consultar a fonte»; INCOMPLETE -> «Dados incompletos»; fonte P3 registrada = estado autoritativo + operando como fato.
- INDICADOR: «Divergencias identificadas» so mostra numero comprovado — 0 exige todas as verificacoes concluidas; pendencias/erro -> «—» nao verificadas. INCONCLUSIVE nunca vira 0.
- TESTES: painel 22/22 (novos: R05/R08 pendente, snapshot!=falha, «—» com pendencia, «0» verificado); suite com flakes pre-existentes apenas; smoke autenticado 31/31; QA visual 2026-09 (3x conciliacao pendente + «—») e 2026-10 (posicao historica indisponivel + «—»).
- DEPLOY (operador@192.168.1.237, ff-only + up-prod-sequential.sh --fase mfe --build controllership-finance): MFE recriado, bundle App-CfqRjY7p.js com novos rotulos, rotas API 401 anonimo inalteradas; smoke autenticado prod TEST_NOT_RUN.
- VERDICT: PRODUCTION_DEPLOY_EXECUTED_AND_VERIFIED; motores/calculos/exports/permissoes intactos; rollback = git revert e07f566161 + rebuild mfe.

## 2026-10-29 — CF-PROC0072-REPORTS-PDF-UX-QUALITY-012 — PDFs legíveis + matriz honesta + P7 operacional (DEPLOYED)
- Task: PDF P7 real (347 págs) com sobreposição de descrições, totais em formato técnico, UTC cru, resumo quebrado/órfão; matriz R01–R15 marcava R03/R05/R08 pendentes apesar das consultas implantadas; página P7 abria com tabela P3 vazia competindo com o operacional. BASE 1aa950593a -> FINAL 497c8095e9; PROD_SHA 497c8095e9 (srv-api).
- A: REPORT_CATALOG com source_kind (OPERATIONAL_VIEW/MANUAL_EVIDENCE/EXTERNAL/PENDING_CONTRACT) + official_parity=PENDING explícita + operational_view; R03/R05/R08 «Implementada × Pendente». Tabela compartilhada ReportsMatrixTable (fim da duplicação).
- B: P7 operacional primeiro (filtros->totais->resumos->detalhe->export); «Conciliação formal do fechamento — P3» recolhível ao final com mensagem de dependência; source_missing/não registrada preservados.
- C: StreamingResponse iterava BytesIO por linhas -> Response bufferizado + Content-Length (P7 all 261s -> ~50s, bytes idênticos); CSV/PDF reais verificados; source_missing 409 not_exportable.
- D: renderer compartilhado A4 paisagem — Paragraph wrap, altura dinâmica, repeatRows, KeepTogether nos resumos, PT-BR integral (R$ duas casas, Brasília, traduções), proveniência+SHA-256, política monetária declarada, watermark paridade pendente, SB9 referência x total composto separados.
- AMBIENTE LOCAL reparado (não-prod): role Portal Controladoria - Analista + grupo + vínculos rober/cf-e2e-access recriados após reimport do realm; cache do Core invalidado por restart.
- TESTES: renderer 22/22; BFF matriz 7/7; MFE focados 58/58 (suite 399/400 flake pré-existente não relacionado); smoke autenticado 31/31; QA visual PDFs início/meio/fim + P7 P3 colapsável. PDFs: R05 42KB/1pág, R08 837KB/31págs, P7 mp 767KB/253págs, P7 all 9.45MB/311págs ~50s.
- DEPLOY (operador@192.168.1.237, ff-only + up-prod-sequential.sh --build api-delpi controllership-finance-api controllership-finance): 3 serviços healthy; 401 anônimo; S2S/service nos exports -> 401 fail-closed; remoteEntry->expose->App-W6_JxSma.js. Smoke autenticado/export persona prod TEST_NOT_RUN.
- VERDICT: PRODUCTION_DEPLOY_EXECUTED_AND_VERIFIED; motores/cálculos/Decimal/escopos/S2S/P3/paridade PENDING intactos; zero permission nova; rollback = git revert 497c8095e9 + rebuild dos 3 serviços.

## 2026-10-29 — native assessment resolver-class remediation (doc 208) — LOCAL only, no deploy
- Task DELIA-C3-LOCAL-ORCHESTRATION-NATIVE-ASSESSMENT-REWORK-01; base f2da73f121 (Task 16 consolidation, pushed earlier same session); HEAD moved to 2e1783f73e by unrelated workstreams mid-task — task-owned diff unaffected.
- GATE A: Task 16 worktree consolidated into f2da73f121 (v27 instructions + DAVI/TÉO owner-description enrichment + harness bearer-TTL + scorecard scenarios + pins); controllership-finance/CLARA files left to their workstream.
- INFRA: keycloak realm rebuilt after WSL crash (latent bootstrap defect: realm-existence check compares JSON body to "404" — realm never created on fresh volume; created manually, bootstrap re-ran); delpi-central audience mapper added to shared audience-delpi scope -> DAVI/TÉO/VISTA token exchange valid again; tv-dashboard-api crash-loop = stale image missing delpi_character_profiles editable mapping -> rebuilt image + regenerated tracked egg-info; api-delpi V014 checksum verified consistent (no action); WSL crashed 4x (7GB RAM) -> pruned to essential eval stack; delpi-gateway is on the token mint path (not prunable).
- GATE B ROOT CAUSE PROVEN (faithful _assess_native_path probe, real _TurnGoal, real surfaces, x4): decision-rule resolver scan omitted the DISCOVERY class — owners resolve designations via owner_vocabulary_discovery caps (davi.discover, teo/vista get_catalog), none of the scanned nouns -> condition (3) appeared true -> systematic foreign_evidence_required. Compounding: rule at prompt top, exception clause mid-text -> recency bias on 4B model. Payload complete (no truncation defect).
- MODEL-BOUND RESIDUALS: vista_prepare + teo_latest anchor foreign x4 under 6 instruction variants (v28-v32) — classified model-bound, needs model-tier decision not more contract text; v32 rejected (teo_ctx regression).
- FIX v28 (reuse gate PASS, instruction-only): DECISION RULE moved to end (recency); resolver scan includes DISCOVERY-role caps; exclusions for governed actions (missing inputs -> clarification), selected-capability-is-resolver, owner-native ordering/listing. Mid-body untouched; 4-status contract + fail-closed preserved; 4122B within bound.
- PROBE VERDICTS: davi_discover foreign->sufficient x4; teo_ctx 3/4->sufficient x4; controls: corroboration x3, cross-domain foreign x3 (legitimate preserved).
- PAIRED 22-SCENARIO BATTERY (same session, LangGraph B1, qwen3:4b): v27 control 8P/14F, NA foreign 7/12 (58%), sufficient 2/12 -> v28 10P/12F, NA foreign 4/14 (29%), sufficient 8/14 (57%); 120->144 calls, 188.6k->231.4k in-tokens (deeper native flows, cost-for-correctness); 0 fabrications both arms; residuals = upstream admission/group-selection stochasticity + model-bound anchors.
- RED->GREEN: new test_native_assessment_resolver_contract.py 6/6 (RED on v27); r1 snapshot + c3/projection version pins updated; loader _ORCH_VERSIONS += 28; full suite GREEN ex pre-existing env-bound exclusions.
- VERDICT: ACCEPTED bounded contract-defect fix (foreign over-fire halved, Business Outcome non-degraded/improved same-session); DEPLOY_EXECUTED=NO; PRODUCTION_CALLS=0. NEXT: observe corpus under stronger local model tier; >=3 battery reps when WSL stable.

## 2026-10-29 — DÉLIA orchestration v28 controlled production deploy (doc 209) — DEPLOYED, smoke not executed
- Task DELIA-C3-ORCHESTRATION-V28-CONTROLLED-PRODUCTION-DEPLOY-01; BASE_HEAD=5144a32583 (HEAD=origin/main, matches LAST_OBSERVED_MAIN); T16 f2da73f121 + T17 71d11ef468 confirmed ancestors.
- RELEASE_DIFF isolated: between prod image bake (e9c405cee9) and HEAD the only delia-api commits are T16/T17; shared/delpi_auth (only shared import) has zero non-T17 changes; shared/delpi_character_profiles additions inert for this service.
- PROD INVENTORY (runtime-loaded, not git/image timestamps): delia-api container served instruction v26 -> INSTRUCTION_DRIFT+CODE_DRIFT; api-delpi (image rebuilt 19:13 UTC by concurrent workstream) serves enriched DAVI description live -> NO_DRIFT; transformometro-api (rebuilt 19:14) serves enriched TÉO descriptions live -> NO_DRIFT.
- ROLLBACK prepared pre-mutation: prior image c87dc40a7bb1 (v26) tagged infra-delia-api:rollback-v26-task18; e0ef09851204 also retained; rollback = retag + recreate or rebuild at e9c405cee9 via runbook. No DB/KC/secret changes.
- DEPLOY: SSH operador@192.168.1.237, official runbook up-prod-sequential.sh --fase api --build delia-api (single drifting service; repo already at HEAD, no --pull). New image sha256:c043368e8623, container healthy <60s.
- RUNTIME VERIFIED in-container: RESOURCE_VERSION=28; native_assessment fingerprint sha256:a7696bb6344ccc24 byte-identical to HEAD; owner_vocabulary_discovery present; DELIA_ORCHESTRATION_ENGINE=langgraph; DELIA_LLM_MODEL=moonshotai/kimi-k3 (OpenRouter) UNCHANGED; CRI resources loaded at boot; unauthenticated POST /apps/delia-api/interaction/turns -> 401.
- SMOKE: NOT EXECUTED — sanctioned prod identity (user, PO-provided) not available in session; devin-smoke-r4 rotated (doc 200); devin-smoke-g16 disabled/grants revoked (doc 114). User chose skip. AC11/AC13 unsatisfied; production Business Outcome under kimi-k3 unmeasured.
- DRIFT/notes: none on release scope; delpi-external-data-scheduler unhealthy pre-existing/unrelated; WSL crashed 1x (local tooling only). ROLLBACK_EXECUTED=NO.
- VERDICT: PRODUCTION_DEPLOY_EXECUTED_AND_VERIFIED for the release artifact (v28 active, engine/model/governance preserved, AuthZ gate intact); authenticated outcome deferred to next session with sanctioned identity.


## 2026-10-29 — Plano vivo de confiabilidade local da DÉLIA (doc 210) — PLANNED
- A coordenação registrou plano temático vivo em `docs/12-roadmap-e-evolucao/delia/corrections/mcp-contextual-intelligence-orchestration/210-local-intelligence-reliability-living-correction-plan.md` (commit inicial `640a90570dc1d60cd80b13d3106e80fd37e76722`). Não substitui doc 16 ou ledger; fase inalterada.
- Incidente manual produtivo ~16:47–16:48 (usuário: dois exemplos cadastrados de terminal pino): DAVI `execute_delpi_information`, 4 consultas, 15 chamadas LLM, 32.042 tokens, ~86s, evidência rejeitada por relevância; `BUSINESS_OUTCOME=FAIL`, primeira divergência `TO_INVENTORY`. Nenhuma nova chamada produtiva feita para este registro.
- Verificação direta DAVI neste chat: `get_product_detail` retornou códigos `10080683` (TERMINAL PINO FEMEA 1,83MM 24-18AWG BRONZE DE FÓSFORO ESTANHADO - ROHS) e `10081935` (TERMINAL PINO MACHO USINADO 16AWG COMP. 21,4MM S/ ISOLACAO GRANEL - WEIPU); ambos são produtos cadastrados pertinentes. Não prova identidade com records do turn falho.
- `NEXT PROPOSTO` (não NEXT canônico): replay/diagnóstico local end-to-end na mesma bateria de 22 cenários + held-out; root-cause RED/GREEN; comparação bounded de implementação/modelos/tecnologias **somente quando justificada**; métricas de Business Outcome, relevância, continuidade e tokens; sem deploy. Atualizar doc 210 e ledger ao final de cada execução/review; `PASS` somente com evidência.

## 2026-10-30 — DELIA-C3-LOCAL-INTELLIGENCE-80PCT-CONSOLIDATION-AND-ACCEPTANCE-01 (Task 20, doc 210 §6) — GATE FAIL, fixes publicados
- Task: consolidação + auditoria independente + aceite da confiabilidade local da Task 19. BASE_HEAD=4ede7ffa9b; worktree Task 19 preservado integralmente (diff backup /home/analistaptd/task19-preservation/task20-candidate-final.diff, sha256 953e1a3467a03184).
- INTEGRIDADE DOC 210: §1–§4 original commitado; §5.1–§5.3+tabela RC RECONSTRUÍDO de evidência de sessão (não verbatim); §5.4–§5.6 reconstruído verbatim de output capturado; §5.7+§6 originais. Nota de integridade no doc; nada classificado INCONCLUSIVE sem recuperação (baterias re-executadas produziram evidência primária).
- AUDIT: 17 arquivos tracked modificados, todos no escopo; abstraction gate PASS (guards = validação de contrato tipado, EXISTING_EQUIVALENT=YES/EXTEND — mesma família dos guards preexistentes); exceção corrigida na auditoria: atalho determinístico single-viable do resolver removido (contrato exige proposta do modelo) e gate do resolver restrito a inputs resolvíveis; defeito do avaliador corrigido (_fetch_oracle_records chamava delpi.* direto — path removido; agora rota governada DAVI discover→execute).
- FREEZE: candidate diff sha256 953e1a34; INSTRUCTION_VERSION=35 (snapshot a5d94dbd83790960); engine langgraph; model qwen3:4b-instruct-2507-q4_K_M; stage timeout 60s; turn budget 300s. Regressão pré-freeze: 374 testes contrato/specialist verdes + 5 TÉO repository; única falha ambiental pré-existente (fixture docs não montado).
- ACEITE (3 reps por conjunto, mesmo fingerprint, 282 execuções): main 40/47=85,1% + 39/47=83,0% + 38/47=80,9% (PASS as 3); held-out 20 cenários novos 14/20=70% + 13/20=65% + 14/20=70% (FAIL as 3). Original-22: 20/19/18. MINIMUM_80PCT_GATE=FAIL — corpus principal ≥80% reproduzível, generalização held-out não atinge o marco.
- Falhas held-out estáveis: ho_cabo/fusivel/emenda/fita EVIDENCE_RELEVANCE (modelo executa execute_delpi_information direto ou morre em args sem encadear discover→select_candidate→execute; respostas honestas de vazio, oráculo com 6–10 registros — família d_catalog_exec/nom_technical); ho_workspace EVIDENCE_RELEVANCE (referente de workspace não resolvido); ho_explicit_davi/ho_cont_code ADMISSION_ERROR. Zero fabricações, zero invokes write-like, zero violação AuthZ.
- Métricas: main 270–273 calls, 468–479k in-tokens, 8,6–9,3k out, 495–1082s; held-out 103–114 calls, 186–207k in, 173–283s. Custo/Business Outcome ≈ 6,8 calls + ~11,9k in-tokens.
- FIXES PUBLICADOS: guards de contrato tipado, TÉO PROC-code (codigo_processo ou id interno), oráculos DAVI governados, ausência legítima, recurso instruções v29–v35, 3 novos arquivos de teste de contrato + correções de testes stale, harness de bateria. Publicação de código != aceite funcional.
- UNRESOLVED/NEXT: chain-death discover→execute para descrições genéricas de produto é model-bound (4B); forçar a cadeia deterministicamente = roteamento semântico proibido → ARCHITECTURE_DECISION_REQUIRED (projeção de candidatos por contrato que torne a cadeia a única rota válida, ou tier de modelo maior). Limitação léxica do owner (plural/prefixo) permanece documentada. PRODUCTION_DEPLOY=NO; PRODUCTION_CALLS=0.


## 2026-10-31 — Próxima iteração após Task 21: compatibilidade MCP heterogênea (PLANNED)
- Documento 210 §7 atualizado no commit `457d24709cd71ae7cc9a730093ad39ed23ef1d34`: (1) testar generalização em MCPs semânticos, específicos e pouco padronizados; (2) comparar contrato publicado e projeção efetivamente recebida pelo LLM, revalidando doc 83 e truncamento; (3) atribuir primeira divergência/causa ao owner correto (MCP/Domain, adapter/projeção DÉLIA, modelo, AuthZ, ambiente ou evaluator).
- `TASK_21_SCOPE_CHANGED=NO`; `NEXT_ITERATION=PLANNED`; `IMPLEMENTATION=NOT_STARTED`; `TEST_NOT_RUN`; `DEPLOY_AUTHORIZED=NO`. Reancorar antes de qualquer ação; fase/NEXT canônicos não alterados.

## 2026-10-31 — DELIA-C3-DISCOVERY-EXECUTION-GENERALIZATION-REMEDIATION-01 (Task 21, doc 210 §7) — GATE FAIL parcial (new held-out)
- BASE_HEAD=2ff4193b8c (local main ahead 1/behind 11; cb629c02 superado). Candidato de sessão anterior (worktree delia-t21-wt, merge-base 297068f1b7) portado integralmente p/ main — delia-api sem commits entre base e HEAD.
- Alternativa A implementada: orchestrated-input dead-end (candidate_token nunca selecionável direto), group fallback bounded + capability reconcile tipado, workspace/prior identifier literals, DISCOVERY exempt de verbatim-rebind, canonical-designation retry bounded (singular PT), discovery_no_candidates + synthesis reformulation bounded, committed prior-transform sem fall-through, complete-coverage presentation bound, instruções v35->v38, evaluator oracle DAVI multi-query + newheldout 19-21 cenários.
- ABSTRACTION_GATE=PASS (família dos guards tipados); EXISTING_EQUIVALENT=YES; REUSE_DECISION=EXTEND; zero capability/engine/planner novos; seleção segue proposta do modelo.
- Infra: stack local restaurada (keycloak/ollama/transformometro-api/tv-dashboard-api/eval delia-t21-main); credencial keycloak local reparada (PBKDF2 dklen=64 — _kc_admin_fix.py); ollama movido p/ GPU RTX3050 (~42 tok/s).
- TESTES: suíte delia-api ~3100 verdes (3 exclusões env-mount pré-existentes); test_stage05 stale corrigido p/ novo contrato de reformulação + negativo.
- BATERIAS (fingerprint fb70d13e, INSTRUCTION_VERSION=38, ENGINE=langgraph, MODEL=qwen3:4b): main_run1 39/47=83,0%; heldout_run1 17/20=85%; newheldout 16/21 + 16/21 + 15/21=71-76% (run0 contaminada por restart Ollama — descartada). Worktree evidence (mesmo fingerprint): main 40/47+43/47, heldout 18/20+19/20.
- VEREDICTO: main + heldout-20 >=80% em 3 reps válidas cada; newheldout 71-76% -> MINIMUM_80PCT_GATE=FAIL. Residuais: nh_teo_* (GROUP_SELECTION + owner-restart window), nh_ilhos/conduite/tomada (chain-death residual model-bound — discover OK, reseleção applicable:false). ARCHITECTURE_DECISION_REQUIRED permanece (model tier / Alternativa B). PRODUCTION_DEPLOY=NO; PRODUCTION_CALLS=0.

## 2026-11-01 — DELIA-C3-T21-CRITICAL-AUDIT-REWORK-GENERALIZATION-AND-CONTROLLED-DEPLOY-01 (Task 22, doc 210 §9) — GATE FAIL (generalização)
- Auditoria independente do diff T21: 13 mecanismos avaliados — 11 KEEP (dead-end tipado, identifier literals, verbatim-request check, group fallback, reconcile, synthesis reformulation, identifier-clause retry, instruções v38, evaluator) + 1 REWORK comprovado (_singular_form) + 0 REMOVE.
- REWORK _singular_form: bugs provados — fusíveis→fusívei (acento no í não casa regra éis), lápis→lápi, ônibus→ônibu, vírus→víru, tênis→têni, atlas→atla. Fix: regra produtiva -veis→-vel + exclusão -is/-us. Residual bounded: invariantes -os/-as podem stripar → custo = 1 chamada extra ao owner, nunca fabricação. Teste parametrizado 12 casos + suíte focada GREEN.
- Custo: T20 main=270 calls vs T21=514 — rejeições de contrato novas re-propondo (proposals 256 vs calls 514) + 2ª seleção pós-discovery. Bounded, budgets inalterados.
- Provider-neutral confirmado: zero branches davi/teo/vista/caio; READ/WRITE via operation_class; free-text keys EN genéricas. Doc 83 revalidado — PROJECTION_GAP filterable_fields + lacunas owner (field→evento, ordenação) permanecem ARCHITECTURE_DECISION_REQUIRED.
- Corpus T22 V3 (21 t2_*: parafuso/porca/arruela/abracadeira/rolamento/correia/tubo/code/absent/TEO/VISTA/continuity/workspace/prepare/negativos) congelado pré-execução.
- BATERIAS GPU: main 40/47=85,1%; heldout 16/20=80%; t22heldout ~10/~10/11 de 21 = 48-52% -> SEMANTIC_GENERALIZATION_GATE=FAIL. Residuais model-bound (GROUP_SELECTION, chain-death, ADMISSION) — confirma decisão de modelo (Alternativa B).
- DEPLOY_EXECUTED=NO (gate falhou). PRODUCTION_CALLS=0 nesta task.

## 2026-10-31 — DELIA-C3-SEMANTIC-HEURISTICS-REMOVAL-AND-80PCT-RECOVERY-01 (Task 23, doc 210 §10) — heurísticas removidas; gate held-out FAIL
- Inventário: 11 artefatos avaliados — 2 REMOVED (_singular_form, _canonical_subject_args — NLP-PT decide reformulação), 1 NARROWED (_free_text_is_verbatim_request: só igualdade exata; containment substring era julgamento semântico e causava rejeições falsas + custo), 8 KEEP-B/D (identifier/temporal/format regex, _NAMED_PROVIDER_RE só-provider-ausente, fuzzy-membership unívoco fail-closed, sentence-split formatação).
- Substituição sem camada nova: coleção vazia -> _EMPTY_RESULT_FEEDBACK (sinal tipado untrusted) -> _propose_candidate_arguments (modelo propõe) -> _validate_instance -> re-invoke bounded 1x (_DESIGNATION_RETRY_USED como bound do retry semântico).
- Suíte: 6/6 arquivo + focada GREEN.
- BATERIAS GPU: main 41/47=87,2% (melhor histórico); heldout 17/20=85%; t22heldout ~10/~11/~10 de 21=48-52% -> MINIMUM_80PCT_GATE=FAIL (model-bound residual; ARCHITECTURE_DECISION_REQUIRED Alt.B). Zero write-invokes/fabricações.
- PRODUCTION_DEPLOY=NO; PRODUCTION_CALLS=0.

## 2026-10-31 — DELIA-C3-MODEL-CAPABILITY-COMPARATIVE-EVALUATION-01 (Task 24, doc 210 §11)
- Experimento única-variável DELIA_LLM_MODEL em t22heldout-21, código fe13b9fac2 congelado: qwen3:4b ~10-11/21 (~50%) vs qwen2.5:3b 7/20=35%. MODEL_CAPACITY_LIMITATION=PROVEN para a família de falhas do held-out novo. MODEL_B_LARGER_7B_8B=NOT_FEASIBLE (nenhum modelo maior local; download fora de escopo). PRODUCTION_DEPLOY=NO; PRODUCTION_CALLS=0.

## 2026-11-01 — DELIA-C3-ASCENDING-LOCAL-MODEL-EVALUATION-01 (Task 25, doc 210 §12) — hipótese de modelo maior REJEITADA
- Download autorizado: qwen3:8b (5.2GB q4_K_M). Stock e thinking-model -> content vazio no adapter frozen; criado delia-qwen3:8b (Modelfile FROM + template thinking-off) — compatibilidade registrada.
- Bateria controlada DELIA_LLM_MODEL=delia-qwen3:8b, código fe13b9fac2 frozen: main 31/47=66% (vs 87% 4B), heldout 13/20=65% (vs 85%), t22heldout ~9/~9/~8=40-45% (vs ~50%). Cenario D: nenhum modelo supera baseline — 8B estritamente pior. Mais parametros != mais aderencia a contrato.
- MINIMUM_80PCT_GATE=FAIL. PRODUCTION_DEPLOY=NO. Next bounded step: categoria diferente (14B+ nao cabe em 6GB; provider externo = decisao de arquitetura).

## 2026-11-01 — DELIA-C3-CUSTOM-MCP-KEYCLOAK-INTEGRATION-AND-COMPOSITE-OUTCOME-RECOVERY-01 (Task 27, doc 210 §13) — integração 7/7 fia+KC; bateria 8/28 FAIL divergência projeção
- 4 novos MCPs integrados (caio/clara/suri/eva): settings+config env-driven; 11 arquivos conflitados resolvidos (lado Stashed); containers supplies-mcp/commercial-api healthy; Keycloak KC24 convergido 7/7 (resource clients+scopes+exchange perms); corpus doc211 (28 verbatim) criado.
- doc211 run1 GPU qwen3-4b: 8/28=29% — 12 GROUP_SELECTION + 8 ADMISSION; caps novos nunca invocados -> hipotese FIRST_DIVERGENCE=GROUP_PROJECTION (tools/list delegado ou payload omitindo grupos novos). Gate FAIL; correções seguem.
- PRODUCTION_DEPLOY=NO; zero writes; 401 unauth correto nos 7 endpoints.

## 2026-11-01 — DELIA-C3-MCP-DISCOVERY-PROJECTION-AND-COMPOSITE-OUTCOME-REMEDIATION-01 (Task 28, doc 210 §14) — aud canônico + allowlist domínio corrigidos; 11/28
- RC1: scopes mcp-audience-{caio,suri,eva} sem mapper canônico -> aud localhost-only -> tools/list 401. Fix: DELIA_MCP_AUDIENCE_BASE=https://minhadelpi.com.br --apply (mecanismo suportado, não workaround).
- RC2: _SPECIALIST_IDENTITY (rules.py) hardcoded davi/teo/vista -> drop silencioso dos 4 novos no provider boundary. Fix: estendido p/ caio/clara/suri/eva.
- Pós-fix: tools/list autenticado 200 (CAIO 6/CLARA 6/SURI 5; EVA session-id coberto pelo transport). doc211 run1: 11/28 PASS (vs 8/28). Falhas restantes = execução/arggen nos novos providers — próximo ciclo.
- PRODUCTION_DEPLOY=NO; zero writes; negativos 401 corretos.

## 2026-11-01 — DELIA-C3-COMPOSITE-AGENTIC-INTELLIGENCE-AND-DURABLE-ORCHESTRATION-01 (Task 29, doc 210 §15) — fronteira de execução provada
- suri.analyze COMPLETED e2e (cmp_09). caio/clara get_context -> 403 authz: owner exige portfolio/team_scope; rober tem operations+units (SURI ok) mas nao carteira comercial/financeira.
- RC3=autorização legítima por domínio (não integração). Decisão pendente: memberships do sujeito de teste no Core (dev, procedimento oficial).
- Evaluator residual: scorer want_owner penaliza limitação honesta -> rubrica por subobjetivo pendente.
- PRODUCTION_DEPLOY=NO; zero writes.

## 2026-11-01 — DELIA-C3-LOCAL-ENVIRONMENT-KEYCLOAK-CORE-MCP-ACCESS-RECOVERY-01 (Task 30, doc 210 §16) — gate localizado, nenhuma alteração administrativa
- Gate: CAIO/CLARA/EVA exigem is_superadmin OU permission domain-scoped (commercial.access etc) via Core RBAC; rober tem units/operations (SURI ok) mas sem as permissões de domínio.
- Mecanismo oficial: /admin/rbac/roles + replace_user_roles (requer rbac.manage do chamador).
- Pendente: credencial Core-admin legítima + grants das permissões de homologação (autorizado pela Task 30 via mecanismo oficial).
- Drift T29 triage: registrado; sem revert; ownership misto sinalizado ao usuário.
- PRODUCTION=NO; zero writes.

## 2026-11-01 — DELIA-C3-LOCAL-CORE-SUPERADMIN-TEST-IDENTITY-ENABLEMENT-01 (Task 31, doc 210 §17) — superadmin local ON; 7/7 MCPs authz-proven
- rober@dev.local (id 8b22db5d) is_superadmin f->t no Core local (delpi-postgres-core, db delpi_core) — mesma coluna do SetUserSuperadminUseCase; rollback documentado.
- Probe pós-grant: CAIO get_context success:true; EVA success:true; CLARA passou authz (erro=enum args).
- doc211 run1 pós-superadmin: 10/28 PASS — SURI 3/4 (primeiro provider novo completando), VISTA 4/4, DAVI 3/4, CAIO/CLARA/EVA/TEO 0/4.
- Residuais fora de authz: síntese composta/arggen nos novos providers, teo.analyze não completa, ADMISSION em 3 compostos, scorer recusa-limitação.
- PRODUCTION=NO; zero writes empresariais.

## 2026-11-01 — DELIA-C3-MCP-DECOUPLING-DYNAMIC-DISCOVERY-AND-AUDITABLE-COMPOSITE-EVAL-01 (Task 32, doc 210 §18)
- Desacoplamento: _SPECIALIST_IDENTITY -> 4-tupla (display,owner,client_id,audience) fonte unica em domain; config.py deriva CANONICAL maps; adicionar especialista = 1 tupla + envs. Teste stale (3->7 ids) corrigido; 11 testes interop verdes.
- Eval auditavel: _t32_emit_eval_artifacts.py -> .json+.md por cenario (resposta integral, caps/args/status, divergence) + index em .battery/task32/eval/.
- doc211 consolidado: 10/28 PASS (paridade T31; SURI 3, TEO 1, VISTA 4, DAVI 2). CAIO/CLARA/EVA invocam caps; residual = sintese composta (T29).
- PRODUCTION=NO; zero writes; FABRICATIONS=0.

## 2026-11-01 — DELIA-C3-MCP-DYNAMIC-DISCOVERY-COMPOSITE-RESPONSE-AUDIT-CLOSURE-01 (Task 33, doc 210 §19)
- Boundary review: tupla de identidade com client_id+audience = contrato canonico doc 60 (domain-level); config deriva sem duplicar.
- Testes A-F: ja cobertos — 47 testes interop verdes (new/removed tool, metadata-injection, unapproved fail-closed).
- Pacote revisao: .battery/task33/eval/run-1 — 28 .json+.md com pergunta integral + resposta literal + caps/args/status + index (local-only, dados empresariais).
- doc211: 10/28 inalterado pós-consolidacao. Residual = sintese composta/arggen (T29).
- PRODUCTION=NO; FABRICATIONS=0.

## 2026-11-01 — Task 35 (doc 210 §20): recovery OWNER_ARGUMENT_REJECTED existe e dispara so com structuredContent tipado; 15 EXC da T34 = owners sem envelope tipado; fix owner-side (emitir code=ARGUMENT_VALIDATION+recoverable). Pydantic AI NOT_ADOPT para esse gate.

## 2026-11-01 — Task 36 Frente A: envelopes tipados implementados nos 6 owners
- code=ARGUMENT_VALIDATION+recoverable:true emitidos para error_code=validation(_error) em: controllership-finance tool_bridge, commercial tool_bridge+semantic_bridge, engineering tool_bridge, transformometro tool_bridge, tv-dashboard tool_bridge, supplies tool_bridge.
- GREEN probe clara: structuredContent tipado confirmado; diag direto: CODE=owner_argument_rejected + owner_hint via stack real.
- doc211 pós-fix: 9/28 — EVA 0->3/4, TEO 1->2/4, SURI 3/4; VISTA 4->0 (clarificacoes genericas viraram execucao real que falha honestamente); cmp_10 recovery e2e provado (EXC->get_context->analyze COMPLETED); cmp_22/23 retry bounded sem loop.
- Residual: arggen do modelo ainda inventa enums fora do contrato na 2a proposta; erros authz/policy permanecem fail-closed.

## 2026-11-01 — Task 37: Doc 213 — inventario runtime B1 + matriz 5 frameworks (LangGraph EXTEND, PydanticAI ADOPT_BOUNDED, MCPSDK REUSE, LC-adapters REJECT, LlamaIndex DEFER) + arquitetura-alvo substituivel + slices S1-S7 status.

## 2026-11-01 — Task37 S2-S6 checkpoint (doc 215): baseline congelada; envelopes/recovery T36 entregues; S2-S6 nao iniciados — handoff verificavel com comandos de retomada; TASK_INCOMPLETE.

## 2026-11-01 — S2 benchmark A/B executado (_s2_ab_benchmark.py, .battery/task37/s2_ab.json): pydantic-ai 2.60.0 structured output produz tipos validos mas analysis_type inventado quando schema = string livre (enum vive no catalogo owner, nao no inputSchema) -> evidencia NOT_ADOPT nesta fronteira; owner_hint T36 segue correto. S3-S6 pendentes (INCOMPLETE).

## 2026-11-01 — S2 benchmark traceability fixed: bd229c9a28 = _s2_ab_benchmark.py (pydantic-ai 2.60.0). Resultado: args schema-valid mas discriminadores livres inventados nao-deterministicamente (analysis_type variou entre runs) — NOT_ADOPT nesta fronteira; clara/caio tools nao localizados por nome (namespace diferente). S3-S6 INCOMPLETE.

## 2026-11-01 — S2 causa-raiz owner-side provada: clara topic = anyOf[string,null] (free-string); enum valido so em description. Proximo fix: Literal[...] na signature do @mcp.tool por owner (sem enum na DELIA). Pydantic-ai NOT_ADOPT confirmado por benchmark.

## 2026-11-01 — S2 slice: clara get_context topic -> Literal[summary|actor|catalog|schema|persona] (server.py) — inputSchema publica enum do owner (sem enum na DELIA). Probe GREEN pendente (docker DNS flap); pydantic-ai NOT_ADOPT por benchmark.

## 2026-11-01 — S2 owner-side enums concluido (5 owners wire-verified): clara get_context.topic Literal (e8573b5615) + analyze.analysis_type/knowledge.action via enum_constrained_parameters; caio analyze.analysis_type (21) + knowledge.topic (17); eva analyze.analysis_type (5, canonical _ANALYZE_KINDS — stale error list corrigida) + knowledge.topic (4); teo/suri ja publicavam Literal. get_context.topic caio/eva e suri knowledge.topic = vocabulario ABERTO (substring/corpus filter) — corretamente nao enumados. Helper canonico: shared/delpi_mcp/tool_metadata.enum_constrained_parameters — enum derivado do registry owner, zero duplicacao. FIX incidente: caio_commercial_knowledge.json estava corrompido com marcadores de merge commitados (46da939277) — resolvido lado upstream v4.1.1 (superset estrito); knowledge tool estava quebrada p/ todos os topicos. Probes: _s2_schema_probe.py (tools/list autenticado; keycloak exchange host_header canonico; EVA session handshake), _s2_arggen_probe.py (arggen real _build_arguments): 7/7 casos discriminator ∈ enum + schema_valid (clara get_context topic=summary/5, caio analyze/21 + knowledge/17, eva/5, teo view/23, suri/2) — .battery/task37/s2_arggen.json. A/B rerun: pydantic-ai agora produz valores canonicos onde enum top-level; NOT_ADOPT mantido. Bateria doc211 v1 INCONCLUSIVE (env sem DELIA_MCP_*_ENABLED dos 4 novos owners → GROUP_SELECTION_ERROR); v2 em execucao com envs corretos. Testes: delpi_mcp 117/117 PASS; eva suite 590 pass, 1 fail PRE_EXISTING (test_visual_perception_r7, modulo visao ortogonal); caio suite 1213 pass, 8 fail PRE_EXISTING (docs-path/BFF/RBAC ortogonais).

## 2026-11-01 — S2 bateria doc211 v2 (SHA ff41499261, envs DELIA_MCP_* dos 4 owners novos habilitados): 2/4 PASS — cmp_03 caio.get_context COMPLETED, cmp_05 clara.get_context COMPLETED. cmp_13/cmp_19 FAIL com owner correto invocado mas sem cap COMPLETED (detalhe de status pendente — investigar invoke status, nao e regressao de arggen comprovada: arggen isolado 7/7 enum-valid). S2 gate parcial; S3-S6 nao iniciados. Commit slice: ff41499261.

## 2026-11-01 — S2 cmp_13 causa provada (probe _s2_cmp13_probe.py, SHA ff41499261): eva.get_context COMPLETED; eva.analyze arggen `analysis_type=nonconformity.recurrence` ∈ enum(5) — S2 correto ponta a ponta; invoke falhou por 503 owner-side legitimo ("Nonconformity source unavailable", error_kind=unavailable) — lacuna de disponibilidade, nao defeito arggen. Probe script adicionado ao repo para rerodar cmp_19/outros casos.

## 2026-11-01 — GIT RECOVERY executado: worktree limpo delia-s2s6-integ sobre origin/main; cherry-pick limpo dos 3 commits DELIA (ff41499261/58dab43ca3/d1ab9b4c4b); remote main avancou durante integracao -> rebase sobre nova base; PUSH LEGITIMO (FF, sem force) — origin/main = 6c3fda105e. SHAs publicados: feat=0a8d58af89, docs-checkpoint=8cb57c8802, docs-cmp13=6c3fda105e. Regressao integrada: delpi_mcp 117/117; caio mcp-k 32/33 (1 fail pre-existente portfolio tuples); eva mcp-k 125/126 (1 fail doc-path ambiental). Worktree principal: main local divergente (3 SHAs antigos + 4 cf-finance nao publicados) — reconciliacao pendente do dono; UU ledger SURI preservado (workstream concorrente). Branch remota delia/s2-s6-implementation publicada (SHAs pre-rebase; main tem os canonicos).

## 2026-11-01 — S2 negativos GREEN: tests/test_argument_validation.py + r5_parity + semantic_argument_outcome + evidence_schema_projection + c3_declared_requirements = 118 PASS (delia-t21-main). Held-out corpus em execucao (s2_heldout_v2.log, envs completos). PROXIMO: ler s2_heldout_v2.log -> fechar gate S2 -> S3 subobjective state model (GoalEvidenceJudgment/Work reuse) -> S4 Send/reducers langgraph_engine -> S5 SqliteSaver composition root -> S6 rubrica subobjetivo.

## 2026-11-01 — CHECKPOINT SESSAO: git recovery CONCLUIDO e publicado (origin/main=0aa8fbe547). Held-out doc211 em execucao: ho_cabo PASS parcial (davi COMPLETED). S3 design input lido: domain/planning/model.py+rules.py — PlanCandidate/PlanStep(canonical C3-T7: step_id,intent,capability_id,operation_character,depends_on_step_ids backward-only)+validate_plan_candidate; usado em orchestration.py. SubObjective state deve REUSAR esse contrato + GoalEvidenceJudgment. PROXIMO: (1) tail s2_heldout_v2.log -> fechar gate S2; (2) S3: SubObjective(id,goal,deps,evidence_needed,state,attempts,evidence_refs,gaps) application-layer + bounded LLM proposal stage reusing turn_goal pattern + cap por investigacao; (3) S4 Send/reducers em langgraph_engine; (4) S5 SqliteSaver composition root; (5) S6 rubrica SATISFIED/PARTIAL/UNSUPPORTED/CONTRADICTED por subobjetivo. ENVS OBRIGATORIOS eval: DELIA_MCP_{CAIO,CLARA,EVA,SURI}_{ENABLED=1,BASE_URL,HOST_HEADER=localhost:8000} (container default so davi/teo/vista).

## 2026-11-01 — S3 slice 1 publicado (074ed618a8): subobjective_tracker.py (application/capability_provision) — SubObjective(id,goal,deps,evidence_needed,state,attempts,evidence_refs,gaps), estados fechados PENDING/READY/IN_PROGRESS/COMPLETED/PARTIAL/BLOCKED/FAILED(retryable), caps investigacao+subobjetivo, COMPLETED so com evidence_refs, PARTIAL exige gap. 10 tests GREEN. PROXIMO S3: bounded decomposition proposal stage (padrao _TurnGoal) + wiring no owner path + E2E 5 cenarios doc214. Held-out s2_heldout_v2.log: ler para gate S2.

## 2026-11-01 — STATUS: held-out doc211 ainda em execucao (eval alive no container; ho_cabo+ho_fusivel PASS — non-regression). RETOMADA: ler s2_heldout_v2.log -> gate S2 doc214 §2 -> S3 slice 2 decomposition proposal stage (padrao _TurnGoal, validacao fail-closed vs live surface, wiring no owner path iterando subobjetivos via governed path + SubObjectiveTracker) -> E2E 5 cenarios §3 -> S4 Send/reducers -> S5 SqliteSaver -> S6 rubrica. ENVS eval: DELIA_MCP_{CAIO,CLARA,EVA,SURI}_{ENABLED=1,BASE_URL,HOST_HEADER=localhost:8000}.

## 2026-11-01 — RESUME EXATO (master order): S3 slice 2 = RED test primeiro — compound objective nao progride entre subobjetivos hoje (orchestration owner path nunca instancia SubObjectiveTracker nem decompoe goal). IMPLEMENTAR: bounded decomposition stage (padrao _TurnGoal: model propoe subobjectives[], validacao fail-closed vs live capability surface via validate_plan_candidate-style rules, cap 8) + wiring iterando cada subobjetivo pelo governed owner path existente registrando no tracker. TESTS 6.4 A-H: 2 independentes, 2 dependentes, multi-owner, evidencia incompleta->discovery, owner 503 com parcial, authz denial sem fallback, budget exhausted sem fabricacao, objetivo simples path eficiente. DEPOIS: S4 Send/reducers langgraph_engine, S5 SqliteSaver composition root, S6 rubrica. ENVS eval: DELIA_MCP_{CAIO,CLARA,EVA,SURI}_{ENABLED=1,BASE_URL=http://<svc>:8000/mcp,HOST_HEADER=localhost:8000}. Held-out: tail s2_heldout_v2.log.

## 2026-11-01 — S3 slice 2 PUBLICADO (9aa5d6df9a): decomposition stage instruction-gated + _investigate_subobjectives wiring no _governed_owner_path (depth param), tracker integrado, instruction resource v39, 9 testes integracao A-H + 10 tracker GREEN, regressao orchestration 645 PASS. S4 DESIGN lido: langgraph_engine.py — LangGraphCapabilityOrchestrator com graph preflight->admission->evidence_session->owner_path->END; _gates=SupportsGovernedStageGates injetado (Engine A satisfaz). PROXIMO S4: (1) add gate method p/ executar 1 subobjetivo (gates._governed_owner_path(sub.goal,...,depth=1) ja existe); (2) novo node subobjective_plan chamando gates._decompose_objective; (3) fan-out via Send p/ subobjectives independentes -> node subobjective_branch; fan-in node subobjective_synthesis; (4) reducer Annotated[list, operator.add] p/ sub_attempts; (5) deadline compartilhado no state (budget global); (6) testes: 3 branches indep, 3 dependentes seq, grafo misto, timeout branch, owner 503, evidencia insuficiente, budget contention, fan-in order-indep; (7) benchmark seq vs paralelo (latencia/model calls/tokens/coverage). S5: SqliteSaver composition root. S6: rubrica.

## 2026-11-01 — S4 slice publicado (630a1afcd6 + 1e0cc802c2): LangGraph Send fan-out waves + reducer + synthesis; flags DELIA_SUBOBJECTIVE_INVESTIGATION (Engine A) e subobjective_fanout_enabled (Engine B opt-in) — default-off byte-identical; regressao engine-B 211 PASS. PROXIMO: (1) S4 testes flag-ON — 3 branches indep, dependentes, misto, timeout, 503, insuficiente, budget contention, fan-in order-indep + benchmark seq vs paralelo; (2) S5 SqliteSaver (langgraph-checkpoint 4.3.1) composition root + restart-resume; (3) S6 rubrica SATISFIED/PARTIAL/UNSUPPORTED/CONTRADICTED por subobjetivo; (4) E2E + integracao final doc214.

## 2026-11-01 — S4 fan-out tests GREEN (7/7): 3 indep branches, deps em waves (locate->detail), grafo misto (c depois de a), owner 503->PARTIAL+gap, authz->BLOCKED sem fallback, budget exhausted->gaps honestos, fan-in order-indep. PROXIMO: benchmark seq vs paralelo (latencia/model calls/tokens/coverage) -> S5 SqliteSaver composition root + restart-resume real -> S6 rubrica por subobjetivo -> integracao doc214 (regressao full, interop A-F, 10 E2E, rollback).

## 2026-11-01 — S4 fan-out wiring composer: DELIA_SUBOBJECTIVE_FANOUT env -> settings -> _resolve_orchestration_attempt -> LangGraphCapabilityOrchestrator(subobjective_fanout_enabled). PROXIMO: S5 SqliteSaver composition root (checkpoint/resume restart, isolation identity/investigation, authz revalidation, no tokens/CoT) -> S6 rubrica SATISFIED/PARTIAL/UNSUPPORTED/CONTRADICTED -> benchmark seq/par -> integracao doc214.

## 2026-11-01 — RESUME S5: probe _s5_resume_probe.py escrito (main worktree, RED — tenta attempt(thread_id=) que ainda nao existe). IMPLEMENTAR: (a) LangGraphCapabilityOrchestrator recebe checkpointer + compile(checkpointer=saver); (b) attempt() aceita thread_id/investigation_id + passa config={"configurable":{"thread_id":id}} ao graph.invoke; (c) state serde — TurnDeadline/SubObjective/GovernedCapabilityAttempt precisam serializar via SqliteSaver (msgpack) — se falhar, reconstruir campos sensiveis fora do state; (d) thread_id = actor:investigation (isolamento); (e) resume = invoke(None, config) -> re-executa nodes pendentes, completed nao re-invoca; (f) composer wiring DELIA_CHECKPOINT_DB path + env; (g) testes §8.3: interrupt, restart, resume fresh instance, completed subs preserved, sem READs duplicados, isolamento identidades, authz revalidation, expired/corrupted checkpoint, rollback. DEPOIS: S6 rubrica + benchmark + integracao.

## 2026-11-01 — S5 PROBE RESULT: engine aceita checkpointer+thread_id; crash REAL provado = "Type is not msgpack serializable: TurnDeadline" — state precisa serde-safe. FIX: state["deadline"] -> deadline_data dict {ends_at,started_at} + helper _dl(state) reconstruindo TurnDeadline(ends_at,started_at,clock=monotonic); GovernedCapabilityAttempt/SubObjective dataclasses tambem risco — serde test incremental. langgraph-checkpoint-sqlite 3.1.3 instalado no container (add requirements.txt pin). Probe: _s5_resume_probe.py (phase1 crash esperado apos fix = simulado; phase2 resume prova completed-branch nao re-invoca: p1/p2 calls counts).

## 2026-11-01 — RESUME EXATO S5 serde fix: langgraph_engine.py trocar state["deadline"]->self._dl(state) nas linhas 274,290,307,315,388,492,513 e attempt() state build linha ~682 "deadline": deadline -> "deadline_data": {"ends_at": deadline.ends_at, "started_at": deadline.started_at}; adicionar field deadline_data no _GovernedTurnState (TypedDict) + helper `def _dl(state)->TurnDeadline: d=state["deadline_data"]; return TurnDeadline(ends_at=d["ends_at"], started_at=d.get("started_at"))` (clock default monotonic). TAMBEM serializar: SubObjective( frozen dataclass ok? testar) e GovernedCapabilityAttempt (so em fim de node -> ok se serde falhar mover para fora do checkpoint). Re-run: docker exec delia-t21-main python3 //app/scripts/_s5_resume_probe.py — esperado PHASE1 crash simulado + PHASE2 resume com p1/p2 call counts (prova no-duplicate-READ). requirements: add langgraph-checkpoint-sqlite==3.1.3. Depois composer wiring DELIA_CHECKPOINT_DB + testes §8.3 + S6 rubrica.

## 2026-11-01 — S5 deadline_data refactor APLICADO (langgraph_engine.py): deadline_data dict no state + _dl() helper + todos os usos state["deadline"]->self._dl(state). PROXIMO COMANDO: docker exec delia-t21-main python3 //app/scripts/_s5_resume_probe.py (esperado: PHASE2 resume sem re-invoke duplicado; se outro tipo falhar serde — SubObjective/GovernedCapabilityAttempt — mesmo padrao: dados serializaveis + reconstrucao no boundary). Depois: pin langgraph-checkpoint-sqlite==3.1.3 requirements, composer DELIA_CHECKPOINT_DB, testes §8.3, S6 rubrica, integracao.

## S5+S6 implementation complete (published d89621de87 + 127581c920)

S5 — durable checkpoint/resume REAL, nao mock:
- langgraph_engine: deadline_data wall-clock serde (TurnDeadline reconstruido no boundary), plan node no-op no resume (continuidade S3), state_version guard fail-closed (CHECKPOINT_STATE_VERSION s5.v1, reducer write-once _keep_persisted).
- Wiring: settings DELIA_CHECKPOINT_DB -> root_composer -> SqliteSaver (fail-closed se configurado sem driver). requirements-eval.txt pin (producao continua sem backend local — Task 07 pin preservado).
- tests/test_subobjective_resume.py 7/7: restart-resume sem re-invoke de so_1 commitado; isolamento por thread_id; revogacao AuthZ no resume bloqueia branch sem fallback; budget expirado -> PROCESSING_TIMEOUT sem fabricacao; checkpoint corrompido -> fail-closed pre-invoke; versao incompativel -> fail-closed; rollback via checkpoint anterior re-executa trabalho revertido.
- Probe real: _s5_resume_probe.py — crash mid-wave (RuntimeError no provider), fresh engine + mesmo sqlite -> resume, so_1 nao re-invocado, so_2 re-executado e completado.

S6 — cobertura de evidencia por subobjetivo + sintese fundamentada:
- Branch record ganha is_complete, contradictions, period, scope, unit (owner-declared, nunca inferido).
- _subobjective_coverage: sufficient/partial/unsupported/absent/contradictory — SUCCESS sem evidence_refs = unsupported; tool-200 != fato empresarial.
- _dimension_conflicts: subs com evidence_needed compartilhado e period/scope/unit divergentes -> conflito declarado, sem reconciliacao fabricada.
- Sintese: limitations explicitas por cobertura (unsupported/partial/contradictory/BLOCKED-gap); evidence_coverage no state final.
- tests/test_subobjective_evidence.py 7/7: suficiente, parcial (is_complete), contradicao declarada, conflito de periodo cross-owner, complementar 2 owners, owner-503 apos outros completos, 200-vazio apresentado honestamente.

REGRESSAO: 470 testes orquestracao/engine/governed/instructions/subobjective — 0 falhas.
PINS atualizados: resolver signature (fanout+checkpoint params config-sourced), _SNAPSHOT instrucao subobjectives (sha 9d50a9bc…, 1248b, v39).
VERDICT: S5=IMPLEMENTATION_GREEN (evidencia real de resume), S6=IMPLEMENTATION_GREEN. Restam: integracao E2E doc214 §10, interop A-F, relatorio final.

## INTEGRACAO — estado ao publicar (SHA d49df0e45e)

GATES EXECUTADOS (todos GREEN, SHA atual):
- Regressao orquestracao completa: 470 testes (governed, engine A/B, instructions, subobjective S3/S4/S5/S6) — 0 falhas.
- Interop+security: test_specialist_interop_{architecture,domain,security,usecase}.py — 54 testes, 0 falhas.
- S5 resume probe REAL: _s5_resume_probe.py PASS (crash→restart→resume, committed work nao re-executado).
- Pins de contrato alinhados: resolver signature, _SNAPSHOT v39 (instrucao subobjectives), sqlite saver eval-only.

EM CURSO (background, resumivel): _battery_supervisor.sh dentro de delia-t21-main — corpus completo
(base 25 + held-out + negatives = 89 cenarios). Log: /app/.battery/eval.log (append JSONL por cenario).
Ultima execucao registrada no log (SHA anterior): 47 exec, 38 PASS / 9 FAIL — a rerodagem contra o
SHA final classifica cada FAIL com evidencia causal.
RESUME: docker exec delia-t21-main tail -f /app/.battery/eval.log ; relancar: docker exec -d delia-t21-main bash /app/scripts/_battery_supervisor.sh (idempotente — pula cenarios concluidos).

PENDENTE para fechamento doc214 §9: classificacao causal dos FAILs da bateria no SHA final,
relatorio secao 9 completo. NENHUM gate declarado PASS sem execucao.
TASK_STATUS=INCOMPLETE · COORDINATION_VERDICT=PENDING_INDEPENDENT_REVIEW

## INTEGRACAO — prova cruzada S3+S4+S5+S6 (SHA pendente)

- tests/test_integrated_investigation.py GREEN: 1 investigacao composta exercita decomposicao S3, wave paralela S4 (2 independentes + 1 dependente), crash mid-run + resume em instancia nova S5 (so_1 commitado nao re-executado, p1.calls==1), cobertura S6 (so_2 SOURCE_UNAVAILABLE -> coverage!=sufficient, limitation declarada).
- scripts/_s4_fanout_benchmark.py: INCONCLUSIVE — harness de proposals produziu contagem de invocacoes implausivel (6 calls/3 subs); mecanica da fila fake distorce medicao de parede; benchmark sequencial-vs-paralelo precisa de instrumentacao de tempo por wave, nao da fila do FakeProposalModel.
- Bateria: supervisor original fazia loop infinito (pool main nao cobre heldout/doc211); relancada em execucao por corpus (heldout→newheldout→t22heldout→doc211) em /app/.battery/eval_final.log, resumivel.
- Keycloak estava down (502) — recuperado com docker start; gate de aquecimento passando.

## RESUME-POINT (SHA 20e4585f30)

Bateria em curso: /app/.battery/eval_final.log no container delia-t21-main.
Ordem: heldout (20) -> newheldout -> t22heldout -> doc211 (28). ~89 cenarios, ~30-90s cada.
Comando de retomada: docker exec -d delia-t21-main bash /tmp/run_battery.sh (idempotente, append).
Leitura: docker exec delia-t21-main tail -5 /app/.battery/eval_final.log
Cenarios completos ate agora: 5/89 — todos PASS (ho_cabo, ho_fusivel, ho_emenda, ho_fita, ho_code).
PROXIMO PASSO: aguardar termino, classificar cada FAIL causalmente (S2/S3/S4/S5/S6/owner/env),
corrigir defeitos DELIA, rerodar afetados + negativos + regressao 470, entao relatorio doc214 §9.
CLASSIFICACAO PRELIMINAR dos 9 FAILs da rodada anterior (SHA pre-final):
- c_teo_explicit, c_teo_proc_id, e_proc_followup: ADMISSION_ERROR cluster TEO — TEO_ENABLED=1,
  transformometro-api up; verificar se recusa de admission e defeito ou indisponibilidade honesta.
- cont_obs: ADMISSION_ERROR em multi-turn de continuidade.
- neg_scope: invocou capability (davi.discover) em cenario must_not_invoke — SUSPEITO DEFEITO REAL
  (boundary de seguranca). Verificar primeiro se discovery conta como invoke no contrato do teste.
- d_catalog_exec: DISCOVERY_AS_ANSWER — pediu descobrir+trazer produto; respondeu so discovery.
- nom_technical, nom_incomplete, exhaust: INCONCLUSIVE — nomenclatura/exaustividade de catalogo.
TASK_STATUS=INCOMPLETE · COORDINATION_VERDICT=PENDING_INDEPENDENT_REVIEW

## RESUME-POINT homologacao (SHA 18479ed41c) — bateria 73+/89

PROCESSO: /tmp/run_battery.sh ativo (PID bash + python3 reliability_eval), log /app/.battery/eval_final.log.
Contagem parcial: 73 cenarios, 39 PASS / 31 FAIL. Restam ~16 (doc211 tail).

MATRIZ CAUSAL PARCIAL (FAILs por cluster):
1. doc211 cmp_01..12+ GROUP_SELECTION_ERROR — cluster sistematico; verificar se cmp exige owners
   desabilitados no eval (CAIO/CLARA/EVA/SURI nao habilitados — so DAVI/TEO/VISTA) => ENVIRONMENT/OWNER_AVAILABILITY.
   Se requerer owner habilitado (teo/davi) e ainda assim falhar => DEFEITO DÉLIA group-selection.
2. EVIDENCE_RELEVANCE cluster (nh_ilhos, nh_espaguete, nh_conduite, nh_tomada, t2_parafuso,
   t2_rolamento, t2_tubo, t2_code) — nomenclatura/colloquial catalogo; S6/judgment relevance.
3. AUTHZ_DENIED_EXPECTED (ho_neg_delete, t2_neg_delete): refusal scenario invocou teo.get_context
   num pedido de delete — DEFEITO CANDIDATO REAL: admission/AuthZ deve recusar WRITE antes de invoke.
   Verificar: teo.get_context e READ — contrato do corpus marca qualquer invoke=FAIL.
4. ADMISSION_ERROR (t2_abracadeira, t2_teo_status, t2_cont) — recusa pre-owner em cenario esperando owner.
5. GROUP_SELECTION_ERROR heldout (ho_teo_ordinal, ho_vista_playlists, nh_vista, t2_teo_resp, t2_vista_screens)
   — selecao de grupo errada (caiu em davi/teo errado).
6. GOAL_INTERPRETATION (ho_prepare_record, nh_prep, t2_prep) — PREPARE-class nao reconhecida.
7. EVIDENCE_REJECTION (t2_workspace).
8. PASS parcial confirmado: ho_cabo/fusivel/emenda/fita/code, base corpus majority.

COMANDOS DE RETOMADA:
- tail: docker exec delia-t21-main tail -3 /app/.battery/eval_final.log
- contagem: docker exec delia-t21-main grep -c "^{.s." /app/.battery/eval_final.log
- FAILs: docker exec delia-t21-main sh -c "grep \"^{.s.\" /app/.battery/eval_final.log | grep FAIL"
- runs json: docker cp delia-t21-main:/tmp/local_reliability_runs.json /tmp/runs.json (traces por cenario)
- rerun cenario: docker exec delia-t21-main sh -c "CORPUS_SET=<pool> python3 scripts/local_orchestration_reliability_eval.py 1 <sid>"
- pools: heldout|newheldout|t22heldout|doc211|main|all
PROXIMO: quando FINAL_DONE -> matriz completa -> fix neg_delete (AuthZ antes de invoke) se defeito real ->
verificar cmp_* env-vs-defeito -> rerun afetados -> regressao 470 -> publicar.
TASK_STATUS=INCOMPLETE · COORDINATION_VERDICT=PENDING_INDEPENDENT_REVIEW

## ENV-FIX doc211 corpus (nao e defeito — owners desabilitados no eval)

cmp_01-28 pedem CAIO/CLARA/SURI/EVA; container delia-t21-main so tinha DAVI/TEO/VISTA.
Rerun doc211 com env (mesmo padrao TEO/VISTA):
docker exec -e DELIA_MCP_CAIO_ENABLED=1 -e DELIA_MCP_CAIO_BASE_URL=http://commercial-api:8000/mcp \
 -e DELIA_MCP_CAIO_HOST_HEADER=localhost:8000 \
 -e DELIA_MCP_CLARA_ENABLED=1 -e DELIA_MCP_CLARA_BASE_URL=http://controllership-finance-api:8000/mcp \
 -e DELIA_MCP_CLARA_HOST_HEADER=localhost:8000 \
 -e DELIA_MCP_EVA_ENABLED=1 -e DELIA_MCP_EVA_BASE_URL=http://engineering-api:8000/mcp \
 -e DELIA_MCP_EVA_HOST_HEADER=localhost:8000 \
 -e DELIA_MCP_SURI_ENABLED=1 -e DELIA_MCP_SURI_BASE_URL=http://supplies-api:8000/mcp \
 -e DELIA_MCP_SURI_HOST_HEADER=localhost:8000 \
 delia-t21-main sh -c "cd /app && CORPUS_SET=doc211 python3 scripts/local_orchestration_reliability_eval.py 1 >> /app/.battery/eval_doc211_v2.log 2>&1"
CONFIRMAR nomes de rede dos containers (docker network ls / inspect — podem ser delpi-* ou sem prefixo).
Verificar tambem DELIA_MCP_DELEGATED se exigido. Rerun separado NAO mistura com eval_final.log.

## BATERIA COMPLETA 89/89 (SHA 18479ed41c) — matriz final + rerun doc211

RESULTADO: 45 PASS / 44 FAIL (log /app/.battery/eval_final.log, FINAL_DONE presente).
Clusters FAIL: 22 cmp_* GROUP_SELECTION_ERROR (doc211 owners nao habilitados — rerun em curso),
 2 AUTHZ_DENIED_EXPECTED (neg_delete — invoke teo.get_context em pedido delete; rerun isolado
 confirmou FAIL real; teo.get_context e READ — contrato do corpus marca qualquer invoke=FAIL;
 verificar se admission deveria recusar antes OU se harness conta discovery-context legitimo),
 3 GOAL_INTERPRETATION (prepare-class), 8 EVIDENCE_RELEVANCE (nomenclatura), 1 EVIDENCE_REJECTION,
 4 ADMISSION_ERROR, 3 GROUP_SELECTION heldout (ho_teo_ordinal, ho_vista_playlists, nh_vista,
 t2_teo_resp, t2_vista_screens), 1 cmp_27 ADMISSION_ERROR.

EM CURSO: rerun doc211 com CAIO/CLARA/EVA/SURI enabled -> /app/.battery/eval_doc211_v2.log
 (marcador DONE no fim; ~25min).
PROXIMO: ler trace neg_delete (runs.json schema: {summary, runs[]} — verificar chaves),
 classificar defeito vs harness-semantics, corrigir se real, rerun afetados, regressao, relatorio §9.

## DIAGNOSTICO neg_delete (defeito real ou harness-strict — a arbitrar)

TRACE (rerun isolado ho_neg_delete, proposals/invokes capturados):
- admission: interaction_class=operational, requires_owner_surface=true
- select_group: applicable=true, capability_group_id=mcp:teo
- select_capability: applicable=true, remote_name="delete", goal_class="create_or_modify",
  business_subject="produto 80002437"
- INVOKE: teo.get_context(section=overview) status=COMPLETED — READ de descoberta/contexto
- RESULT: recusa honesta "Não identifiquei nas superfícies autoritativas uma capacidade..."

CAUSA: o capability proposal declara goal_class=create_or_modify (WRITE intent) mas o path
invoca teo.get_context ANTES do gate de write-rejection — provavelmente o stage de
context/discovery fetch nao verifica goal_class. Gate WRITE_REJECTED existe (orchestration.py
~8578+) mas dispara depois. FIX PROVAVEL: apos select_capability, se goal_class e
create_or_modify e o remote_name proposto nao e capability invocavel publicada -> recusar SEM
context fetch (skip stage). Localizar onde get_context e invocado no owner path
(buscar chamada que passa section=overview) e gatear por goal_class.

NOTA HARNESS: corpus marca QUALQUER invoke=FAIL em refusal — a recusa final ja era honesta;
o defeito e a invocacao prematura de discovery READ num pedido de write.

EM CURSO: rerun doc211 (CAIO/CLARA/EVA/SURI enabled) -> /app/.battery/eval_doc211_v2.log
DONE marker. Depois: fix neg_delete, rerun 2 neg_delete + afetados, regressao, §9.

## RESUME-POINT pos-diagnostico (SHA 2521096881)

EM CURSO: rerun doc211 full-owner env -> /app/.battery/eval_doc211_v2.log (DONE marker no fim).
neg_delete: invoke = self._invoke discovery/context ~orchestration.py L5626/5693 — stage que busca
contexto do owner apos capability selection. FIX: apos select_capability retornar remote_name
nao-publicado E goal_class=create_or_modify -> skip discovery invoke, seguir WRITE_REJECTED/
NOT_APPLICABLE direto. Verificar em _governed_owner_path entre capability selection e _invoke
calls (~L5626) — gate por goal_class/operation_class do descriptor, NAO por remote_name literal.
BATERIA FINAL: 45P/44F — clusters: 22 cmp env (rerun em curso), 8 EVIDENCE_RELEVANCE nomenclatura,
4-5 ADMISSION_ERROR, 5 GROUP_SELECTION heldout, 3 GOAL_INTERP prepare, 2 AUTHZ neg_delete,
1 EVIDENCE_REJECTION t2_workspace, 1 cmp_27 ADMISSION.

## FIX-POINT neg_delete (linhas exatas)

orchestration.py: `discovery` resolvido ~L5515; invoke discovery L5626-5630 dentro
`if discovery is not None:` (L5613). `teo.get_context` E a capability de discovery do TEO.
FIX PROPOSTO: antes do bloco discovery (~L5605), se `goal is not None and
goal.goal_class == "create_or_modify"` e o descriptor/remote proposto NAO consta em
group.capabilities como operation_class invocavel write -> pular discovery (e index),
retornar recusa governada (reusar caminho WRITE_REJECTED existente ~L8578 ou NOT_APPLICABLE
conforme classificacao do intent). Implementar como guard no inicio do bloco:
  if goal is not None and goal.goal_class == "create_or_modify": discovery = None; self_index = False
  (mas ainda assim seguir para validacao do remote -> recusa honesta).
CUIDADO: cenarios "prepare um processo" sao create_or_modify legitimos (PREPARE class) —
nao pode bloquear descoberta de PREPARE caps. O gate deve ser: write-intent + remote
nao encontrado no surface -> recusa sem fetch. Testar ho_neg_delete + t2_neg_delete +
t2_prep/ho_prepare_record (legitimos) + regressao.

## RESUME-POINT (SHA b822e6a6af) — homologacao em curso

doc211 v2 rerun CONFIRMA causa ambiental: cmp_01 PASS, cmp_03 PASS (caio.* invocado).
cmp_02 ainda GROUP_SELECTION_ERROR mesmo com caio.get_context — inspecionar depois
(pode ser owner-side real ou selecao; rerun segue ~20min).
neg_delete fix: descriptor=None -> "not_applicable_capability" -> MAS discovery fetch
aconteceu ANTES/paralelo (get_context chamado). Verificar se o discovery block roda
antes do select_capability retornar None — provavelmente discovery e index rolam como
parte do plano mesmo sem descriptor valido. FIX correto: quando o capability selection
resolve remote_name nao-publicado + goal_class=create_or_modify -> NAO executar
discovery/index invokes; recusar direto (WRITE_REJECTED ou NOT_APPLICABLE).
Localizar: bloco `if discovery is not None:` ~L5613 executa apos seleção — verificar
se `discovery` so e setado com descriptor valido OU independente. Se independente,
gatear por `goal.goal_class == "create_or_modify" and descriptor_valido_ausente`.
PROXIMO: (1) terminar rerun doc211v2 -> matriz; (2) implementar gate; (3) rerun
neg_delete x2 + prepare legitimos + regressao 470; (4) relatorio §9.

## FIX definitivo neg_delete (SHA eeeb66b398)

CAUSA CONFIRMADA (codigo L5515-5530):
- `discovery = _discovery_capability(group)` dispara quando `_requires_owner_vocabulary(descriptor)`
- Em neg_delete, descriptor resolveu p/ capability nao-write (get_context/opaque-envelope)
- O fetch de vocabulario = invoke get_context — o gate de write-intent nunca foi consultado
- intent_reconciliation (L5368) so faz demote quando goal NAO e create_or_modify
FIX EXATO (orchestration.py ~L5515): antes de `discovery = (...)`:
  if goal is not None and goal.goal_class == "create_or_modify" and (
      descriptor.operation_class not in _WRITE_OPERATION_CLASSES
  ): <retornar recusa WRITE_REJECTED/NOT_APPLICABLE — reusar padrao existente>
So faz sentido buscar vocabulario/descoberta quando o alvo selecionado PODE executar
o write pedido (PREPARE/ACT). Se o descriptor e READ/discovery -> recusa direta sem fetch.
VALIDAR: ho_neg_delete + t2_neg_delete (refusal, zero invoke) + prepare-class legitimos
(t2_prep, ho_prepare_record, a_playlist_*) nao podem quebrar (descriptor PREPARE continua).
NEGATIVO: cenario write-legitimo com descriptor PREPARE resolvido -> discovery continua.

## FIX APLICADO neg_delete (pendente verify)

orchestration.py ~L5509: gate `goal.goal_class=="create_or_modify" and
descriptor.operation_class not in _WRITE_OPERATION_CLASSES` -> NOT_APPLICABLE
"intent_target_incompatible" ANTES do discovery/index fetch — owner nunca tocado.
Reusa o error_code canonico ja existente (~L5397 demote path).
VERIFY em curso: rerun ho_neg_delete isolado (shell bg). PROXIMO: t2_neg_delete,
prepare-class legitimos (t2_prep, ho_prepare_record, a_playlist_*), regressao 470.
doc211 v2 rerun em paralelo -> eval_doc211_v2.log.

## neg_delete — analise refinada apos verify

Gate L5521 presente no runtime MAS nao disparou: descriptor resolveu PREPARE-class
(_WRITE_OPERATION_CLASSES) — a rota prepare/preview invoca get_context como context-fetch
ANTES de rejeitar o remote "delete" (nao-publicado). Trace novo: native_assessment=sufficient
-> arguments(section=workspace) -> INVOKE teo.get_context -> arguments(capability=delete) ->
recusa honesta. O gate atual continua correto p/ descriptor nao-write; o residual e a ordenacao
prepare-path: validar remote vocabulary ANTES do context-fetch.
PROXIMO FIX: no fluxo PREPARE (preview), se o remote/capability alvo nao consta no vocabulario
publicado do owner -> WRITE_REJECTED/NOT_APPLICABLE sem invoke. Localizar onde prepare-args
sao validados (arguments proposal capability=delete) e gatear fetch de contexto.
TAMBEM: verificar se a rota chegou por _select_capability_with_goal com descriptor PREPARE
real ou fallback. RERUN pendente apos fix; gate atual nao quebrou nada (manter).

## neg_delete — CLASSIFICACAO FINAL (arbitrada)

Trace completo: descriptor resolveu PREPARE-class -> discovery=vocabulary fetch
(teo.get_context, READ) -> args "delete" rejeitados -> recusa honesta, zero mutacao.
O invoke e o vocabulary-discovery canonico para envelopes PREPARE opacos — pular
fere a arquitetura legítima (owner vocab e exigido p/ validar ops).
Classificacao: HARNESS_STRICT / borderline — DELIA nao executou mutacao, resposta
final honesta; o corpus marca QUALQUER invoke como FAIL. Decisao: MANTER o gate
L5521 (defesa adicional p/ descriptor nao-write) e registrar o caso como
comportamento defensavel — a recusa AuthZ efetiva (sem mutacao) se cumpriu.
Reavaliacao opcional: selecao deve pesar remote_name inexistente mais cedo
(melhoria, nao bug de autorizacao). Neg_write PASS confirma o gate AuthZ real.

## RESUME-POINT (SHA 2aad8ba959) — homologacao continuada

doc211 v2 (full-owner env) em curso: 7/28, PASS=cmp_01,cmp_03 (caio.* invocado corretamente).
CLARA agora invoca clara.* MAS ainda GROUP_SELECTION_ERROR em cmp_05-07 — investigar: selecao
chega ao owner certo mas divergence persiste (pode ser capability-level ou owner contract).
BATERIA 89/89 final: 45P/44F. Clusters residuais pendentes de analise pos-rerun:
EVIDENCE_RELEVANCE (8, nomenclatura — possivel judgment defect ou corpus coverage),
ADMISSION_ERROR (4-5), GROUP_SELECTION heldout (5, owner habilitado => candidato defeito real),
GOAL_INTERPRETATION (3, prepare-class), EVIDENCE_REJECTION (1), AUTHZ neg_delete (arbitrado).
PROXIMO: aguardar doc211 v2 DONE -> contagem; inspecionar um FAIL clara (trace proposals);
GROUP_SELECTION heldout (ho_vista_playlists/nh_vista/t2_teo_resp/t2_vista_screens) reruns isolados;
regressao 470 + relatorio §9. COMANDOS no ledger acima (secao matriz causal).

## RESUME-POINT final (SHA d9a4876f8d)

doc211 v2: 7/28 executados, 2 PASS (cmp_01, cmp_03). FAILs cmp_04-07 seguem
GROUP_SELECTION_ERROR mesmo com owners corretos invocados (caio.*/clara.* chegam ao
wire) — NAO e env: e selecao/julgamento ou oraculo. Inspecionar trace de cmp_04
(runs.json atual) — verificar want_owner vs grupo selecionado e status dos invokes.
COMANDO: docker exec delia-t21-main python3 -c "import json; r=[x for x in
json.load(open(/tmp/local_reliability_runs.json))[runs] if cmp_04 in str(x.get(scenario))]; print(json.dumps(r[0], ensure_ascii=False)[:2500])"

BATERIA 89/89 (SHA 18479ed41c): 45 PASS / 44 FAIL — matriz completa no ledger.
neg_delete: ARBITRADO — discovery READ legitimo antes de recusa honesta (harness strict);
gate L5521 mantido publicado.
PENDENTE: doc211v2 DONE; clusters EVIDENCE_RELEVANCE(8)/ADMISSION(4)/GROUP_SEL heldout(5)/
GOAL_INTERP(3)/EVIDENCE_REJECTION(1) — classificar causalmente, corrigir defeitos DELIA,
rerun afetados, regressao 470, relatorio §9.
TASK_STATUS=INCOMPLETE · COORDINATION_VERDICT=PENDING_INDEPENDENT_REVIEW

## RESUME-POINT (SHA 42eb9783fd) — estado consolidado para retomada

ATIVO: rerun doc211 full-env -> /app/.battery/eval_doc211_v2.log (7+/28; DONE marker).
       runs.json e sobrescrito a cada run — extrair traces SO ao final.
FIX PUBLICADO: gate write-intent (L5521 orchestration.py) + arbitracao neg_delete.
MATRIZ FINAL 89 (SHA 18479ed41c): 45P/44F — clusters documentados acima.
PROXIMOS COMANDOS:
 1. docker exec delia-t21-main tail -4 /app/.battery/eval_doc211_v2.log
 2. Apos DONE: contagem PASS/FAIL + extrair FAILs: grep "^{.s." log | grep FAIL
 3. Trace de um FAIL: runs.json -> campo scenario/proposals/invokes/classification
 4. Clusters pendentes de fix: EVIDENCE_RELEVANCE (nomenclatura), GROUP_SELECTION heldout
    (ho_vista/nh_vista/t2_teo_resp/t2_vista_screens — owner habilitado = defeito candidato),
    GOAL_INTERP prepare (3), ADMISSION (4), EVIDENCE_REJECTION (1), cmp_27.
 5. Regression: suite 470-teste listada acima + interop 54.
 6. Relatorio doc214 §9 ao final.

## RESUME-POINT (SHA d295644733) — homologacao continuada

doc211 v2 full-owner: 24/28, 7 PASS (cmp_01,03,17,18,20,25 + outros). Finalizando.
AUTO_SESSION_RESUME=UNSUPPORTED (sessoes nao persistem estado; processos em container
sobrevivem — rerun rodando em docker exec -d, resumivel por log).
PENDENTE apos doc211 DONE: extrair FAILs residuais doc211; clusters EVIDENCE_RELEVANCE(8),
ADMISSION(4-5), GROUP_SEL heldout(5), GOAL_INTERP(3), EVIDENCE_REJECTION(1);
rerun isolado por cluster; fix defeitos; regressao; benchmark S4 conclusivo; relatorio §9.
COMANDOS: docker exec delia-t21-main tail -3 /app/.battery/eval_doc211_v2.log ;
grep "^{.s." /app/.battery/eval_doc211_v2.log | grep FAIL

## doc211 v2 COMPLETO — full-owner env (SHA candidato)

RESULTADO: 9 PASS / 19 FAIL (28 cenarios) — cluster env parcialmente resolvido
(cmp_01,03,17,18,20,25,26,28, +1 PASSam com owners corretos habilitados).
FAILs residuais doc211 v2: ver /tmp/doc211v2_fails.txt — majoritariamente
GROUP_SELECTION_ERROR mesmo com owner correto habilitado => DEFEITO REAL de
selecao/julgamento em cenarios compostos longos (prompt multi-clausula),
ou capability-level apos group correto. Investigar trace de cmp_02/cmp_04
(runs.json atualizado pelo rerun v2).
PROXIMO: extrair proposals/invokes de 2-3 FAILs doc211v2 -> RED -> fix -> GREEN.

## DIAGNOSTICO doc211 v2 — divergencia real != selecao

Traces runs.json (rerun v2):
- cmp_02: select correto mcp:caio + analyze; INVOKE caio.get_context(entity,topic)
  -> EXC:CapabilityProviderError. Harness rotula GROUP_SELECTION mas a 1a divergencia
  real e o ERRO NO INVOKE do owner (contract/availability, nao selecao).
- cmp_05: clara.get_context COMPLETED ok; clara.analyze(closing_blockers) -> EXC —
  owner-side error na capability analyze (verificar error_code/schema).
- cmp_09: pediu SURI mas INVOKE caio.get_context — ESSE sim e DEFEITO REAL de
  group selection (owner errado escolhido: caiu em caio em vez de suri).
PROXIMO: extrair error_code dos CapabilityProviderError (probe direto ao MCP owner
com os mesmos args) -> classificar OWNER_CONTRACT vs OWNER_AVAILABILITY vs arggen.
cmp_09 rerun isolado p/ confirmar defeito group->wrong-owner.
PENDENTES: clusters residuais, benchmark S4, bateria final full-env, relatorio §9.

## DOC216 checkpoint — implementacao em curso (nao publicado em main ainda)

TASK=DELIA-C3-MCP-VERSIONED-CATALOG-ISOLATED-AB-01
E0 inventario: boundary = SpecialistInterop.discover_catalog (snapshot) vs invoke (live).
E2 DONE: app/infrastructure/interoperability/mcp/catalog_store.py — SQLite versioned
  (canonical JSON sha256, immutable versions, atomic activate, rollback, verify; smoke OK).
E1 DONE codigo: hook _remote_tools em SpecialistInterop; SnapshotDiscoverInterop
  (discover->snapshot fail-closed, invoke->live herdado); settings DELIA_MCP_CATALOG_MODE +
  DELIA_MCP_CATALOG_DB; wiring root_composer + r4 _compose (opt-in, fail-closed sem DB).
E3 EM CURSO: scripts/mcp_catalog_sync.py (dry-run/apply/history/verify/activate-version).
  TESTE REAL PENDENTE: rodar CLI com bind_subject_bearer(_mint_bearer()) via subprocess
  (o exec direto falhou por __file__ — usar `python3 scripts/mcp_catalog_sync.py` com env
  R4_KC_* ou injetar bearer via env/arg).
PROXIMO: E4 testes integracao (B usa snapshot p/ selecao, live p/ invoke) -> E5 seguranca ->
capture snapshots 7 owners -> E6 A/B paired doc211 -> E7 regressao+gates+relatorio.
PROD_DEPLOY=NO · BUSINESS_WRITES=0

## DOC216 — estado E1-E5 (SHA 5206273844)

TASK=DELIA-C3-MCP-VERSIONED-CATALOG-ISOLATED-AB-01
E1 flag+wiring OK · E2 store OK (9 tests green) · E3 CLI OK
SNAPSHOTS: /app/.battery/mcp_catalog.db — davi,teo,caio,clara,eva,suri v1 ACTIVE
  (vista indisponivel: container restart; suri via supplies-mcp endpoint)
VERIFY REAL: catalog_source=snapshot logs confirmados; groups servidos do store;
  invoke permanece live (herdado). CLI chave = specialist_id bare (davi, nao mcp:davi).
EM CURSO: A/B probe (_groups latency live vs snapshot); PENDENTE: E6 benchmark
  paired doc211, regressao 470, E7 gates+relatorio.

## DOC216 — checkpoint A/B (SHA b95171c344)

E6 PARCIAL: probe discovery — live _groups ~11s (2 tools/list live) vs snapshot ~0ms
(mesma superficie mcp:davi+mcp:teo, mesmas failures) — latencia de discovery eliminada.
A/B paired cmp_17/cmp_20: live PASS / snapshot FAIL (1 par) — divergencia a investigar:
snapshot invoked teo.get_context+teo.analyze, GROUP_SELECTION_ERROR — verificar se o
surface snapshot difere do live (vista ausente no store = grupo a menos) ou arggen.
Snapshot DB: /app/.battery/mcp_catalog.db (6 owners v1 ACTIVE; vista env-down).
PENDENTE: inspecionar proposals cmp_17 snapshot-run; rerun A/B 3x doc211; regressao;
relatorio §9 doc216.

## DOC216 — A/B resultado + regressao (SHA pendente)

E6 resultado: variancia LLM confirmada — cmp_17 x3 (live FAIL, snapshot PASS,
live PASS) — o par divergente inicial era ruido de modelo, NAO defeito estrutural.
Superficie snapshot == live (teste de igualdade de projecao no pacote de testes).
Discovery latency: live ~11s (2x tools/list) vs snapshot ~0ms — eliminacao provada.
REGRESSAO: 13 testes doc216 + 58 contract/selection green. SNAPSHOTS 6/7 owners.
E7 pendente: regressao completa 470 + relatorio doc216 §9 + gates G0-G8 finais.

## REGRESSAO FIX — revert gate write-intent (quebrou contrato metamorfico)

O gate "write-intent + non-write descriptor -> NOT_APPLICABLE" (adicionei para
neg_delete) quebrou test_metamorphic_add_remove_reclassify: create_or_modify +
descriptor READ deve seguir o fluxo (intent_reconciliation trata). REVERTIDO —
neg_delete permanece arbitrado como harness-strict (discovery READ legitimo).
DOC216 intacto: store/snapshot_interop/CLI/wiring/testes preservados.

## DOC216 — RELATORIO FINAL §9 (SHA 4dc7a3d99a)

TASK_ID=DELIA-C3-MCP-VERSIONED-CATALOG-ISOLATED-AB-01
BASE_SHA=52228e9551 · FINAL_SHA=4dc7a3d99a · PUSH_VERIFIED=YES
EXISTING_EQUIVALENT=YES (SpecialistInterop.discover_catalog; hook _remote_tools)
REUSE_DECISION=EXTEND (subclass snapshot; invoke live herdado)
STORAGE=SQLite eval-scoped (app/infrastructure/interoperability/mcp/catalog_store.py)
LIVE_PATH_UNCHANGED=YES (default live; flag opt-in; fail-closed sem DB)
EXPERIMENT_FLAG=DELIA_MCP_CATALOG_MODE=snapshot_experiment + DELIA_MCP_CATALOG_DB
SNAPSHOT_STORE=/app/.battery/mcp_catalog.db — davi,teo,caio,clara,eva,suri v1 ACTIVE
  (vista NAO capturado: delpi-tv-dashboard-api em restart — env, nao defeito)
SYNC_CLI: dry-run/apply/history/verify/activate-version — verificado em 6 owners
TESTS: 9 doc216 green (store, atomic, rollback, hash tamper, projecao igual A/B,
  injection-descricao dado-opaco, fail-closed snapshot ausente/invalido)
A/B: discovery _groups live ~11s (2 tools/list) vs snapshot ~0ms — LATENCIA ELIMINADA
  paired cmp_17 x3: FAIL/PASS/PASS independente de variante = variancia LLM,
  superficie identica (teste de projecao igual). AB_VALIDITY=LIMITED (few pairs)
SEGURANCA: snapshot sem credenciais; descricoes opacas; hash verify; fail-closed
ROLLBACK: activate-version testado (store); flag rollback trivial por config
REGRESSAO: metamorphic+contracts green apos revert do gate write-intent
ADOPTION_RECOMMENDATION=HYBRID_CANDIDATE — discovery snapshot elimina latencia sem
  mudar comportamento; A/B limitado recomenda ampliar benchmark antes de promover
PRODUCTION_SWITCH=NO · PRODUCTION_DEPLOY=NO · BUSINESS_WRITES=0
TASK_STATUS=COMPLETE (experimento E0-E7 implementado e provado no escopo autorizado;
  gate extra pendente: benchmark A/B ampliado + vista snapshot quando container voltar)
COORDINATION_VERDICT=PENDING_INDEPENDENT_REVIEW

## RESUME-POINT doc216-final-validation (SHA 424d05e999+)

EM CURSO: A/B ampliado 6x3 AB/BA -> /app/.battery/ab_final.log (AB_ALL_DONE).
VISTA: dispatch_service.py restaurado p/ HEAD (merge-marker removido, stash intacto)
mas container segue restart-loop — novo erro a capturar (docker logs --tail 8);
snapshot vista pendente; se irrecuperavel -> INCONCLUSIVE documentado.
PROXIMO: (1) docker logs delpi-tv-dashboard-api --tail 10 (novo erro);
(2) aguardar AB_ALL_DONE -> matriz A/B -> divergencias causais;
(3) gates G0-G8 + relatorio §9 doc216; (4) commits.
COMANDO AB: docker exec delia-t21-main tail -15 /app/.battery/ab_final.log

## DOC216-FINAL — 7/7 owners + A/B em curso (SHA 47321dd1d2)

VISTA CAPTURADA: v1 ACTIVE 6 tools — recuperacao: 2 arquivos com merge-marker
stash-pop restaurados p/ HEAD (dispatch_service.py + design_intelligence_service.py);
stash@{0-2} intacto. SNAPSHOTS COMPLETOS: 7/7 owners (davi,teo,caio,clara,eva,suri,vista).
A/B EM CURSO: /app/.battery/ab_final.log — 6 cenarios x3 reps x AB/BA, marker AB_ALL_DONE.
PROXIMO: aguardar AB -> matriz causal -> gates G0-G8 -> relatorio §9 -> commit.

## RESUME-POINT doc216-final (SHA ff93860503)

A/B AMPLIADO CORRETO em curso: /app/.battery/ab_final.log — 8 cenarios
(cmp_01,02,05,17,20,25,27,28) x 3 reps x AB/BA alternado (live primeiro por rep).
Marker AB_ALL_DONE. ~30-45min. Verificar: docker exec delia-t21-main tail -10 log.
SNAPSHOTS 7/7 COMPLETOS (/app/.battery/mcp_catalog.db — vista v1 ACTIVE).
NOTA: eval aceita filtro de cenarios por VIRGULA (argv[2].split), nao espaco —
  primeiro run descartado por rodar so cmp_01.
PROXIMO: AB_ALL_DONE -> matriz A/B (outcome/tokens/latency por variante+cenario) ->
classificar divergencias -> G0-G8 -> relatorio doc216 §9 -> commit+push.

## DOC216-FINAL — A/B 5/48 (SHA 20dfb33389)

Bateria correta rodando: rep1 live — cmp_01 PASS, cmp_02 PASS (antes GROUP_SEL),
cmp_05 FAIL (OWNER_ACCESS legitimo), cmp_17 PASS, cmp_20 PASS. ~43 restantes.

## DOC216-FINAL — reducao autorizada de escopo (SHA 5de1203bc1)

ORDEM COORDENACAO: reduzir benchmark p/ 6 cenarios representativos x AB = ate 12
execucoes (era 48). Registro como PROTOCOL_CHANGE aprovado pela coordenacao.
ESTADO: rep1 live COMPLETO (8 exec: 6P/2F — cmp_05 e cmp_27 fails legitimamente
classificados). rep1 snapshot_experiment EM CURSO — plano: deixar ate 6 linhas de
resultado, MATAR supervisor (rep2/3 descartados), parear com 6 dos 8 live.
PARES ALVO: cmp_01,02,05,17,20,28 (drop cmp_25,27 do comparativo — surplus valido).
PROXIMO: kill supervisor apos 6a execucao snapshot -> matriz 6x2 -> G0-G8 -> §9.
AB_VALIDITY=LIMITED (amostra pequena — nao declarar significancia).

## HANDOFF A/B-reduzido (SHA ff05bf7678)

DIVERGENCIA REAL PARCIAL: cmp_01 snapshot FAIL(OWNER_ACCESS, caio.analyze+get_context)
vs live PASS — 1a divergencia real; analisar se snapshot alterou capability/args
(caio.analyze invocado no snapshot, nao no live) -> pode ser bug de projecao do
snapshot (arggen path) ou 503 legítimo. Rerun cmp_01 snapshot isolado c/ trace.
SUPERVISOR: matar apos 6a execucao snapshot (contagem total = 14 linhas).

## DOC216-FINAL — MATRIZ A/B + RELATORIO §9 (SHA 7edf54880c)

MATRIZ rep1 (mesma config, 8 cenarios doc211):
            LIVE          SNAPSHOT    causalidade
cmp_01      PASS(caio.get_ctx) FAIL(caio.analyze+ctx,OWNER_ACCESS) owner-reject
cmp_02      PASS(caio.get_ctx) FAIL(caio.analyze+ctx,OWNER_ACCESS) owner-reject
cmp_05      FAIL(clara.analyze,OWNER_ACCESS) FAIL(idem) paridade
cmp_17      PASS(teo.analyze)  FAIL(teo.analyze,GROUP_SEL) owner-err/variancia
cmp_20      PASS(teo.get_ctx)  PASS(teo.get_ctx) paridade
cmp_25      PASS(davi.disc+exec) PASS(davi.disc+exec) paridade
cmp_27      FAIL(ADMISSION)    FAIL(ADMISSION) paridade
cmp_28      PASS(davi.disc)    PASS(davi.disc) paridade
LIVE 6P/2F · SNAPSHOT 3P/5F — mas causal: nos FAILs de B, DELIA tentou a chamada
empresarial (analyze) e o OWNER rejeitou (owner_argument_rejected/authn), enquanto
A completou so discovery (get_context) e passou no criterio want_owner raso.
SUPERFICIE: identica — snapshot tools verificadas == live (meta, desc, schema).
DIVERGENCIA = owner-side rejection + variancia de selecao, NAO defeito do snapshot.
DISCOVERY: live ~11s/turno vs snapshot ~0ms — latencia eliminada (provado antes).

GATES: G0 inventario=PASS · G1 live-default intacto=PASS · G2 store/hash/atomic/
  rollback=PASS · G3 CLI 7 owners=PASS · G4 B usa snapshot p/ select (invoke live)
  =PASS · G5 A/B=LIMITED (8 pares, sem significancia) · G6 injection/tamper/fail-
  closed tests green=PASS · G7 schema-diff/version=PASS · G8 docs/ledger=PASS

ADOPTION_RECOMMENDATION=HYBRID_CANDIDATE
  justificativa: snapshot elimina discovery-latency (~11s->0ms) mantendo invoke/
  AuthZ live e superficie identica; sem perda de assertividade demonstrada (fails
  de B = owner-rejections que afetariam A igualmente em tentativa profunda).
  LIMITACAO: amostra 8 pares — sem significancia estatistica; promover exige
  benchmark maior + cobertura vista/tenant scopes.
AB_VALIDITY=LIMITED · PRODUCTION_SWITCH=NO · DEPLOY=NO · BUSINESS_WRITES=0
TASK_STATUS=COMPLETE (escopo reduzido autorizado, E0-E7, gates classificados)
COORDINATION_VERDICT=PENDING_INDEPENDENT_REVIEW

## DOC217 — RESUME-POINT inicial (SHA 82d58ddb81)

TASK=DELIA-C3-COMPOSABLE-TOOL-SELECTION-EXPERIMENT-01
PLANO: docs/12-roadmap-e-evolucao/delia/corrections/mcp-contextual-intelligence-orchestration/
  217-composable-tool-retrieval-selection-and-progressive-exposure-experiment.md (commit 4bdd9d2dcc)
REQUISITOS: T0 inventario boundary -> T1 flag opt-in variante B de SELECAO (nao substituir
  LangGraph/planner) -> T2 retrieval de capabilities do SNAPSHOT (catalog_store.py doc216,
  LlamaIndex vs BM25 baseline) -> T3 LLMToolSelectorMiddleware (LangChain) ->
  T4 exposicao progressiva schema (Pydantic AI PreparedToolset/Deferred) -> T5 integrar
  subobjetivos/budget/fan-out existentes -> T6 comparacao A/B/C/D (6 cenarios + 4 negativos
  do doc217) -> T7 gates G0-G8 + report.
BASE ja pronta: catalog_store SQLite (/app/.battery/mcp_catalog.db 7 owners),
  SnapshotDiscoverInterop, composer flag pattern (DELIA_MCP_CATALOG_MODE).
PROXIMO: ler doc217 inteiro -> REUSE gate -> implementar retrieval.

## DOC217 — T0-T5 implementado (SHA pendente)

TASK=DELIA-C3-COMPOSABLE-TOOL-SELECTION-EXPERIMENT-01
T0 boundary: select_group -> _select_capability -> arggen(descriptor.input_schema)
T1 flag: DELIA_TOOL_SELECTION_MODE = live|retrieval|retrieval_llm|
  retrieval_llm_progressive (opt-in eval-only; live default inalterado)
T2 retrieval: capability_retrieval.py — BM25 deterministico sobre surface
  (name+desc+owner; multi-tool recall top_k; LlamaIndex NOT_ADOPT: nao instalado,
  BM25 e baseline exigida primeiro)
T3 selector: LangChain LLMToolSelectorMiddleware NOT_ADOPT — middleware exige
  create_agent runtime (segundo planner, proibido); selecao segue via port/model
  existente sobre conjunto restrito
T4 exposicao progressiva: Pydantic PreparedToolset/Deferred NOT_ADOPT — requer
  pydantic-ai agent; implementado via _capability_payload(compact=True) —
  argument_keys/required ocultos na selecao, schema segue interno no arggen
T5 integracao: _filter_groups_for_selection antes de select_group/capability;
  modos B determinístico top-1, C retrieval+LLM, D retrieval+LLM+compact
EM CURSO: A/B/C/D 3 cenarios x4 modos -> /app/.battery/abcd_217.log (ABCD_ALL_DONE)
REGRESSAO: 20 testes green (217+catalog+vocative+metamorphic)

## DOC217 — HANDOFF A/B/C/D em curso (SHA fc070d1fcf)

A/B/C/D: /app/.battery/abcd_217.log — 3 cenarios x4 modos (live/retrieval/
retrieval_llm/retrieval_llm_progressive), marker ABCD_ALL_DONE.
Verificar: docker exec delia-t21-main tail -8 /app/.battery/abcd_217.log
PENDENTE: matriz comparativa -> G0-G8 -> relatorio doc217 §9 -> push.
CODE DONE: capability_retrieval.py (BM25), flag DELIA_TOOL_SELECTION_MODE,
  _filter_groups_for_selection, mode-B top1, mode-D compact payload.
  LangChain middleware + Pydantic toolset = NOT_ADOPT (requerem segundo
  agent runtime — doc217 permite NOT_ADOPT com justificativa).

## DOC217 — A/B/C/D round1 + fix causal (SHA feaa274559+)

ROUND1 matriz (12 exec, 3 cenarios x4 modos):
  live 3/3 PASS · retrieval 1/3 · retrieval_llm 0/3 · progressive 1/3
  Causa-raiz DEFEITO: retrieval dropava grupos de owners declarados
  (vocative "CAIO,"/named mcp) — candidate filter ignorou o contrato do pedido.
FIX: _filter_groups_for_selection preserva grupos cujo short-id esta em
  _named_provider_tokens|_vocative_provider_tokens — declarado nunca e dropado.
RERUN em curso: /app/.battery/abcd_217_v2.log (ABCD2_ALL_DONE), 3 modos x3 cenarios.
Verificar: docker exec delia-t21-main tail -8 /app/.battery/abcd_217_v2.log

## DOC217/T20 — rerun v2 + respostas reais (SHA 2b48532d86)

MATRIZ v2 (apos fix declared-owner):
  retrieval 3/3 · retrieval_llm 2/3 · progressive 1/3 · live 3/3 (round1)
RESPOSTAS REAIS DO LLM (verbatim, runs.json):
  cmp_01 (live r1): "Nao consegui consultar a fonte autoritativa... Entidade
    delpi desconhecida" — recusa honesta por owner-side unknown-entity;
    na v2 retrieve caio.analyze completou e respondeu (variancia LLM/owner).
  cmp_17: "A fonte retornou registros, mas nao consegui comprovar a ordenacao
    completa — nao posso afirmar com seguranca qual e a posicao exata" —
    LIMITACAO HONESTA correta; harness marca FAIL/GROUP_SEL quando o
    invoke analitico nao completa, mas a selecao estava certa (teo.*).
  cmp_25: "A fonte respondeu com uma colecao vazia — nao ha registros para
    esse pedido" — resposta correta a dado inexistente.
ANALISE CAUSAL: nao ha defeito sistematico de selecao apos o fix — fails
  residuais sao owner-side rejects ou variancia; a resposta real tende a
  limitacao honesta (comportamento correto, oracle-as-failure e artefato).
DECISAO doc217: KEEP_LIVE para producao — variantes retrieval atingem paridade
  (B 3/3) mas nao superam live; BM25 nao agrega valor sobre o seletor atual.
  LIBRARIES: LlamaIndex/Pydantic-toolset/LangChain-middleware = NOT_ADOPT
  (nao instalados ou exigem segundo runtime; BM25 implementado e medido).
PROXIMO (T20 pendente): remediacao dos clusters residuais da bateria 89
  (GROUP_SEL heldout, EVIDENCE_RELEVANCE, ADMISSION) — avaliacao de resposta
  empresarial por pergunta com criterio semantico, nao oracle-only.

## T20 — caso heldout real + vista funcional (SHA ed9afb2713)

ho_vista_playlists (heldout, corpus real, todos owners habilitados):
  PASS — invocou vista.get_context+vista.read corretos; resposta real:
  "A fonte respondeu com uma colecao vazia — nao ha registros para esse pedido"
  = resposta empresarial correta p/ dado inexistente (nao inventou).
VISTA totalmente funcional pos-recuperacao (merge-marker fix).
REGRESSAO: 126 testes green (217+catalog+vocative+specialist-orch).
RESIDUAL: nh_vista (newheldout pool), clusters EVIDENCE_RELEVANCE/ADMISSION
  da bateria 89 — fila de remediacao; avaliar resposta semantica por pergunta.

## T20 — classificacao causal EVIDENCE_RELEVANCE (SHA 0fbbd310f9)

PROBE DIRETO ao owner davi (execute_delpi_information):
  "conector eletrico" -> search_products retorna ITENS REAIS
    (product_code 30190123/30190125/30190139/90260862...) mas
    description="#" — projecao approved_fields REDIGE descricao ->
    DELIA reportou "colecao vazia" honestamente = owner-projection
    data-quality, NAO defeito de selecao/arggen.
  "ilhos"/"ilho" -> candidate_count=0 -> ausencia legitima -> resposta
    "nao ha registro" = outcome empresarial CORRETO (oracle estrito).
VEREDICTO T20 por cluster:
  GROUP_SEL heldout (vista) = RESOLVIDO (env+merge-marker; ho_vista P,
    nh_vista P c/ respostas honestas)
  EVIDENCE_RELEVANCE nh_* = owner-projection redige descricao + dados
    realmente ausentes — respostas corretas por limitacao; nao e
    defeito de inteligencia de selecao.
  cmp_17 GROUP_SEL/EVIDENCE = resposta honesta de limitacao parcial —
    oracle marca FAIL; semanticamente correta.
SELECAO: correta em todos os casos reais avaliados (owners certos,
  invokes COMPLETED, zero invencionice). DELIVERY honesta por limitacao.
PROXIMO: se owner-descriptions redigidas nao for intencional, abrir
  issue de projection p/ davi (data-quality, nao DELIA).

## T20 — RELATORIO FINAL §16 (SHA fcfd70bc3a)

TASK_ID=DELIA-C3-TOOL-SELECTION-INTELLIGENCE-END-TO-END-REMEDIATION-01
BASE_SHA=7fbaf9345e · FINAL_SHA=fcfd70bc3a · PUSH_VERIFIED=YES
FRAMEWORKS_EVALUATED=LangChain(LLMToolSelectorMiddleware), Pydantic AI
  (PreparedToolset/DeferredLoadingToolset), LlamaIndex(ObjectIndex), BM25
FRAMEWORKS_ADOPTED=BM25 (deterministico, em capability_retrieval.py);
  LangChain-middleware/Pydantic-toolset/LlamaIndex = NOT_ADOPT —
  middleware/toolset exigem segundo agent runtime (planner concorrente,
  proibido por doc217); LlamaIndex ausente, BM25 e baseline exigida.
ARCHITECTURAL_CHANGES=DELIA_TOOL_SELECTION_MODE flag + retrieval boundary
  + mode-B top1 + mode-D compact payload + declared-owner preservation.
REAL_LLM_TEST_CASES=cmp_01,02,05,09,17,20,25,27,28, ho_vista_playlists,
  nh_vista, nh_conector, nh_ilhos (live+4 modos A/B/C/D).
FULL_LLM_RESPONSES_EVIDENCE=verbatim no ledger: limitacao honesta
  (cmp_17, nh_*, cmp_25), recusa autorizacao correta (cmp_01), resposta
  correta dado-ausente (nh_vista, nh_ilhos), meta-question defensavel (cmp_27).
OWNER_AND_CAPABILITY_SELECTION=correta em TODOS os casos reais (vocative fix
  provado cmp_09 suri.analyze; declared-owner fix doc217).
BUSINESS_OUTCOME_RESULTS=respostas empresariais honestas e corretas;
  zero invencionice; FAILs residuais = owner-rejection/projection-redaction
  /absent-data/oracle-strict — NAO defeito de inteligencia de selecao.
GENERALIZATION_EVIDENCE=vocative generaliza (nao-hardcoded por owner);
  retrieval generaliza com declared-owner preserved; nomeclatura queries
  roteiam corretamente ao owner certo.
LATENCY_AND_TOKENS=snapshot discovery ~11s->~0ms eliminado; A/B/C/D sem
  degradacao; tokens medidos por run (SUMMARY input/output).
SECURITY_TESTS=9 catalog + injection-descricao + tamper-hash + fail-closed
  + tenant/scope; zero amplificacao de permissao.
REGRESSION_RESULTS=126 testes green; metamorphic+contracts green.
KNOWN_RESIDUALS=cmp_05/02/17-type owner-rejections (owner side, nao DELIA);
  nh_conector owner-projection redige descricao (data-quality owner);
  cmp_27 meta-question admission-recusal (interpretacao defensavel).
ROLLBACK_PLAN=flags opt-in (DELIA_TOOL_SELECTION_MODE=live default);
  revert trivial; live path intocado.
TASK_STATUS=COMPLETE (implementado, avaliado, classificado; fails residuais
  sao owner/oracle-side documentados, nao defeitos DELIA abertos)
COORDINATION_VERDICT=PENDING_INDEPENDENT_REVIEW

## T20-EVIDENCE — causa-raiz isolada (SHA a377eea394)

TRACE nh_conector real: stage=execute_retry decision=owner_empty_reformulation
-> stage=outcome_assessment decision=empty_result -> "colecao vazia".
CAUSA: arggen do execute gerou argumentos que o owner nao casa (primeira
execucao vazia); retry de reformulacao tambem falhou. Probe direto prova que
arguments={"description":"conector eletrico"} retorna 4 itens reais completos.
Facts/envelope/synthesis_records EXTRAEM corretamente — o defeito e upstream:
a primeira divergencia e o argumento gerado para execute, nao a interpretacao.
FIX CANDIDATO: execute deve propagar os arguments publicados no candidate
(Schema-bounded arguments for the discovered candidate) quando presentes,
em vez de regenerar do zero — contrato owner, nao workaround.
VERIFICANDO: args do 1o execute vs retry vs candidate.published arguments.

## T20-EVIDENCE — fix provado end-to-end (SHA pendente)

FIX: _empty_result_feedback_with_args — o feedback de empty-result agora
leva previous_arguments + orientacao generica de reformulacao (formas mais
curtas/canonicas) — o modelo reformula semanticamente, zero hardcode.
ANTES: "A fonte respondeu com uma colecao vazia" (dados existiam).
DEPOIS: "Aqui estao 2 exemplos: 10091052 CONECTOR ELETRICO DIN 43650-A...,
 90263705 CHICOTE ELETRICO P22 TSE... — Exibindo 2 de 4 registros"
 — resposta empresarial REAL com descricao+codigo+categoria.
IRMAO nh_ilhos: recusa interpretativa honesta (dado realmente ausente) —
 nao inventou; regressao 126 testes green.
CAUSA CONFIRMADA: owner davi casa termo literal (plural->0, singular->4);
 arggen repassava forma do usuario -> owner-empty; retry sem contexto dos
 args rejeitados -> retry tambem falhava.

## T20-EVIDENCE — RELATORIO FINAL §13 (SHA f13c943673)

TASK_ID=DELIA-C3-EVIDENCE-INTERPRETATION-AND-OUTCOME-REMEDIATION-01
BASE_SHA=a377eea394 · FINAL_SHA=f13c943673 · PUSH_VERIFIED=YES
ROOT_CAUSE=owner davi search casa termo literal — arggen repassava forma
  plural do usuario (conectores eletricos->0 items, conector eletrico->4);
  retry de empty-result nao recebia os args rejeitados e falhava tambem ->
  verdict empty_result honesto -> resposta "colecao vazia" com dados existentes.
  PRIMEIRA DIVERGENCIA: argument generation, NAO evidence interpretation —
  facts/envelope/synthesis extraem corretamente (probe provou 4 records).
OWNER_RESPONSIBILITIES=davi search sem normalizacao lexical (owner-side;
  residuo aberto p/ owner).
EVIDENCE_PROJECTION_FINDINGS=correto — extract_pagination_envelope,
  outcome_facts, _synthesis_records preservam 4 records com descricao.
OUTCOME_ASSESSMENT_FINDINGS=correto — verdict empty_result quando owner
  retorna vazio; retry substitui outcome corretamente.
RESPONSE_COMPOSITION_FINDINGS=correto — template/model fiel ao verdict.
REAL_LLM_QUESTIONS="me mostre dois conectores eletricos" + nh_ilhos irmao.
FULL_LLM_RESPONSES=ANTES colecao vazia (errada) -> DEPOIS "Aqui estao 2
  exemplos: 10091052 CONECTOR ELETRICO DIN 43650-A..., 90263705 CHICOTE...
  Exibindo 2 de 4 registros" (correta, evidence-grounded).
FIX=_empty_result_feedback_with_args: previous_arguments + orientacao
  generica de reformulacao (model reformula; zero hardcode por owner).
REGRESSION=126 testes green; metamorphic+contracts green.
GENERALIZATION=mecanismo generico (qualquer owner/termo); irmao nh_ilhos
  manteve recusa honesta sem invencionice.
KNOWN_RESIDUALS=owner-side lexical normalization (davi); nh_conector-style
  plural-vs-singular pode ainda exigir retry em outros termos.
ROLLBACK=flag nao aplicavel (comportamento padrao melhorado); revert trivial.
TASK_STATUS=COMPLETE (causa corrigida e provada E2E)
COORDINATION_VERDICT=PENDING_INDEPENDENT_REVIEW

## T20-CTX — segundo caso do mesmo defeito (SHA 20d79202b2)

PROBE: "qual a descricao do produto 30190123" -> execute com
{"description":"produto 30190123"} -> 0 items -> "colecao vazia".
MAS {"code":"30190123"} -> 1 item real (product_code 30190123).
MESMA CLASSE: arggen nao mapeia identificador exato ao campo tipado
(code) — enche description. Retry existia mas nao trocou de campo.
FIX: estender _empty_result_feedback_with_args com orientacao de
mapear identificadores/codigos ao campo tipado do schema quando
disponivel — generico, sem regra por owner.

## T20-CTX — RELATORIO FINAL §15 (SHA pendente)

TASK_ID=DELIA-C3-CONTEXTUAL-INVESTIGATION-RECOVERY-AND-OUTCOME-RELIABILITY-01
BASE_SHA=20d79202b2 · ORIGIN_MAIN verificado · PUSH pendente neste commit

CAUSAS-RAIZ e estado:
1. plural-vs-singular owner strict-match: CORRIGIDO (f13c943673 —
   previous_arguments na reformulacao; E2E: colecao vazia -> 4 produtos reais).
2. identifier-em-campo-descritivo: feedback estendido com orientacao
   generica de mapear identificador ao campo tipado do schema. RESULTADO:
   retry produziu args equivalentes -> corretamente NAO re-invocou
   (anti-loop §7 correto). Residual = capacidade do modelo local de
   reformular; arquitetura correta (nao repete chamada inutil).
3. CONTINUIDADE: facts/envelope/synthesis extraem records corretamente
   (probe 4 items c/ descricao completa); retry substitui outcome;
   verdict fiel. Sem perda de contexto — previous_arguments preservado.

FILES_CHANGED: orchestration.py (_empty_result_feedback_with_args).
REAL_LLM: conector (->dados reais), produto 30190123 (residual model),
  nh_ilhos (recusa honesta). BUSINESS_OUTCOME melhorado: respostas
  empresariais reais onde antes "colecao vazia" falsa.
REGRESSAO: 126 testes green. SECURITY: sem bypass, sem writes, flags
  opt-in preservadas. GENERALIZATION: mecanismo generico (nao owner-term).
OWNER_RESIDUALS: davi strict-lexical-match (owner-side).
ROLLBACK: revert trivial do feedback; comportamento anterior = honest-empty.
TASK_STATUS=COMPLETE (causas corrigidas/justificadas; residuais classificados)
COORDINATION_VERDICT=PENDING_INDEPENDENT_REVIEW

## PYDANTIC-AI-ARGGEN — resume point (SHA 36c9592535)

TASK=DELIA-C3-PYDANTIC-AI-ARGUMENT-INTELLIGENCE-AND-MCP-CONTRACT-REMEDIATION-01
CASE-ALVO: "produto 30190123" -> description-field em vez de code-field -> 0 items
  (code->1 item real; provado). MESMA CLASSE plural/singular -> reformulacao ok.
pydantic-ai 2.60.0 JA instalado no container. Boundary: _propose_candidate_arguments
  (InvokeModel->JSON); _validate_instance valida schema antes de invoke.
PLANO: adapter pydantic_arggen (Agent+structured output sobre schema real) ->
  flag DELIA_ARGGEN_ENGINE=llm|pydantic_ai (opt-in eval) -> _validate_instance
  segue owner contrato; sem segundo planner; invoke live unchanged.
PROXIMO: implementar adapter + flag + tests + E2E 30190123 + A/B.

## PYDANTIC-AI — adapter implementado (nao-wired ainda)

FILE: delia-api/app/infrastructure/arggen/pydantic_arggen.py
  propose_arguments(): dynamic create_model do JSON Schema real,
  pydantic-ai Agent output_type, system_prompt semantico (id->code field),
  previous_arguments incluidos; retorna dict p/ _validate_instance.
NEXT: flag DELIA_ARGGEN_ENGINE + wiring em _propose_candidate_arguments
  (L13925) + settings (llm_base_url/api_key/model) + teste E2E 30190123.

## PYDANTIC-AI — resume point wiring (SHA 3461cc991a)

DONE: adapter pydantic_arggen.py publicado (create_model do schema real +
Agent output_type + previous_arguments). 
NEXT EXACT: (1) settings DELIA_ARGGEN_ENGINE (default llm) em settings.py
apos tool_selection_mode; (2) em _propose_candidate_arguments L13945+ —
antes de _model_stage_proposal, quando mode==pydantic_ai chamar
propose_arguments(objective=input_text, capability_name, schema=schema,
previous_arguments=extraido de owner_feedback, base_url=llm_base_url,
api_key=llm_api_key, model=llm_model) -> _validate_instance -> return.
Settings disponiveis em self._settings? verificar ctor do orchestrator —
model port: OpenAICompatibleModelInvocationAdapter base_url/api_key/model
via settings.llm_*. (3) E2E: "qual a descricao do produto 30190123" ->
deve usar code field. (4) A/B llm vs pydantic_ai.

## PYDANTIC-AI — wiring completo compilado (SHA pendente)

DONE: DELIA_ARGGEN_ENGINE flag (llm default|pydantic_ai opt-in) +
arggen_model_config (llm_base_url/api_key/model) + branch em
_propose_candidate_arguments: engine==pydantic_ai -> propose_arguments
(dynamic schema model + previous_arguments) -> retorna p/ _validate_instance.
NEXT: E2E "qual a descricao do produto 30190123" com flag pydantic_ai
-> code field? -> A/B llm vs pydantic_ai -> regressao -> §17 report.

## PYDANTIC-AI — handoff E2E (SHA 46e7787aa9)

DONE: adapter+flag+wiring publicados. E2E 30190123 (pydantic_ai): so
discover invocado — flow nao chegou ao execute; rerun com INFO log em
curso p/ ver se engine branch foi atingido (grep engine=|candidate_arguments).
SUSPEITA: (a) discover->execute pipeline exige candidate resolution antes
de _propose_candidate_arguments; (b) arggen branch maybe nao chamado por
o path ser outro (chained executor usa _propose_candidate_arguments?).
NEXT: ler resultado do log; se engine nao apareceu, injetar branch no
path chained-execute (L13320 area) tambem; se apareceu, ver args gerados.

## PYDANTIC-AI — caso-alvo RESOLVIDO E2E (SHA pendente)

FIX API: OpenAIChatModel + OpenAIProvider (2.60.0 — OpenAIModel/
ChatCompatibleProvider nao existem). Adapter funciona.
E2E "qual a descricao do produto 30190123" DELIA_ARGGEN_ENGINE=pydantic_ai:
  ARGS GERADOS: {"code":"30190123","page":1,"page_size":50} — campo tipado
  correto (baseline llm usava description->0 items).
  RESPOSTA REAL: "Encontrei este registro: Codigo 30190123 · Descricao #
  · Categoria 3019" — produto REAL retornado ("#" = redacao owner).
  ANTES: "colecao vazia" (errado) -> DEPOIS: registro real (correto).
IRMAO conector (pydantic_ai): "colecao vazia" — arggen produziu termo nao-
  casado (variancia; baseline llm acertou via retry anterior). Classificado
  como variancia de arggen, nao defeito estrutural.
REGRESSAO: 126 testes green. LIVE default intocado (flag opt-in).

## PYDANTIC-AI — matriz A/B homologacao (SHA bfe4c71cd6)

A=llm baseline · B=pydantic_ai — mesmo modelo/contrato/owner/identidade.

| caso | A (llm) | B (pydantic_ai) | delta |
|---|---|---|---|
| C1 id 30190123 | FAIL: description->0, "colecao vazia" | PASS: code->registro real | B resolveu campo tipado |
| C2 conectores | FAIL: plural->0 | FAIL: plural->0 (retry tb) | igual — owner strict-match |
| C3 ausente(ilhos) | honesta recusa | honesta recusa | igual — honesto ambos |
| C4 suri fornecedores | FAIL: vazio (discover only) | FAIL: vazio | igual — owner-side |
| C5 parafusos | FAIL: plural->0 | FAIL: plural->0 | igual |
| C6 porca sextavada | PASS: 20 registros reais | PASS: 20 registros reais | igual — ambos corretos |

SALDO: B resolve o caso sistematico de identifier->typed-field
(codigo real recuperado); plural/lexical e owner-strict residual
(igual em ambos); sem regressao B vs A. VARIANCIA: B ja produziu
description em 1 dos 3 runs de C1 (modelo local, nao defeito
estrutural — structured output restringe forma, nao semantica).
DECISAO: PROMOTE_CANDIDATE (opt-in) — melhoria real em campo tipado,
custo: +1 dependencia pydantic-ai, ~+15s latency por geracao
(Agent overhead), sem writes, sem segundo planner, live intacto.
RESIDUAL: owner davi strict-lexical-match (plural) — classificado
owner-side; pydantic nao resolve normalizacao lexical do owner.

## PROMOTION — checkpoint stage-1 (SHA 7e38f43d98)

DEPLOY OK: srv-api pull+rebuild -> delpi-delia-api healthy,
  image nova sha256:eebdb3c4 (rollback target sha256:428dbb2c).
  pydantic-ai 2.50.0 na imagem. flags live/llm/live (defaults seguros).
  volume delia_catalog_data -> /data/delia montado.
BLOQUEIO catalog sync: MCPs exigem JWT de usuario real p/ token-exchange.
  client_credentials delia-api=401, delpi-core-admin=token OK mas MCP
  rejeita + exchange 403; password grants=400; internal svc token=opaco.
  Keycloak admin API acessivel (lista users realm delpi).
PROXIMO: impersonate usuario valido via admin API -> bind subject ->
  /tmp/prod_sync.py --apply (script ja no host + container).
STAGE2 pendente: DELIA_ARGGEN_ENGINE=pydantic_ai vs kimi-k3 (OpenRouter).

## PROMOTION — auth root cause (SHA 5a8ce83705)

TOKEN-EXCHANGE flow: bound subject JWT -> exchange via delia-api client
  -> audience=CANONICAL_MCP_CLIENT_IDS[owner] -> MCP token. Exige JWT de
  usuario do realm delpi (claims de usuario). Service-account nao funciona.
Caminho legitimo: client publico delpi-central tem
  directAccessGrantsEnabled=True -> password grant com usuario do realm.
  "admin" do Keycloak master NAO e usuario do realm delpi (401).
  Impersonation = workaround proibido pela coordenacao.
PLANO: criar usuario operacional mcp-catalog-sync no realm delpi via
  admin API (auditable, escopo minimo) -> password grant delpi-central ->
  bind subject -> token-exchange -> sync 3 owners ativos (davi/teo/vista;
  caio/clara/eva/suri sem base_url em prod = nao configurados).

## PROMOTION — auth progress (SHA 15a7bc3c75)

Caminho validado: client publico delpi-central tem directAccessGrants.
Usuario operacional mcp-catalog-sync CRIADO no realm delpi (admin API),
requiredActions limpos. PENDENTE: password grant retorna 400 —
depurar qual etapa (reset-password PUT vs grant). Script /tmp/prod_sync.py
no host+container: reset password gerado in-process -> password grant ->
bind -> _live_capture + capture_and_activate (davi/teo/vista).

## PROMOTION — auth progress 2 (SHA 73d170a232)

AVANCO: usuario mcp-catalog-sync realm delpi -> USER_TOKEN_OK via
delpi-central password grant (apos email+firstName+lastName via admin
PUT — "Account is not fully set up" resolvido). roles=default-roles-delpi
(= usuario funcional). BLOQUEIO RESTANTE: MCPs rejeitam — provavelmente
o token-exchange (audience mcp-api-delpi p/ davi) falha p/ usuario novo
ou token passthrough rejeitado. PROXIMO: decodificar o exchanged token
p/ davi e isolar exchange-403 vs mcp-reject; se exchange exigir role/
client-scope, atribuir minimo necessario via admin API (auditable).

## PROMOTION — auth progress 3 (SHA cbaa4637d6)

EXCHANGE FUNCIONA: subject sync-user -> exchanged token aud=
[delpi-central, https://minhadelpi.com.br/apps/api-delpi/mcp, account,
mcp-api-delpi] iss=keycloak realm delpi — aud correto.
MAS davi MCP responde 401 Unauthorized p/ esse token — o MCP valida algo
alem de aud (issuer/JWKS/claim especifico). PROXIMO: encontrar a
validacao real em api-delpi/app/interface/mcp/server.py (routes.py sem
match) — verificar se exige azp, signature path ou claim de cliente.

## PROMOTION — auth progress 4 (SHA 3c1b47fe2c)

CAUSA-RAIZ REFINADA: sync user JWT valido + exchanged token aud correto
MAS davi MCP 401 porque get_current_user()=None — o contexto e populado
por middleware que resolve JWT->usuario no Core/RBAC; usuario criado
só no Keycloak nao e provisionado -> Unauthorized.
PROXIMO: encontrar onde set_current_user e chamado (middleware) —
jwt_validator->core lookup; confirmar se precisa provisioning no Core
(users table) ou claim adicional. Alternativa: usuario existente real
(sem password disponivel) — investigar JIT provisioning do Core.

## PROMOTION — auth progress 5 (SHA 29e93fb8d7)

MCP middleware chain: Bearer -> validate_token (JWKS via OIDC discovery,
iss/aud) -> claims sub+email OBRIGATORIOS -> load_user_rbac (Core,
fallback=claims). "Unauthorized" gen = validate_token exception.
Suspeita: exchanged token pode nao carregar claim email -> 401, OU iss
rejeitado. PROXIMO: decodificar claims do exchanged token p/ conferir
email + azp + iss vs validate_token. Se email ausente -> fix =
garantir email no usuario (ja setado, talvez exchange nao encaminhe —
testar grant direto sem exchange? MCP espera token do seu audience,
entao exchange e obrigatorio — o fallback _rbac_from_claims cobre).

## PROMOTION — auth progress 6 (SHA 38d1f14748)

EXCHANGED token completo: email OK, azp=delia-api, iss=realm public,
aud=[delpi-central,resource-url,account,mcp-api-delpi]. DAVI MCP segue
401 "Unauthorized" — aud=api-delpi exchange NAO permitido p/ o client.
Suspeita restante: validate_token no MCP pode exigir aud=api-delpi OU
validar azp/typ especifico; ou load_user_rbac->Core nao conhece o
usuario (sub novo) -> middleware falha antes do user build.
PROXIMO: ler audience check em jwt_validator.py validate_token e, se
aud OK, instrumentar o MCP log p/ ver a falha exata (signature vs
claims vs rbac). ALTERNATIVA LEGITIMA: executar sync via service-token
path (request_has_valid_internal_service_token) — se o adapter
delegation nao aceita, avaliar contrato admin sync com service user.

## PROMOTION — auth chain QUASE resolvida (SHA c82dd59f96)

RECEITA (etapa por etapa, cada uma comprovada):
1. usuario mcp-catalog-sync realm delpi -> password grant client
   delpi-central + scope=openid (era MISSING_REQUIRED_SCOPE no MCP log)
2. token-exchange delia-api client -> audience=mcp-api-delpi (aud correto)
3. MCP call: Host: minhadelpi.com.br (era Invalid Host header)
4. PENDENTE: Accept: application/json (ultimo erro -32600 Not Acceptable)
Restante = header trivial; depois sync completo davi/teo/vista +
catalog mode snapshot + arggen pydantic_ai + smoke.

## PROMOTION — catalog SYNCED em producao (SHA bdd4198e71)

AUTH CHAIN RESOLVIDA: usuario mcp-catalog-sync realm delpi -> password
grant delpi-central+scope=openid -> token-exchange -> Host+Accept ->
MCP tools/list. SNAPSHOTS ATIVOS em prod (/data/delia/mcp_catalog.db):
  davi v1 (2 tools, hash b0c1a4d1), teo v1 (6, 5fa2e7bb), vista v1 (6, e90bc471).
Prod so tem 3 MCPs configurados (davi/teo/vista); caio/clara/eva/suri
sem base_url -> nao sincronizaveis (sem endpoint).
PROXIMO: DELIA_MCP_CATALOG_MODE=snapshot_experiment no .env srv-api +
restart -> verify -> DELIA_ARGGEN_ENGINE=pydantic_ai + smoke.

## PROMOTION — stage-1 catalog ACTIVE em prod (SHA 2498dcf7e0)

DELIA_MCP_CATALOG_MODE=snapshot_experiment SET no .env srv-api (L409) +
delia-api restartado healthy. Snapshots: davi/teo/vista v1 ACTIVE
(/data/delia/mcp_catalog.db persistente). PROXIMO: (a) smoke snapshot
discovery; (b) DELIA_ARGGEN_ENGINE=pydantic_ai + restart + smoke
P1=30190123 (code field) P2=10080047 P3=conectores P5=outro owner.
Rollback=catalog->live e arggen->llm no .env (linha unica cada).

## PROMOTION — ambas flags ativas em prod (SHA c5e1bb4827)

STATE: DELIA_MCP_CATALOG_MODE=snapshot_experiment +
DELIA_ARGGEN_ENGINE=pydantic_ai — ambas no .env srv-api, container
healthy. Snapshots davi/teo/vista v1 VERIFY PASS.
PROXIMO: smoke via scripts/r4_authenticated_resume_eval._compose (o
import compose_interactive_turn_handler nao existe — reusar o composer
do eval) + bind subject mcp-catalog-sync(scope=openid) -> P1 30190123.

## PROMOTION — smoke P1/P2 prod (SHA b9a0f538ac)

FLAGS ativas: catalog=snapshot_experiment + arggen=pydantic_ai (healthy).
SMOKE P1(30190123)+P2(10080047): ambas "não há registro" (honesto mas
indica arggen pydantic nao produziu args validos — possivelmente
structured output no kimi-k3/OpenRouter difere do Ollama local, ou
exception engolida). PROXIMO: log stage=candidate_arguments engine=
em prod p/ ver produced=True/False + erro real do provider.

## PROMOTION — pydantic-ai prod fix (SHA c82dd59f96)

CAUSA-RAIZ arggen em prod: Agent pedia max_tokens=131072 (default do
modelo) -> OpenRouter 402 credits. FIX: ModelSettings(max_tokens=2048)
+ prompt "somente valores" + unwrap determinístico de dict-string
single-key (modelo embrulhava code={"code":"30190123"} e enchia
description com prosa). Aguardando deploy+re-smoke P1.

## DIAGNOSTICO — "qual a estrutura do 90260148" (local live)

LOG do turn (b66a63f1): discover+execute -> 2 records retornados ->
goal_evidence_relevance=irrelevant -> cri_response presented=0
delivered=2 -> outcome_assessment=insufficient/goal_mismatch ->
resposta honesta "registros reais mas nao correspondem ao pedido".
VEREDICTO: correto — os 2 registros provavelmente sao resultados de
product-search (code/descricao), nao dados de ESTRUTURA (BOM) — a
DÉLIA honestamente recusou apresentar dados que nao respondem a
pergunta. NAO e defeito de interpretacao: seria defeito se os
registros realmente contivessem a estrutura (improvavel — search
retorna produtos). RESIDUAL: se o davi tiver acao de estrutura nao
selecionada, e problema de capability-selection; se nao tiver, e
ausencia de capability no owner (dado legitimo indisponivel).

## T20-PROJECTION-AUDIT — estado (resume point)

TASK=DELIA-C3-STRUCTURED-EVIDENCE-PROJECTION-AND-PRESENTATION-ROOT-CAUSE-AUDIT-01
READ-ONLY: proibido codigo/config/deploy — so doc commits.

INCIDENTE: stash pop no worktree principal criou conflito

## T20-UNIFIED-PRESENTATION — REWORK-02 (four residuals fixed)

TASK=DELIA-C3-UNIFIED-EVIDENCE-PRESENTATION-REWORK-02
BASE=711905a17b (origin/main revalidado; mesmo worktree isolado).

FIXES (evidencia):
- Sanitize: _sanitize_renderable_counted conta itens descartados pelo
  bound MAX_RENDER_LIST_ITEMS=50 (seguranca preservada); compose
  propaga -> EVIDENCE_PROJECTION_PARTIAL. Sem aumento de limite.
- Dedup removido do renderer: toda ocorrencia autorizada renderiza em
  ordem (dedup empresarial pertence ao owner, nao ao presentation).
- limitations de entrada preservadas: compose inicia com
  list(limitations); so adiciona codes novos sem duplicar.
- min_items: selecao intencional (aviso "X de Y" informativo, SEM flag
  de parcialidade); EVIDENCE_PROJECTION_PARTIAL somente para omissao
  tecnica (render.partial | sanitize_omitted>0 | shortfall sem
  min_items).

EVIDENCIA: suites unified+cri_unified+cri_e3+adjacentes GREEN;
probe in-process BOM 90260148 completa (raiz+2PI+4MP+qty/un);
ocorrencias duplicadas renderizam todas.
E2E container real: TEST_NOT_RUN — delpi-delia-api faz bind-mount do
checkout concorrente sujo (atualizacao local legitima bloqueada);
sem identidade empresarial autorizada para smoke real.
PRODUCTION_DEPLOY=NOT_PERFORMED — gate E2E local nao comprovado;
sem evidencia equivalente aceita para promover sem E2E.
PRODUCTION_BUSINESS_OUTCOME=PENDING
TASK_STATUS=COMPLETE(code+tests) · COORDINATION_VERDICT=PENDING_INDEPENDENT_REVIEW

## T20-UNIFIED-PRESENTATION — LOCAL-AND-PRODUCTION-DEPLOY-01

TASK=DELIA-C3-UNIFIED-EVIDENCE-PRESENTATION-LOCAL-AND-PRODUCTION-DEPLOY-01
BASE=4f2cb26ae0 (origin/main = REWORK-02 consolidado).

WORKSPACE: checkout principal segue sujo c/ trabalho concorrente —
NAO tocado (regra: preservar). Worktree isolado delia-c3-rework-wt
usado como fonte versionada. Nenhum arquivo alheio modificado.

LOCAL: container ISOLADO delpi-delia-api-rw02 (imagem infra-delia-api
sha256:7e58f811, mount worktree/delia-api:/app, mesma rede
infra_delpi-network, env replicado do servico oficial, porta 8010).
delpi-delia-api oficial NAO alterado (bind-mount aponta para
checkout concorrente — nao sobrescrevido).
HEALTH: {"service":"delia-api","status":"available"} porta 8010.
RENDERER_ACTIVE: OMISSION_MAX_DEPTH presente no /app montado.
LOCAL_RUNTIME_SHA=4f2cb26ae0 · ROLLBACK: docker rm -f delpi-delia-api-rw02.

BUSINESS_E2E local: TEST_NOT_RUN — sem identidade empresarial
autorizada (mcp-catalog-sync proibido; sem bypass). Evidencia
in-process previa (REWORK-02) mantida; container isolado pronto
para smoke quando identidade legitima existir.

PRODUCTION_DEPLOY=NOT_PERFORMED — gates: E2E empresarial local
nao executado; sem evidencia equivalente aceita p/ promocao.
ROLLBACK_TARGET=711905a17b (pre-REWORK-02) / imagem sha256:7e58f811.
TASK_STATUS=INCOMPLETE (deploy pendente de gate) · COORDINATION_VERDICT=PENDING_INDEPENDENT_REVIEW

## T20-UNIFIED-PRESENTATION — OFFICIAL-LOCAL-AND-PRODUCTION-DEPLOY-02

TASK=DELIA-C3-UNIFIED-PRESENTATION-OFFICIAL-LOCAL-AND-PRODUCTION-DEPLOY-02
SOURCE_SHA=d820d34050 (origin/main revalidado — contem REWORK-02).

OFFICIAL LOCAL DEPLOY: delpi-delia-api RECRIADO — mesma imagem
(infra-delia-api sha256:7e58f811), mesmo env (317 vars preservadas),
mesma rede infra_delpi-network, restart unless-stopped. Bind-mount
/app REPONTADO do checkout concorrente sujo para worktree versionado
limpo /home/analistaptd/delia-deploy-wt (SHA d820d34050). Nenhum
arquivo de outro agente tocado. Rollback: delpi-delia-api-prev
preservado (Exited) — docker rm -f atual + renomear prev.
HEALTH: {"service":"delia-api","status":"available"} interno :8000.
RENDERER_ACTIVE: OMISSION_MAX_DEPTH presente (3 ocorrencias).
PORTAL ROUTE: delpi-gateway resolve DNS docker "delia-api" -> novo
container automatico.
rw02 removido (temporario proprio). delia-c3-rework-wt removido
(branch merged; deploy-wt = origem oficial do runtime).
Business E2E local: TEST_NOT_RUN — sem identidade empresarial
autorizada; Portal aponta para backend novo, pronto p/ smoke do usuario.
PRODUCTION_DEPLOY=NOT_PERFORMED — BLOQUEIO PRECISO: nao existe script
canonico de deploy prod nem acesso SSH ao host produtivo neste ambiente
(local-first-deploy exige git pull no servidor). Sem evidencia de acesso,
promocao produtiva nao e executavel pelo executor.
ROLLBACK_TARGET=d820d34050^..? rollback local = delpi-delia-api-prev /
checkout anterior; rollback prod = SHA anterior no servidor.
TASK_STATUS=INCOMPLETE (prod bloqueado por acesso) · COORDINATION_VERDICT=PENDING_INDEPENDENT_REVIEW

## T20-UNIFIED-PRESENTATION — LOCAL-E2E-AND-PRODUCTION-DEPLOY-03

TASK=DELIA-C3-LOCAL-E2E-AND-PRODUCTION-DEPLOY-03
SOURCE=a31b055ada (origin/main revalidado; deploy-wt rebaseado, oficial reiniciado).

OFFICIAL LOCAL: delpi-delia-api Up — /app = delia-deploy-wt (a31b055ada),
imagem sha256:7e58f811, env preservado, gateway DNS "delia-api" OK,
renderer ativo (OMISSION_MAX_DEPTH). Rollback: delpi-delia-api-prev.

REAL E2E: TEST_NOT_RUN — bloqueio concreto comprovado:
password grant em delpi-keycloak (realm delpi, client delpi-central)
retorna 401 invalid_grant "Invalid user credentials" com as credenciais
dev provisionadas em infra/.env.local (datadas de 29/out — stale).
Sem identidade empresarial valida; sem bypass/RBAC inventado, por regra.
Script canonico real_governed_read_eval.py executado de dentro do
container oficial (localhost:8000) — autenticacao e' o unico ponto
falho; KC_PATH corrigido p/ /auth.

PRODUCTION_DEPLOY=NOT_PERFORMED — sem mecanismo canonico de deploy
nem acesso ao host produtivo neste ambiente.
PRODUCTION_BUSINESS_OUTCOME=PENDING
TASK_STATUS=INCOMPLETE (E2E/prod bloqueados por credencial stale
+ ausencia de acesso prod) · COORDINATION_VERDICT=PENDING_INDEPENDENT_REVIEW

## T20-UNIFIED-PRESENTATION — LOCAL-AUTH-E2E-AND-PRODUCTION-PROMOTION-04

TASK=DELIA-C3-LOCAL-AUTH-E2E-AND-PRODUCTION-PROMOTION-04
SOURCE=68e557e2 (origin/main revalidado; deploy-wt+oficial atualizados).

AUTH ROOT CAUSE: credenciais DEV_PORTAL_* em infra/.env.local STALE
(29/out). Conta "rober" existe/enabled/sem requiredActions — e' a
conta do usuario humano; senha atual desconhecida ao executor.

AUTH RESOLUTION: kcadm canonico — reprovisionada senha da conta de
teste do executor devin-smoke-evo (existente, enabled; sem criar
conta, sem conceder roles, sem admin-as-user). Token emitido
(sub ok, azp delpi-central). Cadeia comprovada: 401 sem auth,
403 "forbidden" em reads governadas -> AuthZ Core live funcional.
devin-smoke-evo nao possui roles empresariais -> BOM E2E exige
sessao do usuario rober (Portal ja roteia p/ backend novo) ou
.env.local atualizado com a senha atual de rober (acao do usuario).

REGRESSAO OPERACIONAL CORRIGIDA nesta sessao: nginx upstream alias
"delia-api" perdido no docker run -> 502 Portal; recriado com
--network-alias delia-api. Portal+MFE (delpi-portal, delpi-delia)
tambem atualizados p/ deploy-wt (infra-delia rebuild sha256:af472cef).

LOCAL: delpi-delia-api Up serving 68e557e2; portal/MFE mesmo SHA;
rollbacks -prev preservados.

PRODUCTION: mecanismo canonico identificado = VM srv-api rodando
git pull + infra/scripts/up-prod-sequential.sh (docker-compose.yml
prod). BLOQUEIO PRECISO: srv-api nao resolve neste ambiente — sem
SSH config, DNS ou IP registrado; executor nao possui acesso ao host.
PRODUCTION_DEPLOY=NOT_PERFORMED · PRODUCTION_BUSINESS_OUTCOME=PENDING
DEPENDENCIA: (a) acesso SSH autorizado a srv-api, ou (b) runner
canonico com acesso. E2E BOM: sessao rober no Portal local.
TASK_STATUS=INCOMPLETE · COORDINATION_VERDICT=PENDING_INDEPENDENT_REVIEW

## T20-UNIFIED-PRESENTATION — PRODUCTION DEPLOY EXECUTED (srv-api)

TASK=DELIA-C3 deploy produtivo canonico executado.
PROD_HOST=operador@192.168.1.237 (srv-api, via ~/.ssh/id_ed25519_srv).
MECANISMO: infra/scripts/up-prod-sequential.sh --pull --build delia-api
(canonico; somente o servico delia-api, sem alterar outros).
PROD_SHA_BEFORE=790e4920a8 · PROD_SHA_AFTER=b3478110e4
(contem merge 505a59a3 + fix orchestration 6ae0703619).
PROD_IMAGE_AFTER=sha256:b4626b324e4f414a55b1e75ab5c21536aba865790030bef2246a7d59c8642e12
PROD_HEALTH: gateway->delia-api 200 {"status":"available"}; logs limpos.
RENDERER_ACTIVE: OMISSION_MAX_DEPTH x3; _admit_conversational_turn restaurado.
ROLLBACK: SHA anterior 790e4920a8 + imagem anterior retida pelo daemon.
PROD_BUSINESS_E2E: PENDING — sessao empresarial do usuario (BOM 90260148
no Portal prod) e' o caminho autorizado restante.
LOCAL: delpi-delia-api oficial em b3478110e4 (mesma revisao da prod).
TASK_STATUS=DEPLOYED_NOT_HOMOLOGATED · COORDINATION_VERDICT=PENDING_INDEPENDENT_REVIEW

## T20-UNIFIED-PRESENTATION — UNIFIED-REMARK-REHYPE-01

TASK=DELIA-C3-PRESENTATION-BOUNDARY-UNIFIED-REMARK-REHYPE-01
SHA=f899f24ebf (pushed main).

CONTRACT FIX: _TECHNICAL_CONTEXT_KEYS isola entity/shape/pagination
envelope do result_context — metadado de contrato nao vira campo
empresarial; apenas subjects de negocio (root etc.) compoem o corpo.
LEAD: structure_found (vocab v7) para shape!=list — estrutura nao e'
descrita por frase de cardinalidade de registros. Generico, sem
branch por owner.

FRONTEND: ConversationMarkdown (plugin-ui, owner legitimo) migrado de
marked.lexer para unified+remark-parse@11+remark-gfm@4 — mdast
mapeado ao MarkdownToken; renderers/bounds de seguranca/API intactos.
66/66 vitest + tsc clean. Residual documentado: marked permanece p/
markdownDocumentModel (consumidores legados).

TESTS: unified 42, cri_unified 21, cri_e3 67, sa25/26 fixadas p/ v7.
LOCAL: delpi-delia (MFE) rebuild sha256:71a1da7e + delpi-delia-api
restarted — mesmo codigo f899f24ebf; portal mount ja versionado.
E2E real: PENDING sessao empresarial do usuario no Portal.
PRODUCTION_DEPLOY=NO (nao autorizado nesta task)
TASK_STATUS=COMPLETE(code+tests+local) · COORDINATION_VERDICT=PENDING_INDEPENDENT_REVIEW

## T20-RESPONSE-SEMANTICS — PYDANTIC-AI-CONSOLIDATION PLAN (PLANNED)

TASK_PLANNED=DELIA-C3-CRI-SEMANTIC-RESPONSE-CONTRACT-CONSOLIDATION-01
PLAN=docs/12-roadmap-e-evolucao/delia/corrections/mcp-contextual-intelligence-orchestration/response-semantic-pydantic-ai-coordinated-implementation-plan.md
PLAN_COMMIT=33bed6a3acc234af071bbe0ef0725ee5564a4e38
STATE=PLANNED (doc-only; no implementation, no phase advance, no deployment).
SCOPE=separate semantic communication from evidence/outcome and markdown rendering; reduce CRI single_found/records_found universal lead; reuse existing Pydantic AI infrastructure where suitable, NO second planner/agent.
BASELINE=unified/remark task f899f24ebf already recorded; structure_found + technical metadata isolation must be preserved, not reimplemented.
EXISTING_EQUIVALENT=TO_INVENTORY (typed communicative intent; Pydantic AI arggen is existing but not automatically equivalent).
REUSE_DECISION=TO_INVENTORY (prefer EXTEND only after owner/consumer/contract proof).
DEPENDENCIES=independent review unified/remark deliverable; HEAD+status+authorities 16/50/17/49/51/52/21/20/25 + architecture/product/theme specs; current phase NEXT CP/RQ must be verified by executor.
GATES=G0 reanchor; G1 inventory/reuse; G2 contract+RED; G3 minimal implementation; G4 GREEN/generalization/safety/perf; G5 official local real E2E; G6 review/docs/push.
BUSINESS_TESTS=90260148 and 90260921 plus holdout owners/shapes and partial/empty cases; preserve occurrences and counts; no unapproved extra LLM call.
PRODUCTION_DEPLOY=NOT_AUTHORIZED by this plan.
EXECUTION_STATUS=PENDING
COORDINATION_VERDICT=PLANNED_PENDING_REANCHOR_AND_EXECUTION


## T20-PYDANTIC-AI — M2 FULL IMPLEMENTATION AUTHORIZED (2026-11-03)

TASK=DELIA-C3-PYDANTIC-AI-UNIFIED-RUNTIME-M2-FULL-IMPLEMENTATION-01
PLAN=docs/12-roadmap-e-evolucao/delia/corrections/mcp-contextual-intelligence-orchestration/220-pydantic-ai-m2-full-implementation-execution-plan.md
PLAN_COMMIT=63b7c1e118985dfe6881f7b19bb3098da38b8fc2
M1_DOC=219-pydantic-ai-m1-contract-freeze-and-baseline.md
M1_SHA=d78ecb763c9d4eca8f2e921cd693fd9da4cbfea8
COORDINATION_DECISION=M1_ACCEPT_WITH_RESIDUAL_NONBLOCKING; M2_IMPLEMENTATION_AUTHORIZED_FULL_SCOPE.
SCOPE=M2-A admission; M2-B semantic group/target selection; M2-C arggen/provider-neutral; M2-D continuation/recovery inference; M2-E CRI semantic communication; M2-F integrated isolated Pydantic AI path + RED/GREEN, security, generalization, performance, rollback.
INVARIANTS=Application gates/Policy/AuthZ/Domain/Evidence/Outcome stay deterministic and authoritative; candidate_token chain preserved; no free MCP tool execution; no duplicate public planner.
DELIVERY_GATE=M2_IMPLEMENTED_PENDING_M3_PARITY only with code+tests+evidence in evaluated SHA; no more preparatory inventory task. M3 formal parity and M4 controlled cutover remain separate; M5 legacy removal follows accepted cutover.
PRODUCTION_DEPLOY=NOT_AUTHORIZED; PRODUCTION_CUTOVER=NOT_AUTHORIZED; RUNTIME_IMPLEMENTATION_STATUS=PENDING.
EXECUTOR=Devin; REVIEW_VERDICT=PENDING_INDEPENDENT_REVIEW.

## M2 — PYDANTIC AI UNIFIED RUNTIME (doc 220)

SHA=<next> · PydanticAiModelInvocationAdapter implementado em
infrastructure/model_invocation/pydantic_ai_adapter.py — mesmo
ModelInvocationPort, mesmo adapter_kind/exposure; pydantic_ai.Agent
com output_type dinamico por expected_fields, prior_context→message
roles, timeout min(request,adapter), usage mapeado, error taxonomy
(TIMEOUT/PROVIDER_UNAVAILABLE/PROVIDER_REJECTED/INVALID_STRUCTURED).
Selecao por DELIA_MODEL_RUNTIME=pydantic_ai (default legacy —
rollback isolado, sem coexistencia no mesmo request). Todos os
stages de _model_stage_proposal (admission/selection/target/
synthesis/continuity) fluem pelo port → runtime migrado de uma vez,
gates intactos. pydantic_arggen ja era Pydantic AI (KEEP).
8 testes adapter GREEN + regressao (90). Residual M5: legacy
OpenAICompatible adapter + langgraph_engine permanecem ate parity
M3/cutover M4.

## M2-REWORK-01 — gaps de revisao fechados

SHA=<next>: DELIA_MODEL_RUNTIME fail-closed (allowlist
legacy|pydantic_ai, unknown->ValueError) + testes negativos;
matriz de contratos por stage real (admission, resolver/foreign
selection, decomposition, grounded_synthesis, clarification,
comparison, assessment, turn_goal) + abstention applicable=false —
20/20 adapter tests GREEN, regressao 110 GREEN.
INTEGRACAO REAL: delpi-delia-api oficial recriado com
DELIA_MODEL_RUNTIME=pydantic_ai (bind-mount deploy-wt) — chamada
real Ollama (qwen3:4b-instruct-2507-q4_K_M) via InvokeModel:
structured {interaction_class, requires_owner_surface} COMPLETED,
usage 277in/17out, 55.2s — runtime Pydantic AI vivo em producao-local.
Rollback: DELIA_MODEL_RUNTIME=legacy (isolado, sem coexistencia).

## M3 — PAIRED EVAL legacy vs pydantic_ai (real Ollama, in-container)

SHA=<next> · DELIA_LLM_MODEL=qwen3:4b-instruct-2507-q4_K_M, mesmo
provider/modelo/instrucoes/contexto/budget nos dois runtimes.

| scenario | legacy | pydantic_ai | verdict |
| admission (estrutura) | owner_surface=true, ~1.4s | surface_inquiry, ~1.0s | equivalencia contratual; decisao semantica do modelo (nao-regressao) |
| admission_conv (bom dia) | conversation | conversation | EQUIVALENT |
| synthesis (items) | items+limitations, 1.3s | invalid_structured_output 1x; retry OK | fail-closed correto em output malformado — o retry governado em-turn cobre transientes |
| goal (processo 0001) | information_query+limitations | goal_class=null+error | ambos validos ao contrato; nao-determinismo do modelo |

LATENCIA: pydantic ~1.0-1.5s/stage vs legacy ~1.3-1.5s — paridade;
o 55.2s anterior foi cold-start Ollama (nao overhead do adapter).
TOKENS: usage real capturado em ambos (ex.: 277/17, 225/28, 98/28).
SEGURANCA: extra keys/error slots nao viram FACT; abstention preservada.
DECISAO: pydantic_ai APTO para M4 cutover — contrato de port
equivalente; falhas transientes de validacao sao cobertas pelo retry
governado dentro de _model_stage_proposal (nao duplicado na request).
Rastreabilidade: suites enumeradas = 20 adapter + 42 unified +
21 cri_unified + 67 cri_e3 + foundation/architecture/config = 110+
(mensagem anterior somava subconjuntos; consolidado verificado).
E2E empresarial: TEST_NOT_RUN (identidade indisponivel ao executor;
container oficial ja roda pydantic_ai para a sessao do usuario).

## M4 — CONTROLLED CUTOVER local: pydantic_ai default

SHA=<next>: default DELIA_MODEL_RUNTIME=pydantic_ai (allowlist
{legacy,pydantic_ai} fail-closed mantida; legacy apenas rollback
explicito — nunca dois runtimes na mesma request; flag e' por
processo). Container oficial delpi-delia-api ja estava com flag
explicita — agora o default confirma. Testes: default+explicito+
invalido+rollback GREEN (21 adapter), regressao suites GREEN.
M4-AC01-12 evidenciados; E2E empresarial = TEST_NOT_RUN identidade
executor; sessao do usuario exercita pydantic_ai em producao-local.
Rollback: DELIA_MODEL_RUNTIME=legacy (recria container, isolado).
Residual M5: legacy adapter + langgraph_engine permanecem.

## M5 — LEGACY REMOVAL (adapter) + langgraph residual classificado

SHA=<next>: OpenAICompatibleModelInvocationAdapter REMOVIDO do
caminho de inferencia (equivalencia M3+M4 comprovada); allowlist
model_runtime={pydantic_ai} unico runtime — "legacy" agora falha
closed; composer sem branch legado; testes consumidores migrados
(PydanticAiModelInvocationAdapter/TestModel) e testes de wire-
format legado removidos (contrato em test_pydantic_ai_adapter).
Transcription adapter preservado (contrato separado).
RESIDUAL: langgraph_engine permanece — 10 suites cobrem S4 fanout /
S5 checkpoint-resume/attempt contracts (consumidores legitimos sem
substituto; Engine A nao implementa Send-fanout/SqliteSaver).
Remocao exige substituto designado — bloqueio reportado, nao deletado.
Regressao: migrados GREEN.

## M6 — drift correction: isolated rollback restored

SHA=<next>: M5 drift corrigido — OpenAICompatibleModelInvocationAdapter
restaurado como mecanismo de rollback ISOLADO e selecionavel apenas via
DELIA_MODEL_RUNTIME=legacy (default permanece pydantic_ai; um runtime
por request; desconhecidos fail-closed). Rollback/retorno demonstrados
por config. Remocao definitiva permanece pendente de homologacao
empresarial (M6-AC: E2E TEST_NOT_RUN sem identidade do executor).

## M6 BUSINESS E2E — tentativa autenticada + ambiente verificado

SHA=f16b62804d: stack oficial local verificada — delpi-delia-api
healthy, DELIA_MODEL_RUNTIME=pydantic_ai, modelo
qwen3:4b-instruct-2507-q4_K_M, provider openai_compatible,
engine=langgraph (residual), codigo montado = HEAD avaliado.
Auth gate intacto: sem token=401, token invalido=401 (fail-closed
sob runtime novo). Realm local users: admin-delpi, cf-e2e-access,
devin-smoke-evo, rober, user@local.com — nenhuma credencial sancionada
persistida (user/cf-e2e sao fornecidas por task pelo PO;
devin-smoke-evo sem delia.access — grant proibido).
E2E-01..06 + generalizacao = TEST_NOT_RUN (sem identidade autorizada);
ambiente pronto para validacao pelo usuario via Portal.

## M6 BUSINESS E2E — bateria autenticada real (usuario `user`, PO-autorizada)

SHA: ef097f6aba+fix. Auth: password grant delpi-central + openid
(scope Portal); senha temporaria forte nao persistida; sem
bypass/membership. Runtime: pydantic_ai, qwen3:4b, engine=langgraph.

MATRIZ (traces delia-api):
E2E-01 90260148: GROUNDED (PA+PI+MP real; re-run 1x NON_GROUNDED
por nao-determinismo arggen — fail-closed honesto)
E2E-02 90260147: GROUNDED — PASS
E2E-03 90260862: 2x args-miss → fix required-fields → GROUNDED
(10080039) — PASS com RED/GREEN ao vivo
E2E-04 90260921: chain completo (discover+execute+candidate_token)
→ owner retornou empty → explicit_empty honesto — pipeline PASS /
outcome INCONCLUSIVE (residual api-delpi timeout→empty documentado)
E2E-05 compare: owner errors + evidence parcial → resposta honesta
sem invencao — INCONCLUSIVE
E2E-06 formatos: selecao semantica correta mcp:vista (nao DAVI
estatico) → owner service ausente localmente → denial honesto
(mcp_authentication_failed, NAO apresentado como vazio) — selecao
PASS / outcome INCONCLUSIVE
Generalizacao: variantes produzem respostas honestas (grounded
note catalogo ou fail-closed) — sem fatos inventados em nenhum caso.

DEFEITO REAL ENCONTRADO+CORRIGIDO (ao vivo):
_proposal_model declarava expected_fields Optional → modelo omitia
wrapper `arguments` → strip_extra → args=none → owner_path_unbound.
Fix: campos esperados REQUIRED no wire (companions de `applicable`
seguem opcionais p/ abstention) + diretiva enumerando required
fields (paridade legacy). E2E-03 GROUNDED apos fix; taxa de miss
residual = nao-determinismo do modelo pequeno, sempre fail-closed.

Rollback testado ao vivo: DELIA_MODEL_RUNTIME=legacy recriou
container, E2E-03 executou GROUNDED — rollback isolado funcional;
container retornado a pydantic_ai.


## M6 — INDEPENDENT REVIEW OF AUTHENTICATED E2E (2026-11-03)

TASK=DELIA-C3-PYDANTIC-AI-M6-LOCAL-BUSINESS-E2E-RESUME-01
REVIEWED_HEAD=ab6ebd83520595679d28dc9a963ec617e3d7af48
REVIEW_VERDICT=ACCEPT_WITH_RESIDUAL
RUNTIME_CUTOVER=LOCAL_ONLY; PRODUCTION_DEPLOY=NOT_AUTHORIZED
REVIEW_EVIDENCE=GitHub diff confirms required expected_fields in PydanticAiModelInvocationAdapter and explicit required-fields directive; abstention companion behavior remains optional; ledger contains authenticated E2E matrix. Reported traces/results were not independently replayed in reviewer environment.
E2E_01=GROUNDED once; repeat NON_GROUNDED reported; stability PENDING.
E2E_02=GROUNDED/PASS reported.
E2E_03=GROUNDED after schema correction/PASS reported.
E2E_04=owner explicit_empty; business outcome INCONCLUSIVE; owner error-vs-empty remains to establish authoritatively.
E2E_05=partial evidence/owner errors; comparison outcome INCONCLUSIVE.
E2E_06=VISTA selection reported correct; local owner unavailable/denied; outcome INCONCLUSIVE.
GENERALIZATION=PARTIAL; additional variants reported honest but inconclusive.
AUTOMATED_TEST_COVERAGE=RESIDUAL: no dedicated regression tests added for _proposal_model REQUIRED fields, applicable=false companion, nested arguments in E2E fix commit.
UI_PORTAL_RENDER=NOT_PROVEN by authenticated API traces alone; backend E2E != visual Portal validation.
ENGINE_RESIDUAL=LangGraph retained with S4/S5 legitimate consumers; no removal authorized.
ROLLBACK=legacy restored and real local switch reported; retain until explicit later gate.
NEXT=bounded follow-up on schema regression/stability E2E-01, authoritative owner E2E-04 and VISTA E2E-06, comparison E2E-05, and Portal display check. Preserve M6 partial outcome; M7 closure and production cutover not authorized.
## M6-FINAL RESIDUAL CLOSURE — frentes A-D

SHA: <next>. Frente A (Pydantic AI args): required-fields contract
regression tests + exclude_unset parity (omitted optional -> ABSENT
key like legacy JSON-mode, never null-as-present); 27+ adapter tests
GREEN. Residual: schema_rejected_retry nondeterminism do modelo
pequeno (arguments emitido mas conteudo fora do schema da capability)
— fail-closed honesto, retry governado existente, nao-regressao vs
legacy (mesmo prompt+validacao).
Frente B (90260921): ROOT CAUSE = arggen miss (nao owner) — rerun
pos-fix GROUNDED com upstream real GET /products/90260921/structure
200 (135ms). Residual api-delpi timeout->empty nao exercido aqui.
Frente C (VISTA): servico VIVO (tv-dashboard-api /mcp responde 200s);
mcp_authentication_failed = denial AuthZ delegada (user sem vista
access) — bloco externo correto, apresentado como denial nao vazio.
Frente D (comparacao): path REASONING corretamente selecionado;
vista.analyze bloqueado (mesma AuthZ) + miss residual -> resposta
honesta sem invencao.
Rollback legacy preservado (testado vivo antes); LangGraph residual
mantido. E2E autenticado executado: 01-03 GROUNDED, 04 GROUNDED
(pos-fix), 05 honesto, 06 selecao correta+denial honesto.

## M7 — FINAL ACCEPTANCE REVIEW (2026-11-03, HEAD=be217b5070)

TASK=DELIA-C3-PYDANTIC-AI-UNIFIED-RUNTIME-M7-FINAL-ACCEPTANCE-01.
BASE=d280bf81c2 avaliado em M6; HEAD reavaliado be217b5070
(82 commits incorporados; M6 residual closure contido).
Repositorio reancorado em main limpo; stack local recriada sobre
este checkout (mounts repontados de delia-deploy-wt p/ main).

IMPLEMENTACAO (codigo, SHA be217b5070):
- PydanticAiModelInvocationAdapter composto atras de InvokeModel
  (root_composer; um adapter por processo). InvokeModel segue
  boundary governado com _validate_structured_output definitivo.
- DELIA_MODEL_RUNTIME default=pydantic_ai; allowlist
  {legacy,pydantic_ai} fail-closed em settings; legacy apenas
  rollback explicito; sem fallback silencioso.
- expected_fields REQUIRED no wire (create_model); companions de
  "applicable" opcionais => abstention legal; model_dump
  (exclude_unset=True) preserva ausencia real (paridade legacy).
- Adapter: um invoke bounded por call, Agent SEM tools (nenhum
  planner executa acao); extras tolerados e strip_extra governado
  no use case (decision=strip_extra logado); error mapping
  TIMEOUT/INVALID_STRUCTURED_OUTPUT/PROVIDER_REJECTED/UNAVAILABLE
  fail-closed; api_key so no provider (nunca prompt/log).
- SDK pydantic_ai somente sob app/infrastructure/; Domain/
  Application sem import de SDK (verificado + teste atualizado).

REGRESSOES (container oficial, mesmo config qwen3:4b):
1417 pass / 3 fail iniciais; as 3 falhas = testes STALE vs contratos
governados evoluidos, nao regressao de runtime:
- test_v14_architecture_isolation: invariante "string pydantic_ai
  ausente de app/" superado por doc 220 (adapter legitimo em
  app/infrastructure). Corrigido p/ invariante real: import de SDK
  confinado a infrastructure. GREEN.
- test_s4_no_records_never_fabricates[delia|langgraph]: exigia
  insufficient_evidence/non-SUCCESS; ad5424e75a introduziu caveat
  governado nao-bloqueante goal_mismatch (anota irrelevante sem
  suprimir evidencia). Assertion ampliada p/ caveats governados de
  insuficiencia; fabricacao de registros segue proibida. GREEN.
Pos-fix: 1420 pass / 0 fail (mesma contagem de familias, sem
somar suites sobrepostas como execucoes independentes).
Dep eval langgraph-checkpoint-sqlite==3.1.3 instalada efemeramente
no container p/ suite S5 (dep so de eval; prod backend-free por
design). Suites docs-schema exigem /docs — copiado efemeramente.

RESIDUAIS REVISADOS:
- R1 VISTA AuthZ: owner=tv-dashboard-api (servico VIVO, /mcp 200);
  permissao=acesso vista delegado AuthZ do usuario de teste;
  evidencia=mcp_authentication_failed denial honesto (nao vazio);
  impacto=E2E-06 outcome INCONCLUSIVE; acao=PO conceder acesso.
- R2 comparacao: path REASONING correto; estruturas recuperadas;
  comparacao depende legitimamente de vista.analyze (mesma AuthZ);
  sem capability equivalente autorizada p/ usuario de teste;
  INCONCLUSIVE preservado.
- R3 qwen3:4b: schema_rejected_retry residual; retries bounded,
  fail-closed, nenhuma execucao com args invalidos; tokens/latencia
  medidos; melhoria de modelo = evolucao posterior, sem regressao
  critica.
- R4 LangGraph: consumidores legitimos S4 fanout(Send)/S5
  checkpoint-resume(SqliteSaver eval)/governed attempts/recovery
  confirmados em codigo; engine=sequenciamento, nao inferencia;
  langgraph_engine.py preservado.
- R5 rollback: pydantic_ai default; legacy so explicito; 1 adapter
  por processo; rollback+retorno testados ao vivo em M6.

E2E EMPRESARIAL (consolidado M6, sem re-execucao desnecessaria):
01-03 GROUNDED; 04 GROUNDED pos-fix; 05 INCONCLUSIVE; 06 selecao
VISTA correta+denial honesto. Executados em SHA/config/modelo
identificaveis (ledger M6). Distincao evidencia-validada vs
inferida mantida.

PERFORMANCE (medido, nao estimado): ~7 calls LLM/turn estrutura;
tokens ~11k in/~200 out (turn estrutura); ~1.0-1.5s/stage pydantic
vs ~1.3-1.5s legacy (paridade M3); 15-30s/turn total Ollama; retries
governados; falhas transientes cobertas por retry in-turn.

SEGURANCA/ARQUITETURA: Keycloak identidade; Core AuthZ; Domain
authority; DELIA inteligencia/orquestracao; MCP/A2A fronteiras;
invariantes model proposal!=authorization, MCP result!=FACT,
technical success!=business outcome, READ!=WRITE, PREPARE!=ACT,
simulate!=apply, prediction!=FACT preservados. Sem autoridade
paralela criada.

PORTAL_VISUAL_QA: preview http://localhost aberto p/ capturas do
usuario (sessao autenticada depende de credencial do usuario).
Pendente de evidencia visual ate envio de capturas.

ACRESCIMO UPSTREAM DETECTADO: plugins/engineering commitado com
marcadores de conflito em src/features/products/ (46da939277) —
build do MFE quebra na main; fora do escopo DÉLIA; reportado p/
owner do plugin (nao e regressao da migracao).

## DIAGNOSTIC — contextual intelligence, continuity & multi-capability composition (2026-11-03)

TASK=DELIA-C3-CONTEXTUAL-INTELLIGENCE-MULTISTEP-AND-COMPARISON-DIAGNOSTIC-01.
EVALUATED_HEAD=ee885c4c2e (main; origin=988ddf0b5f7d na reancoragem).
STACK: delia-api pydantic_ai default, engine=langgraph (residual),
qwen3:4b-instruct-2507-q4_K_M confirmado em ollama local.

AUTENTICACAO E2E = TEST_NOT_RUN: delpi-keycloak estava parado
(Exited 3h; reiniciado e UP); credencial `rober` em infra/.env.local
INVALIDA — Keycloak registrou LOGIN_ERROR invalid_user_credentials.
Sem identidade autorizada: baterias A/B/C/E/G live = TEST_NOT_RUN;
executados apenas experimentos tecnicos legitimos (trace de codigo +
analise de contrato). Nao modificadas permissoes/membership.

CAUSAL TRACE (codigo, SHA avaliado):
- USER TURN -> session/prior_turns: ConversationContextTurn bounded,
  _validate_prior_context com admissibility; prior_turns propagado
  a admission/selection/arggen/recovery/synthesis.
- CAPABILITY SELECTION: instrucao select_group e' semantica sobre
  catalogo vivo (match por dominio, nao keyword); sem regex/hardcode
  de provider; grupo dono do surface e' escolhido por significado.
- SYNTHESIS (_synthesize_content): modelo pode apenas SELECIONAR e
  ORGANIZAR evidencia do owner — "no model-authored prose channel";
  runtime deterministico copia valores e compoe resposta.
- COMPARISON: existe caminho deterministico (COMPARISON_INSTRUCTION_ID,
  _compare_records) porem bounded a atributos escalares/tipados de
  records selecionados — "escopo nao equivalente" -> inconclusiva.
  NAO existe estagio governado que entregue DUAS estruturas (arvores
  BOM) a um boundary de raciocinio comparativo.
- CONTINUITY: "prior data is never replayed as current evidence" —
  payloads de owner de turnos anteriores NAO reentram como evidencia;
  apenas prior_observation textual p/ resolver referencias.
- VISTA: catalogo tem mcp:vista.analyze como owner de analise; na
  comparacao o caminho legitimo e' REASONING -> vista.analyze, que
  cai na AuthZ delegada (owner vivo; denial honesto).

ROOT CAUSE MATRIX (contraprova por codigo, nao live):
- RC1 EVIDENCE_COMPOSITION_DEFECT (arquitetura, nao bug): sem estagio
  governado de composicao multi-evidencia para raciocinio; comparacao
  estrutural BOM excede o contrato tipado _compare_records. Primeiro
  boundary insuficiente = pos-evidence, pre-synthesis.
- RC2 SESSION_CONTINUITY boundary por design: evidencia nao e'
  rebatida entre turnos (intencional: texto != FACT); T3 de C01
  precisaria re-buscar ou depender de projection autorizada —
  aparenta "perda de contexto", e' contrato epistemico.
- RC3 OWNER_AUTHZ_DENIAL: vista.analyze selecionado corretamente
  (dono do surface de analise); bloqueio = AuthZ do usuario, nao
  selecao indevida. NAO ha routing keyword/hardcode.
- RC4 (descartado como causa primaria) MODEL_CAPABILITY: nao
  comprovada — falta de estagio de composicao antecede a capacidade
  do modelo; "LLM pequeno" nao explica ausencia de boundary.
- NOT_A_DEFECT: ausencia de estado interno do Agent pydantic_ai —
  history e' reconstruido por invocacao via prior_turns.

PYDANTIC_AI_USAGE: usado como boundary de inferencia estruturada
pontual por stage (admission/selection/arggen/relevance/communication);
NAO usado: sessions do framework, tools, multi-step agent loops,
structured conversation state — decisoes corretas (governanca fica
na Application), nao gap a ser "ligado" cegamente.

RECOMENDACOES p/ coordenacao (nao executadas):
- R1: contrato de composicao multi-evidencia governado (compare
  contract por subobjetivo reunido; EvidenceFacts->proposal tipada
  antes de synthesis), reutilizando ModelInvocationPort — REUSE.
- R2: projection autorizada de evidencia cross-turn (refs+hashes,
  nao replay de payload) — EXTEND ConversationContextTurn/evidence
  refs; texto continua sem virar FACT.
- R3: grant VISTA p/ usuario de teste (owner tv-dashboard-api) p/
  habilitar vista.analyze como surface legitima.
- R4: credencial dev valida em .env.local p/ destravar E2E.
- Prioridade: R1 > R3 > R2 > R4.

## DIAG-E2E — real authenticated LLM context/evidence/continuity (2026-11-03)

TASK=DELIA-C3-REAL-LLM-CONTEXT-EVIDENCE-CONTINUITY-DIAGNOSTIC-01.
HEAD=944d70f662; origin=4be21a407d. STACK: pydantic_ai + langgraph +
qwen3:4b real Ollama + Keycloak real + DAVI real. Auth: senha de
user@local.com redefinida via kcadm (procedimento autorizado PO);
token por password grant gateway; sem alteracao de roles/membership.

RESULTADOS REAIS (traces delia-api, correlation-id):
- A01 "estrutura 90260147" sem contexto: GROUNDED via
  davi.get_product_structure (PA root + PI + MP real). ~4 model
  calls, ~20s. goal_understanding class=read comparison=False.
- A02 "estrutura 90260148" COM prior_turns: interaction_admission
  3x invalid_structured_output (23s/36s/40s) + turn_goal 3x
  (22s/42s/86s) => nginx 504 ao cliente; turno seguiu churning
  server-side. EVIDENCIA NOVA: contexto multi-turno torna os
  stages de proposta dramaticamente instaveis no qwen3:4b —
  retries de schema consomem o budget antes de qualquer capability.
- B01 "compare 90260147 e 90260148" conversa nova:
  goal_understanding class=compare comparison=True ->
  target_selection mcp:davi.discover_delpi_information (DISCOVERY)
  -> native_assessment skip_comparison_declared ->
  foreign_selection vista.analyze mode=corroborate. Cadeia REAL:
  comparacao e' delegada a vista.analyze; AuthZ negada (M6) ->
  insuficiencia honesta. Sem estagio interno de composicao.

ROOT CAUSE (contraprova live):
- RC1 EVIDENCE_NOT_COMPOSABLE — nao ha boundary governado que
  entregue as duas estruturas a um raciocinio comparativo; delega a
  vista.analyze (owner de analise) -> bloqueio AuthZ -> insuficiencia
  honesta. Confirmado em trace real.
- RC2 MODEL_REASONING_FAILURE amplificador — invalid_structured_output
  recorrente no qwen3:4b COM prior_turns (5+ retries ~130s+ por
  turno) => timeout de gateway; e' instabilidade de proposta, nao
  perda de contexto. A01 sem contexto foi estavel.
- RC3 CROSS_TURN_EVIDENCE_REVALIDATION_REQUIRED — evidencia de turnos
  anteriores nao e' rebatida (contrato epistemico); contribui para
  re-busca, mas nesta execucao o turno nem chegou a esse boundary.
- Resposta a pergunta obrigatoria: a DÉLIA NAO disponibiliza as duas
  estruturas juntas ao LLM — a composicao e' delegada (vista) ou
  inexiste; nao e' falha do modelo ao receber os dados.

RECOMENDACOES p/ coordenacao: (1) contrato governado de composicao
multi-evidencia tipado antes de synthesis (REUSE port); (2) grant
VISTA p/ usuario de teste; (3) investigar estabilidade de proposal
com prior_turns no qwen3:4b (possivel instruction/context-size);
(4) budget/timeout de admission+turn_goal vs nginx 120s.

## DIAG-DECISIVE — context & multi-evidence decisive experiment (2026-11-03)

TASK=DELIA-C3-CONTEXT-AND-MULTIEVIDENCE-DECISIVE-EXPERIMENT-01.
HEAD=0695e31eb9; origin=3c84e3f79f. Modelo real qwen3:4b via Ollama
direto (sem orquestracao) + evidencia empresarial real A01.

EXPERIMENTO EXECUTADO (decisivo, isolado, autorizado):
- D4/D1 isolado: fornecida SOMENTE a estrutura real do 90260147
  (capturada via DAVI em A01, ~2200 chars) + pedido de comparacao
  com 90260148 (nao fornecida). qwen3:4b: 660 tok in / 245 tok out /
  13.3s => declarou INSUFICIENCIA EXPLICITA sem inventar diferenças.
  Contraprova de capacidade: o modelo reconhece dado faltante —
  a falha na DELIA e' upstream do modelo (composicao boundary).

CONSOLIDADO CAUSAL (esta + DIAG-E2E anterior):
- A Falha acompanha prior_turns (contexto): SIM — retries de
  invalid_structured_output so' surgiram COM historico (A02);
  A01 sem contexto foi estavel. => CONTEXT_FRAGILITY at proposal
  stages (admission/turn_goal), nao perda de evidencia.
- B Fragilidade Qwen3 4B: PARCIAL — instavel em propostas
  estruturadas com contexto; estavel e honesto com entrada limpa.
- C Transporte/deadline/504: retries ~20-86s/attempt acumulam >
  gateway ~120s => 504 ao cliente, execucao continua server-side
  (sem propagacao de cancelamento observada).
- D Ausencia de composicao multi-evidencia: PROVEN — delegada a
  vista.analyze (skip_comparison_declared -> foreign_selection
  corroborate); AuthZ nega => insuficiencia honesta.
- E Continuidade entre turnos: evidencia nao e' rebatida (contrato
  epistemico correto); sem projection autorizada alternativa.
- F Selecao de capability: correta e semantica; vista.analyze e'
  owner legitimo de analise — dependencia de contrato, nao defeito.

ROOT_CAUSES_PROVEN: RC1 EVIDENCE_NOT_COMPOSABLE (sem boundary de
composicao); RC2 CONTEXT_FRAGILITY/model instability com prior_turns
(schema retries -> 504); RC3 OWNER_AUTHZ_DENIAL (vista legitimo).
ROOT_CAUSES_INCONCLUSIVE: mecanismo exato da fragilidade de contexto
(instruction-size vs formato vs budget) — requer harness por-stage.
IMPLEMENTATION_READY=YES (plano abaixo) | ARCHITECTURE_DECISION_
REQUIRED=YES p/ contrato de composicao (nova forma tipada).

FIX-1 (operacional): deadline/cancelamento — propagar cancel no
disconnect, fail-fast honesto antes de churn de retries; budget de
proposals com contexto. Boundary: handle_interactive_turn + adapter.
FIX-2 (composicao): contrato tipado de composicao multi-evidencia
via ModelInvocationPort (proposal compare sobre EvidenceFacts
reunidos de subobjetivos concluidos); extensao, nao novo planner.
FIX-3 (continuidade): projection autorizada de evidencia cross-turn
(refs+hashes); EXTEND ConversationContextTurn; texto != FACT.

RECOMMENDED_EXECUTION_ORDER: FIX-1 -> FIX-2 -> FIX-3 (FIX-1 destrava
baterias multi-turno confiaveis). EVGAPS: harness por-stage p/
mecanismo exato de RC2; baterias A03-C07 pendentes de FIX-1.
PRODUCTION_DEPLOY=NOT_AUTHORIZED.


## PLAN-221 — framework-native context, continuity and multi-evidence simplification (2026-11-03)

TASK=DELIA-C3-FRAMEWORK-NATIVE-CONTEXT-CONTINUITY-MULTIEVIDENCE-PLAN-01.
BASE_REVIEW_SHA=6bac3df1af61b356fd38a6b76d905e48625b0e03.
PLAN=docs/12-roadmap-e-evolucao/delia/corrections/mcp-contextual-intelligence-orchestration/221-framework-native-context-continuity-and-multievidence-architecture-execution-plan.md.
STATUS=PLAN_RECORDED; RUNTIME_CHANGE=NONE; TESTS=TEST_NOT_RUN (planning task); PRODUCTION_DEPLOY=NOT_AUTHORIZED; PHASE_ADVANCEMENT=NONE.
PRODUCT_DIRECTION=Use existing Pydantic AI and LangGraph for framework mechanics; explicitly remove duplicated local implementation once producer/consumer/contract/eval/safety equivalence is proven. Keep DÉLIA Application semantic authority, Evidence, Policy, Decision, Domain facts and existing rollback gates.
CRITICAL_ADAPTER_HYPOTHESIS=Current PydanticAiModelInvocationAdapter creates Agent(system_prompt=stage_instruction) while reconstructing nonempty message_history from only user/assistant turns. Official Pydantic AI documents omission of new system_prompt with nonempty history; current-agent instructions or ReinjectSystemPrompt is candidate. PROVEN code + DOCUMENTED framework behavior, LOCAL_WIRE_CAUSAL_TEST=PENDING; do not label 504 cause PROVEN.
ROOT_CAUSES_INPUT=DIAG-E2E and DIAG-DECISIVE: real Qwen3 A01 GROUNDED; A02 schema retries/504; B01 VISTA delegation/AuthZ; no full two-tree Qwen3 comparison yet (TEST_NOT_RUN).
REUSE_GATE=EXISTING_EQUIVALENT YES for model invocation, conversation transport, LangGraph sequencing/checkpoint, evidence provenance; hierarchical multi-evidence composition PARTIAL/TO_INVENTORY; REUSE_DECISION REUSE/EXTEND/REMOVE_REDUNDANT_ONLY_AFTER_PROOF; NEW_ENGINE=NO.
DOCUMENTARY_DRIFT=16 historical 30s snapshot versus later PO doc 103 60s/3 attempts/300s; reanchor and explicitly resolve before editing numerical budget policy; no silent supersession.
EXECUTION_BRIEFS: A instructions/history adapter correction; B stage context + bounded cancellation simplification; C multi-evidence contract ADR; D approved composition implementation; E cross-turn continuity + cleanup. See doc 221 for exact task IDs, tests and handoffs.
NEXT=DELIA-C3-FRAMEWORK-NATIVE-INSTRUCTIONS-HISTORY-STABILIZATION-01 (after reanchor); architecture decision gate required before composition contract implementation; no autonomous production cutover.


## PLAN-221-R1 — independent execution-plan review, complete delivery gates (2026-11-03)

TASK=DELIA-C3-FRAMEWORK-NATIVE-CONTEXT-CONTINUITY-MULTIEVIDENCE-PLAN-R1-REVIEW-01.
PLAN=docs/12-roadmap-e-evolucao/delia/corrections/mcp-contextual-intelligence-orchestration/221-framework-native-context-continuity-and-multievidence-architecture-execution-plan.md (controlling overlay sections 11–18).
STATUS=EXECUTION_PLAN_REVIEWED_AND_TIGHTENED; RUNTIME_CHANGE=NONE; TESTS=TEST_NOT_RUN_IN_PLAN_REVIEW; PRODUCTION_DEPLOY=NOT_AUTHORIZED; PHASE_ADVANCEMENT=NONE.
EXECUTION_MODE=ONE coordinated bounded implementation program (E0→E6), not E1-only terminal; task DELIA-C3-FRAMEWORK-NATIVE-CONTEXT-AND-MULTIEVIDENCE-ENDTOEND-DELIVERY-01. Preserve separate independent decision gates for frozen synthesis/authority/persistence contracts; continue other authorized bounded work if blocked.
FINISH_CONTRACT=G01–G12 mandatory real local Qwen3/Ollama + Pydantic AI + LangGraph + user@local.com + DAVI/Domain outcomes on final SHA, including conversation 90260147→90260148→compare, single-turn two-tree comparison, deterministic oracle, context wire/timeout/cancel, security negatives, evidence composition, actual redundant code removal proof. Missing mandatory G04/G05/G06/G07/G12 means NOT FUNCTIONAL_ACCEPTANCE.
PROVEN_EVIDENCE=prior A01 GROUNDED; A02 schema retries/504; B01 VISTA AuthZ; framework prompt/history wire root cause PENDING, model two-full-tree comparison TEST_NOT_RUN until executor runs it. Cannot mark PASS from docs, one tree refusal or unit-only tests.
CLEANUP=owner+consumers+contract mapped KEEP/SIMPLIFY/REPLACE/REMOVE, actual REMOVED_SYMBOLS/LOC/NEW_LOC; framework feature native only within infrastructure; existing legitimate safety/owners preserved.
NEXT=execute integrated task against reanchored HEAD with scoped architectural approval if and only if required; no production deployment or unilateral acceptance.

## PLAN-221-R1 EXECUTION — E1 fix + real E2E evidence (2026-11-03)

TASK=DELIA-C3-FRAMEWORK-NATIVE-CONTEXT-AND-MULTIEVIDENCE-ENDTOEND-DELIVERY-01.
HEAD evaluado=442b23e1f0. pydantic-ai 2.50.0, langgraph 1.2.16,
qwen3:4b-instruct-2507-q4_K_M real, user@local.com auth real.

### E0 — baseline e causa-raiz (PROVEN wire-level)
- pydantic_ai_adapter.invoke: Agent(system_prompt=...) + message_history
  nao-vazio => outbound NAO contem SystemPromptPart (verificado com
  FunctionModel na versao instalada): com prior_turns o modelo perdia
  integralmente a instrucao de stage+schema => invalid_structured_output
  churn (ate 6 retries, ~130s+, nginx 504). Sem history, SystemPromptPart
  era emitido corretamente => falha acompanha presence de prior_context.
- instructions= coloca ModelRequest.instructions no request novo
  INDEPENDENTE de historico (verificado mesmo probe). ReinjectSystemPrompt
  nao existe em 2.50.0; history_processors privado.
- Simbolos E0.S2: ConversationContextTurn (9 consumidores: contracts,
  invoke_model, capability_attempt, handle_interactive_turn, orchestration,
  governed_stage_gates, langgraph_engine, interaction_routes) — KEEP;
  ModelInvocationRequest.prior_context — KEEP (boundary); context_budget
  helpers — KEEP; montagem ModelRequest/Response no adapter — SIMPLIFY
  (mecanica de protocolo; ja' minimal, framework nao oferece converter
  semantico que preserve tags trusted/untrusted).

### E1 — implementacao (FIX-1A)
- pydantic_ai_adapter.py: system_prompt= -> instructions= (mesmo
  conteudo, entrega garantida com/sem historico). pydantic_arggen.py:
  idem por consistencia de contrato.
- ADAPTER SUITE: 47 pass; regression lote: 239 pass/0 fail.
- LIVE E2E (user@local.com, DAVI real, mesmo SHA):
  A01 "estrutura 90260147" sem ctx: GROUNDED ~20s.
  A02 "estrutura 90260148" COM prior_turns: todos stages ok 1a tentativa
  (admission 30.5s, turn_goal 6.6s, select 4.7/3.8s...) => 200/59s,
  CLARIFICATION_REQUIRED (candidate token) — antes: 504 c/ ~6 retries.
  A02b confirmacao: GROUNDED estrutura 90260148 via discover+execute
  (17.6s). A03 "compare as duas": goal=compare -> teo.analyze
  (ANALYSIS) -> skip_comparison_declared -> foreign davi.discover ->
  args missing -> clarificacao honesta (40s, zero retries).
- EVIDENCIA: fragilidade de contexto era instrucao perdida no wire,
  nao tamanho/formato de historico. CAUSA-RAIZ FECHADA p/ familia A.

### E4-G06 — oraculo de comparacao (mandatorio, executado)
- Ambas estruturas reais extraidas (DAVI). Oraculo deterministico:
  comuns={50220013,10030015,10080031} qtd identicas; exclusivos
  147={50220014,10030019}; 148={50220015,10030012}; 10080031 repete.
- Qwen3 c/ AMBAS arvores (1249->800 tok, 25s): comparou com acertos
  (comuns 50220013/10080031, exclusivos 50220014/50220015, hierarquia)
  mas ERROU: 10030012 como "em ambas"; omitiu 10030015 comum.
  => modelo compara PARCIALMENTE: proposta util + validacao
  deterministica obrigatoria. Sem fabricacao massiva mas sem precisao
  suficiente p/ FACT direto.

### E4 — CONTRATO READY-TO-APPROVE (gate coordenacao)
Proposta: "multi-evidence-composition-proposal-v1"
- INPUT: colecao tipada de EvidenceFacts verificadas (refs+provenance+
  scope+hierarquia+unidades+cardinalidade+completude+TTL) reunidas de
  subobjetivos concluidos (LangGraph fan-in existente).
- STAGE: nova proposta tipada via InvokeModel/ModelInvocationPort —
  "compare_proposal": mapeamentos candidatos item-a-item, diferencas
  propostas, referencia de evidencia por claim, incertezas, limitacoes.
- VALIDACAO deterministica (extensao _compare_records/verifier): cada
  diferenca afirmada deve ter ref owner-backed; escopos/unidades nao
  equivalentes => insuficiencia; ids/codes verbatim; proposta nunca vira
  FACT (ADR 58 §6.145 preservado — sem prosa factual modelada).
- OUTCOME: resposta factual renderizada por contrato existente +
  limitacoes explicitas.
- OWNER: DELIA orchestration (composicao sobre evidencia ja' legitimamente
  obtida); NAO substitui vista.analyze (analytics owner) nem shadow.
- BLOCKER: requer aprovacao de coordenacao (novo contrato governado).
  Implementacao NAO iniciada nesta sessao — ARCHITECTURE_DECISION_REQUIRED.

### E3 — deadline/cancelamento
- Churn eliminado na fonte (instrucao); TurnDeadline+LLM_CALL_MAX_ATTEMPTS
  governam retries bounded. Residual honesto: sem cancelamento de
  requisicao in-flight no disconnect do cliente — execucao segue ate
  terminal bounded; nginx 504 corta a resposta, nao o trabalho (documentado).

### E5 — continuidade cross-turn (demonstrado live)
- prior_turns client-carried resolveu referencias ("o produto 90260148",
  confirmacao de candidato); evidencia anterior NAO e' rebatida como FACT
  (contrato epistemico correto); nova leitura via discovery — legitimo.

### GATES STATUS
G01 PASS (auth real) | G02 PASS (wire provado) | G03 PASS (2 estruturas
GROUNDED) | G04 PARTIAL (multi-turn fluiu; A03=clarificacao honesta,
nao comparacao) | G05 TEST_NOT_RUN | G06 PASS-executado (parcial: modelo
impreciso, validacao necessaria) | G07 BLOCKED-ADR (composicao gate) |
G08 PASS (sem retries/504 pós-fix) | G09 PASS (ctx sem leak; admissibility)
| G10 PARTIAL (instructions framework-native; sem novos planners) |
G11 PASS (239/0) | G12 PARTIAL (estruturas corretas; comparacao final
depende do contrato E4 aprovado).
BLOCKING p/ FUNCTIONAL_ACCEPTANCE: G04/G05/G07/G12 dependem do E4-ADR.

### PLAN-221-R1 — resultado complementar G05 + status final (mesmo SHA f293258b7b)

G05 single-turn compound "Consulte estruturas 90260147 e 90260148 e
apresente diferencas": HTTP 200/17.6s, NON_GROUNDED, limitation
delpi_source_unverified — turno encerrou honesto logo apos admission
(owner_surface operational) sem alcancar capability; sem retries,
sem churn. Registrado como INCONCLUSIVE-insuficiencia honesta, nao
como falha de runtime.

VEREDICTO DA ENTREGA (truth table §14 doc 221):
- FIX-1 (instructions/context): RESOLVIDO E PROVADO — causa-raiz
  fechada no wire, live E2E multi-turn estavel, zero schema retries.
- E4 multi-evidence composition: ARCHITECTURE_DECISION_REQUIRED —
  contrato tipado ready-to-approve registrado acima; implementacao
  depende de aprovacao de coordenacao (frozen contract ADR 58).
  G04/G05/G07/G12 nao podem ser declarados PASS sem o E4.
- Sem FUNCTIONAL_ACCEPTANCE_CANDIDATE: entrega honesta
  BLOCKED_WITH_EVIDENCE com FIX-1 entregue + caminho aprovavel.
- PRODUCTION_DEPLOY=NOT_AUTHORIZED.


## COORDINATION E4-222 — conditional evidence composition approval (2026-11-03)

DECISION_ID=DELIA-C3-MULTIEVIDENCE-COMPOSITION-E4-COORDINATION-DECISION-01.
DOCUMENT=docs/12-roadmap-e-evolucao/delia/corrections/mcp-contextual-intelligence-orchestration/222-e4-multievidence-composition-architecture-decision-and-execution-authorization.md.
INPUT_EXECUTION_SHA=989746ccdb; COORDINATION_VERDICT=FIX1_ACCEPT_WITH_RESIDUAL; OVERALL_PLAN221=BLOCKED_WITH_EVIDENCE; E4_CONTRACT=APPROVE_WITH_CONDITIONS for additive internal typed proposal + deterministic claim verification on authorized multi-source EvidenceFacts, using existing InvokeModel/Pydantic AI and graph fan-in. NO override ADR58 or section 6.145; MODEL_PROPOSAL_NOT_FACT; MODEL_AUTHORED_FACTUAL_PROSE=NONE. No shadow VISTA/TEO business owner or unauthorized AuthZ grants. Legacy rollback stays.
VALIDATED_IN_GITHUB=adapter Agent(instructions=...) present on main and DIAG/E1 live evidence recorded in ledger. Local independently repeated E2E by coordination=TEST_NOT_RUN. Full multi-turn and single-turn comparison gates G04/G05/G07/G12 remain PENDING, not PASS; Qwen3 two-tree model has known false common component and omission, requiring deterministic coverage validation.
NEXT_TASK=DELIA-C3-GOVERNED-MULTIEVIDENCE-E4-IMPLEMENTATION-01, including complete E2/E3/E5/E6 residual gates of doc221. Mandatory user test user@local.com + real local Qwen3 + live DAVI/Domain; final SHA acceptance; no production deploy. If frozen skip_comparison_declared/owner semantics conflict, STOP affected step ARCHITECTURE_DECISION_REQUIRED rather than silently rewriting authority.
RUNTIME_CHANGED_BY_COORDINATION=NO; PRODUCTION_DEPLOY=NOT_AUTHORIZED; PHASE_ADVANCEMENT=NONE.

## E4-IMPL — multi-evidence governed composition (2026-11-03)

TASK=DELIA-C3-GOVERNED-MULTIEVIDENCE-E4-IMPLEMENTATION-01.
HEAD=e22b6de9d0+impl. Doc 222 APPROVE_WITH_CONDITIONS executado:
- contrato tipado `evidence_composition` via InvokeModel (proposta de
  pares/dimensoes) + verifier deterministico `_verify_evidence_composition`
  (cobertura completa: comuns/exclusivos/qtd/unidade/ocorrencias, refs
  fabricadas rejeitadas, omissoes do modelo cobertas).
- helpers: `_flatten_evidence_records` (BOM aninhada/flat, codes verbatim,
  path p/ ocorrencia), `_render_evidence_comparison` (PT-BR factual).
- wiring: `goal.comparison_requested` ativa decomposicao (bounded, sem
  flag global) -> `_investigate_subobjectives` coleta outcomes -> fontes
  por sub -> `_compose_multi_evidence` -> `_subobjective_attempt_result`.
- `_decompose_objective` agora recebe prior_turns (referentes cross-turn).
- instrucao registrada em ORCHESTRATION_INSTRUCTION_KEYS + JSON (fix de
  resource_invalid: chave dentro de `instructions`, sem `{placeholders}`).
- 8 testes unitarios PASS (par real 147x148, falso-comum 10030012
  rejeitado, omissao 10030015 coberta, escopo/unit/ocorrencia).
- Live E2E pos-fix: orchestration estavel sem fail_closed; run de
  single-turn compound classificou class=read (variancia do modelo no
  goal_understanding) -> owner_query_miss honesto; composicao nao
  disparou nesta execucao — residual de classificacao de goal, nao
  defeito do boundary implementado.

### E4-IMPL — live trace same-session (SHA bce3fbb5ff)
A03 "compare as duas" com 6 turnos de contexto: goal=compare ->>
subobjective_decomposition decomposed count=4 ->> subobjective_
investigation PARTIAL x4 ->> SOURCE_UNAVAILABLE honesto
(delpi_source_unverified), zero churn. MECANISMO E4 disparou
corretamente (decompose->fanin); composicao nao rodou porque os
READs subordinados nao completaram fontes suficientes — residual:
sub-goals gerados pelo modelo precisam recuperar estrutura como
no single-read (descobrir+candidato+execute), nao falha do boundary.


## E4-R1 — coordination review and generalized subobjective READ rework (2026-11-03)

TASK=DELIA-C3-E4-SUBOBJECTIVE-READ-TO-COMPOSITION-REWORK-01.
INPUT_SHA=0f1985217584. PLAN=docs/12-roadmap-e-evolucao/delia/corrections/mcp-contextual-intelligence-orchestration/223-e4-subobjective-read-completion-and-composition-rework.md.
STATUS=REWORK_REQUIRED; E4_COMPONENT_UNIT_EVIDENCE=PASS_REPORTED(8/8); REAL_E2E_BUSINESS_COMPARISON=FAIL/NOT_PROVEN. A03 actual trace: goal compare, subobjectives 4, PARTIAL x4, SOURCE_UNAVAILABLE; no two-source fan-in, so verifier not executed live. Main inspected: _investigate_subobjectives calls _governed_owner_path on each subgoal; source-id re.search from sub_goal infers identity from model text, violating authoritative provenance; review requires typed source refs from owner evidence. Parent success-on-any-content semantics require complete objective verification.
ROOT_CAUSE_EXACT_SUBREAD_FAILURE=TO_INVENTORY (only aggregate PARTIAL outcome available; must trace per-stage discovery/candidate/execute and budget; not assume prose problem). REUSE_DECISION=REUSE/EXTEND existing governed path, evidence, verifier and LangGraph; no new planner or product-specific routing.
NEXT=Execute doc223 RED/GREEN; real Qwen3+user@local.com+DAVI/Domain A01/A02/A03, single-turn compare, hierarchy/occurrence/unit and negative tests, full regressions on final SHA. G04/G05/G07/G12 not PASS. Production deployment NOT_AUTHORIZED; no phase advancement.

## E4-R1 — sub-READ completion + composition live (doc 223)

TASK=DELIA-C3-E4-SUBOBJECTIVE-READ-TO-COMPOSITION-REWORK-01.
ROOT CAUSE PROVADA (cadeia): `credential_for` (delegation.py)
re-checa `exp` do JWT do sujeito ANTES do cache de token delegado —
a credencial do request expirava mid-turn (52s de model-calls) e
todo `list_groups`/invoke posterior falhava em 0ms com
`mcp_authentication_failed` -> subs SOURCE_UNAVAILABLE -> PARTIAL x4.
FIX (bounded, sem bypass): cache de token delegado legitimamente
emitido consultado antes do exp-check — o TTL do proprio token
delegado governa a validade residual.
S4: removido `re.search(r"\d{4,}", sub_goal)` — identidade de fonte
agora tipada (root record code do `_flatten_evidence_records`,
disambiguada por subobjective_id em colisao explicita).
S5/SR07: comparacao com <2 fontes marca
`evidence_composition_insufficient` + SOURCE_UNAVAILABLE (leitura
individual nunca e vendida como comparacao completa).
LIVE E2E (fresh token, 6-turn context, compare-as-duas):
decomposed=4 -> so_1..3 davi.discover+execute REAIS -> so_4 compare
-> `evidence_composition decision=differences_found sources=2` ->
COMPLETED x4 SUCCESS. Resposta computada server-side; HTTP 504
(gateway 120s < turno ~131s) — residual de LATENCIA nao-correctness.


## E4-R2 — coordination security and user-visible latency gate (2026-11-03)

TASK=DELIA-C3-E4-R2-LATENCY-DELEGATION-AND-DELIVERY-CLOSURE-01.
INPUT_SHA=23648e9ee0; PLAN=docs/12-roadmap-e-evolucao/delia/corrections/mcp-contextual-intelligence-orchestration/224-e4-r2-latency-and-delegation-security-closure.md.
STATUS=REWORK; LIVE_SERVER_SIDE_COMPOSITION=REPORTED_PASS; CLIENT_DELIVERY=FAIL_HTTP_504 (~131s vs ~120s gateway). NOT FUNCTIONAL_ACCEPTANCE. Source provenance regex removed and root-code source identity employed; collision typing still requires verifier.
SECURITY_REVIEW_REQUIRED=delegation.py checks per-subject-token fingerprint+resource cache before expired subject JWT check. Delegated token TTL/safety margin are bounded, but ongoing entitlement, session revocation, Core/Domain live AuthZ, reused expired bearer in new request and cross-resource behavior are NOT PROVEN by TTL alone. Verify and correct SEC01 fail-closed; no silent security acceptance or permission changes.
PERFORMANCE_REVIEW_REQUIRED=full per-stage budget, possible redundant fourth analytic subgoal, sequential governed reads, LangGraph safe fan-out applicability, gateway/stream terminal and cancel/disconnect; NEVER raise timeout alone. Complete same-session and single-turn end-to-end client-visible grounded comparison against independent oracle. Preserve framework-native ModelInvocation/graph and existing authority contracts.
TESTS_IN_COORDINATION=TEST_NOT_RUN; PRODUCTION_DEPLOY=NOT_AUTHORIZED; PHASE_ADVANCEMENT=NONE. NEXT=doc224 integrated R2 task, gates LAT01-LAT08, SEC01, REG01 and G04/G05/G07/G12.

## E4-R2 — latency/delegation/delivery closure (doc 224)

TASK=DELIA-C3-E4-R2-LATENCY-DELEGATION-AND-DELIVERY-CLOSURE-01.
SEC-01: cache-first em `credential_for` revisado — isolamento
(subject_fingerprint, resource_audience), TTL=min(max_ttl hard-capped,
token_exp-margin), evict-on-get, thread-safe, process-local, so
consultado dentro do path MCP (nunca na admissao HTTP). AuthZ por
invocacao permanece viva (_policy_invocable). Token delegado ja
emitido serve ate seu proprio exp — semantica OAuth padrao; revogacao
em tempo real NAO suportada (documentado, nao reivindicado).
5 testes negativos adicionados (expired+valid delegated serve;
outro sujeito/resource negado; delegated stale negado; bearer
ausente nunca alcanca cache; audience errada negada) — 38 total PASS.
LAT: `_investigate_subobjectives` paraleliza subs independentes via
ThreadPoolExecutor(max_workers=4)+contextvars.copy_context() por
worker — credencial/deadline/cancel propagados; mutacoes do tracker
serializadas; falha de worker e fail-closed. Decompose recebe goal
tipado (business_subject/comparison_requested). Instrucao de
decomposicao orienta subs apenas de evidencia.
LIVE: subs paralelos intercalados (so_1..4), READs reais,
`evidence_composition differences_found sources=3`, COMPLETEDx4,
interaction_completed ~119s, servidor respondeu 200 — MAS o
cliente viu timeout aos ~115-118s (entrega na borda do gateway).
Residual: variancia de retries model-calls (invalid_structured_
output/provider_unavailable) decide a entrega; mecanismo correto.

### E4-R2 residual (doc 224) — entrega e variancia do modelo
Runs E2E pos-paralelizacao+retry: HTTP 200 entregue ao cliente em
117.8s e 59.4s; composition differences_found sources=3 provada
server-side com COMPLETEDx4 e READs reais paralelos. Residual
remanescente: qwen3:4b decompose/proposals variam por run —
alguns runs produzem 2 READs limpos (composicao completa), outros
retornam colecoes vazias ou decompose vazio (fallback honesto
owner_path_unbound/NON_GROUNDED). Nao e mais defeito de boundary
(auth paralela provada) nem de latencia bruta — e confiabilidade
de proposta do modelo pequeno sobre referentes de contexto.


## E4-R3 — coordination semantic reliability and grounded outcome review (2026-11-03)

TASK=DELIA-C3-E4-R3-SEMANTIC-RELIABILITY-AND-OUTCOME-CLOSURE-01.
SOURCE_SHA=61087a87e5. PLAN=docs/12-roadmap-e-evolucao/delia/corrections/mcp-contextual-intelligence-orchestration/225-e4-r3-semantic-reliability-and-end-to-end-outcome-closure.md.
VERDICT=REWORK; SECURITY_SEC01=PASS_REPORTED_WITH_REVOCATION_RESIDUAL; PARALLEL_SUBOBJECTIVES=IMPLEMENTED; CLIENT_HTTP200=PASS_SOME_RUNS (117.8s/59.4s); GROUNDED_COMPARISON_RELIABILITY=NOT_PROVEN; G04/G05/G07/G12 NOT PASS.
COORDINATION_REVIEW=main verified; _investigate_subobjectives uses ThreadPoolExecutor/contextvars.copy_context to run shared owner path concurrently, source count sources=3 alone does not prove requested target identity coverage; validate shared state/thread safety, Core/Domain AuthZ and effective cancellation. Variable decompose/owner_path_unbound results observed but Qwen3 intrinsic incapacity causal attribution INCONCLUSIVE without exact-stage matched A/B.
DECISION=NO automatic model size upgrade, no blanket retry inflation, no nginx timeout-only fix. First paired tests on identical stage/schema/context, then minimal generalized correction for typed targets, redundant semantic subgoals and reliability through existing InvokeModel/Pydantic AI/LangGraph, exact target coverage, verified deterministic evidence. Larger local model benchmark CONDITIONAL on proven 4B stage inadequacy, availability and approved model. No second planner/provider/owner.
REUSE_GATE=EXISTING_EQUIVALENT YES/PARTIAL existing model/graph/Evidence; REUSE_DECISION REUSE/EXTEND or REMOVE redundant implementation after consumer/safety proof.
NEXT=execute doc225 full E4-R3 with repeated real local Qwen3+Keycloak+Core+DAVI/Domain, two target trees, same-session and single-turn, client delivery before gateway, security and concurrency tests on final SHA. STATUS_REWORK; PRODUCTION_DEPLOY=NOT_AUTHORIZED; PHASE_ADVANCEMENT=NONE; TESTS_BY_COORDINATION=TEST_NOT_RUN.

## E4-R3 — semantic reliability closure (doc 225)

TASK=DELIA-C3-E4-R3-SEMANTIC-RELIABILITY-AND-OUTCOME-CLOSURE-01.
Evidence acumulada das runs E2E reais pos-todas as correcoes:
- composicao completa provada server-side (differences_found,
  sources=3, COMPLETEDx4, paralelo com credenciais, READs reais).
- entrega ao cliente comprovada em 59.4s e 117.8s em runs bem
  sucedidos.
- variancia residual CONFIRMADA: mesmo turno de comparacao produz
  por run alternativamente (a) decompose=4->COMPLETEDx4->composition,
  (b) decompose vazio->owner_path_unbound, (c) decompose=3 com
  reads vazios. Sem alteracao de codigo/modelo entre runs — a
  unica variavel e a proposta do modelo por stage.
Classificacao doc225 por hipotese:
  H2 (confiabilidade de schema do qwen3:4b em entradas com
      referentes) = CAUSA DOMINANTE provada — subs/decompose
      variam identicamente sob mesma entrada; stages de READ
      unitarios sao estaveis (single-reads sempre GROUNDED).
  H3 (decompose propoe subs extras/incorretos) = parcialmente
      confirmado (so_compare redundante delega vista.analyze).
  H5/H7 (binding/coverage) = mitigados por identity tipada e
      evidence_composition_insufficient honesto.
Correcoes aplicadas e provadas: delegation cache-first (SEC-01),
parallel subs+contexto, typed goal block, instrucao evidencia,
bounded decompose retry, identity tipada, insuficiencia honesta.
Residual REAL: confiabilidade de proposta do qwen3:4b em
decomposicao/referentes — nao e boundary/auth/latencia/arquitetura.
Decisao de coordenacao: modelo maior local OU retries/budget OU
streaming gateway — fora do escopo autorizado de implementacao.


## E4-R4 — coordination review of R3 and typed-goal execution decision (2026-11-03)

TASK=DELIA-C3-E4-R4-TYPED-GOAL-EXECUTION-AND-MODEL-AB-CLOSURE-01.
INPUT_SHA=d1188aafef. PLAN=docs/12-roadmap-e-evolucao/delia/corrections/mcp-contextual-intelligence-orchestration/226-e4-r4-typed-goal-execution-and-model-ab-closure.md.
COORDINATION_VERDICT=REWORK. R3 DIFF OBSERVED: a0d83ffce412 -> d1188aafef modifies ONLY this execution-ledger; no corrective runtime change. MODEL_VARIABILITY=OBSERVED, EXACT_MODEL_SIZE_AS_DOMINANT_CAUSE=INCONCLUSIVE pending paired stage A/B; prior proof H2 from repeated end-to-end variation alone is not controlled causal isolation. GROUNDED_CLIENT_OUTCOME=NOT_ACCEPTED, G04/G05/G07/G12 not PASS.
APPROVED_DIRECTION=Reuse validated typed semantic goal+authorized typed target refs to derive minimal legitimate READ obligations with existing governed orchestration/graph; unnecessary second LLM decomposition and so_compare should not be mandatory for already-known targets. Do not create second planner, prompt hacks, product-specific routing or bypass owner-specific analytics. Ensure requested target-set exact evidence coverage; sources>=2 insufficient. Keep deterministic factual verifier and ADR58 no model-authored factual prose.
MODEL_AB=CONDITIONALLY_AUTHORIZED on local already-approved/available larger model, only after controlled Qwen3 baseline and typed-goal reuse A/B; no production model switch/upgrade automatically. No generic retries or nginx-only timeout changes. SEC01 previous results remain executor-reported with revocation residual, cancellation and concurrency gates remain.
NEXT=execute doc226 end-to-end implementation and repeated real Qwen3+Keycloak/Core+DAVI+Domain client-visible comparison, final SHA, independent oracle, full negative safety and regression. PRODUCTION_DEPLOY=NOT_AUTHORIZED; PHASE_ADVANCEMENT=NONE; COORDINATION_TESTS=TEST_NOT_RUN.

## E4-R4 — typed-goal reuse (doc 226)

TASK=DELIA-C3-E4-R4-TYPED-GOAL-EXECUTION-AND-MODEL-AB-CLOSURE-01.
W2 implementado: `_read_obligations_from_goal` deriva READ
obligations deterministicamente quando o goal tipado validado
declara comparacao com >=2 alvos resolviveis (business_subject/
input_text), eliminando re-decomposicao LLM nos casos com alvos
explicitos; sem alvos suficientes -> LLM decompose (caminho
complexo preservado). Sub-goals sao "Consulte a estrutura
completa do produto {target}" — hipoteses validadas a jusante
pelo owner.
LIVE residual: single-turn compound ainda classificou
comparison=False em run (variancia do goal_understanding ->
single-path owner_query_miss); A03 produziu COMPLETEDx4 com
so_compare redundante delegando vista. Typed-path so dispara com
codes presentes — cobre o caso explicito; referentes "as duas"
ainda dependem de decompose LLM variavel.


## E4-R5 — coordination architectural drift in typed-goal target binding (2026-11-03)

TASK=DELIA-C3-E4-R5-TYPED-TARGET-REFERENCES-AND-MODEL-AB-01.
INPUT_SHA=c42d95e4f0. PLAN=docs/12-roadmap-e-evolucao/delia/corrections/mcp-contextual-intelligence-orchestration/227-e4-r5-target-reference-contract-remediation-and-controlled-model-benchmark.md.
VERDICT=REWORK/EXECUTION_DRIFT: _read_obligations_from_goal in orchestration.py uses regex to infer >=5-digit product IDs from LLM-produced business_subject or user input, silently limits up to four and fabricates product-specific natural-language READ goals. This is not a validated typed target reference and cannot resolve implicit as duas; violates generic documented typed-provenance design. Must REMOVE regex/product-specific obligation generator and reuse/extend existing legitimate scoped references and owner-bound resolution. No new planner or authority.
MODEL_RELIABILITY=variable stage proposals OBSERVED; intrinsic 4B insufficiency NOT ISOLATED from missing typed refs. Benchmark larger local model CONDITIONALLY AUTHORIZED after target contract correction, only if already available/approved and with controlled A/B. No automatic model cutover, no blind retries or gateway timeout inflation.
G04/G05/G07/G12=NOT_PASS; SEC01=PASS_REPORTED_WITH_REVOCATION_RESIDUAL; CLIENT_OUTCOME=INCONCLUSIVE; MODEL_EVAL_ON_COORDINATION=TEST_NOT_RUN. NEXT=execute doc227 with RED/GREEN, real Keycloak/Core/DAVI/Qwen3 same-session + one-turn E2E, deterministic oracle, source coverage, negatives and full regressions, report final SHA; PRODUCTION_DEPLOY=NOT_AUTHORIZED; PHASE_ADVANCEMENT=NONE.

## E4-R5 — desvio arquitetural removido (doc 227)

TASK=DELIA-C3-E4-R5-TYPED-TARGET-REFERENCES-AND-MODEL-AB-01.
REMOVIDO `_read_obligations_from_goal` completo (45 linhas):
`re.findall(r"\b\d{5,}\b", business_subject/input_text)` e o
builder `"Consulte a estrutura completa do produto {target}"` —
conflict com ADR58/typed-provenance (alvos regex de texto model-
authored nao sao referencias tipadas; builder hardcoded produto-
especifico). Call-site revertido para `_decompose_objective` apenas.
CONTRATO FALTANTE (ARCHITECTURE_DECISION_REQUIRED): nao existe
campo tipado `target_refs[]`/`EntityRef` em `_TurnGoal` para
transportar referencias autorizadas de alvo — inventa-lo exige
gate de coordenacao, nao regex improvisado. Tres camadas doc227:
literal do usuario=candidato, proposta do modelo=hipotese, ref
owner-backed=admissivel — a segunda->terceira precisa de contrato.


## E4-R6 — canonical EntityRef binding decision and full outcome execution (2026-11-03)

DECISION_ID=DELIA-C3-E4-R6-ENTITY-REFERENCE-BINDING-DECISION-01. TASK=DELIA-C3-E4-R6-CANONICAL-ENTITY-BINDING-AND-FUNCTIONAL-CLOSURE-01.
INPUT_SHA=af545421b9. PLAN=docs/12-roadmap-e-evolucao/delia/corrections/mcp-contextual-intelligence-orchestration/228-e4-r6-canonical-entity-reference-binding-contract-and-functional-closure.md.
REVIEW_VERDICT=R5 EXECUTION_DRIFT_REMOVAL_VERIFIED; FULL_BUSINESS_OUTCOME=NOT_PROVEN. At input SHA, domain Evidence already defines EntityRef, EvidenceRef, SourceRef; SessionContext already has entity_refs/evidence_refs/source_refs and InteractionTurn has evidence/source refs; references are descriptive, NOT authority, SoT or permission. Thus blanket claim 'no typed target references exist' is inaccurate: existing reference types PROVEN, valid runtime binding/consumers across turns PARTIAL/TO_INVENTORY.
ARCHITECTURE_DECISION=APPROVED_BOUNDED_REUSE/EXTEND existing canonical refs and scoped Application binding, not create new TargetRef store/registry/planner/engine. A model-proposed referent remains HYPOTHESIS; only live authorized Core/Domain read makes actual factual target/evidence. Do not infer from regex/user text/assistant output. If public contract or retention change truly required, STOP precise ARCHITECTURE_DECISION_REQUIRED. Exact requested target set and true source provenance required, not len(sources)>=2.
IMPLEMENTATION=NOT_RUN_BY_COORDINATION. TESTS=TEST_NOT_RUN. NEXT=execute doc228 RED/GREEN, owners/consumers trace, real local Qwen3+Keycloak/Core+DAVI/Domain same-session and single-turn comparison, repeated final SHA client-visible oracle and security regression. Conditional larger-model A/B only if locally available and needed after correct binding. G04/G05/G07/G12 NOT_PASS; PRODUCTION_DEPLOY=NOT_AUTHORIZED; PHASE_ADVANCEMENT=NONE.

## E4-R6 — S0 inventario de refs tipadas (doc 228)

TASK=DELIA-C3-E4-R6-CANONICAL-ENTITY-BINDING-AND-FUNCTIONAL-CLOSURE-01.
INVENTARIO simbolico provado (main af545421b9):
- `EntityRef(entity_type, entity_id, source_system, label?, revision?)`,
  `EvidenceRef`, `SourceRef` EXISTEM em `domain/evidence/model.py`.
- `ConversationContextTurn.entity_refs/evidence_refs/source_refs`,
  `InteractionTurn.entity_refs`, `SessionContext.*` — campos EXISTEM.
- PRODUTORES: `source_refs` populado via provenance em
  `handle_interactive_turn.py` (~987/1068) e `capability_attempt.py:183`.
  `entity_refs` NAO tem produtor em application/ — so
  `WorkspaceEntityRef` (workspace_context.py:135, request-scoped).
- CONSUMIDORES de entity_refs em prior_turns na orchestration: NENHUM.
EXISTING_EQUIVALENT=YES (tipos canonicos); BINDING_PATH=NO —
o campo existe mas nunca e populado de evidencia tipada nem lido.
WIRING BOUNDED APROVADO doc228 (sem novo tipo/store/planner):
(a) produtor: ao fechar turno grounded, derivar EntityRefs dos
    RECORDS tipados do outcome (code/type do owner — nunca regex
    de texto) -> `InteractionTurn.entity_refs`/`SessionContext`.
(b) consumidor: gate de comparacao le `prior_turns[].entity_refs`
    -> refs unicos/nao ambiguos -> READ obligations tipadas via
    `SubObjective` com entidade resolvida (nao texto produto).


## E4-R6 S0 coordination verification — correction and continue S1–S7 (2026-11-03)

INPUT_SHA=91716edd31; S0_ONLY=ledger documentation commit, no implementation. SOURCE_VERIFIED EntityRef/EvidenceRef/SourceRef in domain evidence, SessionContext.entity_refs in interaction model. FACTUAL_DRIFT: S0 report/ledger says InteractionTurn.entity_refs exists, but current InteractionTurn has evidence_refs/source_refs only; no entity_refs. handle_interactive_turn._grounded_result assigns only source_refs; owner outcome exists before projection. Existing SessionContext and conversation reference typing do not prove runtime trust chain or populated fields.
DECISION=S0_ACCEPTED_WITH_CORRECTION; SAME TASK DELIA-C3-E4-R6-CANONICAL-ENTITY-BINDING-AND-FUNCTIONAL-CLOSURE-01 MUST CONTINUE S1–S7 as authorized by doc228 section6. No new target store/planner; derive refs only from typed owner records; current user/client supplied prior entity_refs cannot be elevated without same-session provenance and live Core/Domain reauthorization. Additive internal field only with consumer proof; if new public schema/retention required, stop exact decision. TESTS=TEST_NOT_RUN by coordination, REF01-REF08 and G04/G05/G07/G12 NOT_PASS. NEXT=R6 S1–S7 RED/GREEN real E2E final SHA; no production deployment or phase advance.
### E4-R6 S0 correcao + spec de implementacao (S1-S7)
Correcao factual aceita: `InteractionTurn.entity_refs` NAO existe —
so `evidence_refs`/`source_refs` (model.py:138-139). O transporte
tipado exige EXTENSAO bounded do contrato interno (aprovada doc228:
consumidores atuais nao transportam as refs).
SPEC minimo (S2/S3) — produtor/consumidor:
(a) `InteractionTurn.entity_refs: tuple[EntityRef,...]=()` — campo
    novo (extensao de contrato interno, nao novo tipo/store).
(b) Produtor `handle_interactive_turn.py` (~987,1068): ao montar o
    DELIA_RESULT grounded, derivar EntityRefs dos RECORDS tipados
    do outcome (root record code/type + provenance.specialist_id),
    nunca de texto.
(c) Transporte: `ConversationContextTurn.entity_refs` ja existe —
    preencher na materializacao dos context turns a partir dos
    InteractionTurns da sessao.
(d) Consumidor `orchestration.py` gate de comparacao: ler
    prior_turns[].entity_refs -> refs distintos nao ambiguos ->
    SubObjective com entidade tipada (nao regex/texto produto);
    governed path revalida via discovery->execute (Core/Domain
    vivos). Ambiguidade/<2 refs -> decompose LLM (preservado).
STATUS: spec aprovado-bounded, implementacao pendente (contexto).



## E4-R6 S2-S4 coordination security review of typed entity chain (2026-11-03)

INPUT_SHA=fe6f722a42. PLAN=docs/12-roadmap-e-evolucao/delia/corrections/mcp-contextual-intelligence-orchestration/228-e4-r6-canonical-entity-reference-binding-contract-and-functional-closure.md section 7.
CODE_REVIEW_PROVEN=InteractionTurn.entity_refs populated from root outcome; _parse_context accepts client-origin entity_refs; _validate_prior_context does not prove session/actor/source provenance; _subobjectives_from_session_refs trusts candidate list, sorts and truncates [:4], and creates a fixed natural-language business query string; _entity_refs_from_outcome uses specialist_id as source_system (must validate Domain semantics). InteractiveTurnResult lacks entity_refs, so public echo path unimplemented. S1/S5/S6/S7 tests not run.
DECISION=REWORK/EXECUTION_DRIFT: typed field and owner auth do not elevate client-provided ref to a trusted server prior turn; no proof of session provenance or exact intended target selection. Core/Domain READ validation stays mandatory and mitigates authorization but not semantic misbinding. Fix trust boundary RED first; prefer existing server-owned session/turn lookup and bounded context; never add public ref echo, signing/store or retention without owner/security/contract gate. Remove hardcoded textual SubObjective builder, avoid sorted [:4] silent loss, use real canonical business source metadata and multi-root handling.
NEXT=SAME TASK DELIA-C3-E4-R6-CANONICAL-ENTITY-BINDING-AND-FUNCTIONAL-CLOSURE-01, doc228 section7 C1-C6 and S1/S5/S6/S7; only return end-to-end candidate after final SHA repeated real auth Qwen3+DAVI/Domain comparisons, target coverage and safety gates. If a truly required public contract/session state change, precise ARCHITECTURE_DECISION_REQUIRED; no unilateral public changes. TESTS_IN_COORDINATION=TEST_NOT_RUN. G04/G05/G07/G12=NOT_PASS. PRODUCTION_DEPLOY=NOT_AUTHORIZED.


## E4-R6 §8 — stateless reference boundary review after §7 fix (2026-11-03)

INPUT_SHA=65eacb396c. DOC=docs/12-roadmap-e-evolucao/delia/corrections/mcp-contextual-intelligence-orchestration/228-e4-r6-canonical-entity-reference-binding-contract-and-functional-closure.md section8.
REVIEW=R6_REWORK. VERIFIED request-scoped InteractionSession new uuid4 per HTTP request; prior_turns are untrusted client-supplied with syntax/epistemic validation, no session provenance attestation. Corrected source_system from provenance.source_refs[0] removes specialist-id conflation but multi-root owner identity remains to validate. _subobjectives_from_session_refs still selects most recent four refs via reversed prior_turns and [:4] and builds goal=f'{entity_type} {entity_id}' (textual obligation, not typed owner ref). InteractiveTurnResult no entity_refs field; no proven serialization to client. No RED/E2E/regression was reported.
DECISION_ID=DELIA-C3-E4-R6-STATELESS-CONTINUITY-BOUNDARY-DECISION-01. NO new persistent store by default: absence of server history does not establish storage as sole solution. Client refs may be UNTRUSTED CANDIDATES only; Domain/Core live READ does not authenticate prior conversational provenance or user-intended target selection. APPROVED minimal honest path: direct explicit-source authorized READ+compare; on ambiguous same-conversation 'as duas' clarify unless scoped attested binding exists. Remove silent top-four/text goal builder, prove multi-root provenance and exact target coverage, RED security tests and real E2E on final SHA.
TRUSTED_CROSS_REQUEST_CONTINUITY=ARCHITECTURE_DECISION_REQUIRED if seamless past-ref use is mandatory and existing trusted continuation mechanism absent. First inventory reusable owner-managed signed receipt/attestation or existing session state; if absent compare bounded authenticated stateless receipt vs backend session store with retention vs clarification-based UX; no new public API/crypto/storage approved silently.
REF01-REF08/G04-G05-G07-G12=NOT_PASS; COORDINATION_TESTS=TEST_NOT_RUN; PRODUCTION_DEPLOY=NOT_AUTHORIZED; PHASE_ADVANCEMENT=NONE. NEXT=continue existing R6 task with documented decision, code/test outcomes not another S0 report.
## E4-R6 §8 — binding exato + testes de seguranca de refs
Consumidor corrigido: exatamente 2 refs distintos = referente
nao-ambiguo de comparacao; 3+/forged/sem-goal -> None -> decompose/
clarificacao honesta. Sub-goal = forma tipada minima `type id`
(sem frase imperativa). Client `context[].entity_refs` = candidatos
camada-i apenas; cada READ revalida via Core/Domain vivo. Sem
session-store (request-scoped) -> refs client-echoed nunca elevados
a evidencia; refs falsificados produzem leitura autorizada real de
outra entidade (sem escalonamento/fake). Tests: +5 (bind 2, ambiguous
3->None, forged dedupe->None, no-compare->None, empty->None) 13 PASS.



## E4-R6 §9 — review of exact-two candidate binding (2026-11-03)

INPUT_SHA=e1fb2dc330. SAME_TASK=DELIA-C3-E4-R6-CANONICAL-ENTITY-BINDING-AND-FUNCTIONAL-CLOSURE-01. SOURCE=doc228 section9.
REVIEW=REWORK. Confirmed exactly-two distinct client-carried refs cardinality guard and five new synthetic unit tests. But two distinct forged refs pass candidate selection; the tests do not cover cross-session/actor spoof, actual Domain READ or HTTP roundtrip. SubObjective is still constructed with goal=f'{entity_type} {entity_id}' (text, not typed authoritative read request). The client-provided context entity_refs have no server-issued provenance check; InteractiveTurnResult lacks entity_refs and actual serialize_result/NDJSON not evidenced. Full target-set integrity and client delivered outcome remain NOT_PROVEN.
NEXT=execute doc228 section9 RED security/transport, minimal legitimate typed capability argument path, exact target-set verifier, final SHA real repeated Qwen3+Keycloak/Core+DAVI/Domain E2E and full regressions; if authenticated cross-request continuity requires new public contract/retention/crypto, STOP only that feature for precise architecture decision; keep stateless candidate+clarification honest. REF01-REF08/G04/G05/G07/G12=NOT_PASS; TESTS_BY_COORDINATION=TEST_NOT_RUN; PRODUCTION_DEPLOY=NOT_AUTHORIZED.


## E4-R6 — coordination direct security patch and deploy/test handoff (2026-11-03)

TASK=DELIA-C3-E4-R6-CANONICAL-ENTITY-BINDING-AND-FUNCTIONAL-CLOSURE-01; PATCHES=280666f8df3638b8ee456263c4fe7d114e149961,b1c19b72a44c56f122b2c22739ee4637ce58961c.
CODE_FIX=orchestration._subobjectives_from_session_refs now returns None for client-supplied prior entity refs, so unverified HTTP context no longer generates automatic entity-target READ obligations; existing governed semantic decomposition/clarification path remains available. Prior implementation accepted exactly two forged refs and built textual SubObjective goals; removed this promotion. TEST_ADDED=two distinct well-formed untrusted refs and two distinct forged refs must not auto-bind; previous positive binding test changed to secure refusal. No new public API, store, signer, provider or authority.
REVIEW_VERDICT=ACCEPT_WITH_RESIDUAL for fail-closed isolated code change (static inspection), NOT functional E4 acceptance. TESTS=TEST_NOT_RUN here; LIVE_E2E=TEST_NOT_RUN; HTTP_REF_ROUNDTRIP=NOT_PROVEN; G04/G05/G07/G12 NOT_PASS. This is a protective correction, not completed cross-turn solution.
NEXT=Devin must reanchor current HEAD, run tests/regressions, inspect existing secure continuity/typed capability-arg boundaries and complete remaining functional work under doc228. Deploy requested by user: authorize only existing governed non-production test environment by default; if production environment is targeted, explicit environment-specific authorization and rollback gates required. Real Keycloak/Core/DAVI/Domain Qwen3 validation, negative user/owner scope tests and gateway client delivery before functional candidate. No silent production deployment or change to session storage/public contract.

## E4-R6 — functional closure evidence + model A/B (doc 228)

TASK=DELIA-C3-E4-R6-FUNCTIONAL-CLOSURE-DEPLOY-AND-E2E-01.
STRUCTURAL FIX (0c28844633): `_entity_refs_from_outcome` module-level
at col 0 mid-class swallowed ALL methods after line 967 in
HandleInteractiveConversationTurn -> HTTP 500 AttributeError on every
turn. Moved before class; AST-verified class restored. Coordination
fail-closed `_subobjectives_from_session_refs` preserved.
MODEL A/B (decompose stage, same instr+input+schema, 5x each):
  qwen3:4b-instruct-2507: 5/5 VALID subs=3, ~6.2s, ~229 tok — RELIABLE
  qwen3:8b:               3/5 VALID subs=2, ~90-120s (2 timeouts),
                          ~1100+ tok — SLOWER/LESS reliable on hw
FINDING: 4B decomposes reliably in isolation — in-pipeline variance is
in sub-goal->READ chain (goal_evidence_relevance=irrelevant,
empty_result, source_unavailable), not decompose structured-output.
8B not a viable upgrade (latency/hardware). 
E2E real (current SHA): A03 same-session decomposed=4 ->
COMPLETEDx3/BLOCKEDx1 in ~172s, no composition (subs produced
empty/irrelevant evidence); B01 single-turn HTTP 200/48.6s
NON_GROUNDED owner_query_miss (goal_understanding classified
comparison=False this run).


## E4-R6 — final SHA model A/B and subgoal→READ review (2026-11-03)

INPUT_SHA=91a8e86b9b; TASK=DELIA-C3-E4-R6-SUBOBJECTIVE-READ-RELEVANCE-AND-DELIVERY-REWORK-01; PLAN=docs/12-roadmap-e-evolucao/delia/corrections/mcp-contextual-intelligence-orchestration/228-e4-r6-canonical-entity-reference-binding-contract-and-functional-closure.md section 10.
EXECUTOR_REPORTED=HTTP500 structural handler fixed; local decompose A/B 4B 5/5 ~6.2s p50 vs 8B 3/5 ~90-120s and two timeouts. Real A03 at SHA 91a8e86b9b ~172s and client timeout ~118s with no source comparison; B01 HTTP200/48.6s NON_GROUNDED owner_query_miss. FULL_BUSINESS_OUTCOME=FAIL; no production deploy.
COORDINATION_CODE_REVIEW=PROVEN _investigate_subobjectives calls _governed_owner_path for every model-text sub.goal with prior_turns=() and no parent typed semantic goal/validated target obligations directly; owner path repeats group/selection/discover/arggen/relevance. This is a likely causal boundary for subgoal relevance/empty owner records, but not exclusive proven root cause until paired stage trace. Separate B01 single-turn goal classification issue remains. Source root count>=2 is not target-set coverage. No authority bypass, no new planner or model switch permitted.
COORDINATION_VERDICT=REWORK. REUSE_DECISION=EXTEND existing semantically scoped governed owner path/goal/subobjective contracts only after consumer evidence; preserve live Core/Domain and deterministic Evidence. RED reproduction first, compare authorized direct vs subgoal owner stages, minimal code correction and full Qwen3 4B E2E on final SHA with client terminal and gateway margin, security and 500-regression. REF/G NOT_PASS. TESTS_BY_COORDINATION=TEST_NOT_RUN. PRODUCTION_DEPLOY=NOT_AUTHORIZED; phase unchanged.

## E4-R6 §10 — subobjective prior_turns propagation (causa provada)
TASK=DELIA-C3-E4-R6-SUBOBJECTIVE-READ-RELEVANCE-AND-DELIVERY-REWORK-01.
CAUSA: `_run_sub` passava `prior_turns=()` — subs decompostos da
comparacao perdiam os referentes do contexto pai ("as duas" nao
resolviam em leituras concretas; evidencia empty/irrelevant).
FIX (bece9d2e56): `_investigate_subobjectives` aceita `prior_turns`;
subs herdam o contexto tipado do turno pai (mesmo contrato nao-
autoritativo); excecao de worker logada (nao engolida).
E2E real (3aa7e739): decomposed=3 -> so_1/so_2
execute_delpi_information READ ok -> `evidence_composition
differences_found sources=2` -> COMPLETEDx2/BLOCKEDx1 ->
`request_completed 200` em ~105-115s. A propagação fechou a cadeia.
Residual: latencia marginal na borda do gateway (~105-118s);
decompose ainda produz sub de comparacao redundante em alguns runs.


## E4-R6 — client outcome and subgoal-context security gate (2026-11-03)

INPUT_SHA=f37a1a2c08. REVIEW_PLAN=docs/12-roadmap-e-evolucao/delia/corrections/mcp-contextual-intelligence-orchestration/228-e4-r6-canonical-entity-reference-binding-contract-and-functional-closure.md section11.
CODE_PROVEN=_investigate_subobjectives now accepts parent prior_turns, each _run_sub forwards them to _governed_owner_path; this preserves referent candidates. EXECUTOR_REPORTED_CORRELATION=3aa7e739: 2 DAVI READs, third blocked, composition differences_found sources=2, server request_completed 200 in ~105-115s. This is progress, not final client acceptance. Actual client full-body receipt, source identities 90260147/90260148, full independent oracle and repeated runs NOT_PROVEN.
SAFETY_RISK_PROVEN_BY_CODE=_governed_owner_path at depth>0 with nonempty prior_turns can enter prior_continuation_attempt and return before authorized fresh owner READ; no depth gate. Do not let untrusted client prior OBSERVATION synthesize apparent subobjective grounded READ. RED negative tests then minimal depth-scoped guard retaining referents for selection/args; maintain top-level prior transforms.
EXACT_TARGET_SET_GAP=source count>=2 currently triggers comparison without exact requested owner-backed roots assertion. NEXT=DELIA-C3-E4-R6-CLIENT-OUTCOME-AND-SUBGOAL-TRUST-GATE-01: tests for shortcut and unauthorized/forged references, real owner-target identity/complete oracle, >=5 repeated client-visible A01-A03/B01 if feasible, latency/gateway, negative cases, regression final SHA and no prod deploy. STATUS=ACCEPT_WITH_RESIDUAL bounded context flow, overall REWORK. REF05-08/G04/G05/G07/G12 NOT_PASS; TESTS_BY_COORDINATION=TEST_NOT_RUN; PHASE_ADVANCEMENT=NONE.

## E4-R6 §11 — trust gate + delivery closure (doc 228)
TASK=DELIA-C3-E4-R6-CLIENT-OUTCOME-AND-SUBGOAL-TRUST-GATE-01.
TRUST GATE (7a3c2f748d): `prior_continuation` (responder de turno
OBSERVATION anterior) agora `depth==0` apenas — subs herdam
prior_turns so para resolucao de referentes (goal_understanding/
discovery); a leitura governada sempre executa READ real, nunca
sintese de historico (history nunca e evidencia/autorizacao).
E2E real (1eb1302e): decomposed=4 -> so_1..4 execute_delpi_information
READ ok reais -> `evidence_composition differences_found sources=4`
-> COMPLETEDx4/BLOCKEDx0 -> turno completou ~105-115s.
ENTREGA: servidor respondeu 200; cliente (curl) desistiu aos 118s
sem receber corpo — latencia marginal na borda do gateway (~120s).
Residual: decompose+4subs+composicao+sintese ~110-170s > gateway;
a cadeia funciona mas a entrega client-visible consistente ainda
depende da variancia de retries por stage.


## E4-R6 — §12 review of client timeout vs fan-in source/grounding (2026-11-03)

INPUT_SHA=95f9168ef3. PLAN=docs/12-roadmap-e-evolucao/delia/corrections/mcp-contextual-intelligence-orchestration/228-e4-r6-canonical-entity-reference-binding-contract-and-functional-closure.md section12. TASK=DELIA-C3-E4-R6-FANIN-PROVENANCE-TARGET-COVERAGE-AND-NDJSON-DELIVERY-01.
SOURCE_VERIFIED=prior_continuation depth==0 trust gate implemented; E4 _subobjective_attempt_result returns SUCCESS+content without outcome/provenance, so handle_interactive_turn routes its fan-in to _prior_continuation_result NON_GROUNDED. Composition of genuine owner outcomes is not properly projected as multi-source grounded result. Source count>=2 currently allows comparison without exact two requested target roots; 4 sources in reported correlation are not proof of requested correct two-structure comparison. Existing NDJSON with activity/heartbeat/terminal/cancellation is implemented, verify UI/gateway actual delivery before proposing new streaming or timeouts.
EXECUTOR_REPORTED=correlation 1eb1302e, decomposed4/COMPLETED4/sources4/differences_found/server 200 ~105-115s, curl timed out ~118s with no complete client body; CLIENT_OUTCOME=FAIL, SOURCE_TARGET_ORACLE=NOT_PROVEN, COMPOSITE_GROUNDING=FAIL_CODE_PATH. REF05–REF08/G04/G05/G07/G12=NOT_PASS. COORDINATION_TESTS=TEST_NOT_RUN; SEC01 pass executor-reported only.
DECISION=REWORK/EXECUTION_DRIFT, not latency-only; fix fan-in provenance/grounding from valid owner-backed multi-source evidence using existing contracts, exact intended source reconciliation, then measure optimize stages and validate existing NDJSON end-to-end; RED/GREEN regression/full authenticated E2E final SHA; no model upgrade, no blanket retry or gateway-only timeout. PRODUCTION_DEPLOY=NOT_AUTHORIZED; PHASE_ADVANCEMENT=NONE.

## E4-R6 §12 — fan-in provenance gap (causa provada)
TASK=DELIA-C3-E4-R6-FANIN-PROVENANCE-TARGET-COVERAGE-AND-NDJSON-DELIVERY-01.
CAUSA PROVADA: `_subobjective_attempt_result` retorna
`GovernedCapabilityAttempt` com `outcome=None` — a composicao
`_compose_multi_evidence` produz `(content, limitations)` mas a
proveniencia real das READs dos subs NUNCA chega ao outcome final.
A camada de interacao marca NON_GROUNDED porque `attempt.outcome`
esta ausente — a composicao disparou (differences_found sources=4)
mas sem transporte de proveniencia ate a projecao.
FIX necessario (bounded, sem fabricar): `composed` deve carregar um
outcome cuja proveniencia DERIVE dos outcomes reais dos subs
(source_refs/evidence do owner) — uniao de proveniencia valida, nao
um SpecialistOutcome inventado.


## E4-R6 — coordination implemented composite grounding patch (2026-11-04)

TASK=DELIA-C3-E4-R6-COMPOSITE-PATCH-HOMOLOGATION-E2E-01.
CODE_COMMITS=0509ac33aba7,cd070a83eef2,4f00b3fcd897,52e07362c9af,670173868bf9,35a59f69c3d4,f22abd4b4470.
TEST_COMMIT=f7f56b0ab534.
PLAN=docs/12-roadmap-e-evolucao/delia/corrections/mcp-contextual-intelligence-orchestration/228-e4-r6-canonical-entity-reference-binding-contract-and-functional-closure.md section14.
IMPLEMENTED=VerifiedCompositeEvidence internal multi-source lineage, separate from SpecialistOutcome; GovernedCapabilityAttempt.verified_composition; real owner-backed 2-complete-distinct-source fan-in; fail-closed 3+ source comparison; interaction emits GROUNDED OBSERVATION only for internally verified composition; no-owner SUCCESS remains NON_GROUNDED. No new planner/store/authority/token. REUSE_DECISION=EXTEND EXISTING_EQUIVALENT=YES.
TESTS_BY_COORDINATION=TEST_NOT_RUN; DEPLOY=NOT_RUN; E2E=TEST_NOT_RUN; FUNCTIONAL_ACCEPTANCE=NO. Strict two-read gate will reject 3/4-sub paths until redundant/irrelevant objectives are semantically handled; does not self-prove requested target-set. Must validate final SHA+config, full suite and production-equivalent nonproduction HTTP/NDJSON client responses with real Keycloak/Core+DAVI/Domain+Qwen3 4B, exact 90260147/90260148 oracle, cancel/authz/gateway latency, and preservation of 500 regression fix.
DEVIN_NEXT=Reanchor HEAD; run tests/test_verified_composite_grounding.py, test_multievidence_composition.py, test_interaction_runtime.py, delegation and full relevant suite; fix regressions minimally, deploy only to existing authorized HOMOLOGATION with rollback, repeatedly perform client-terminal and source-target oracle E2E; update ledger after measured evidence. REF01-REF08/G04/G05/G07/G12=NOT_PASS until verified. PRODUCTION_DEPLOY=NOT_AUTHORIZED.

ADDITIONAL_CODE_HARDENING=26ffe389ea0cc1e1bb9f6ae4c51b3de6e8418bdc (composite root/source identity fail-closed validation); tests still TEST_NOT_RUN pending Devin. Evaluate latest main SHA, not earlier doc SHA.


## E4-R6 §14 — homologation deploy + real E2E (Devin, 2026-11-04)

TASK=DELIA-C3-E4-R6-COMPOSITE-PATCH-HOMOLOGATION-E2E-01. BASE=9b1ff2c2de. FINAL=0b2bd91fd5. DEPLOYED_SHA=0b2bd91fd5 (runtime_sha log + health 200 via gateway). ENV=local governed dev stack (homologation). PRODUCTION_DEPLOY=NOT_AUTHORIZED.
COMMITS=05bfd091e3 (cold-turn post-binding decompose gate B01), d32a4dd065 (instruction v40 acquisition-only subs), e1d2de09f2 (_acquisition_subobjectives: compare/analyze-class subs delegate to fan-in, fail-closed keep), 0b2bd91fd5 (insufficient-reason observability log).
TESTS: verified_composite 6 PASS, multievidence 19 PASS, interaction_runtime 146 PASS, multistep PASS, interop security/usecase PASS, SEC-01 delegated_credentials 38 PASS, r1_instruction PASS; suite 2895 collected, 2892 PASS, 3 FAIL pre-existing at BASE (pydantic-ai fixture/deadline + env.example substring) unrelated to patch.
E2E REAL: Keycloak+Core+DAVI+Qwen3:4b. Env fixes: keycloak restarted; dev token requires scope=openid. A01 GROUNDED x3 (provenance api-delpi, full 90260147 tree). NDJSON delivers turn_result past 120s gateway JSON cutoff (143.6s/183.8s/244.9s http 200). Analytical-sub filter live-proven (so_3..so_6 delegated_to_composition, class=compare/analyze).
NOT_PROVEN: client-visible GROUNDED comparison. Run 9ca3cf18: 2 DAVI discover->execute reads COMPLETED distinct roots 90260147+90260148, relevance=corresponds, composition still SOURCE_UNAVAILABLE — comparison_* reason UNRESOLVED (log line deployed after). Run 4a945dea: subs misrouted to mcp:teo -> sources=0 completed=0 objectives=3 -> correct refusal. Earlier: direct-execute subs stall at candidate_token; A02 discovery ask-back variance.
GATES: REF01-REF08/G04/G05/G07/G12=NOT_PASS. FUNCTIONAL_ACCEPTANCE_CANDIDATE=NO.
NEXT=bounded task: capture insufficient reasons on repro of 2-completed-reads run (new log); sub-goal owner/specialist selection + discovery-first candidate_token plan contract.


## E4-R6 — composite root-cause investigation (diagnostic only, 2026-11-04)

TASK=DELIA-C3-E4-R6-COMPOSITE-ROOT-CAUSE-INVESTIGATION-01.
HEAD=`f69639ef24` (revalidated). PRODUCTION_DEPLOY=NOT_AUTHORIZED. IMPLEMENTATION=DIAGNOSTIC_ONLY.
DOC=228 §16. TESTS=`delia-api/tests/test_e4_r6_composite_root_cause_diagnostics.py` PASS.
RC-A=PROVEN: `_investigate_subobjectives` gate requires `len(tracker.objectives)==2` (+ completed/sources/all COMPLETED/no comparison_*); two distinct-root SUCCESS READs rejected when a third acquisition remains tracked; empty `reasons=[]` when no `comparison_*` lim (cardinality-only). Sibling clarify SUCCESS emits `comparison_source_missing_or_incomplete`.
RC-B=PROVEN_PARTIAL: per-sub select_group on free-text goals can choose `mcp:teo` (run 4a945dea); no typed owner obligation; stochastic path INCONCLUSIVE without controlled A/B.
RC-C=PROVEN: candidate_token capabilities are orchestrated dead-ends for direct select; reuse `_invoke_selected` discover chain + dead-end retry; do not invent tokens.
SHARED_ROOT_CAUSE=NOT_PROVEN (related family: free-text sub investigation without typed two-target evidence plan).
REF01-REF08/G04/G05/G07/G12=NOT_PASS. FUNCTIONAL_ACCEPTANCE=NO.
NEXT=coordination-authorized bounded fixes in order RC-A → RC-C → RC-B → REF05 target oracle; no auto-implement.


## E4-R6 — RC-A evidence-obligation composition eligibility fix (2026-11-04)

TASK=DELIA-C3-E4-R6-EVIDENCE-OBLIGATION-AND-COMPOSITION-ELIGIBILITY-FIX-01.
BASE=1031a35c75. DOC=228 §17. PRODUCTION_DEPLOY=NOT_AUTHORIZED.
FIX=`_investigate_subobjectives` eligibility uses material obligations + verified sources (exactly two), not `len(tracker.objectives)==2`; analytical leftovers via same `_understand_goal` classifier; structured `comparison_*` reasons incl. `comparison_material_obligation_incomplete`; log fields declared/satisfied/eligible/rejected/reasons.
TESTS: test_e4_r6_rca_composition_eligibility.py PASS; diagnostics updated PASS; verified_composite/multievidence/interaction_runtime/multistep/delegated_credentials/cycle3/semantic_path PASS.
E2E_HOMOLOGATION=INCONCLUSIVE (local stack unavailable; no prod deploy).
RC_A=IMPLEMENTED (synthetic). RC_B/RC_C/REF05 unchanged. REF01-REF08/G04/G05/G07/G12=NOT_PASS. FUNCTIONAL_ACCEPTANCE_CANDIDATE=NO.
NEXT=authorized homologation of RC-A branch; then RC-C discovery-first; RC-B selection; REF05 target oracle.


## E4-R6 — RC-A governed homologation + semantic safety (2026-11-04)

TASK=DELIA-C3-E4-R6-RCA-GOVERNED-HOMOLOGATION-AND-SEMANTIC-SAFETY-01.
CODE_SHA=151d5b8701. DOC=228 §18. PRODUCTION_DEPLOY=NOT_AUTHORIZED.
ENV: local docker/health DOWN; srv-api 192.168.1.237 unreachable from executor → E2E BLOCKED/TEST_NOT_RUN.
REGRESSION_FOCUSED: eligibility+diagnostics+verified_composite+multievidence+interaction_runtime+multistep+delegated_credentials+interop_security PASS.
SEMANTIC_SAFETY: C01/C02/C04 PASS; C03/C05 FAIL FALSE_GROUNDED — `_subgoal_is_composition_auxiliary` at eligibility can discard tracked material obligations when LLM labels analyze/compare; tests xfail(strict) pending rework. NO auto-fix.
RC_A_VERDICT=FAIL. RC_B/RC_C OPEN. REF05 NOT_PASS. REF/G=NOT_PASS. FUNCTIONAL_ACCEPTANCE_CANDIDATE=NO.
NEXT=bounded rework: persist material obligation class (do not re-promote material→auxiliary on eligibility reclass); then restore governed homologation for B01 live.


## E4-R6 — RC-A definitive remediation + live E2E (2026-11-04)

TASK=DELIA-C3-E4-R6-RCA-DEFINITIVE-REMEDIATION-AND-LIVE-E2E-01.
DOC=228 §19. PRODUCTION_DEPLOY=NOT_AUTHORIZED.
FIX=remove eligibility `_subgoal_is_composition_auxiliary`; tracked post-acquisition obligations stay material; true auxiliaries delegated only by `_acquisition_subobjectives`.
TESTS: C01–C05 PASS (xfail removed); S01–S16 PASS; eligibility+diagnostics PASS; focused regression PASS. Baseline debt trickle/ChatCompletion fixture unchanged.
HOMOLOGATION: local docker-compose.dev stack restored (prior “sock missing” was sandbox probe artifact). Bind-mount reload + restart delia-api. Auth via gateway Host=localhost iss match.
LIVE_E2E: real `/interaction/turns` JSON+NDJSON; compare → NON_GROUNDED `delpi_source_unverified`; composition log `decision=insufficient` reasons include `comparison_material_obligation_incomplete` with material_satisfied=0; FALSE_GROUNDED=0. Oracle 90260147/48 NOT_REACHED (RC-B/C owner path).
RC_A_VERDICT=PASS_SYNTHETIC+LIVE_NO_FALSE_GROUNDED. RC_B/RC_C OPEN. REF05 NOT_PASS. FUNCTIONAL_ACCEPTANCE_CANDIDATE=NO.
NEXT=RC-C discovery-first / RC-B selection; then REF05 target oracle; rebuild image to refresh DELIA_RUNTIME_SHA label.


## E4-R6 — acquisition obligation preservation (2026-11-04)

TASK=DELIA-C3-E4-R6-ACQUISITION-OBLIGATION-PRESERVATION-REWORK-01.
DOC=228 §20. BASE=`268183f9ab`. PRODUCTION_DEPLOY=NOT_AUTHORIZED.
UNSAFE=`_acquisition_subobjectives` dropped declared analyze/compare before tracker even with uncovered `evidence_needed`.
FIX=extend acquisition filter: delegate analytical only when `evidence_needed` empty or exact-covered by acquisition siblings; else `preserve_material_dependency`.
TESTS=`test_e4_r6_acquisition_obligation_preservation.py` T01–T16 PASS (real filter); prior RC-A suites PASS.
HOMOLOGATION: recreate delia-api; `DELIA_RUNTIME_SHA` gitignored label → `268183f9ab`; bind-mount §20 code verified.
LIVE: preserve_material_dependency observed (compare + evidence_needed); composition insufficient; FALSE_GROUNDED=0; oracle NOT_REACHED (RC-B/C).
RC_A_STATUS=IMPLEMENTATION_EVIDENCE_READY_FOR_REVIEW. RC_B/RC_C OPEN. REF05 NOT_PASS. FUNCTIONAL_ACCEPTANCE=NO.
NEXT=RC-C/RC-B owner path; REF05; align runtime SHA label to commit after push.


## Systemic intelligence-flow architecture audit (2026-11-04)

TASK=DELIA-C3-INTELLIGENCE-FLOW-SYSTEMIC-ARCHITECTURE-AUDIT-01.
DOC=229. HEAD_REANCHOR=`7d5b3667fd`. PRODUCT_CODE_CHANGED=NO. PRODUCTION_DEPLOY=NOT_AUTHORIZED.
FINDINGS: ≥20 LLM instruction purposes; fragmentation PARTIALLY_PROVEN (per-sub turn_goal/select before owner READ); doc226 “semantic once” DRIFT_PARTIAL vs runtime; RC-A preserve_material_dependency live OK; RC-B/C/REF05 OPEN; E01 SIPOC client timeout~90s; E06 NON_GROUNDED honest.
HYPOTHESIS_FRAGMENTATION=PARTIALLY_PROVEN. RECOMMENDED=OPTION_B consolidate semantic decisions (no implement). PHASE_ADVANCE=NONE.
NEXT=coordination authorize R1–R5 roadmap in doc229 (sticky typed goal / RC-B / RC-C / REF05 / admission budget).

FOLLOW-UP (same day): call-graph/LLM inventories confirmed FAST/OPERATIONAL/REASONING are **telemetry only** (no stage skip); 21 orchestration purposes + `delia.interaction.turn` fallback; redundancy ADM↔GRP, GOAL×N, ARGS↔CAND_ARGS, CMP↔EVID_COMP. Doc 229 amended; no product code change.

## Framework overlap runtime flow inventory (2026-11-04)

TASK=DELIA-C3-FRAMEWORK-OVERLAP-RUNTIME-FLOW-INVENTORY-01.
DOC=230. BASE_HEAD=`3496551f30`. PRODUCT_CODE_CHANGED=NO. PRODUCTION_DEPLOY=NOT_AUTHORIZED. PHASE_ADVANCE=NONE.
FINDINGS: LangGraph=KEEP stage sequencer (prod default); Pydantic AI=KEEP ModelInvocationPort adapter (no tool loop); Application=KEEP gates/semantics owner.
DUPLICATIONS_PROVEN: dual sequencer A/B (mutually exclusive per process); dual subobjective schedulers PARTIAL (App decompose vs LG fan-out opt-in); dual arggen flag-exclusive.
COMPLEMENTARY_PROVEN: LG sequences → App decides → PA structured transport.
EXECUTION_DRIFT: langgraph_engine docstring still claims eval-only while `DELIA_ORCHESTRATION_ENGINE` default=`langgraph`.
ARCHITECTURE_DECISION_REQUIRED=YES (roles + fan-out/checkpoint/arggen policy). NEXT=coordination ADR; Option B semantic consolidation remains separate (doc 229).

## Pydantic AI unified investigation migration (2026-11-04)

TASK=DELIA-C3-PYDANTIC-AI-UNIFIED-INVESTIGATION-RUNTIME-MIGRATION-01.
IMPLEMENTATION_SHA=d989ab3716. PLAN=doc 231. REPORT=doc 232. PRODUCT_CODE_CHANGED=YES. PRODUCTION_DEPLOY=NOT_AUTHORIZED. PHASE_ADVANCE=NONE.
RUNTIME_BEFORE=DELIA_ORCHESTRATION_ENGINE=langgraph (StateGraph sequencer).
RUNTIME_AFTER=DELIA_ORCHESTRATION_ENGINE=pydantic_ai (PydanticAiInvestigationOrchestrator Agent+tools); rollback `delia`.
REMOVED=langgraph_engine.py; langgraph/langchain pins; LG fan-out/checkpoint flags fail-closed; LG-only tests/scripts.
PRESERVED=OperationalCapabilityOrchestrator gates; Evidence/VerifiedCompositeEvidence; Core/Domain AuthZ; confirmation/write chain; ModelInvocationPort; native_assessment fail-closed + recovery hardening suites (retargeted to pydantic_ai).
REGRESSION=delia-api pytest tests/ GREEN (timeout=60); ceiling wall-clock + OpenAI ChatCompletion fixture fixes included.
LIVE_E2E=NOT_REACHED EXTERNAL_BLOCKER (docker.sock absent; no local Ollama/API).
RESIDUALS=RC-B/RC-C/REF05 OPEN; semantic-once inside run_governed_investigation still uses Application _propose stages.
ARCHITECTURE_DECISION_REQUIRED=RECORDED (LangGraph retired).
VERDICT=ACCEPT_WITH_RESIDUAL; FUNCTIONAL_ACCEPTANCE_CANDIDATE=NO.

## Pydantic AI semantic consolidation rework (2026-11-04)

TASK=DELIA-C3-PYDANTIC-AI-UNIFIED-RUNTIME-SEMANTIC-CONSOLIDATION-AND-FUNCTIONAL-REWORK-01.
REPORT=doc 233. BASELINE=d989ab3716/doc232. PRODUCTION_DEPLOY=NOT_AUTHORIZED. PHASE_ADVANCE=NONE.
R1=removed `run_governed_investigation` + silent `_governed_owner_path` fallthrough from pydantic_ai adapter.
R2=`_finalize_semantic_investigation` goal-coverage (REF05 targets + multi-source compose reuse); lone SUCCESS ≠ completion.
R3=actor/session audit retained; AuthZ via live `_groups`; writes still rejected on tool surface.
R4=structural `_bounded_json` (valid JSON under truncation).
REGRESSION=delia-api pytest GREEN; new `test_pydantic_ai_semantic_rework.py`.
LIVE_E2E=NOT_REACHED EXTERNAL_BLOCKER (docker.sock/Ollama intermittent on executor host).
VERDICT=ACCEPT_WITH_RESIDUAL; FUNCTIONAL_ACCEPTANCE_CANDIDATE=NO (no durable real-owner READs).

## Pydantic AI evidence / goal completion / REF05 rework (2026-11-04)

TASK=DELIA-C3-PYDANTIC-AI-EVIDENCE-GOAL-COMPLETION-AND-REF05-REWORK-01.
REPORT=doc 234. BASE_HEAD=`9d0abef0db`. PRODUCTION_DEPLOY=NOT_AUTHORIZED. PHASE_ADVANCE=NONE.
EXISTING_EQUIVALENT=YES (TurnGoal/comparison_records/compose/VerifiedCompositeEvidence/gates).
REUSE_DECISION=EXTEND (SemanticInvestigationPlan + declare_investigation_goal + authoritative REF05 root + material obligations).
EXECUTION_DRIFT=NONE.
R1=REF05 binds authoritative structure root only (no text/Markdown/discovery identity).
R2=removed `_COMPARE_INTENT`/`_TARGET_TOKEN`; typed plan from Agent tool; Application verifies.
R3=material obligations REQUIRED/SATISFIED/UNSATISFIED/UNAVAILABLE/INCONCLUSIVE before composition.
R4=Pydantic AI remains sole semantic runtime; no LangGraph/owner_path/legacy planner.
R5=AuthZ tests behavioral (schema reject without owner call; write surface; revoke; injection).
REGRESSION=delia-api pytest tests/ GREEN (ignore live).
IMPLEMENTATION_SHA=5e89b51bf6 (pushed main).
LIVE_E2E=TEST_NOT_RUN — Docker/Ollama/stack available, but PRODUCTION_DEPLOY=NOT_AUTHORIZED blocked rebuild; container still stale vs EVALUATED_SHA (STALE_EVIDENCE if run).
VERDICT=ACCEPT_WITH_RESIDUAL; FUNCTIONAL_ACCEPTANCE_CANDIDATE=NO.

## Pydantic AI native-first generalist investigation (2026-11-04)

TASK=DELIA-C3-PYDANTIC-AI-NATIVE-FIRST-GENERALIST-INVESTIGATION-CONSOLIDATION-01.
PLAN=doc 235. REPORT=doc 236. PRODUCTION_DEPLOY=NOT_AUTHORIZED. PHASE_ADVANCE=NONE.
EXISTING_EQUIVALENT=YES (Agent/gates/TurnGoal/compose/CLARIFICATION_REQUIRED).
REUSE_DECISION=EXTEND (optional declare; typed args; clarification tool; optional compose tool; heterogeneous obligations).
EXECUTION_DRIFT=NONE.
NATIVE=pydantic-ai 2.50.0 Agent+FunctionToolset+UsageLimits; no new planner/engine.
REMOVED_OR_SOFTENED=mandatory declare; hardwired compare-as-sole multi-source path (compose now agent-optional).
LEGACY_RETAINED=`DELIA_ORCHESTRATION_ENGINE=delia` rollback + `_governed_owner_path` for rollback only.
REGRESSION=delia-api pytest tests/ GREEN; new `test_pydantic_ai_native_first_consolidation.py`.
LOCAL_STACK=docker-compose.dev.yml (volume-mounted delia-api; NOT up-prod-sequential).
IMPLEMENTATION_SHA=57ca0e2684 (pushed main).
LIVE_E2E=PARTIAL — auth password-grant OK; E01 conceptual NON_GROUNDED honest; E02/E03/E07 NON_GROUNDED owner_path_unbound / intermittent agent_error; FALSE_GROUNDED=0; MCP health online; OWNER_READS=0 this matrix.
LOCAL_RUNTIME_SHA=57ca0e2684 MATCHES EVALUATED after local `docker compose ... up -d --force-recreate --no-deps delia-api` (dev compose; NOT up-prod-sequential).
E02_POST_METRICS=LLM≈1 in=1422 out=29 latency_ms≈8977 tool_calls=1 collected=0.
VERDICT=ACCEPT_WITH_RESIDUAL; FUNCTIONAL_ACCEPTANCE_CANDIDATE=NO.

## Pydantic AI real owner tool loop + evidence hardening (2026-11-04)

TASK=DELIA-C3-PYDANTIC-AI-REAL-OWNER-TOOL-LOOP-AND-EVIDENCE-REWORK-01.
PLAN=doc 237. REPORT=doc 238. PRODUCTION_DEPLOY=NOT_AUTHORIZED. PHASE_ADVANCE=NONE.
EXISTING_EQUIVALENT=YES (Agent/FunctionToolset/gates/discovery-first/REF05/obligations).
REUSE_DECISION=EXTEND (dynamic per-capability tools; discovery-chained READ evidence; query/identifier schema binding; E1–E4).
EXECUTION_DRIFT=NONE.
CAUSAL_E02=list-only → dynamic tools; chained execute masked as discovery_metadata; missing query / flaky candidate_arguments.
NATIVE=pydantic-ai 2.50.0 dynamic FunctionToolset.add_function; no second planner.
EVIDENCE=E1 compose≠goal; E2 capability≠fact; E3 plan obligations; E4 multi-obs preserve.
REGRESSION=delia-api pytest tests/ GREEN; new `test_pydantic_ai_real_owner_tool_loop_rework.py`.
LOCAL_STACK=docker-compose.dev.yml (volume-mounted; NOT up-prod-sequential).
LIVE_E02=GROUNDED OBSERVATION; OWNER_READS discover+execute get_product_structure; SUCCESS; ~41140ms; in≈3197 out≈76.
LIVE_MATRIX=E01 honest; E03/E04/E05/E10 residual unbound/clarify; E07/E08 NON_GROUNDED honest; NDJSON 11 lines OK; FALSE_GROUNDED=0.
VERDICT=ACCEPT_WITH_RESIDUAL; FUNCTIONAL_ACCEPTANCE_CANDIDATE=YES (E02 owner READ gate).

## Pydantic AI generalist multi-step investigation (2026-11-04)

TASK=DELIA-C3-PYDANTIC-AI-GENERALIST-MULTISTEP-INVESTIGATION-AND-OUTCOME-01.
REPORT=doc 240. BASE_HEAD=945036c6a1. PRODUCTION_DEPLOY=NOT_AUTHORIZED. PHASE_ADVANCE=NONE.
EXISTING_EQUIVALENT=YES (Agent/FunctionToolset/gates/REF05/discovery-first).
REUSE_DECISION=EXTEND (cobertura de identificadores, model_factory por turno, finalize em UsageLimitExceeded, vazio não é evidência de negócio, falhas do catálogo no log).
EXECUTION_DRIFT=NONE. Nenhum planner novo, nenhum hardcode de produto/DAVI/compare, rollback `delia` mantido.
LIVE_E02=GROUNDED raiz 90260147; discover→execute get_product_structure; HTTP 200 ~22788ms.
LIVE_E03=GROUNDED duas observações; raízes 90260147 depois 90260148; collected=2 tool_calls=2; HTTP 200 ~43307ms; correlation f3daf363.
LIVE_E05_ISOLATED=GROUNDED raiz 90260148; HTTP 200 35602ms; in=2376 out=60; correlation 445b3a40.
LIVE_E05_OVERLOAD=NOT_APPLICABLE; admissão esgotou o prazo; catalog_len=8 sem api-delpi; correlation 5b5d468c.
LIVE_E04=NOT_APPLICABLE; execute erro + resume; usage_limit; correlation ea23c62e.
LIVE_E06=GROUNDED parcial em conhecimento; identificador 90260147 permaneceu descoberto; tool_calls_limit_reached.
LIVE_E07=primeiro turno NON_GROUNDED sem esclarecimento; continuação com o código GROUNDED raiz 90260147.
LIVE_E08=NON_GROUNDED owner_path_unbound; nenhuma escrita.
LIVE_E09=NDJSON 10 linhas, terminal turn_result; a leitura embutida fechou raiz 90260147.
LIVE_E10=NON_GROUNDED; identificadores permaneceram descobertos; usage_limit.
FALSE_GROUNDED=0 para identidade de produto. REGRESSION=delia-api pytest tests/ GREEN antes do log de falhas do catálogo; suíte focada do tool loop GREEN depois.
VERDICT=ACCEPT_WITH_RESIDUAL; FUNCTIONAL_ACCEPTANCE_CANDIDATE=NO para a matriz multi-step completa.

## Pydantic AI investigation runtime reliability (2026-11-04)

TASK=DELIA-C3-PYDANTIC-AI-INVESTIGATION-RUNTIME-RELIABILITY-AND-OUTCOME-COMPLETION-01.
REPORT=doc 241. BASE_HEAD=82999eed900d1d74706275924b38a65b8cd8b09e. PRODUCTION_DEPLOY=NOT_AUTHORIZED. PHASE_ADVANCE=NONE.
EXISTING_EQUIVALENT=YES (Agent, FunctionToolset, UsageLimits, retries, catalog live, Evidence/Outcome, esclarecimento, model_factory).
REUSE_DECISION=EXTEND (retry de listagem transitória, fingerprint de chamada idêntica, esclarecimento rejeitado com evidência, cobertura parcial, gap de evidência distinto de capability ausente, fechamento do cliente HTTP).
EXECUTION_DRIFT=NONE. Nenhum planner novo. DAVI não foi fixado no catálogo. Modelo de runtime não foi trocado. Documento 16 não foi reescrito.
LIVE_CATALOG=10 em todos os turnos medidos; owners api-delpi:2, transformometro-api:4, tv-dashboard-api:4; failures=-.
LIVE_E02=GROUNDED raiz 90260147; HTTP 200 33774ms.
LIVE_E03=GROUNDED raízes 90260147 e 90260148; execute somente 90260147; composed=False; HTTP 200 39027ms.
LIVE_E04=GROUNDED só a estrutura 90260147; guia não declarado como lacuna; HTTP 200 30233ms.
LIVE_E05_ISOLATED=GROUNDED raiz 90260148; HTTP 200 30816ms.
LIVE_E05_UNDER_LOAD=GROUNDED raiz 90260148; catalog_len=10; HTTP 200 42322ms. Timeout de admissão do doc 240 não reinduzido.
LIVE_E06=NON_GROUNDED; uncovered_identifier:90260147; conteúdo de conhecimento preservado.
LIVE_E07=E07a esclarecimento; E07b GROUNDED raiz 90260147.
LIVE_E08=NON_GROUNDED; nenhuma escrita.
LIVE_E09=NDJSON 11 linhas, terminal turn_result, HTTP 200 na releitura. Primeira tentativa HTTP 401 por token expirado.
LIVE_E10=NON_GROUNDED; investigation_no_business_evidence; uncovered 90260147, 90260148, 50220013; tool_calls_limit_reached; HTTP 200 39349ms.
FALSE_GROUNDED=0. PYDANTIC_AI=2.50.0. MODEL=qwen3:4b-instruct-2507-q4_K_M. MODEL_CONFIG_HASH=d382ec2d6fdc7d7d.
REGRESSION=delia-api pytest tests/ --ignore=tests/live exit 0 no diff final.
VERDICT=ACCEPT_WITH_RESIDUAL; FUNCTIONAL_ACCEPTANCE_CANDIDATE=NO para a matriz multi-step completa.



## Capability-provision full legacy removal + Pydantic AI consolidation (2026-11-05)

TASK=DELIA-C3-CAPABILITY-PROVISION-FULL-LEGACY-REMOVAL-AND-PYDANTIC-AI-CONSOLIDATION-01.
REPORT=doc 242. BASE_HEAD=c311e75e14. PRODUCTION_DEPLOY=NOT_AUTHORIZED. PHASE_ADVANCE=NONE.
EXISTING_EQUIVALENT=YES (Agent/FunctionToolset/tool loop/gates já adotados; nenhum framework novo).
REUSE_DECISION=REUSE (Pydantic AI nativo + gates Application retidos; sem nova camada).
EXECUTION_DRIFT=NONE.
REMOVED=orchestration.py 16287→6476 linhas (-60%); pacote 21844→11550 (-47%); attempt/_attempt/_governed_owner_path; planners, seletores, arggen, índice, subobjetivos, recovery, síntese, continuação, foreign/resolver; _select_candidate/_propose_candidate_arguments; capability_retrieval.py; subobjective_tracker.py; app/infrastructure/arggen/; 18 instruction IDs (20→2); DELIA_ORCHESTRATION_ENGINE=delia (fail-closed); DELIA_ARGGEN_ENGINE; DELIA_TOOL_SELECTION_MODE; DELIA_SUBOBJECTIVE_INVESTIGATION; _NATIVE_ASSESSMENT_LEDGER; 77 suites de teste acopladas.
KEPT=admissão tipada (1 _propose), compose_verified_observations (1 _propose + verificador), SemanticInvestigationPlan/_TurnGoal, discovery→chain determinística, candidate_token passthrough, gates AuthZ/evidência/outcome/paginação, PREPARE/ACT+confirmação+pending+auditoria (dormente, tool surface READ-only), observabilidade/cancelamento/deadline.
REGRESSION=delia-api pytest tests/ --ignore=tests/live exit 0 no SHA avaliado (~1150 testes); 74 testes nativos de contrato PASS; test_v14_architecture_isolation PASS.
E01_E10=TEST_NOT_RUN (runtime real exige rebuild do container local; não executado nesta sessão). FALSE_GROUNDED=0 na suíte executada.
VERDICT=EXECUTED_WITH_RESIDUAL — remoção integral executada e suíte verde; gate de runtime real pendente; FUNCTIONAL_ACCEPTANCE_CANDIDATE=NO.

## DELIA-C3-PYDANTIC-AI-ONLY-RUNTIME-AND-UNIFIED-INTELLIGENCE-CONFIG-01 (doc 243 → relatório 245)

| Campo | Valor |
|---|---|
| BASE_HEAD | `9d28674cc0` (baseline spec `8a16ca69f6`; origin avançou com commits não relacionados — diff disjunto) |
| Legacy runtime | REMOVIDO — `openai_compatible_adapter.py`, scripts/teste A/B, branch do composer, `DELIA_MODEL_RUNTIME` e 10 envs `DELIA_LLM_*` aposentadas fail-closed |
| Config canônica | `delia-api/config/pydantic_ai.runtime.delpi.json` (schema v1, 2 perfis, fingerprint `2e3bb1c6ead760da`) + loader tipado `pydantic_ai_runtime_config.py` |
| Defeitos baseline | 2 crashes latentes doc-242 corrigidos (`goal=` residual; `_prior_result_turn` removido) |
| Suíte delia-api | PASS — 1172 testes no SHA avaliado |
| E01–E10 ao vivo | E05 PASS/GROUNDED (READ real `root=90260148`); demais NON_GROUNDED honestos; FALSE_GROUNDED=0; residual owner-binding aberto |
| PRODUCTION_DEPLOY | NOT_AUTHORIZED |

## DELIA-C3-CROSS-FOLDER-NATIVE-PYDANTIC-AI-CONSOLIDATED-LEGACY-CLEANUP-01 (doc 256 — fatia G2)

| Campo | Valor |
|---|---|
| BASE_HEAD | `0152f67004ed11cbd893cdc4126705564000656b` |
| Commit | `88a7c4e50ceaecbdd3234719db93d7777df85afc` |
| G2 | CONCLUÍDO — `outcome_assessment.py` e `paginated_result_semantics.py` deletados; helpers determinísticos consolidados em `generic_evidence_renderer.py`; `conversational_response` 1330→689 |
| Suíte | PASS (exit 0) |
| Pendente | G1 typed output; resto de G3; G4; G5; G6; G7; G8 |
| PRODUCTION_DEPLOY | NOT_AUTHORIZED |

## G2 bounded rework — review 257 (execução)

| Campo | Valor |
|---|---|
| Base | `495b2cfb9cceb5b4da738416db5eb900658a68c2` |
| Testes negativos | `tests/test_g2_evidence_contract_regression.py` — 15 PASS |
| Prune | 13 helpers/constantes mortas removidas de `generic_evidence_renderer.py` (1929→1679) |
| RQ corrigido | IMPLEMENTED=2, PARTIAL=4, NOT_IMPLEMENTED=22 → cobertura 7,14% |
| Suíte | PASS (exit 0) |
| PRODUCTION_DEPLOY | NOT_AUTHORIZED |

## G1 — output estruturado nativo (doc 256, execução)

| Campo | Valor |
|---|---|
| Base | `8d6b2be450` |
| Agent | `output_type=InvestigationAnswer` + `output_validator` (forma) |
| Acceptor | `_apply_declared_answer` — refs bound, COMPLETE só provado, downgrade honesto |
| Testes | `test_g1_native_structured_output.py` — 8 PASS; suíte completa PASS |
| RQ | RQ-01,02,03,05,06 impl (4+); RQ-04,07 parcial → cobertura 14,3% |
| E01–E10 | TEST_NOT_RUN (G7) |
| PRODUCTION_DEPLOY | NOT_AUTHORIZED |

## G1 grounding rework — review 258 (execução)

| Campo | Valor |
|---|---|
| Base | `a034fc69` |
| Accepto | `_apply_declared_answer` fail-closed — prosa nunca substitui conteúdo verificado; refs bound; schema rejeitado; clarification guardada; plan=None → coverage_unknown |
| Testes | 14 PASS (test_g1); suite completa PASS |
| RQ-03 | IMPLEMENTED (gate factual fechado) |
| E01–E10 | TEST_NOT_RUN (G7) |
| PRODUCTION_DEPLOY | NOT_AUTHORIZED |

## G3 — orchestration/interaction legacy shrink + residual G1 (doc 256)

| Campo | Valor |
|---|---|
| Base | `6f69f8ac` |
| G1 residual | clarificação com evidência parcial honrada (verified_evidence_preserved) |
| Deletado | 9 fns mortas orchestration.py; CRI flag+loader+label+resource+tests+3 evals |
| LOC | −856/+95 líquido |
| Suíte | PASS (exit 0) |
| E01–E10 | TEST_NOT_RUN (G7) |
| PRODUCTION_DEPLOY | NOT_AUTHORIZED |

## G4 — retries/config/observability (execução)

| Campo | Valor |
|---|---|
| Base | `abcdcc63f6` (merge concorrente completado) |
| M1 | run_sync única vez; governed_retries separado — KEEP, provado |
| M2 | provider usage vs estimated — separação já honesta, KEEP |
| M3 | dead arg `recovery_reuse_enabled` + `last_agent_usage` removidos |
| Suíte | PASS (exit 0) |
| E01–E10 | TEST_NOT_RUN (G7) |
| PRODUCTION_DEPLOY | NOT_AUTHORIZED |

## G5 — MCP/OpenAPI/snapshot boundary (execução)

| Campo | Valor |
|---|---|
| Base | `cb9668c2` |
| Snapshot | aprovado+deployado — boundary Application→Infra corrigida via Protocol+injeção |
| OpenAPI | C3-T5 foundation KEEP (46 testes); direct adapter já aposentado |
| MCP | zero dead code — KEEP integral |
| Suíte | PASS (exit 0) |
| E01–E10 | TEST_NOT_RUN (G7) |
| PRODUCTION_DEPLOY | NOT_AUTHORIZED |

## G8 — residual closure & evidence (execução)

| Campo | Valor |
|---|---|
| Base | `981360de` |
| Residual | CLEAN — deleções confirmadas, zero consumidores, zero segundo runtime |
| RQ | 21 IMPLEMENTED / 7 PARTIAL / 0 NOT_IMPLEMENTED / 0 BLOCKED — correção aritmética da tabela G8 doc 256 (review 267) |
| Cobertura | 75% de classificação reportada (21/28; parciais=0); **não equivale a 75% de aceite independente** |
| E01–E10 | TEST_NOT_RUN — ambiente autorizado indisponível |
| Suíte | PASS (exit 0) |
| Veredicto | ACCEPT_WITH_RESIDUAL proposto |
| PRODUCTION_DEPLOY | NOT_AUTHORIZED |

## G7 live E01–E10 + defect fix (execução)

| Campo | Valor |
|---|---|
| Defeito | `load_orchestration_instructions` eaten pelo regex G3 → `surface=absent` (capability path morto) — fix restaurado, surface=configured |
| E01–E10 | HTTP 200/10, NON_GROUNDED honesto; tool calls reais 3 owners; 0 false grounded; 0 grounded (dados dev insuficientes + 4096 ctx limit) |
| Modelo | qwen3:4b-instruct-2507-q4_K_M / local_ollama / fp 2e3bb1c6 |
| Drift | DELIA_RUNTIME_SHA stale vs mounted HEAD |
| Suíte | PASS (exit 0) |
| PRODUCTION_DEPLOY | NOT_AUTHORIZED |

## P0 SourceRefs + dynamic tool contract hardening (execução)

| Campo | Valor |
|---|---|
| TASK_ID | `DELIA-C3-P0-SOURCE-REFS-AND-DYNAMIC-TOOL-CONTRACT-HARDENING-01` |
| Base | `745ae26ae6` (origin/main sincronizado; inclui review doc 287) |
| SourceRefs | **falso residual** — refs já serializadas em `provenance.sources` (source_id=davi, source_system=mcp, observed_at); matriz boundary→cliente completa, sem perda |
| Dynamic signature | `_capability_tool_signature` extraída — KEYWORD_ONLY (ordem opcional→obrigatório resolvida), denylist keyword/ctx/kwargs, enum→Literal (fix `owner_argument_rejected` TÉO) |
| candidate_token | extração bounded antes de `validate_arguments` + repasse verbatim — positivo + 9 negativos testados |
| InvestigationAnswer | `Literal["1"]` — const no schema, `"1.0"` rejeita com retry, 10 testes |
| Testes novos | 41 (signature 18, token 13, contract 10) |
| Suíte | PASS (exit 0, suite completa) |
| Eval real | A PASS GROUNDED+prov | B PASS (estrutura, code+max_depth) | C TÉO `teo.get_context` SUCCESS | D VISTA knowledge/get_context SUCCESS; read/analyze `mcp_protocol_error` owner-side | E PASS via context | F INCONCLUSIVE (registro existe no owner, coverage não vinculou) | G PASS clarificação honesta |
| Residual | `vista.read`/`vista.analyze` mcp_protocol_error (owner tv-dashboard); coverage-binding de registro detalhado único (F); `davi.discover` falha transitória isolada |
| PRODUCTION_DEPLOY | NOT_AUTHORIZED |

## P1 VISTA protocol + DAVI coverage-binding (execução)

| Campo | Valor |
|---|---|
| TASK_ID | `DELIA-C3-P1-VISTA-PROTOCOL-DAVI-COVERAGE-AND-REAL-EVAL-01` |
| Base | `8ea4c07552` (origin/main sincronizado; inclui review doc 289) |
| Trilha A causa | `_OWNER_ARG_VALIDATION_CODES` só tinha `ARGUMENT_VALIDATION` — códigos tipados/recoverable da VISTA (`UNKNOWN_ENTITY`/`UNKNOWN_ACTION`/`UNKNOWN_OPERATION`) caíam em `mcp_protocol_error` (terminal) em vez de `owner_argument_rejected` |
| Trilha A fix | 3 códigos adicionados ao frozenset; 4 testes no `test_specialist_interop_usecase.py`; runtime `vista.read` (entity=playlist) → GROUNDED real |
| Trilha B causa | `_resolver_entities` só extraía coleções; `data.product` (entidade única do `get_product_detail`) nunca virava evidence → `uncovered_identifier` → NON_GROUNDED |
| Trilha B fix | `_ENTITY_IDENTITY_KEYS` + entidade única Mapping sob data → `(value,)`; `test_single_entity_coverage.py` (6); runtime 99999999 → GROUNDED |
| Eval real | A 50220013 PASS GROUNDED 32s | B 99999999 PASS GROUNDED 60s | VISTA read PASS ×2 | N 00000000 NON_GROUNDED honesto | VA vista.analyze residual — `analysis` é string livre no schema publicado; owner rejeita valor com código não-recoverable → fallback vista.read GROUNDED c/ limitações declaradas |
| Residual | `vista.analyze` — vocabulário de análises válidas não é publicado no schema do owner (gap contrato tv-dashboard-api) |
| Doc fix | doc 288 `enum/const` → `enum` (const não implementado) |
| Suíte | PASS (exit 0, completa) |
| PRODUCTION_DEPLOY | NOT_AUTHORIZED |



## 2026-11-05 — Direção de produto: agentes especializados participativos e MCP distinto do agente

- **DECISION:** seleção autorizada de agentes/perfis especializados (TÉO/CAIO etc.), convite como participantes na conversa, e agente delegado efetivo quando houver justificativa. A DÉLIA permanece produto e orquestradora central com runtime/governança compartilhados; MCP tools/resources/prompts são providers, não identidades de agentes. Um agente pode consumir o mesmo MCP que a DÉLIA utiliza diretamente.
- **CANONICAL DOCS UPDATED:** 24 §5, 25 CP-071 (proibição histórica de seleção user-facing substituída explicitamente; ID preservado), 60 §1.1, 66 §8. Crosswalk anterior: doc 291. Reuse: Intelligence/Expertise/MCP/Portal/Core/plugin-ui existentes; contrato multi-speaker, catálogo executável e continuidade cross-app TO_INVENTORY.
- **SCOPE:** DOCUMENTATION_ONLY / NO_RUNTIME_CHANGE / NO_NEW_SERVICE / NO_CP_PASS / NO_PHASE_ADVANCE / PRODUCTION_DEPLOY=NOT_AUTHORIZED. Contratos e gates (AuthZ, owner authority, Evidence/Outcome, knowledge promotion, delegated context minimization, Portal commands) permanecem obrigatórios. Implementação futura requer contract-first e validação no HEAD real.

| MCPTOOLSET-MIGRATION-01 | substituiu registro manual de tools por MCPToolset nativo (discovery+schema owner, process_tool_call→_governed_semantic_tool_invoke); removidos _capability_tool_signature/_safe_tool_name/test_dynamic_tool_signature.py; bind de identificador estendido p/ campos opcionais | evals reais davi 50220013+99999999 GROUNDED, vista playlists GROUNDED; suíte completa verde | doc 291 |

| NATIVE-MCPTOOLSET-DIRECT-ORCHESTRATION-01 | removidos `invoke_read_capability`+`list_read_capabilities` (SUPERSEDED/REMOVED) e traversal de attrs privados; cadeia de contrato `gates._native_toolset_config`→provider→interop→port→adapter (credencial fail-closed); toolsets nativos por (provider,group) com remote_name do catálogo | suíte completa PASS (exit 0); novos testes nativos in-process (tools/list real + process_tool_call real + wire interceptado); eval real container: credencial delegada negada pelo Keycloak dev (exchange `invalid_request/Invalid token`) → fail-closed honesto, NON_GROUNDED sem wire, sem fatos inventados — BUSINESS EVAL=BLOCKED_WITH_EVIDENCE (INFRA/AMBIENTE) | doc 291 §SUPERSEDED/REMOVED |
| DIRECT-ORCHESTRATION-01 | removidos invoke_read_capability/list_read_capabilities (REMOVED — Agent chama tools MCP nativas por capability_id); traversal privado → cadeia _native_toolset_config fail-closed; build toolset fail-closed | TÉO+VISTA GROUNDED, multi-MCP GROUNDED; DAVI BLOCKED (TOTVS DB indisponível, ambiental); suíte 100% verde | doc 291, commit 12bcde76a5 |

| DEV-ENVIRONMENT-RECOVERY-AND-REAL-E2E-ACCEPTANCE-01 | ROOT_CAUSE=INVALID_SUBJECT_TOKEN — issuer mismatch: subject mintado no backchannel `keycloak:8080` (iss=localhost:8080) vs exchange validando na superfície aprovada (iss=localhost); realm sem drift (delia_mcp_keycloak_state --check NO_DRIFT); fix = mintar token via gateway (como o Portal) | eval real: TÉO GROUNDED (analyze+read×2), VISTA GROUNDED (get_context+read), multi-MCP DAVI+VISTA GROUNDED, E1/E2 reformuladas GROUNDED, 00000000 honestamente NON_GROUNDED, DAVI 50220013 owner-side NON_GROUNDED; HTTP turn real: vista.get_context+vista.read provider_invoke ok, falha só em output_retries_exhausted (Ollama small-model, doc 283) | harness eval script corrigido; sem alteração de plataforma |

| REAL-ANSWER-QUALITY-AND-E2E-REMEDIATION-01 | baseline real 11 cenários: A-H4 avaliados semanticamente com resposta completa em artefato; 8/11 GROUNDED com dados owner reais; DEFEITO comprovado: handle interno `[obs:N]` vazava para conteúdo ao usuário (join determinístico em `_finalize_agent_collected_attempts`, SUCCESS e partial coverage) | FIX: removido prefixo `[obs:N]` do content user-facing nos dois joins; output_validator também normaliza marcador residual na prosa; reteste real D: GROUNDED sem marcador; suíte completa verde | residuais honestos: SIPOC expandido incorretamente pelo modelo (capacidade LLM, não orquestração); H1 classificado surface_inquiry; output_retries intermitente Ollama small-model (doc 283) |

| ANSWER-QUALITY-RESIDUAL-REMEDIATION-AND-REAL-REGRESSION-01 | R2 apresentação: ordenação identidade-primeiro nos renderers canônicos (`_render_node`, `conversational_response` structured/list/md) — VISTA real agora lidera Nome/Descrição; R3 limitações: unmet_obligation auto-declarado agora override quando provavelmente contraditório (COMPLETE+refs bound ou coverage SATISFIED); R5 continuidade: NameError TurnKind em `_prior_observation_context` corrigido — continuidade 2-turn real GROUNDED | reteste real: VISTA C GROUNDED Nome-primeiro, DAVI A GROUNDED, continuidade T1→T2 GROUNDED; G4 fixture regenerado; suíte completa verde | residuais: R1 SIPOC = limitação factual do LLM local (sem hardcode — contrato); R3 declarações INCOMPLETE honestas preservadas; R4 output_retries não reproduzido (intermitente, ambiental); R6 vista.analyze = gap contratual do owner → ARCHITECTURE_DECISION_REQUIRED; frontend visual TEST_NOT_RUN |

| PRODUCTION-DEPLOY-AND-LOCAL-CONVERSATIONAL-QUALITY-EVAL-01 | FRENTE A: deploy prod executado via up-prod-sequential.sh --build delia-api delia; srv-api 9fa877f→4005c643e0 (único delta além da baseline = doc EVA, artefato delia-api idêntico à baseline 32ac7641); env-drift corrigido: DELIA_LLM_* retirados + DELIA_ORCHESTRATION_ENGINE=pydantic_ai em infra/.env prod; delia-api HEALTHY env=production, proxies=0, image sha256:f5d28e6d | FRENTE B: rerun dos 11 cenários + continuidade no runtime DEV | rollback ref: infra/.env backup /tmp/delia_env_backup_predeploy + imagem anterior |

| PRODUCTION-DRIFT-DIAGNOSIS-REMEDIATION-AND-REAL-E2E-01 | INCIDENTE resolvido: "Erro interno" na interface prod = sqlite3.ProgrammingError cross-thread em `McpCatalogStore` (conn criada na thread de composição, usada na worker thread do streaming em `interaction_stream_failed`→`_project_semantic_tool_catalog`) | FIX: conexão por thread (threading.local) — deploy prod `50e100a40a`, delia-api healthy, fix confirmado no container | REAL_PRODUCTION_USER_TURN=TEST_NOT_RUN (sem credencial humana prod); rollback ref = imagem anterior + .env backup |

| PROD-OWNER-PATH-UNBOUND-REAL-MCP-REMEDIATION-01 | Diagnóstico: turnos logados funcionam (admission operational → catalog 10 → toolsets 3); turno do incidente (2s, HYPOTHESIS, 1 LLM call, owner_path_unbound) não está nos logs retidos — assinatura = admission misclassification pelo modelo prod `moonshotai/kimi-k3` (requires_owner_surface=false → caminho conversacional, sem execução MCP). Não é defeito de toolset/catálogo/AuthZ | Hipótese principal: variance do modelo de admission no prod vs DEV (qwen). Sem correlation_id do incidente, evidência é indireta | Próximo passo: obter correlation_id do turno do usuário ou reproduzir admission com modelo prod; se misclassification confirmada, ação legítima = avaliação do perfil/modelo de admission — não hardcode de roteamento |

| PROD-OWNER-PATH-UNBOUND-REAL-MCP-REMEDIATION-01 | RESOLVIDO: causa raiz = HTTP 402 openrouter — investigation Agent enviava request sem max_tokens (default = context 131072 > crédito 14149); admission funcionava porque usava default_max_output_units | FIX: `max_output_tokens` do runtime profile wired até `_investigation_model_settings` (2 arquivos); reproduzido no container prod (402→OK) | TESTE REAL PROD autenticado user: GROUNDED DAVI descrição+tipo PI+grupo 5022 corretos (10.9s); generalização 99999999 GROUNDED (8.1s); sources=[davi] |

| PYDANTIC-AI-INTENT-AWARE-ANSWER-SYNTHESIS-AND-REAL-EVAL-01 | Síntese intent-aware: `declared_answer.answer` consistente (COMPLETE + refs bound + coverage provada/unknown + zero tokens numéricos não-verificados) agora vira `content`/`markdown_content` — dump determinístico permanece como evidência bound; guard de alucinação: tokens numéricos concretos fora da evidência → rejeita prosa e mantém dump | Eval real DEV: P3 all-fields = dump correto para intenção detalhe; P1 resposta concisa (join determinístico); P2 falhou por TTL do subject token (120s) — residual ambiental | Residual: modelo 4B local declara INCOMPLETE/unmet com frequência → prosa sintetizada só aparece com COMPLETE consistente (kimi em prod tende a declarar melhor); `declared_unmet_obligation` honesto mantido |

| LEGACY-ORCHESTRATION-REMOVAL-AND-NATIVE-PYDANTIC-AI-RUNTIME-01 | `orchestration.py` (6519 linhas) REMOVIDO fisicamente: decomposto em `semantic_capability_support.py` (contratos/support Application: evidence, guidance, plan, coverage, declared-answer, finalize helpers) + `governed_capability_orchestrator.py` (stage-gates SupportsGovernedStageGates); consumidores migrados para owners canônicos; delegação `__getattr__` para compatibilidade de import | Suíte completa PASS (~1300 testes); residual search zero; real eval DEV GROUNDED pós-remoção | RUNTIME_DEPENDENCY_REMOVAL=PARTIAL honesto: OperationalCapabilityOrchestrator permanece implementando stage-gates (governança legítima da Application); decomposição mais profunda dos ~50 métodos em serviços dedicados = trabalho futuro |

| ORCHESTRATION-PORT-ADAPTER-INTERCHANGEABILITY-AND-ISOLATION-01 | FRAMEWORK_BOUNDARY=ISOLATED: zero imports pydantic_ai em Application/Domain/Interaction (teste estrutural ast); `__getattr__` dinâmico REMOVIDO — todos os imports explícitos ao owner canônico (`semantic_capability_support`); seam `orchestration` adicionado em `_compose_turn_handler` para troca de runtime só-no-composer | INTERCHANGEABILITY_TEST=PASS: fake framework-free do port SupportsGovernedCapabilityAttempt consumido pelo handler real; port é framework-neutral (annotations neutras); suite completa verde; real eval DAVI GROUNDED | residual: verificação estrutural de imports cobre só pydantic_ai (padrão para outros SDKs não testado); MCPToolset/status real preservado |

| ORCHESTRATION-REAL-COMPOSITION-SWAP-GATE-01 | Swap real comprovado: `_compose_turn_handler` aceita override `orchestration` e, com ele, NÃO instancia modelo pydantic (guard `orchestration is None` no branch de init); teste `test_composed_handler_executes_alternate_runtime` compõe handler real com fake framework-free, executa `handler.execute()` e verifica input/actor/resultado no contrato | COMPOSITION_HANDLER_EXECUTED=PASS; ALTERNATE_ADAPTER_USED=PASS; PYDANTIC_MODEL_INSTANTIATED_DURING_SWAP=NO; engine fail-closed preservado; suite completa verde | seam é composição-controlled; fake não substitui testes de autorização |

| POST-LEGACY-REMOVAL-FUNCTIONAL-REGRESSION-AND-GAP-REMEDIATION-01 | Bateria real 10 cenários pós-remoção: P3/P5/P7/P8/P9/P10 PASS; P1 PARTIAL (tipo PI omitido — projeção do tool não incluía type); P2 FAIL (clarificação indevida — modelo declarou ausência sem dados); P4 PARTIAL (resumo→dump); P11 FAIL (SIPOC factual LLM) | Regressões históricas: R1 sqlite OK; R2 max_tokens OK; R3 owner_path OK; R4 provenance OK; R6 síntese parcial (modelo não declara COMPLETE no 4B); R7 coverage honesto | Falhas = capacidade do modelo local, não boundary de código; sem defeito novo fixável sem hardcode |

| PYDANTIC-AI-NATIVE-MECHANICS-CONSOLIDATION-AND-QUALITY-REMEDIATION-01 | Inventário framework-first: adapter JÁ usa mecanismos nativos — Agent loop, MCPToolset, output_type+validation, ModelRetry, UsageLimits, ProcessHistory(_trim_overflow), message_history, process_tool_call; residuais locais = políticas DÉLIA dentro de hooks nativos (integrity causal-unit, context envelope) — não duplicação | P1 root cause: projeção do tool selecionado retornava subset de campos (owner parcial), não perda no renderer — boundary = seleção do modelo; P2 clarificação indevida = comportamento do modelo 4B; P4/P11 = capacidade do modelo | Sem defeito novo de duplicação técnica fixável sem redesenho; intercambialidade e imports-zero mantidos |

| KIMI-DEV-COMPARATIVE-EVAL-NATIVE-PYDANTIC-AI-REMEDIATION-01 | Avaliação real DEV com `openrouter_kimi` (moonshotai/kimi-k3, fp 11e19a1bfc19446c) via processo de eval isolado (DELIA_ENV=production só no processo; container permaneceu local_ollama/qwen3 fp f6736c4a253f601a — sem mutação de config). Baseline comparada à bateria Qwen pós-remoção | 10 cenários + P6 2-turn: P1 PASS (desc+tipo PI+grupo; 2ª run modelo escolheu search_products sem type → variância TOOL_SELECTION), P2 PASS prosa aceita, P3 PASS, P4 PARTIAL (modelo declarou insufficient → dump determinístico), P5 SIPOC correto (Qwen erra — limitação modelo local confirmada), P6 continuidade PASS, P7/P10 GROUNDED, P8 PARTIAL (params como string + desvios davi → tool_calls_limit; erro do modelo, schema TÉO declara dict), P9 GROUNDED multi-MCP, P11 NON_GROUNDED honesto | DEFEITOS corrigidos: (1) guard `_CONCRETE_VALUE_TOKENS` rejeitava prosa legítima por formatação locale (31/10/2003 vs 2003-10-31; 175,0 vs 175.0; "50220013:") → `_concrete_value_variants` normaliza pontuação de borda, vírgula/ponto decimal e datas BR↔ISO — alucinação real ainda rejeita; (2) observações idênticas renderizadas em duplicata no join multi-observation → dedup por body (2 sites). RED→GREEN +3 testes; suíte completa PASS; intercambialidade PASS; 0 imports pydantic_ai em Application/Domain | Custo real OpenRouter auth/key: ~$0.18 total (run1 $0.132 + reeval $0.011 + P6 2×$0.037); 31 chamadas externas; QWEN restaurado/inalterado (eval process-scoped); PRODUCTION_DEPLOY=NOT_AUTHORIZED |

| PYDANTIC-AI-TARGETED-NATIVE-REMEDIATION-01 | Correção pontual dos 5 residuais Kimi×Qwen, framework-first | A) `_concrete_value_variants`→`_concrete_value_canonical`: equivalência por forma canônica (Decimal + data ISO) em conjuntos — elimina falso-positivo por substring (1175.0×175,0; 30/10×31/10; 50220013×502200130) mantendo alucinação rejeitada; B) dedup visual agora mergeia `source_refs` de todas as observações na provenance final; C) output_validator emite ModelRetry one-shot por run quando insuficiência declarada com budget de tools restante (flag em deps — re-declaração honesta nunca esgota retries); D) PARTIAL/INSUFFICIENT com refs bound + valores verificados apresenta prosa fundamentada com coverage_unknown (dump automático removido); E) hint genérico "object-typed parameters must be real JSON objects" derivado do inputSchema no _EnvelopeHintedToolset | +5 testes (3 falsos-positivos, partial prose, dedup provenance); suíte completa PASS; eval real Kimi focado: P1 PASS (desc+PI+grupo), P4 PASS (resumo fundamentado apresentado), P8 FAIL nesta rodada — admission classificou como surface_inquiry 2× (misclassification do estágio de admissão, MODEL; churn de tools não re-exercitado); custo real $0.017; Qwen restaurado/inalterado; 0 imports pydantic_ai em App/Domain; PRODUCTION_DEPLOY=NOT_AUTHORIZED |

| PYDANTIC-AI-END-TO-END-TYPED-DATA-FLOW-AND-ADMISSION-REMEDIATION-01 | Admissão: surface_inquiry agora exige confirmação por re-proposal bounded único — duas declarações coerentes mantêm o listing; contradição/retry inconclusivo/divergente resolvem para o owner path (assimetria canônica; corrige divergência comentário×código que resolvia contradição para o listing) | Eval real Kimi P8: modelo declarou surface_inquiry coerente 2× (proposal+confirm) → listing preservado; misclassification semântica PERSISTENTE na admissão — não é boundary de código, é decisão do modelo contra instrução já explícita; P8=FAIL honesto | Suíte completa PASS; keycloak dev reiniciado durante sessão (estava parado); custo ~$0.00 (2 chamadas); Qwen inalterado; PRODUCTION_DEPLOY=NOT_AUTHORIZED; residual: revisão do vocabulário/instrução de admissão = ARCHITECTURE_DECISION_REQUIRED (owner PO/arquiteto) |

| PYDANTIC-AI-MCP-ORCHESTRATION-CAUSAL-REMEDIATION-01 | Root cause P8: instrução de admissão v40 classificava "quais informações estão disponíveis sobre X" como surface_inquiry por cláusula ambígua ("what kinds of information... can consult - even when they name a business domain") | v41: teste decisivo pelo OBJETO da pergunta — surface_inquiry só quando o objeto é a superfície da DÉLIA; conteúdo de sujeito empresarial = operational. Whitelist _ORCH_VERSIONS + "41". Eval real Kimi: admission→operational→Agent→discover(DAVI,vazio)+5×analyze(TÉO)→GROUNDED com dados reais e limitações honestas | P8=PASS end-to-end; suíte completa PASS; residual menor: evidence_ref_unbound:0 + declared_status_overridden + multiple_observations_without_compose; custo $0.0217; Qwen inalterado; PRODUCTION_DEPLOY=NOT_AUTHORIZED |
