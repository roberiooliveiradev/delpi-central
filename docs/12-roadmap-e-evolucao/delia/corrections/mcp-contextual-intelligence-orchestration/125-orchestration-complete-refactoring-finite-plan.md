# 125 — Plano completo e finito de refatoração do orquestrador DÉLIA

**PLAN_ID:** DELIA-ORCHESTRATION-RESPONSIBILITY-REFACTOR-FINITE-01  
**Data:** 2026-10-23 · **Status:** PLANNED / ARCHITECTURE_REVIEW_REQUIRED · **Executor futuro:** Devin/Cursor · **Coordenação:** DÉLIA Architecture.  
**Escopo:** `delia-api/app/application/capability_provision/orchestration.py`. **Este plano não autoriza diffs de runtime, deploy ou avanço de fase.** A aprovação de execução pertence ao Product Owner depois de concluída e revista a correção D5 independente.

## 0. Autoridade — ler de novo no HEAD de cada pacote

Reancoragem obrigatória: `git status`, `HEAD`, `origin/main`, Project Instructions, `.cursor`, [16](../../16-execution-master-plan.md) → [50](../../50-standalone-copilot-application-architecture.md) → [17](../../17-component-and-contract-map.md) → [49](../../49-architecture-and-design-patterns-standard.md) → [51](../../51-platform-integration-baseline.md) → [52](../../52-standalone-repository-and-bootstrap-plan.md) → [21](../../21-data-and-state-model.md) → [20](../../20-testing-and-acceptance-matrix.md) → [25](../../25-requirements-traceability.md); [24](../../24-product-specification.md), [03](../../03-capability-model.md), [60](../../60-agent-interoperability-mcp-a2a-and-tool-protocols.md), execução ledger `docs/12-roadmap-e-evolucao/delia/evidence/execution-ledger.md`.

**Decisões precedentes vinculantes:** [ADR 58](./58-adr-llm-semantic-decision-ownership.md), [roadmap finito 59](./59-orchestrator-refactoring-finite-execution-roadmap.md) — Q03 encerrado ACCEPT_WITH_RESIDUAL, B1 formally deferred —, [auditoria integral 57](./57-orchestration-complete-second-pass-static-audit.md) com grupos F01–F42 e [56](./56-orchestration-audit-semantic-ownership-checkpoint.md), [matriz 113](./113-s0-contract-freeze-and-responsibility-matrix.md), [S4 117](./117-s4-orchestration-redistribution-decision.md), [contrato D5 124](./124-d5-generalizing-root-cause-and-implementation-contract.md). Reusar as decisões/histórico, **não iniciar nova auditoria ilimitada**. Em conflito: STOP → EXECUTION_DRIFT/ARCHITECTURE_DECISION_REQUIRED e remeter ao owner; este 125 nunca revoga 59, 117 ou authority superior.

**Baseline observado neste planejamento:** `orchestration.py` no HEAD inspecionado tem 12.026 linhas, ~472.600 caracteres, 195 definições identificadas por varredura textual (inclui funções internas; não é AST). Métricas informativas, não métricas de aceite. Reancorar novamente ao iniciar, pois a correção D5 está em execução concorrente.

## 1. Objetivo, exclusões e Definition of Done

**Resultado desejado:** `OperationalCapabilityOrchestrator` orquestra turnos/capabilities e delega para contratos de application/domain e adapters legítimos; seleção de intent permanece LLM-driven, determinístico guarda segurança, elegibilidade, evidence e outcome. Retirar texto user-facing, recursos declarativos e transformações de evidência de onde houver contrato/destino comprovado. Preservar Clean Architecture, sem circular imports, duplicação, novo planner, segundo registry, sidecar engine, nova autoridade ou migrations por organização.

**Invariantes congelados:** DÉLIA standalone; Keycloak identidade, Core AuthZ, Domain rules/facts, MCP/A2A interoperability não autoridade; discovery≠approval; seleção LLM é hipótese; `MODEL_AUTHORED_FACTUAL_PROSE=NONE`/selection-only onde vigente; distinguir prosa conversacional não factual autorizada por decisões posteriores; READ≠PREPARE≠ACT, Policy/Decision/consent/idempotency/audit, 60/3/300, rollback e prompt provenance. Não reabrir Q01–Q03 nem B1 por refactor. Não misturar mudanças funcionais D5 nem voice/dictation concorrentes.

