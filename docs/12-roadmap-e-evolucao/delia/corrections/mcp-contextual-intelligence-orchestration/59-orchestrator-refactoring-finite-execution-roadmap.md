# 59 — Roadmap executivo fechado para refatoração semântica do orquestrador DÉLIA

**TRACK_ID:** `DELIA-C3-ORCHESTRATOR-SEMANTIC-REFACTOR-FINITE-ROADMAP-01`
**DATA:** 2026-10-19
**ESTADO VIGENTE:** `I04_FINITE_REFACTOR_CONTINUATION` (Product Master 2026-10-20; plano de seis pacotes preservado; `I04_ACCEPTED=NO`; Q01 autorizado como gate de entrada; Q02-B/C/Q03 condicionados ao gate anterior). **Estado anterior** `OPTION_B_Q02_A_EXCEPTION_AUTHORIZED_FOR_I04_ONLY` permanece histórico na seção 0.
**BASE_HEAD de planejamento:** `095f3f0bb22cf92518e0cf075a6fd1a0fc73cd92` (revalidar `origin/main`, `HEAD` e `git status` a cada execução; updates concorrentes não integram automaticamente o escopo).
**CANÔNICO:** execução 16; standalone 50; ownership 17; patterns 49 §14.1; baseline 51; bootstrap 52; state 21; tests 20; traceability 25; product 24; MCP/A2A 60; `.cursor/rules/development-standards-index.mdc`, `delia-execution-protocol.mdc`, `plan-construction.mdc`; ledger atual.
**EVIDÊNCIAS:** [56](./56-orchestration-audit-semantic-ownership-checkpoint.md) e [57](./57-orchestration-complete-second-pass-static-audit.md), 10.592 linhas/179 definições, 42 grupos de achados; [58](./58-adr-llm-semantic-decision-ownership.md) direção `APPROVED`; ledger §6.145 (`selection-only` congelado), §§6.299–6.300.
**ROADMAP DE REFERÊNCIA EXISTENTE:** [README da trilha](./README.md) I00–I04 → Q01 → Q02 → Q03. **Esta entrega especializa Q01–Q03 e explicita o gate I04, não revoga a ordem nem habilita Q01 sem aceite.**

## 0. Product Master Option B — alteração pontual da dependência Q02-A (2026-10-19)

**AUTHORITY:** [16 — Decisão vigente de execução](../../16-execution-master-plan.md) + registro Product Master na coordenação v10; ledger §6.313. **EVIDENCE:** [62 — G0 final I04 gate](./62-g0-bounded-i04-remediation-compare-and-c02-budget.md), ledger §6.311–§6.312. **ARCHITECTURE BINDING:** [58 — ADR semantic ownership](./58-adr-llm-semantic-decision-ownership.md). G0 Option A encerrou sem I04 aceite após um rework; avaliação live C02 admitiu fonte operacional mas selecionou DAVI (3x)/TÉO (1x) e nunca VISTA na amostra; SIPOC/continuidade hipotética também falharam, apesar de 1647 testes backend reportados verdes. **I04 não aceito.**

**Alteração exclusivamente na transição de entrada do pacote Q02-A:** `G0_FAIL + PRODUCT_MASTER_OPTION_B_APPROVED + PRE_Q01_INVENTORY_60_REUSED + ONE_RESIDUAL_CONSUMER_CHECK → Q02_A_I04_REMEDIATION_ALLOWED`. Sem concluir G0/I04, sem autorizar ou aceitar Q01 e sem execução sequencial normal de Q02. Q01 ainda fica condicionado a um gate legítimo posterior; Q02-B, Q02-C e Q03 continuam `NOT_AUTHORIZED`. Os **seis pacotes** e seus testes/política anti-loop continuam sendo a autoridade; a exceção é um desvio controlado de uma aresta, não um pacote novo nem uma revisão global do plano. Ao concluir Q02-A, a coordenação examina o resultado e decide explicitamente I04 e os gates posteriores; nenhum avanço implícito.

**Task única autorizada:** `DELIA-C3-I04-EXCEPTION-B-Q02-A-SEMANTIC-CONSOLIDATION-01`. Responsável implementação/testes/live/commit = Cursor; responsável inventário/contratos/gate/review = coordenação. Antes de diff: `git status/HEAD/origin/main`, reanchor canônico e **uma única** busca residual repo-wide `rg` de callers alterados vs doc 60 — retornar delta contratual à coordenação, sem reinventariar 42 grupos. Capturar goldens e RED em C02 model real e fake/provider-neutral antes de mudança, SIPOC sem tool, mudanças de assunto, anáforas, negation, catálogo rename/add-remove/reorder e safe personal scope. `EXISTING_EQUIVALENT=YES` para `InvokeModel/_propose`, goal tipado, `OperationalCapabilityOrchestrator`, `TurnDeadline` e `CapabilityProviderPort`; `REUSE_DECISION=REUSE|EXTEND`. Se faltar contrato legítimo, STOP.

**Escopo:** S01–S11/S15/S20–S22 e F27/F32/F40 **somente onde forem decisões linguísticas semânticas**, com menor diff de consolidação de admission/goal/group/capability e critérios de applicability contextual. LLM propõe significado/capability a partir do catálogo vivo governado; código determinístico valida membros, live Core/Domain AuthZ, provenance, schema, deadlines e invariantes. Não mover Q02-B argumentos/index/provenance nem Q02-C comparação/synthesis/duplicated _select_candidate nesta exceção; nenhum new planner, engine por regex, provider branch, registry, Chat dependency, factual prose channel ou ACT/autonomia. Exceções de parsing sintático, logs/redaction e checagens de identificadores continuam legítimas.

