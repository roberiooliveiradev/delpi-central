# 04 — Etapa 01: Baseline factual e harness de eval

**Status:** EXECUTED / EVIDENCE_RECORDED — relatório de baseline, não é aceite.
**TASK_ID:** DELIA-C3-CONVERSATIONAL-INTELLIGENCE-GAP-CLOSURE-01-STAGE-01
**MODE executado:** BASELINE_AND_EVALUATION_ONLY — nenhuma correção funcional implementada.
**BASE_HEAD:** `57da7fac0554eb2daff6c7737dca94ef7f94c8a5` (revalidado contra `origin/main`; fast-forward aplicado — local estava 4 commits documentais atrás).
**Data:** 2026-10-15
**Classificações:** PROVEN | TO_INVENTORY | PLANNED | TARGET; execução = PASS | FAIL | INCONCLUSIVE | TEST_NOT_RUN.
**Revisão:** INDEPENDENT_REVIEW=PENDING — execução não se autoaceita.

## 0. Reanchor

- HEAD = referência; `git status` mostra alterações concorrentes do usuário em `plugins/*` e `requests-api` — preservadas, nenhuma staged.
- Fase revalidada: `C3_STARTED=YES; C3_EXECUTED=NO; C4_AUTHORIZED=NO; C5_AUTHORIZED=NO; CURRENT_NEXT=RETURN_TO_ARCHITECTURE_COORDINATION`.
- Autoridades consultadas: docs de governança da pasta (`README`, `01`, `02`, `03`), doc 70 §16, ledger §6.169–6.170, regras `.cursor` carregadas no contexto.
- Escopo respeitado: somente leitura, testes, fixtures/fakes e este relatório. Nenhum prompt/contrato/planner/policy alterado.

## A. Inventário do runtime — mapa real

```
USER INPUT
└─ handle_interactive_turn.execute()                        [app/application/interaction/handle_interactive_turn.py]
   ├─ auth (PlatformAccessContext + permission gate)
   ├─ orchestrator.attempt()                                 [capability_provision/orchestration.py]
   │  ├─ _groups() → live surface (_project_surface, ≤60 entradas)
   │  ├─ _select_target()
   │  │   ├─ select_group        (model call #1 — só se >1 grupo)
   │  │   └─ select_capability   (model call #2)
   │  ├─ _understand_goal        (model call #3 — goal_class read|analyze|compare|create_or_modify|clarify)
   │  ├─ _assess_native_path     (model call #4 — só se >1 grupo)
   │  ├─ [foreign path: select_foreign_capability + invoke] (bounded, 1 grupo estrangeiro)
   │  ├─ plan: _requires_owner_vocabulary(descriptor)?
   │  │   └─ discovery DISCOVERY capability (args por schema vazio — sem model call)
   │  ├─ _build_arguments        (model call #5 — tool inputSchema + owner_vocabulary/foreign_evidence/business_subject)
   │  ├─ _unproven_identifier_inputs (demote invented ids → missing)
   │  ├─ _resolve_missing_inputs → select_resolver (model call #6 — só se missing)
   │  ├─ _clarification_question → clarification_wording (model call #7 — só se missing)
   │  ├─ PREPARE → _attempt_prepare: prepare_invoke → project_proposal_preview
   │  │            → _effective_confirmation_policy (owner confirmation_requirement = única autoridade)
   │  │            → direct (owner declarou) | CONFIRMATION_REQUIRED (pending write + digests)
   │  │            → ACT via _execute_prepared_act → commit_proposal
   │  └─ READ/ANALYSIS → _invoke_selected → _synthesize_content (model call #8 — items/fields + presentation hint)
   │                     → _render_synthesis (determinístico) | fallback render_specialist_outcome
   │
   ├─ SUCCESS            → _grounded_result (presentation.v1, deterministic)
   ├─ SOURCE_UNAVAILABLE / AUTHZ_DENIED → _source_terminal_result (deterministic, nunca narra pelo modelo)
   ├─ CONFIRMATION_REQUIRED / WRITE_REJECTED / CLARIFICATION_REQUIRED → _write_lifecycle_result
   └─ NOT_APPLICABLE / orchestrator None → general model (delia.interaction.base v3) → NON_GROUNDED
```