**DoD global:** matriz por função/consumidor/contrato/destino, grupos alvo classificados KEEP|EXTRACT|EXTEND|SKIP_WITH_DECISION; todas as extrações autorizadas com paridade de assinatura/comportamento e testes por SHA; nenhuma nova autoridade; nenhuma perda de casos CRI/non-CRI, MCP/OpenAPI, conversa/no-tool, D4/D5/D8, negativos/policies, generalização; documentar resíduos honestos. Arquivo ficar menor não é DoD. Etapa final review independente; `PLAN_COMPLETE=YES` apenas após aceite final com evidence.

## 2. Inventário orientador por região no arquivo vigente

| Região aproximada | Funções/responsabilidade | Diagnóstico/destino candidato (não aprovado automaticamente) |
|---|---|---|
| 1–860 | imports, constantes, 17 blocos de instrução/model stage, lineage | Contratos e código permanecem; apenas **texto declarativo** candidato a recurso JSON/loader existente segundo 16 §CRI, 49/74. Sem mover typed proposal/schema para JSON. |
| 860–1320 | candidate/index/schema eligibility | KEEP até mapa de consumers; validação pode reutilizar `interaction/argument_validation.py` somente se idêntica semanticamente. |
| 1300–1750 | discovery, surface_inquiry, comparação/evidência | KEEP orchestration para flow/discovery; projeção expositiva é candidata a presentation existente, após contract gate. |
| 1750–2400 | `_contract_fact_rows`, `_compact_evidence`, `_evidence_rows`, schema completeness | **D5 ACTIVE OWNER:** NENHUMA extração até o pacote 124 aceito. Depois separar evidence/projection de schema validation com contrato previamente demonstrado. |
| 2400–3050 | `_render_synthesis`, `_compose_answer`, comparações/detalhes/listas, continuation | Responsabilidades de apresentação candidatas ao leaf `conversational_response.py`, somente depois de externalizar dependências legitimamente compartilhadas e preservar selection-only. |
| 3050–3800 | `_guidance_*`, estruturação/excerpts, resolver/prior context | Projeção de documentação é candidata a evidence/guidance leaf; **S4 doc117 determinou SKIP** porque não existe destino seguro simples: não reverter sem nova evidência/abstraction gate. |
| 3800–4300 | schemas, arguments, semantic capability views | Application schema/contract; priorizar reusable validation existente, evitar imports de framework e duplicação. |
| 4300–5010 | `_canonical_key`, `_redact_text`, `_sanitize_renderable`, format/rich render/markdown | Fronteira crítica compartilhada. Mapear call graph/consumers antes de qualquer movimento. Nunca duplicar sanitizer. Presentation leaf só consome projection saneada, sem depender de orchestration. |
| 5010–5380 | preview, activity, resume/checkpoint/error bookkeeping | KEEP fluxo e transições; contratos Activity/Pending/TurnBudget já existentes. |
| 5380–6995 | `OperationalCapabilityOrchestrator.attempt/_attempt` | É a orquestração central; orientar-se a delegação por responsabilidades, **não** dividir artificialmente o state machine ou alterar gates de execução. |
| 6995–9000 | resolver, reasoning/goal, continuation, owner reads e PREPARE/ACT | Manter decisões tipadas e safety; extrair somente validação puramente determinística com contrato/owner existente; não reabrir B1. |
| 9000–9767 | evidence→outcome/CRI, groups, selection/plan | Candidato a delegação para `outcome_assessment.py` / `conversational_response.py` e capability projection, sem mudança semântica. |
| 9767–10866 | model-stage proposal, repair, owner contract recovery, admission | Reusar `InvokeModel`, retry/budget/contracts; recursos declarativos versionados, lógica de proposal permanece governada e tipada. |
| 10866–12026 | capability selection, schema args, candidate discovery/invoke | Core orchestration KEEP; extrair só validação pura duplicada, mantendo owner mechanics em adapter. |

**Nota:** intervalos são orientação estática, não autorização para cópia/movimento em massa; call graph e HEAD prevalecem sobre números de linha.

## 3. Destinos existentes e gate por responsabilidade