**Gates de saída (não negociáveis):** full backend + RED/GREEN + segurança, PREPARE/ACT negativa, proveniência, providers equivalentes e no-tool. Live autorizado sobre SHA/config/model/deploy correto: C02 deve selecionar owner/capability semanticamente adequados pelo catálogo aprovado e produzir orientação de formatos **ou disclosure explícito de gap owner comprovado** — jamais DAVI/TÉO por ranking lexical; SIPOC e diálogo hipotético devem responder sem tool desnecessária; DAVI/TÉO/OpenAPI owner reais não podem regredir; 1 cold + 2 warm e limite estrito 30 s; resultado funcional != HTTP 200. Na ausência de precondição GLPI, positivo pessoal = `TEST_NOT_RUN`; nunca simular. Aceite de Q02-A exige review independente `ACCEPT|ACCEPT_WITH_RESIDUAL` sem blocker de segurança. Máximo **um rework de Q02-A**, e **zero G0**; fail persistente STOP/Product Master/owner/contract.

```text
ORIGINAL_SEQUENCE=G0_Q01_Q02A_Q02B_Q02C_Q03
EXCEPTION=OPTION_B_Q02_A_I04_ONLY
PRODUCT_MASTER_APPROVED=YES
G0_OPTION_A=STOP_EXHAUSTED
G0_REWORK_REMAINING=0
I04_ACCEPTED=NO
Q01_AUTHORIZED=NO
Q01_EXECUTED=NO
Q02_AUTHORIZED=NO
Q02_A_EXCEPTION_AUTHORIZED=YES_I04_ONLY
Q02_A_IMPLEMENTATION_EXECUTED=YES
Q02_A_INDEPENDENT_REVIEW=PENDING
Q02_B_AUTHORIZED=NO
Q02_C_AUTHORIZED=NO
Q03_AUTHORIZED=NO
MODEL_AUTHORED_FACTUAL_PROSE=NONE
C3_EXECUTED=NO
C4_AUTHORIZED=NO
C5_AUTHORIZED=NO
LIVE_EVAL=TEST_NOT_RUN
NEXT=COORDINATION_INDEPENDENT_Q02_A_REVIEW
```

## 1. Por que o plano precisa ser fechado

O roadmap anterior tem Q01–Q03, mas Q01 permanece `Q01_AUTHORIZED=NO` porque `I04_ACCEPTED=NO`. Novas correções isoladas de I04 repetiram o ciclo RED → patch → review → novo patch sem uma definição objetiva do que constitui encerramento da refatoração. A ADR 58 decidiu o ownership semântico, mas **não autorizou diff**. A solução é uma sequência de **seis pacotes com escopo, entrada, evidência, teste e saída**, limite de rework e revisão única por pacote — nunca aceitar regressão de segurança para “cumprir o prazo”.

## 2. Resultado final esperado e limites

**DoD de produto:** interpretação/conteúdo semânticos vêm do LLM existente; execução determinística valida contrato, provenance e security/authority; sem regex de intenção nem ranking lexical que se sobreponha ao modelo; continuidade atende ao tipo de tarefa (comparar ≠ listar); índices e argumentos respeitam contrato owner; cálculo/rendering legítimos e governança permanecem; latência total estrita 30s nas amostras aceitas; DAVI/TÉO/VISTA/OpenAPI e interação sem ferramenta têm outcomes e evidências verificáveis.

**Não é DoD:** redução arbitrária de linhas; apenas remover regex; HTTP 200; fixture verde isolada; comportamento do Chat; nova camada planner; declaração de PASS quando owner/identidade impõe bloqueio.

**Congelamentos:** `MODEL_AUTHORED_FACTUAL_PROSE=NONE` e `selection-only` (ledger §6.145) não serão alterados neste roadmap. Se o resultado exigido for impossível nesse contrato, registrar `ARCHITECTURE_DECISION_REQUIRED` e **parar somente o subescopo afetado**, preservando demais gates. Produto/owner/Policy/AuthZ e PREPARE/ACT permanecem intactos.

## 2.1 DoD de produto LLM-enabled — não implementar compreensão em Python

**PRINCÍPIO VINCULANTE (Product Master, esclarecimento do ADR 58):** não estamos desenvolvendo um LLM nem uma linguagem de programação de prompts; construímos **a DÉLIA, produto que utiliza a inteligência de LLMs existentes** por `InvokeModel/_propose`, contexto relevante, instruction lineage, catálogo vivo de capabilities e adapters autorizados. O objetivo é **generalização para perguntas não antecipadas**, não a aprovação de fixtures codificadas. Priorizar qualidade de instruções/contexto e propostas semânticas tipadas; evitar lógica `if/regex/stem/keyword/cluster/rank` que decida intenção, grupo, capability ou continuidade no lugar do modelo. Um prompt com exceção por owner/pergunta é também acoplamento e não resolve o problema.

**Boundary operacional:** modelo propõe intenção/contexto/goal/group/capability/clarificação/plano semântico proporcional; não cria FACT, autorização, owner contract, identificador nem task outcome empresarial sozinho. Código faz **somente validação legítima** (schema, catálogo vivo elegível, AuthN/Core/Domain AuthZ, provenance, security, Policy/Decision, idempotência, deadlines, confirmação/PREPARE/ACT/postcondition), e não reinterpreta linguagem após a proposta do modelo. `reject` linguístico semântico por baixa sobreposição de palavras = candidato a eliminação; `reject` de dados/segurança/contrato = preservado fail-closed. Uso de MCP/A2A/OpenAPI continua por port/adapter e não implica invocation de todas as tools.

**Gate mensurável da refatoração:** antes/depois por SHA/model/prompt lineage/config/context version. Exigir (a) C02 seleção **sem branch VISTA** com capability adequada e resposta ou owner gap comprovado; (b) SIPOC e hipóteses sem tool indevida; (c) referência contextual, mudança de assunto, negação e ambiguidade; (d) providers equivalentes renomeados, reordenados, adicionados/removidos, MCP e OpenAPI não-MCP; (e) nenhuma regressão de owner-grounded DAVI/TÉO, zero ACT indevido e `selection-only`; (f) cold/warm, contagem de chamadas, latência real <=30s e resultado funcional. Menos código, nova regex, resposta genérica/soft-land ou HTTP 200 **não** substitui um `PASS_TASK_OUTCOME`. Sem evidência de modelo real, registrar `TEST_NOT_RUN/INCONCLUSIVE`, nunca PASS.