**Model calls por turno (observado):** 3–5 no caminho OPERATIONAL padrão (2 grupos forçam select_group + native_assessment); produção confirmou 5 proposals antes do write (~33s total, stage timings 2–11s cada). Discovery args não consomem proposal (schema vazio → short-circuit). Resolver/clarification/synthesis/candidate/comparison são condicionais.

**Estrutura das instruções (auditada integralmente):** 13 instruction IDs em `orchestration.py` (v7 global via `SELECTION_INSTRUCTION_VERSION`) + `delia.interaction.base` v3. Todas com structured output JSON estrito, `allowed_keys` fechado, lineage (id+version+sha256) e `declared_epistemic_class=HYPOTHESIS`. Nenhum canal de prosa factual do modelo — `MODEL_AUTHORED_FACTUAL_PROSE=NONE` mantido.

| Instruction | Chars | Output | Fallback |
|---|---|---|---|
| select_group | 1425 | applicable, capability_group_id | none → NOT_APPLICABLE |
| select_capability | 930 | applicable, remote_name | none → NOT_APPLICABLE |
| turn_goal | 1201 | goal_class, comparison, output_mode, business_subject, scope | default goal "read" |
| native_assessment | 1019 | status | "sufficient" |
| arguments | 2398 | arguments, missing_inputs | None → clarify/not_applicable |
| select_resolver | 927 | applicable, remote_name | → clarification |
| clarification_wording | 887 | question | `_clarification_content` (genérico) |
| grounded_synthesis | 1873 | items, presentation | `render_specialist_outcome` (raw dump) |
| foreign_selection | 755 | foreign_capability_id | native/corrob degrade |
| analysis_continuation | 954 | applicable, remote_name | none |
| comparison | 1061 | left/right record refs | verdict não comparável |
| candidate_arguments | 549 | arguments | → arguments path |
| select_candidate | 554 | applicable, action_id | NOT_APPLICABLE |
| interaction.base (v3) | 1561 | resposta geral | NON_GROUNDED |

**Orçamentos (fatos de código, não política nova):** `MAX_OPERATIONAL_PLAN_STEPS=3`, `MAX_REPLAN_ROUNDS=1`, `MAX_SURFACE_CHARS=6000`, `MAX_ARGUMENTS_BLOCK_CHARS=14000`, `MAX_SURFACE_ENTRIES=60`, `MAX_ARGUMENT_KEYS=16`, `MAX_MISSING_INPUTS=8`, `MAX_OWNER_EVIDENCE_CHARS=12000`, `MAX_RENDER_CONTENT_CHARS=2000`, `MAX_FOREIGN_GROUPS=1`, `MODEL_STAGE_TIMEOUT` por estágio + `TurnDeadline` global. Tokens por call não mensuráveis no harness fake (TEST_NOT_RUN — provider real necessário).

## B. Baseline de avaliações

Harness novo `delia-api/tests/test_conversational_intelligence_baseline.py` (15 testes; estende o padrão `test_intelligence_loop_evals.py` — nenhum segundo framework). Model proposals scripted reproduzem os traces de produção; o objeto sob teste é o pipeline determinístico.

**Suíte baseline no SHA de referência:** `1069/1069 PASS` (1054 preexistentes + 15 novos). Casos executados (observado vs esperado):