| Responsabilidade | Equivalent | Reuse decision preliminar | Owner/destino |
|---|---|---|---|
| Semantic proposal, planner context | YES | REUSE/KEEP | `InvokeModel` + orchestration (typed proposals) |
| Capability projection/contracts | YES | REUSE/EXTEND condicionado | `capability_provision/contracts.py`, `domain/capability_catalog/model.py`, adapters existentes |
| Schema argument validation | YES | REUSE se paridade | `interaction/argument_validation.py` e schema validation existente |
| Evidence relevance, contract-doc vs business FACT | YES, partial | EXTEND apenas após D5 | `outcome_assessment.py` e fronteira evidence legítima, sem criar outra authority |
| Conversational text and field labels | YES | REUSE/EXTEND | `conversational_response.py` + `config/cri_presentation.delpi.json` v4 + `cri_instruction_resource.py` |
| Prompt and instructions as declarative resources | TO_INVENTORY by lineage | REUSE/EXTEND se contrato | loaders/versioned resource pattern atual; nenhum prompt registry novo |
| Guidance structural projection | TO_INVENTORY legitimate destination | SKIP pending evidence | Respeitar 117; só evoluir destino se algum contrato/consumer existente suportar sem novo boundary artificial |
| Audit/Pending/Action state | YES | KEEP/REUSE | `pending_proposals.py`, activity, interaction domain; sem segundo executor |
| Shared sanitization | TO_INVENTORY consumer graph | KEEP until proven | Uma implementação e contratos; sem duplicar em application/infrastructure |
| Runtime adapter mechanics | YES | KEEP boundary | MCP/OpenAPI adapters, nunca branches provider no orchestration |

**Abstraction Gate obrigatório por extração:** necessidade + owner + source + consumer + contract + segurança + tests + rollback; equivalente existente? diminui coupling real? preserve framework independence? Se não → SKIP_WITH_DECISION. Não deixar import circular governar design: esclarecer boundary antes de extrair.

## 4. Fases finitas e dependências — começo, meio e fim

**R0 — Freeze e baselines (READ-ONLY):** esperar conclusão/review da task D5/124, reancorar; harmonizar doc 57 F01–F42 + doc113 G-SA + doc117; capturar AST-based definition/call graph e imports internos/externos somente do arquivo e destino candidate; mapear cada função alvo KEEP|EXTRACT|EXTEND|SKIP e contracts/consumers/CP-RQ; congelar golden D4/D5/D8, MCP DAVI/TÉO/VISTA+unknown, OpenAPI, no-tool, multi-turn, reads/writes negados, CRI on/off, 60/3/300, lineage. **AC-R0:** matriz exaustiva por funções afetadas, 0 decisões implícitas, D5 baseline aceito/congelado, owners e rollback. Sem diff código.

**R1 — Instruções e recursos declarativos (conditionally):** mapear cada `*_INSTRUCTION` e seus lineage/hash/version/consumers, comparar recursos existentes/decisões 16 §CRI e 74; migrar somente textos extensos cujo destino JSON/loader legítimo está provado e cuja migração não altera conteúdo ou instruction-id; prompt snapshot byte-/semantically equivalent e invalid-resource fail-closed. Caso há conflito com lineage imutável: SKIP/ARCH_DECISION. **AC-R1:** same prompts/hash or documented version evolution approved, prompts validated, no selection divergence, no duplicated copy.

**R2 — Sanitização/projeção de evidência e contratos:** após D5 estabilizado, separar transformação de payload/document-schema/records em contratos/projections existentes e limitar `orchestration.py` à invocação e coordenação; sem mover `_canonical_key/_sanitize_renderable/_redact_text` cegamente. Contratos tipados para categorias `BUSINESS_RECORD|OWNER_GUIDANCE|ENTITY_SCHEMA|CONTROL_PLANE` são **hipótese de desenho**, não criação autorizada; reutilizar classificações reais, ADR se nova authority/contracts material. **AC-R2:** D5/D5-R pertinência, D8 intacto, schema question positivo, homogêneos business keys, RC1/RC2 e injection negativos, no raw JSON unwanted.

**R3 — Evidence/Outcome / CRI composition:** mapear `_outcome_facts`, `_apply_outcome_assessment`, `_cri_presented_record`, `_compose_cri_response`, `_synthesize_content` a `outcome_assessment.py` e `conversational_response.py`; encaminhar estruturas tipadas sanitize/provenance, reusar vocabulary JSON v4; não reclassificar HTTP success como business outcome. **AC-R3:** resultado/cobertura/limitações/paridade CRI on/off no SHA, D5/D8, no factual prose by model, no circular imports.