**Não amplia fase:** no momento, apenas Q02-A como exceção I04 de §0; Q01/Q02-B/C/Q03 continuam bloqueados. Esta seção apenas explicita o objetivo/DoD do roadmap já aprovado; não abre Q02-C, refatoração de argumentos ou novo modelo/agent/serviço.

## 3. Seis pacotes, sem voltas ilimitadas

| Pacote | Dependência/gate de entrada | Escopo único e artefato verificável | Saída / go-no-go |
|---|---|---|---|
| **G0 — Fechamento I04** | ADR 58 aprovado; I04 ainda NÃO aceito | Uma revisão conclusiva dos requisitos I04 com matriz de owner-vs-DÉLIA, DAVI/TÉO/VISTA/HTTP/no-provider, 30s, provenance, task outcome, continuidade. Distinguir bugs transversais de `OWNER_CONTRACT_GAP`, vínculo GLPI ausente e indisponibilidade externa. Se necessário, **um** rework bounded para blocker transversal provado. | `I04_ACCEPTED` apenas por review independente. Se não: `I04_BLOCKED` + decisão explícita de Product Master (remediação adicional, defer/rescope ou stop); **não iniciar Q01** silenciosamente. |
| **Q01 — Preparação e consumer gate** | G0 `I04_ACCEPTED`, autorização explícita da coordenação para Q01 | Aproveitar 56/57 sem reiniciar inventário: identificar callers, imports, testes, contratos/owners e usos transversais das 42 categorias; `EXISTING_EQUIVALENT`/`REUSE_DECISION` por mudança. Congelar golden baselines e RED adversarial antes de remover código. | Mapa de consumidores de todo o arquivo, classes `REMOVE/REPLACE/KEEP/ADR`, matriz teste→achado, rollback e SHA; **sem refatorar runtime ainda**. |
| **Q02-A — Interpretação única** | Entrada normal: Q01 revisada; **exceção única Option B aprovada:** somente remediação I04 sem Q01 autorizado, usando dossier 60 + residual `rg`/golden baseline | Remover/substituir rotas de interpretação linguística manual (regex coverage/guidance/prior cues/ordinal, index clusters e semantic score/veto, singleton group and prior skip) e consolidar decisões repetidas admission/goal/group/capability **usando `InvokeModel`/`_propose` já existentes**. Preservar seleção live e contracts. | Testes RED→GREEN de paráfrase, negação, mudança de assunto, intent vs. topic, ferramenta opcional; redução comprovada de duplicação; nenhum caminho provider-specific. |
| **Q02-B — Argumentos, index e provenance** | Q02-A e full regression PASS | Revisar `_free_string_grounded_in_user_input`, string passthrough, `_unproven_identifier_inputs`, identificador ordinal e `_eligible_self_index_probe`. Propostas LLM tipadas; origem factual validada por user-span/evidence/owner refs; READ exploratório tratado como interpretação, não FACT. Index probes somente sob owner contract. | Produto real via Domain owner, NO_MATCH fundamentado, ID inventado rejeitado, renamed/non-MCP/metamorphic, paginação correta; sem escalada de permissão. Se novo contrato requerido: STOP para ADR. |
| **Q02-C — Continuidade, síntese e organização interna** | Q02-B e suite/regression PASS | Eliminar `list-as-compare`, `recover_empty_selection` como fake task success, texto anterior como fonte autoritativa, sizing/coverage de palavras como outcome. Preservar seleção-only; reutilizar evidence estruturada existente; deduplicar chamadas a `InvokeModel` fora de `_propose` e extrair helpers puros **somente por coesão/consumers reais**, nunca novos serviços/ports/engine de conveniência. | Comparação real entre campos autoritativos ou insuficiência explícita; K1/K2/TÉO, C02/VISTA, DAVI search/follow-up e conversa sem tool; comparabilidade e 30s; **sem prosa empresarial livre de modelo**. |
| **Q03 — Aceite independente e encerramento** | Todos Q02-A/B/C examinados por review; nenhuma regressão crítica aberta | Revisar arquitetura pós-diff, owners, contratos, generalização, performance/repetição, segurança e task outcomes no exato SHA/config live; residual search completo; documentar exceções e descontinuar correções fora do escopo. | Um único parecer `ACCEPT | ACCEPT_WITH_RESIDUAL | REWORK | EXECUTION_DRIFT | INCONCLUSIVE`. `C3_EXECUTED` **não** avança automaticamente. Fechar track ou retornar decisão de Produto com blockers identificados. |

**Execução Cursor:** cada pacote = *um prompt fechado, uma implementação bounded se autorizada, uma suite e um report factual*. Q02-A/B/C podem ser executados na mesma sessão Cursor/worktree com checkpoints e revisões por gates, sem chat novo por função. **Sem revisão por microhelper.**

## 4. Política anti-loop

1. **Máximo de uma tentativa de rework por pacote** após a primeira entrega. Persistindo FAIL em requisito material, STOP-THE-LINE e encaminhar uma **decisão objetiva** de escopo/contrato/owner no chat de coordenação. Não abrir `R1/R2/R3` do mesmo sintoma indefinidamente.
2. Exceção: falha crítica de segurança deve ser isolada e remediada antes de qualquer deploy; não pode receber `ACCEPT_WITH_RESIDUAL` para liberar o gate. A regra de limite organiza decisões, não suspende correção de risco crítico.
3. **Nenhum novo prompt fora dos seis pacotes** para o mesmo grupo de achados, salvo prova nova de risco/contrato e decisão explícita documentada. Incidentes de owner com bloqueio externo passam para owner legítimo, com `BLOCKED/TEST_NOT_RUN`; não geram patches no orquestrador.
4. **Um review de coordenação por pacote**. Dúvidas de implementação são resolvidas dentro da execução e do contract gate, não convertidas em dezenas de subchats.
5. Se produção não puder ser testada com mesmo subject/scope/provider, declarar `TEST_NOT_RUN` e exigir o responsável/gate — nunca usar credencial de outro sujeito para “fechar o teste”.
6. Se objetivo entra em conflito com seleção-only, segurança ou authority congelada, registrar `ARCHITECTURE_DECISION_REQUIRED` e devolver alternativas; nunca relaxar o contrato por conveniência.
7. Migrations/deploy ficam sujeitos a autorização e runbook. Uma etapa feita na docs não vira fase/runtime `PASS`.