| Caso | CI | Observado | Esperado | Veredito |
|---|---|---|---|---|
| A — "Como criar um processo?" | CI-01 | tópico `'processo'` inventado → owner rejeita → `SOURCE_UNAVAILABLE` | orientação com vocabulário real | **FAIL** (reproduzido) |
| A sibling — tópico válido | CI-01 | SUCCESS, guia renderizado | idem | PASS |
| A — classe `orient` no goal | CI-01 | normalizada silenciosamente para `read` | classe capaz de expressar orientação | **FAIL** (estrutural) |
| A — hazard guidance→PREPARE | CI-01 | "como criar" pode alcançar PREPARE se o modelo selecionar; nenhum gate semântico | pergunta de orientação nunca inicia write | **FAIL** (hazard, gate ausente) |
| B — create incompleto | CI-04/05 | `missing=0` com `changes` sem campo inner required → PREPARE READY → direct ACT → commit rejeita | completude inner detectada ou perguntada antes de ACT | **FAIL** (reproduzido end-to-end) |
| B sibling — changes completo | CI-03 | SUCCESS via mesmo path direto | idem | PASS |
| B negative — PREPARE NOT_READY | CI-05 | render truthfull, ACT nunca invocado | idem | PASS |
| C — "último cadastrado" sem ordem | CI-07 | record_index escolhido pelo modelo é renderizado como resposta | insuficiência declarada | **FAIL** (suficiência não verificada) |
| C sibling — com data ambígua | CI-08 | idem — `atualizado_em` usável como proxy de criação sem verificação | ordenação autoritativa exigida | **FAIL** (mesmo gap) |
| C negative — `items:[]` | CI-07 | fallback renderiza dump verbatim dos 10 registros | resposta de insuficiência | **FAIL** (fallback = dump, não limitação) |
| D — descrição de produto | CI-09 | resposta direta determinística, 0 synthesis calls | idem | PASS (controle positivo) |
| E — rename invariance A | CI-10 | mesmo FAIL estrutural em owner renomeado | idem | **FAIL** (genérico — PROVEN) |
| E — rename invariance B | CI-10 | mesmo FAIL estrutural | idem | **FAIL** (genérico — PROVEN) |
| Budget — write path | — | 5 model calls (production-like) | — | baseline medido |

CI-06, CI-11..CI-18: **TEST_NOT_RUN** nesta etapa — não prioritários; o harness cobre o arcabouço para executá-los nas etapas seguintes.

**Limites de evidência:** proposals scripted medem pipeline + gates, não o comportamento do modelo real — o comportamento do modelo real é evidência de produção (logs) e não foi reproduzido com provider LLM (TEST_NOT_RUN para métricas de tokens/custo reais).

## C. Diagnóstico de causa-raiz