**R4 — Apresentação residual e guidance (conditional gated):** avaliar dependências concretas de `_render_synthesis`, `_compose_answer`, `_detail_lines`, `_guidance_*`, `_format_*` após R2/R3. Só mover ao compositor existente se não precisar importar orchestration e se for semanticamente presentation. Se exigir nova abstração/leaf ou violar decisão 117: **SKIP_WITH_DECISION**, registrar o porquê em vez de inventar `record_presentation.py`. Extrair texto user-facing para JSON governado somente onde realmente declarativo (sem transformar regras ou algoritmo em JSON). **AC-R4:** presentation parity PT-BR/Markdown/conteúdo literal/limites/unknown fields/CRI/non-CRI, no duplication, security.

**R5 — Contratos de schema, goal e model-stage (conditional):** redução de duplicação residual em `_build_arguments`, `_schema_*`, `_select_* `, `_propose`, `_repair_once` por reutilização de typed contracts e validation existing. Preservar LLM semantic ownership, one governed proposal lineage, timeout/retry, 60/3/300 e autorização. **AC-R5:** proposal snapshots + no-tool, resolver/foreign/candidate, context followup, unknown/provider rename; não mudar semântica de seleção para reduzir linhas.

**R6 — Orchestrator core + safety regression (PRESERVE):** após as extrações, revisão final do `OperationalCapabilityOrchestrator` (até aqui `attempt/_attempt` continuam owner de orchestration): corrigir apenas imports/dead code identificados por caller graph e testes, não reescrever state machine, não mexer no PREPARE/ACT, policy/idempotency/audit nem B1. **AC-R6:** nenhum registry/engine/shadow autoritário, no circular imports, architecture tests green, zero behavior drift no-go, caller parity.

**R7 — Integrated acceptance + optional release (FIM):** suíte backend e arquitetura completas, coverage per CP/RQ, metamorphic tests (rename/reorder/remove/add capabilities), negative MCP injection & AuthZ, business outcome D4/D5/D8, local Ollama zero egress, production Kimi bounded quando autorizado; registrar SHA/model/config/lines of evidence. Deploy **não é automático por existir refatoração**: gate operacional e PO específico para produção, rollback e postcondition; teste wire real autenticado ou TEST_NOT_RUN. Report final + ledger + review independente, `PLAN_COMPLETE` somente após coordenação ACCEPT e provas.

## 5. Contrato de trabalho por etapa

`R0→R1→R2→R3→R4→R5→R6→R7` em ordem, etapas SKIP permitidas pelo Abstraction Gate, mas sem pular gates de segurança e evidência. Cada etapa começa por reanchor. READ-only R0 antes de qualquer diff; uma PR/commit bounded por etapa com checklist de função origem→destino, imports eliminados, API consumers, contract compat, security, tests e rollback. Não misturar alterações concorrentes. Green obrigatório no SHA do diff; se a etapa é estritamente documentação, registrar TEST_NOT_RUN de runtime.

**Vereditos revisão coordenação:** ACCEPT | ACCEPT_WITH_RESIDUAL | REWORK | EXECUTION_DRIFT | INCONCLUSIVE. Um único rework bounded por pacote; segunda falha ou contrato divergente ⇒ STOP/Product Master, jamais pacotes infinitos. Executor não se autoaceita. `ACCEPT_WITH_RESIDUAL` só libera pacote seguinte se não bloquear sua pré-condição. Novos ADRs/authority changes interrompem exclusivamente subescopo dependente.

**Status inicial:** R0–R7=PLANNED/NOT_AUTHORIZED. Bloqueio explícito: tarefa D5/124 em execução; antes de R0, verificar HEAD, outcome/review e se o patch tocou projeção/evidence/CRI. Não tocar D5 em paralelo. Este plano organiza trabalho, **não altera** 59 nem o ledger de fase por si.

## 6. Matriz transversal de testes

- Semantic: sem heurística lexical, questions inéditas, D4/D5/D5-R/D8/D8-R/SIPOC, changed topic, multi-turn, owner-ambiguous, no-tool.
- Discovery/interop: DAVI/TÉO/VISTA/unknown provider, surfaces changes, candidate-token, owner unavailable/401, truth of capability published vs allowed.
- Evidence: business record vs schema vs guidance vs control-plane; positive schema-specific question; entity fields homonyms; null/empty/truncated; provenance and full coverage tests.
- Rendering: CRI/non-CRI, JSON vocabulary valid/invalid, PT-BR labels, markdown safety, no raw metadata leak, values verbatim, format guidance.
- Safety/actions: read/write split, simulate/apply, prepare/confirmation/act, AuthZ live, audit/idempotency, injection, credential redaction, timeout/retries.
- Outcome: no HTTP-200-as-success, real owner postconditions where available, token count actual vs estimated, model config recorded.
- Clean code: no framework/SDK in domain/application, no import cycle, modules by legitimate owner, no duplicated sanitizers/strings, residual search and migration diff.