## 5. Matriz de aceite única e imutável por pacote

**Suítes obrigatórias:** full `delia-api`, testes de contratos, R1–R5, SEM/SEMARG, I01–I04, interop/safety, provider-neutral renaming/new tool/add-remove/reclassify, no-provider, quantidade/negação/identificadores falsos, prompt injection, scopes pessoais e total≠page; avaliar independentemente sobre SHA/config e comparar baseline.

**Live obrigatório quando autorizado:** matriz mínima DAVI READ/discovery/continuity; TÉO guidance e casos sem vínculo tratados honestamente; VISTA formats/guidance/C02 latency; OpenAPI/HTTP non-MCP; saudação/SIPOC/hipotéticos sem tool; concorrência controlada/cold-warm; zero ACT em READ. Material ACT permanece fora de escopo e em gate legítimo. Definir holdouts **antes do patch**, medir stage, chamadas modelo, SLA de 30s e completion real, não apenas HTTP status.

**Critérios transversais de saída:**

- RQ-1: A seleção semântica se generaliza entre perguntas não previstas e providers/ausência de provider.
- RQ-2: Propostas LLM não são autoridade; schema, provenance, Core/Domain AuthZ e policy fail-closed.
- RQ-3: Sem reclassificação por regex/cluster e sem workflows específicos por owner.
- RQ-4: Continuidade resolve transformação pedida em vez de reproduzir texto como resultado.
- RQ-5: Sem double planner, shadow source, import/runtime do Chat ou quebra de bounded context.
- RQ-6: Segurança, PREPARE/ACT, idempotência e pós-condição **não regrediram**.
- RQ-7: Testes/evals no SHA/config real, conclusões `PASS/FAIL/PENDING/INCONCLUSIVE/TEST_NOT_RUN` verdadeiras.
- RQ-8: Performance com limite, residuals quantificados e rollback executável.

**CP/RQ:** vincular CP-263/264/265 e CP-015/029 quando aplicáveis, sem inventar CP; a execução define RQ granular e acceptance test correspondente.

## 6. Plano de persistência e decisão

- Para cada pacote: código/diff/testes com SHA, um relatório de implementação e um review independente. Atualizar README/ledger **após evidência**, não gerar múltiplos documentos duplicados por hipótese.
- **Regra original histórica:** `Q01/Q02/Q03` ficam `PLANNED / NOT_AUTHORIZED` até G0. **Exceção de 2026-10-19:** somente Q02-A `AUTHORIZED_FOR_I04_ONLY` pela seção 0. **Exceção vigente de entrada (2026-10-20):** seção 11 — Q01 autorizado com `I04_ACCEPTED=NO`; Q02-B/C/Q03 continuam condicionados ao gate anterior. ADR58 `ARCHITECTURE_DIRECTION=APPROVED` não concede `I04_ACCEPTED`. O fence abaixo é o snapshot de 2026-10-19.
- O encerramento do roadmap pode ser `ACCEPT_WITH_RESIDUAL` **somente** quando residual não violar gate material de segurança, proveniência, autorização ou outcome declarado como obrigatório. O que permanecer bloqueado deve ter owner/contrato/próximo responsável e não ser declarado PASS.

```text
FINITELY_SCOPED_PACKAGES=6
PACKAGE_SEQUENCE=G0_I04_EXIT|Q01|Q02_A|Q02_B|Q02_C|Q03
MAX_REWORK_ATTEMPTS_PER_PACKAGE=1
ON_REPEAT_FAILURE=STOP_ESCALATE_ARCHITECTURE_OR_OWNER_DECISION
SOURCE_AUDIT=56_57
BINDING_ARCHITECTURE=58
ORIGINAL_I04_Q01_Q02_Q03_ORDER=PRESERVED_EXCEPT_ONE_Q02_A_ENTRY
Q01_AUTHORIZED=NO
Q02_AUTHORIZED=NO
Q02_A_EXCEPTION_AUTHORIZED=YES_I04_ONLY
Q02_B_AUTHORIZED=NO
Q02_C_AUTHORIZED=NO
Q03_AUTHORIZED=NO
I04_ACCEPTED=NO
C3_EXECUTED=NO
C4_AUTHORIZED=NO
C5_AUTHORIZED=NO
CODE_DIFF=NONE
TESTS=TEST_NOT_RUN
NEXT=CURSOR_SINGLE_BOUNDED_Q02_A_I04_REMEDIATION
```


## 7. Divisão de trabalho executiva após levantamento GPT (2026-10-19)

O Product Master determinou que **levantamento, diagnóstico documental, inventário de contratos, consumidores, testes e planejamento ficam com o GPT/coordenação; o Cursor somente executa refatoração de código e sua validação técnica**, conforme gates de fase.

