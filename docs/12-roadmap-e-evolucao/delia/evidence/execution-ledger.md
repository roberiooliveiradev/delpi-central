

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