## 7. Report por pacote e fechamento

```text
PLAN_ID=DELIA-ORCHESTRATION-RESPONSIBILITY-REFACTOR-FINITE-01
STEP=R0|R1|R2|R3|R4|R5|R6|R7
BASE_HEAD= FINAL_HEAD= ORIGIN_MAIN= PUSH_VERIFIED=
AUTHORITIES_READ= LEDGER_REFERENCE= CP_RQ=
FUNCTION_GROUP= OWNER= SOURCE= CONTRACT= CONSUMERS=
EXISTING_EQUIVALENT= REUSE_DECISION= KEEP_EXTRACT_EXTEND_SKIP=
FILES_CHANGED= IMPORT_GRAPH= DEAD_CODE= RUNTIME_DIFF=
RED_GREEN= FULL_BACKEND= ARCH_TESTS= SAFETY= GENERALIZATION=
EVAL_SHA_PROMPT_MODEL_CONFIG= D4_D5_D8_OUTCOME=
PRODUCTION_RELEASE= PROD_AUTH_HOMOLOGATION=
EXECUTION_DRIFT= RESIDUALS= REWORK_USED=
EXECUTOR_VERDICT= COORDINATION_REVIEW_REQUIRED=YES
```

**FIM:** publicar relatório de aceite independente, matriz antes/depois de responsabilidades, evidência de que o orquestrador delega operações não-orquestrativas legítimas, decisões de SKIP justificadas, resultados funcionais preservados e plano concluído ou bloqueado com causa formal. Nunca dizer COMPLETED por LOC menor/testes verdes apenas.

## 8. Organização modular e prevenção de novos monólitos — diretriz PO (2026-10-23)

**Decisão de objetivo:** a refatoração deverá produzir módulos pequenos, coesos e reutilizáveis por responsabilidade, não apenas um `orchestration.py` menor acompanhado de novos monólitos. Esta seção acrescenta **candidatos físicos e gates concretos**, sem autorizar sua criação antecipada. O documento 52 permite subáreas de application somente após necessidade real e Abstraction Gate; o documento 117 congelou o SKIP de guidance/presentation por inexistência de destino simples naquele SHA. Esta seção **não anula** 117: R0/R2 devem apresentar nova evidência de boundary/consumer para reavaliar eventual destino; caso contrário, SKIP_WITH_DECISION.

### 8.1 Estrutura existente confirmada em main

- `application/capability_provision/{orchestration.py,contracts.py,ports.py,conversational_response.py,outcome_assessment.py,paginated_result_semantics.py}`
- `application/interaction/{argument_validation.py,capability_attempt.py,contracts.py,presentation.py,pending_proposals.py,turn_budget.py,turn_observability.py,workspace_context.py}`
- `application/model_invocation/{invoke_model.py,contracts.py,governed_retries.py}`
- `config/cri_presentation.delpi.json`, loader `infrastructure/config/cri_instruction_resource.py`.

**Owner físico:** manter `capability_provision` como composição da integração enquanto a arquitetura vigente o prescrever. `interaction`, `model_invocation`, `domain/capability_catalog` e adapters retêm suas responsabilidades; não migrar para outros bounded contexts nem importar adapters em domain/application.

### 8.2 Mapa de arquivos previstos — CRIAR SOMENTE MEDIANTE GATE