- [60 — pré-Q01 já levantado pelo GPT](./60-pre-q01-consumers-contracts-tests-inventory.md): 42/42 achados mapeados para chamadas internas, testes e owners/contratos; `HandleInteractiveConversationTurn`, `CapabilityProviderPort` e adapters MCP/OpenAPI confirmados. Descoberto classificador lexical externo em `paginated_result_semantics.py`; testes existentes que reforçam ranking lexical e `prior_turns` skip identificados. Limite declarado: busca indexada GitHub retornou zero mesmo em símbolo existente; Cursor executa só **uma** busca residual `rg` para validação de consumer drift no SHA local — não um novo inventário amplo.
- [61 — G0 e handoff só para refatoração](./61-g0-evidence-prepared-and-cursor-only-implementation-handoff.md): estado honesto de I04 (DAVI/HTTP com avanço, VISTA C02 HTTP504, comparação ainda lista, TÉO precondition sem subject vinculado), regras de stop, RQ/RED/DoD de cada pacote Q02-A/B/C e matriz live/no-tool/segurança.
- **Q01 permanece bloqueado** até G0/autoridade; a preparação documental antecipada não é `Q01_EXECUTED` e não libera Q02. No gate autorizado, GPT revisa o inventário 60 e qualquer drift que Cursor apure antes do diff. Assim Q01 não vira ciclo redundante de análise no Cursor.
- **Cursor não redesenha ownership/ADR, não reinicia exploração do orquestrador, nem decide aceite/phase.** Após autorização de cada pacote, faz somente menor diff, testes RED/GREEN, full backend, live conforme runbook, relatório e commit/push.
- Anti-loop de 59 segue válido: G0+Q01+Q02-A/B/C+Q03, máximo um rework bounded por pacote, stop/escalate diante de falha persistente. Exceção necessária: vulnerabilidade material impede deploy e demanda remediação governada.

```text
GPT_PRE_Q01_RESEARCH=COMPLETED_WITH_CONNECTOR_LIMITATIONS
G0_I04_ACCEPTED=NO
Q01_AUTHORIZED=NO
Q02_AUTHORIZED=NO
CURSOR_OWNER=CODE_REFACTOR_TEST_LIVE_ONLY_AFTER_PHASE_GATE
DOC60=CONSUMER_CONTRACT_TEST_INVENTORY
DOC61=G0_EXECUTION_CARDS
```


## 8. Coordination v10 — independent Q02-A first review (2026-10-19)

**REVIEWED_HEAD:** `7e62894e2faa6a1b9c3fc348546f91c1a8112272` (one commit after `38342414f57071d8e6f6d588454311c3663304a1`); `orchestration.py` blob `9d82c34bb6ac71807bc7d1c249df9982a2b18c3f`. **INDEPENDENT_REVIEW_VERDICT=REWORK** for **Q02-A test/outcome coverage and residual semantic fallback**; G0 remains CLOSED, no wider Q02 change permitted. This is an independent **GitHub static source/diff/test-assertion review**, not a GPT execution of pytest or live model eval. The executor's 1664/1664 PASS and 0 ACT are `PASS_EXECUTOR_REPORTED`, not an independently reproduced runtime outcome.

**Accepted implementation direction:** `_is_information_coverage_inquiry`, continuity/guidance lexical cue regex and index intent clusters/scores removed; prior-turn admission no longer skipped; group model now queried even on singleton; live group membership normalization is exact/unambiguous; no new planner/provider-specific runtime branch, public contract or observed permission bypass. `InvokeModel/_propose`, domain/Core validation and frozen `selection-only` still reused. This is **not** final I04 acceptance.

**BLOCKING A — inadequate functional test replacements:** `tests/test_q02a_semantic_consolidation.py` preprograms `FakeProposalModel` with `mcp:vista`/correct capability and asserts that route executes; repeating the *same* canned proposal for C02 paraphrase/negation/rename/order does NOT test real model semantic preference among DAVI/TÉO/VISTA, nor SIPOC explanatory content or hypothetical compare task completion (only `NOT_APPLICABLE` and 0 tools). Valid unit wiring coverage is accepted; claims of `PASS provider-neutral semantic selection/outcome` are **not proven** by these fixtures. New group-selection prompt includes category examples close to C02; unseen semantic holdouts must verify this does not overfit.

**BLOCKING B — weakened negatives without equivalent outcome oracles:** `test_k3_no_relevant_topic_clarifies_without_nested_read` removed the assert that inappropriate nested filled READs do not happen and now permits `SUCCESS/NOT_APPLICABLE`; `test_k2_short_but_sufficient_limitation_ask_not_expanded` now explicitly tolerates a full checklist dump and uses a broad string check. K2 incomplete-checklist tests were retargeted from under-selection to preselected all-item proposals. Hence ledger §6.315 claim "no weakened negatives" contradicts the source diff. These tests are insufficient to demonstrate the declared nonregression in task-focused guidance, data relevance and continuity. **Do not restore the old lexical veto or keyword checker**. Replace with bounded **task-outcome/faithfulness oracles** using owner evidence and correct, incomplete, misleading, missing-proposal and adversarial model proposals, separately classifying safety, authorization, utility, and completion. A valid catalog ID is not proof that it answers the question; fallback/rejection may be correct while user task still fails. No free factual prose or new typed evidence contract.

**BLOCKING C — remaining implicit singleton applicability:** `_select_group()` still returns the sole group when `_propose` returns `None` (`if len(eligible)==1`), although Q02-A's goal is to avoid interpreting singleton membership as semantic relevance. Current explicit `applicable=false` test does not exercise `None`. Analyze provider availability/model failure/timeout and preserve fail-closed behavior; no new semantic engine. `unique_structural_ticket_list_capability` in existing `paginated_result_semantics.py` also uses lexical request classification as a short circuit; **TO_INVENTORY/FUTURE_GATE**, not authorization for this task to rewrite external helper or Q02-B/C paths without approved scope. Record residual truthfully rather than asserting all lexical interpretations are gone.

**Mandatory SINGLE bounded Q02-A rework:** `DELIA-C3-I04-EXCEPTION-B-Q02-A-ONE-REWORK-01`. Scope limited to (1) replace weakened behavioral assertions/fixture retargets by meaningful negative/positive task-outcome oracles and explicit `NOT_PROVEN` for real semantic routing without real-model eval, (2) correct the missing-proposal singleton route **if** it can select an inappropriate live owner/capability when semantic relevance is unproven, preserving membership/AuthZ/security and 30s, (3) prove no silent wrong-owner factual PASS in C02/K2/K3 and no checklist dump for limitation-only intent, using existing model interface/owners/contracts, (4) avoid C02-specific lexical examples embedded as unique pass condition, (5) measure added admission/group calls and budget in actual authorized real-model environment if available. Exactly one diff/review cycle, not many microtasks. If actual owner/contract or runtime prevents live, `TEST_NOT_RUN`/BLOCKED; no production deploy implicitly approved.