| # | Defeito | Etapa responsável | Evidência | Causa-raiz | Reuso | Etapa futura |
|---|---|---|---|---|---|---|
| 1 | Tópico/valor inventado para campo string sem enum | `_build_arguments` + gatilho de discovery | test_ci01_*: `_requires_owner_vocabulary`=False p/ string; `owner_vocabulary` ausente do bloco | **PROVEN** — `_is_open_vocabulary` cobre só object/array opacos; campos string cujo vocabulário legal é do owner não disparam DISCOVERY → modelo chuta valor | EXTEND (regra de envelope/vocabulário) | 03 |
| 2 | Semântica "orientar" inexistente no goal contract | `_understand_goal` | test_ci01_goal_class_has_no_orientation_class; `_GOAL_CLASSES`={read,analyze,compare,create_or_modify,clarify} | **PROVEN** — contrato de goal_class não representa orientação; "como criar" classifica como ação | EXTEND (contrato bounded do goal) | 02 |
| 3 | Seleção write em pergunta de orientação | `select_capability` instrução | test_ci01_hazard: "crie → prefer PREPARE" como keyword hint | **PROVEN parcial** — hazard demonstrado; a seleção real depende do modelo (não determinístico). A instrução não distingue "como criar" de "crie" | EXTEND (instrução existente, não nova) | 02/03 |
| 4 | Completude declarada só no schema externo | `_build_arguments` + `_attempt_prepare` | test_ci04: `missing=0` com inner required ausente; vocabulary presente como texto untrusted | **PROVEN** — validação determinística só contra `input_schema` da tool; `changes` opaco não é revalidado contra entity_schema do owner; o owner (TÉO) projetou READY no PREPARE e rejeitou só no commit → dupla falha (pipeline não valida + owner valida tarde) | REUSE owner contract (entity_schemas já vem no catalog) + EXTEND validação bounded pré-PREPARE | 04 |
| 5 | Confirmação não solicitada | `_effective_confirmation_policy` + owner | test_ci04 + código: `explicit_user_confirmation=false` → direct | **PROVEN = owner-declared, não bug DÉLIA** — a policy veio do contrato do especialista; DÉLIA honrou. Se a intenção é confirmar creates, a correção é no owner/governança, não na DÉLIA | REUSE (nenhuma mudança DÉLIA) | — (registro p/ governança) |
| 6 | "Último" sem prova de ordenação/cobertura | `_synthesize_content` | test_ci07/08: seleção de índice é único árbitro; `items:[]` → dump verbatim, sem resposta de insuficiência | **PROVEN** — não há verificação de ordenação autoritativa, cobertura de página ou resposta bounded de "evidência insuficiente"; fallback renderiza tudo | EXTEND (síntese/renderer existentes; reusa outcome.limitations) | 05 |
| 7 | Erro do owner vira "consulta falhou" sem retry/vocabulário | `_error_attempt` / invoke | test_ci01: lista "available: [...]" chega como erro terminal | **PROVEN parcial** — a resposta do owner carregava o vocabulário correto, mas nenhum estágio a reutiliza (sem segundo bounded attempt) | EXTEND (bounded replan com owner-hint — MAX_REPLAN_ROUNDS=1 já existe mas só para surface-change) | 03/04 |
| 8 | Personalidade não alcança caminho operacional | `handle_interactive_turn` + `instruction.py` | inventário: instrução v3 só alimenta o fallback NOT_APPLICABLE; SUCCESS/erros têm renderers determinísticos sem voz de personalidade | **PROVEN (estrutural)** — `DELIA_INTERACTION_INSTRUCTION` alcança somente o caminho não governado; docs de personalidade não aparecem em nenhum instruction content nem no composer | TO_INVENTORY decisão (Etapa 05; `MODEL_AUTHORED_FACTUAL_PROSE=NONE` congela opções) | 05 |

**Não-raiz descartada (PROVEN):** bearer/auth — corrigido no hotfix `e75a86246b`; produção confirma invocations reais (timing>0). Não é problema de inteligência. Seleção de grupo/capability nos traces foi semanticamente correta em todos os casos observados (guide para orientação, PREPARE para create) — os defeitos estão a jusante.

## D. Avaliação das instruções ativas

**Funcionam:** structured output estrito + `allowed_keys` + lineage + fallback determinístico por estágio; untrusted-data framing consistente; `_unproven_identifier_inputs` demove ids inventados; clarification nunca vaza nomes técnicos; síntese só seleciona (sem prosa) — desenho sólido de separação modelo/autoridade.