| Arquivo candidato / extensão | Responsabilidade única | Reuso antes da criação | Entrada/gate |
|---|---|---|---|
| **EXTEND** `outcome_assessment.py` | suficiência, comparabilidade, aderência entre evidência e resposta requisitada | funções `assess_outcome`, `EvidenceFacts` atuais | R2/R3; sem importar orchestration |
| **EXTEND** `conversational_response.py` | composição de apresentação a partir de projeção confiável | `CriComposition`, rótulos governados e `compose_cri_response` | R3/R4; separar render de seleção |
| **EXTEND** `argument_validation.py` | validação pura de schema/argumentos, sem provider mechanics | `normalize_arguments`, `validate_arguments` | R5; equivalência de schema e erros comprovada |
| **EXTEND** `contracts.py` e `ports.py` existentes | DTOs/protocols tipados e boundaries entre coordinator e módulos | tipos atuais; sem namespace redundante | R0/R2 antes de moving functions |
| **CANDIDATE NEW** `capability_provision/evidence_projection.py` | projeção/sanitização provider-neutral de evidence, business records, contract/schema/guidance com invariantes de trust | `outcome_assessment.py`, `interaction/presentation.py`, sanitizadores existentes | R2, apenas se função e consumers provarem que nenhuma implementação existente comporta esse contrato |
| **CANDIDATE NEW** `capability_provision/guidance_projection.py` | transformar guia/documentação de owner em seções tipadas, sem responder intenção ou selecionar provider | guidance atual, evidence_projection proposto, compositor existente | R4, **bloqueado** até resolver dependências e justificar revisão da decisão 117 |
| **CANDIDATE NEW** `capability_provision/response_projection.py` | construir DTO renderizável a partir de evidência e decisão, sem texto de UI | `conversational_response.py` e `interaction/presentation.py` | R3/R4; escolher apenas se não duplicar compositor/DTO existente |
| **CANDIDATE NEW** `capability_provision/semantic_surface_projection.py` | visão descritiva de capabilities elegíveis sem autorização implícita, para user/meta contexto | `ProviderSurface.groups`, `CapabilityGroup`, `_surface_inquiry_content` | R4/R5; apenas se consumer adicional e desacoplamento reais provados |
| **CANDIDATE RESOURCE** JSON versionado para instruções de etapas | textos/instruções declarativas com lineage id/version/hash; nunca Policy/schema executável | loader de instruções atual e recursos existentes, `cri_instruction_resource.py` | R1 após compatibilidade byte/hash e owner |

**Não criar todos os candidatos.** Um candidato sem owner, consumidores reais, redução comprovável de coupling ou contrato estável recebe `SKIP_WITH_DECISION`; não gerar package vazio, service, registry ou engine novo. Nenhum dos nomes candidatos representa autoridade congelada.

### 8.3 Dependências direcionadas / transversalidade

O desenho-alvo de imports deve ser acíclico:

`orchestration.py` → contracts + `InvokeModel` + ports + `evidence_projection` (se aprovado) + `outcome_assessment` + `conversational_response`.

Projeção de evidência (caso aprovada) → contratos domain/application e funções puras já existentes; **NUNCA** → orchestration, infrastructure SDK, HTTP, DB, auth token, provider branch ou componente de apresentação.

Composição conversacional → DTO/projeção saneada, vocabulário governado validado; **NUNCA** → orchestration, MCP adapter ou Core/Domain client. Cada utilitário de canonicalization/redaction/sanitization tem **um único owner**; mover com todos os consumers ou manter no local vigente; nunca copiar para eliminar import circular. Transversalidade significa função pura/contrato reutilizado por consumidores legítimos da DÉLIA, não generic-utils sem owner.

### 8.4 Guardas contra novo monólito

- **Coesão comprovada:** cada arquivo define contrato, owner, consumers e responsabilidade em docstring/README de boundary; classes públicas e helpers não devem depender de detalhes de outros fluxos.
- **Complexidade observável:** a execução apresenta linhas/funções/complexidade/dep graph antes e depois, porém **sem limite arbitrário de LOC como gate isolado**. Crescimento desproporcional de módulo leaf obriga demonstrar coesão; não esconder complexidade por fragmentação artificial.
- **Imports/contratos:** testes de ausência de ciclos, dependência domain/application livre de adapters e testes de isolamento dos módulos leaf.
- **Textos e prompts:** declarativo versionado em recursos existentes quando houver schema/loader legítimos; nenhum dicionário de idioma expansivo na orquestração; nenhum algoritmo, classificação de intenção ou Policy em JSON.
- **Generalização:** nenhum branch por DAVI/TÉO/VISTA/operationId, keywords de pergunta, schema `entities.playlist` hardcoded; owners novos/removidos/reordenados precisam funcionar sem modificar planner.
- **Parity primeiro:** RED/green, invariantes de schema/erro/payload, D4/D5/D8, CRI on/off, ACT gating e budget antes de retirar imports/funções antigas.
- **Refactor-only:** em R1–R6, nenhuma alteração funcional oportunista; se um defeito for descoberto, registrar task separada e bloquear extração dependente, não absorver silenciosamente.
- **Ativos compartilháveis:** publicar apenas interfaces semânticas reais de `EvidenceFacts`, `OutcomeVerdict`, `CriComposition`, `CapabilityGroup`, etc.; não expor utilitários internos como serviços ou bridges artificiais.