**Go/no-go:** full backend/security/safety pytest, adversarial metamorphic fake-model behavior, honest `selection-only` and no ACT/credential leak; **real model** C02 cold1+warm2, SIPOC useful answer, hypothetical follow-up, DAVI/TÉO/VISTA/OpenAPI/no tool, rename/reorder/add-remove/equivalent, negative injection/IDs, task outcomes, max wall 30s **only if operationally authorized**. Without real model/owner evidence, I04 remains `NO`. If correction demands new contract/regex classifier/provider branch/second planner, STOP and return to coordination/Product Master, not silent implementation.

```text
Q02_A_IMPLEMENTATION_EXECUTED=YES
Q02_A_FIRST_INDEPENDENT_REVIEW=REWORK
Q02_A_BOUNDED_REWORK_AUTHORIZED=YES
Q02_A_BOUNDED_REWORK_EXECUTED=YES
Q02_A_REWORK_REMAINING=0
Q02_A_ARCHITECTURE_DIRECTION=PARTIALLY_PROVEN_STATIC
Q02_A_REAL_MODEL_SEMANTIC_SELECTION=TEST_NOT_RUN
Q02_A_TASK_OUTCOME=NOT_PROVEN
I04_ACCEPTED=NO
Q01_AUTHORIZED=NO
Q02_AUTHORIZED=NO
Q02_B_AUTHORIZED=NO
Q02_C_AUTHORIZED=NO
Q03_AUTHORIZED=NO
C3_EXECUTED=NO
C4_AUTHORIZED=NO
C5_AUTHORIZED=NO
PRODUCTION_DEPLOY_AUTHORIZED=NO
NEXT=COORDINATION_FINAL_Q02_A_REVIEW_OR_STOP
```


## 9. Coordination v10 — Q02-A post-deploy real-model evidence (2026-10-19)

**EVIDENCE PROVENANCE:** Product Master's relay of **three** real authenticated production requests on deployed host git `2ed7dbc489218b755783f5d61c49090de25f9cc9`. The GitHub comparison `7e62894e2faa6a1b9c3fc348546f91c1a8112272 → 2ed7dbc489218b755783f5d61c49090de25f9cc9` contains **only** docs 59 and ledger updates (no `delia-api` application code), so the Q02-A source blob under review is unchanged. Executor reported `up-prod-sequential.sh --pull --build delia-api`, healthy container, subject `user`, `MATERIAL_ACT=0`. Detailed raw JSON was referenced as server-local `/tmp/delia_q02a_live_results.json`; coordination did **not** access server-local file, full logs/correlation IDs, actual HTTP payloads or directly replay model calls. Treat timings/status/outcomes as **EXECUTOR_REPORTED_LIVE_EVIDENCE**, code path attribution as **PROVEN_STATIC** where explicitly noted, and generalized task/outcome as not yet independently certified. No production deployment newly authorized here.

| Case | Executor reported observation | Coordination classification | Boundary |
|---|---|---|---|
| C02: "Quais formatos de dados estão disponíveis?" | HTTP 200, 16,957 ms; admission `owner_surface/operational`; `mcp:vista/get_catalog`; `GROUNDED/OBSERVATION`; output describes display formats but has partial "busca sem correspondência" envelope | **PASS_OWNER_SELECTION (1 sample)**; `TASK_OUTCOME=PARTIAL/INCONCLUSIVE` until full requested formats/catalog response and owner fidelity verified | Strong improvement against pre-Q02-A DAVI×3/TÉO variant. One run ≠ generalization/cold+2warm |
| SIPOC: "O que é SIPOC?" | HTTP 200, 14,166 ms, admission `conversational`, no owner; `NON_GROUNDED/HYPOTHESIS`, `turn_budget_limited`, no concept explanation | `PASS_CONVERSATIONAL_ADMISSION`; **FAIL_TASK_OUTCOME** | Correct no-tool routing ≠ useful conversational answer |
| Hypothetical generation + compare | HTTP 200, 13,519 ms, `conversational`, no owner, `turn_budget_limited`, no useful hypothetical answer/continuity | `PASS_NO_OWNER_ADMISSION`; **FAIL_TASK_OUTCOME** | No evidence that multi-turn hypothetical continuity or compare succeeded |

**Code-bounded diagnostic:** `HandleInteractiveConversationTurn._execute_observed` receives `NOT_APPLICABLE` from admitted no-owner turn and invokes the **existing** `_invoke` with `CONVERSATIONAL_FALLBACK_STAGE_CAP_SECONDS=12.0`; `InteractionError(MODEL_TIMEOUT)` soft-lands to `_conversational_budget_result` with `turn_budget_limited`. That mechanism is confirmed in current `handle_interactive_turn.py`, but root cause (actual inference latency vs two model calls vs context/instruction/schema overhead vs host/provider scheduling) is **TO_VERIFY** from per-stage trace and request ID. Do not infer from 14s wall time that the whole 30s global turn was exhausted: **12s stage cap and 30s global turn are different bounds**. Relaxing cap blindly, replacing answer with Python template, introducing a new inference pipeline or sacrificing strict 30s is **NOT AUTHORIZED** by Q02-A.

