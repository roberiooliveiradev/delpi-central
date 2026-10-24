

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