### 8.5 Entregáveis adicionais por etapa

**R0:** árvore atual/árvore-alvo condicional + matriz `ORIGIN FUNCTION → MODULE OWNER → SOURCE → CONSUMERS → CONTRACT → KEEP/EXTEND/NEW/SKIP` e precedência de extrações. Registrar número estimado e delta real de módulos após gate.

**R1:** tabela `instruction-id → existing resource/loader → consumer → version/hash → migration decision`; não converter tudo indiscriminadamente.

**R2:** definir e testar projeção/sanitização compartilhável antes de mover call-sites, ou justificar permanência; proteger negativa RC1/RC2/D5.

**R3:** interfaces claras Evidence→Outcome→Presentation, sem circular imports, com paridade de composição.

**R4:** justificar por evidência nova qualquer revisão da decisão S4/117; migrar textos ao loader legítimo se cabível, mas nenhuma nova engine de guidance.

**R5:** centralizar validações idênticas em owner atual, sem deslocar interpretação semântica do LLM.

**R6:** verificar que coordinator contém principalmente sequencing/budget/selection/revalidation/invoke/ACT governance; emitir lista explícita de KEEP legítimos e resíduos SKIP.

**R7:** além dos outcomes, evidência estrutural (imports acíclicos, isolamento de leaves, ausência de duplicação, coverage de consumidores, tamanho/complexidade antes/depois e recursos validados). O aceite final verifica redução de coupling, não apenas LOC.

**Regra final:** `NEW FILE = CONTRACT + OWNER + REAL CONSUMER + NO EXISTING EQUIVALENT + RED/GREEN PARITY`. Se qualquer componente faltar, não criar o arquivo e registrar o motivo. Esta seção é **PLANNED**, condicionada aos gates R0–R7 e à estabilização independente da correção D5/124.

## 9. Blueprint de execução modular — contratos e ordem técnica (planejamento, 2026-10-23)

**Status:** PLANNED_ONLY; a task de estabilização pré-refatoração está sendo executada em paralelo e não deve receber commits deste plano. Esta seção concretiza a seção 8, sem revisar a decisão S4/117 por mera preferência e sem autorizar R0. No primeiro gate R0, revalidar SHA, authorities e ledger; o arquivo-alvo pode ter mudado.

### 9.1 Contratos candidatos (nenhuma classe nova aprovada)

1. **Projeção segura de evidência:** entrada = outcome owner tipado + origem + limitação + contexto de contrato já validado; saída = representação read-only sanitizada, distinguindo `business_record`, `guidance`, `entity_schema`, `control_plane` **apenas se a taxonomia tiver equivalência canônica comprovada**. Proibições: execução, AuthZ, model invocation, apresentação, inferência de FACT. Candidatos: `outcome_assessment.py` / `evidence_projection.py`; decidir no R2 pelo acoplamento real.
2. **Avaliação de suficiência:** entrada = evidência projetada + requerimentos tipados + hipótese de intenção, saída = `OutcomeVerdict` com razões/limitações. Reuso preferencial: `outcome_assessment.py`. Nunca converter existência de payload ou HTTP 200 em outcome.
3. **Projeção de guidance:** entrada = documentação owner saneada e seleção semântica tipada existente, saída = seções bounded com provenance e estado de cobertura. Proibida heurística lexical de intenção e cópia de `_canonical_key`/sanitizers. Após R2, verificar se o leaf legítimo já existe; caso contrário SKIP conforme 117 até decisão nova.
4. **Resposta conversacional:** entrada = `OutcomeVerdict` + records apresentados/limitações/provenance; saída = conteúdo fiel e seguro ao usuário. Reuso: `conversational_response.py` + JSON governado v4. Proibido acessar MCP/Domain/DB, selecionar capabilities ou autorizar ACT.
5. **Proposta de LLM:** entrada = contexto permitido e superfície viva autorizada; saída = proposta tipada validada. Reuso: `InvokeModel`, contracts existentes e coordenação. Prompts declarativos podem migrar para recurso com lineage preservada; o modelo não valida suas próprias permissões.
6. **Estado de tentativa e ações:** entrada = plano tipado e gates prévios, saída = `GovernedCapabilityAttempt` + audit/outcome. Reuso: interaction contracts, pending_proposals, TurnBudget; permanece governado e fail-closed. Nenhuma extração sem testes negativos materiais.

### 9.2 Ordem obrigatória de desacoplamento