**Effect on existing §8 REWORK decision:** retain `Q02_A_INDEPENDENT_REVIEW=REWORK` and one rework remaining. Reported C02 live selection **partially closes** the prior lack of *any* real-model evidence for intended provider; it **does not** resolve K2/K3 weakened tests, missing-proposal singleton or prove C02 complete success, SOP/guidance/owner contract, and exposes real conversational-output failures. Amend the already-authorized `DELIA-C3-I04-EXCEPTION-B-Q02-A-ONE-REWORK-01` validation focus (no second rework prompt): first capture same correlation-stage timings, admission/fallback counts and exact model call timeout; assert meaningful task outcome on real no-tool SIPOC/hypothetical and C02 fidelity; restore test oracles without lexical classifiers. An **in-scope** correction is possible only if shown to be a bounded Q02-A admission/semantic sequencing issue using existing ports/instructions. If root requires modification to unrelated conversational response runtime, inference provider capacity/config, Q02-C refactor or new contract, **STOP→ROOT_CAUSE/OWNER→COORDINATION/PRODUCT_MASTER_DECISION**; do not silently expand this one rework. Operational deploy and testing require their own authorization.

**States unchanged (coordination snapshot, pre-execution):** `Q02_A_REWORK_AUTHORIZED=YES_ONCE`; `Q02_A_REWORK_REMAINING=1`; `Q02_A_ACCEPTED=NO`; `I04_ACCEPTED=NO`; `Q01_AUTHORIZED=NO`; `Q02_B/C_AUTHORIZED=NO`; `C3/C4/C5` unadvanced. No new runtime change or test made by coordination.

**Execution update (2026-10-20):** the single rework `DELIA-C3-I04-EXCEPTION-B-Q02-A-ONE-REWORK-01` was executed; ledger §6.318. `Q02_A_REWORK_REMAINING=0`. Live SIPOC/hypothetical `turn_budget_limited` stays `TO_VERIFY` outside this diff (12s conversational stage cap). No second rework.

## 10. Coordination — fechamento do rework Q02-A e continuidade solicitada (2026-10-20)

**DECISÃO PRODUCT MASTER comunicada na coordenação:** fechar o rework técnico Q02-A e dar continuidade à refatoração previamente definida. **REVIEW:** `ACCEPT_WITH_RESIDUAL` aplica-se **somente** ao diff bounded RQ-01–RQ-04 de Q02-A; não declara conclusão funcional do pacote, `I04_ACCEPTED` ou avanço de fase. Esta decisão sucede o snapshot pré-revisão em §8/§9 apenas para o fechamento administrativo/técnico; não reescreve a evidência histórica.

**BASE DE EVIDÊNCIA:** rework `ef88e59933174a58e83ea08aaf5aabdc2e0392f1` mantido no código; revisão executor em `8406b74fc7a13cb71244e45e018af07ed1fe353f` com 34/34 testes focados PASS, nenhum diff e `MATERIAL_ACT=0`. RQ-03 singleton sem proposta = `not_applicable` (provado estaticamente); RQ-01/RQ-04 = oráculos fixture relatados; RQ-02 = wiring fixture e 1 owner real VISTA correto, mas **resposta C02 parcial**. SIPOC resposta real útil (uma amostra), hipóteses/compare com `turn_budget_limited` no teto conversacional 12s; sem conclusão de continuidade. DAVI/TÉO/OpenAPI e generalização live `TEST_NOT_RUN`; full suite pós-revisão `TEST_NOT_RUN` (suite anterior PASS relatado). `HTTP 200` e `is_complete=true` não certificam task outcome.

**RESIDUAIS:** F3 formatos C02 = Q02-B/Q02-C/owner fidelity; F4 teto conversacional 12s + continuidade = fora Q02-A; F5 lexical `unique_structural_ticket_list_capability` = residual documentado fora Q02-A. Nenhum segundo rework de Q02-A permitido (`Q02_A_REWORK_REMAINING=0`). Preservar docs 56/57 (auditoria feita), ADR 58 (direção aprovada), inventário 60 e plano 59 (6 pacotes). Sem novo inventário, engine, planner ou regex de intenção.

**GATE DE CONTINUIDADE:** solicitação de continuidade **não** equivale, por si, a `I04_ACCEPTED` nem revoga a dependência do §0/§3. Preparar e submeter **uma decisão explícita de entrada** para o próximo pacote: ou (a) satisfazer/rever I04 com evidência e liberar Q01 segundo gate existente, ou (b) aprovar exceção Product Master de dependência com escopo e testes definidos, registrando alteração normativa em doc 16 antes de qualquer diff Q01/Q02-B/Q02-C. Até esse ato, usar exclusivamente os documentos existentes para definir o próximo bounded step; nada de execução de código por autorização implícita.

```text
Q02_A_BOUNDED_REWORK=ACCEPT_WITH_RESIDUAL_TECHNICAL_SCOPE
Q02_A_FUNCTIONAL_GATE=INCONCLUSIVE
Q02_A_REWORK_REMAINING=0
I04_ACCEPTED=NO
Q01_AUTHORIZED=NO
Q02_B_AUTHORIZED=NO
Q02_C_AUTHORIZED=NO
Q03_AUTHORIZED=NO
NEXT=PRODUCT_MASTER_EXPLICIT_CONTINUATION_GATE_ON_16_AND_59
```

## 11. Product Master — exceção de continuidade I04 (2026-10-20)

**AUTHORITY:** Plano Mestre 16, decisão vigente de 2026-10-20. **TASK:** `DELIA-C3-I04-FINITE-SEMANTIC-REFACTOR-EXECUTION-01`. Esta seção formaliza a exceção. Não executa Q01, Q02-B, Q02-C nem Q03.

A dependência ordinária `I04_ACCEPTED → Q01 → Q02-A → Q02-B → Q02-C → Q03` continua sendo a ordem dos pacotes. A exceção abre somente a entrada de Q01 enquanto `I04_ACCEPTED=NO`. Q02-A permanece fechado no rework técnico, com residuais funcionais abertos e sem segunda tentativa. ADR 58, `SELECTION_ONLY_GROUNDED_SYNTHESIS`, orçamento global de 30s e teto conversacional de 12s não mudam. Deploy de produção não está autorizado. Nenhum pacote se autoaceita: o gate seguinte só abre depois de review da coordenação.