**Incompletas:** `ARGUMENTS_INSTRUCTION` cobre schema externo, mas `owner_vocabulary` chega como blob de texto untrusted sem obrigação de completude inner (gap #4); campos string com vocabulário restrito não têm instrução de enumeração (gap #1); `GOAL_INSTRUCTION` sem classe de orientação (gap #2); `CAPABILITY_SELECTION_INSTRUCTION` keyword-hint "crie→PREPARE" não distingue orientação (gap #3); `SYNTHESIS_INSTRUCTION` não exige verificação de ordenação/cobertura para claims posicionais e `items:[]` não tem contrato de resposta de insuficiência (gap #6).

**Sobreposição:** mínima — cada estágio tem responsabilidade única; `turn_goal` + `native_assessment` + `select_capability` repartem semântica de intenção em 3 propostas separadas (custo: 3 calls) — fusão é candidata de otimização, não correção (TO_INVENTORY em Etapa 02).

**Redundância:** nenhuma instrução redundante encontrada; 13 IDs é razoável — o risco é de contexto, não de contagem.

**Contexto insuficiente:** business_subject só alimenta arguments/synthesis, não selection; catálogo owner só alcança arguments quando envelope dispara discovery (gap #1); prior_turns passa a quase todos os `_propose` (bom), mas não a `select_group`.

**Tokens/latência:** 5 proposals ~9.9KB de instrução no path write + blocos de dados bounded; produção mostra 2–11s por call (~33s no turno) — latência total é o custo dominante, não o tamanho dos prompts.

## E. Mapa de evolução (Etapa → gap)

- **Etapa 02 (intenção/instruções):** gaps 2, 3 — contrato de goal com classe de orientação (ou equivalente bounded), remoção do keyword-hint write no select_capability, reavaliação da fusão goal+assessment.
- **Etapa 03 (discovery/guidance):** gaps 1, 7 — vocabulário owner para campos restritos (string sem enum), reuso de owner-hints de erro como evidência bounded, fluxo guidance disponível/ausente.
- **Etapa 04 (completude/resolução):** gap 4 — completude inner via contrato owner (entity_schemas já publicado no catalog), classificação valor expresso/default declarado/inferência/decisão humana antes de PREPARE.
- **Etapa 05 (síntese/personalidade):** gaps 6, 8 — verificação de ordenação/cobertura para claims posicionais, resposta bounded de insuficiência (vs dump), conexão da personalidade ao caminho operacional dentro dos congelamentos.
- **Etapa 06 (generalização/aceite):** CI-06, CI-11..CI-18 + métricas reais de modelo (tokens/custo/latência no provider real).

## F. Reuse decisions (diagnóstico)

| Gap | EXISTING_EQUIVALENT | REUSE_DECISION |
|---|---|---|
| 1 vocabulário string | YES (`_is_open_vocabulary`/`_requires_owner_vocabulary`, discovery) | EXTEND |
| 2 goal_class | YES (`_TurnGoal`/`GOAL_INSTRUCTION`) | EXTEND |
| 3 seleção write | YES (`CAPABILITY_SELECTION_INSTRUCTION`) | EXTEND |
| 4 completude inner | YES (`_build_arguments` + catalog entity_schemas) | EXTEND |
| 6 suficiência/ordenação | YES (`_synthesize_content`, outcome.limitations) | EXTEND |
| 7 owner-hint reuse | TO_INVENTORY (bounded repair existe para surface-change apenas) | EXTEND |
| 8 personalidade | TO_INVENTORY (instrução base + docs personality) | TO_INVENTORY |

Nenhuma nova abstração necessária nos gaps comprovados. `ARCHITECTURE_DECISION_REQUIRED` não disparado — todas as correções candidatas cabem nos módulos existentes.

## Segurança / contratos

- Nenhum bearer/secret/prompt sensível nos testes ou neste doc; payloads fake, nomes neutros.
- Nenhum contrato produtivo alterado; harness novo é test-only (`TEST_ONLY` exposure class).
- Injection: blocos untrusted já delimitados; CI-11 TEST_NOT_RUN (etapa 06).
- Concurrent user changes preservadas; staged somente este doc + o arquivo de testes + ledger.

## Residuais

- Métricas de tokens/custo real: TEST_NOT_RUN (provider LLM real fora do harness).
- CI-06, CI-11..CI-18: TEST_NOT_RUN (não prioritários nesta etapa).
- Comportamento do modelo real vs scripted proposals: gap de evidência aceito; produção já mostrou os mesmos outputs observados.
- Independência: self-review; INDEPENDENT_REVIEW=PENDING.