```text
R0 baseline + map de imports/callers
  → estabilização D5 aceita e congelada
  → R1 recursos declarativos (independente, se gate permitir)
  → R2 fixar contrato de projeção/sanitização com testes (SEM mover consumers primeiro)
  → R3 migrar um consumer Evidence→Outcome→Presentation por vez (paridade)
  → R4 reavaliar guidance/formatting S4/117 somente após R2/R3
  → R5 reduzir duplicações reais de validation/proposal
  → R6 reduzir coordinator imports/branches comprovadamente redundantes
  → R7 eval/independent review e possível release separado
```

Evitar ciclo de import: application contracts/domain model ficam a jusante; orchestration importa projeções/avaliação/apresentação, nunca o inverso. Adapter SDK/DB/HTTP não é importado por domain/application. Proibido helper genérico sem owner; utilitários compartilhados só após ≥2 consumidores concretos e contrato idêntico comprovado (um único consumidor pode justificar módulo somente quando a responsabilidade exigir isolamento real, não por LOC).

### 9.3 Roteiro de migração por função (candidatos iniciais)

| Função/grupo origem | Destino preferencial | Pré-condição objetiva | Decisão provisória |
|---|---|---|---|
| `_contract_fact_rows`, `_compact_evidence`, `_evidence_rows` | projeção existente; `evidence_projection.py` apenas se gate | D5 accepted + sanitization caller graph + type/provenance tests | TO_INVENTORY |
| `_without_control_plane`, `_is_capability_descriptor` | mesma fronteira de projection, se legítima | RC1/RC2 negatives + homonymous business records | TO_INVENTORY |
| `_guidance_section_records`, `_select_guidance_records`, `_deterministic_guidance_content` | guidance projection somente se contrato independente | evidência nova que supera 117, import DAG | SKIP até prova |
| `_compose_answer`, `_detail_lines`, `_render_synthesis`, `_md_*format*` | `conversational_response.py` ou presenter existente | projeção saneada e API input sem imports de orchestration | TO_INVENTORY |
| `_outcome_facts`, `_apply_outcome_assessment` | `outcome_assessment.py` se refactor preserva role | acoplamento e testes CRI on/off, verdict limitations | TO_INVENTORY |
| `_schema_required_gaps`, `_argument_completeness_gaps` | `interaction/argument_validation.py` apenas por equivalência | parity de errors/defaults/open vocabulary | TO_INVENTORY |
| `_surface_inquiry_content`, `_group_summaries` | capability projection existente | descobrir se outro consumer legítimo exige API; preserve published≠permission | KEEP salvo prova |
| `_attempt`, `_invoke_selected`, `_select_target`, PREPARE/ACT chain | `orchestration.py` | preservar state/owner boundaries | KEEP |
| `*_INSTRUCTION` + textos user-facing | recurso versionado/loader atual | lineage/hash, contract frozen, provenance | TO_INVENTORY |

### 9.4 Gates mensuráveis e anti-monólito

Por pacote apresentar: (a) **antes/depois** de funções por módulo, import DAG, dependências por direção e callers; (b) contratos de entrada/saída e exemplos em fixtures reais minimizados; (c) redução comprovada de acoplamento e ausência de cópias dos mesmos sanitizadores; (d) testes de isolamento das unidades extraídas; (e) suite full/safety/generalization nos SHAs; (f) impacto em tempo/tokens apenas se medido; (g) caminho de rollback por commit/serviço.

Sem limites arbitrários de LOC, mas **se um módulo candidato acumular mais de uma responsabilidade independente**, rejeitar a extração e voltar ao contrato. Se surgir dependência circular, refatorar na direção de contrato existente ou SKIP; proibir imports reversos e service locator como workaround. Nenhuma movimentação extensa pode ser justificada só por "limpeza".

### 9.5 Gate de saída para R0 e controle de concorrência

**R0 só começa quando** a estabilização pré-refatoração executada pelo Devin tiver report SHA, AC D5/D5-R/D8-R/PT-BR, deploy/outcomes quando autorizados e parecer independente. Até esse marco: PLAN 125 pode evoluir documentalmente; R0–R7 seguem NOT_AUTHORIZED. O executor de D5 não deve incluir este blueprint no diff de runtime. A revisão formal da arquitetura registra novamente KEEP/EXTEND/NEW/SKIP e NEXT_ALLOWED_STEP; se houver divergência com 59/117/125, STOP, não redesenho silencioso.