```text
DECISION=I04_FINITE_REFACTOR_CONTINUATION
PRODUCT_MASTER_AUTHORIZED=YES
I04_ACCEPTED=NO
Q02_A_TECHNICAL_REWORK=CLOSED_WITH_RESIDUAL
SECOND_Q02_A_REWORK=NOT_AUTHORIZED
Q01_EXCEPTION_ENTRY=AUTHORIZED
Q01_EXECUTED=NO
Q02_B=CONDITIONAL_ON_Q01_GATE
Q02_C=CONDITIONAL_ON_Q02_B_GATE
Q03=CONDITIONAL_ON_Q02_C_GATE
C3_PHASE_ADVANCEMENT=NOT_AUTHORIZED_BY_THIS_DECISION
PRODUCTION_DEPLOY_AUTHORIZED=NO
NEXT=Q01_CONSUMER_GATE
```

## 12. Q01 — consumer gate executado (2026-10-20)

**TASK:** `DELIA-C3-I04-FINITE-SEMANTIC-REFACTOR-EXECUTION-01`. **BASE de código:** `78f1ca51679f886cb48e87b15cc6b8df0cf9e0f4`, igual ao commit documental anterior porque ele não altera `delia-api`. **FONTE REUTILIZADA:** documento 60, SHA de levantamento `9dad78c53beb2a5e5de50695fbb590b40440baf6`. Sem nova leitura das 10.592 linhas e sem reclassificar os 42 achados.

```text
Q01_CONSUMER_MAP=VERIFIED
Q01_CONTRACT_IMPACT=NONE
Q01_TEST_BASELINE=RECORDED
Q01_ROLLBACK=DEFINED
Q01_ACCEPTED=NO
Q02_B_AUTHORIZED=NO
RUNTIME_DIFF=NONE
NEXT=COORDINATION_Q01_REVIEW
```

**Consumidores.** O import de produção de `orchestration` continua só em `root_composer.py`. `capability_attempt.py` cita o módulo em comentário. Não há import em plugin, MFE ou outra API. A entrada continua `HandleInteractiveConversationTurn` → `attempt`. Os símbolos de Q02-B/Q02-C ainda referenciados têm callers em `orchestration.py` e em testes de `delia-api`.

**Drift desde o documento 60.** `contracts.py` e `ports.py` não mudaram. `handle_interactive_turn.py` e `root_composer.py` mudaram em `95e6c61264` (soft-land G0) e `9a8b05063d` (ditado VD-F03), sem contrato novo de capability. As linhas citadas no documento 60 para os helpers de Q02-A estão obsoletas: `_is_information_coverage_inquiry` não existe mais. Os helpers de Q02-B e Q02-C continuam definidos, em outras linhas: `_free_string_grounded_in_user_input`, `_eligible_self_index_probe`, `_unproven_identifier_inputs`, `_single_free_text_argument_from_input`, `_user_list_ordinal`, `_prior_listing_hint`, `_count_covered_extraction_units`, `_prior_extraction_incomplete`, `_render_is_list_replay_not_compare`. `classify_result_intent` e `unique_structural_ticket_list_capability` continuam em `paginated_result_semantics.py`. O nome `recover_empty_selection` não existe mais; a realocação desse comportamento fica para Q02-C. `experimental_arguments_budget_guard` continua no construtor, default falso.

**Contrato.** Nenhum DTO, porta ou contrato de owner mudou nesta verificação. Impacto classificado como drift interno de implementação. Não há `ARCHITECTURE_DECISION_REQUIRED`.

**Testes.** As suítes listadas na seção 4 do documento 60 seguem no repositório. Houve suíte adicional de Q02-A (`test_q02a_semantic_consolidation.py`). As contagens do documento 60 não foram recoletadas e a suíte completa não foi reexecutada neste pacote (`TEST_NOT_RUN`). A baseline registrada é a lista de suítes a preservar no rollback dos pacotes seguintes.

**Rollback.** Este pacote é documental. Reverter o commit desfaz o registro. Não há migration nem mudança de runtime. O rework Q02-A não é revertido aqui. O rollback de Q02-B/Q02-C, quando existirem, é reverter o commit do pacote.

**Código removido:** nenhum. Q02-B não inicia neste ciclo.


## 13. Coordination independent review — Q01 accepted with residual (2026-10-20)

**EVIDENCE BASE:** Q01 report on `374f5c2a21f9435483588b238e7090b73f1d46fa`; §§11–12 and document 60 §6; only documentation changed between `78f1ca51679f886cb48e87b15cc6b8df0cf9e0f4` and Q01 HEAD. Four Q01 outputs (consumer map, contract impact, test baseline list, rollback) recorded. No new external runtime consumer or contract change reported; full regression/live not run for documentation-only gate. **REVIEW = ACCEPT_WITH_RESIDUAL (Q01 only).** Residual: full test baseline is inventoried, not freshly executed; remains mandatory in Q02-B code-changing package. `recover_empty_selection` old symbol absent and Q02-C behavior not assessed here.

**AUTHORIZED NEXT:** Product Master's §11 exception is now satisfied for entry into **Q02-B only**. Implement bounded arguments/index/provenance change per §3, ADR58, audits56–57, inventory60 with RED/GREEN, owner contract and strict 30s, preserved 12s conversational cap. Q02-B cannot self-accept or deploy; no Q02-C until independent coordination review of Q02-B. In case of new owner contract/provenance representation gap, STOP affected subscope → ARCHITECTURE_DECISION_REQUIRED. Preserve I04=NO, Q02-A rework=0, full safety/authorization boundaries.

```text
Q01_COORDINATION_REVIEW=ACCEPT_WITH_RESIDUAL
Q01_ACCEPTED=YES
Q02_B_AUTHORIZED=YES_BOUNDED_ENTRY
Q02_B_EXECUTED=NO
Q02_C_AUTHORIZED=NO
Q03_AUTHORIZED=NO
I04_ACCEPTED=NO
PRODUCTION_DEPLOY_AUTHORIZED=NO
NEXT=CURSOR_Q02_B_ARGUMENTS_INDEX_PROVENANCE
```
