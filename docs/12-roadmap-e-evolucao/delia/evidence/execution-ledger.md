

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
