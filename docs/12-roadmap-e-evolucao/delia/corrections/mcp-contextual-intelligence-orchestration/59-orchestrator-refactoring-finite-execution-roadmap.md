# 59 — Roadmap executivo fechado para refatoração semântica do orquestrador DÉLIA

**TRACK_ID:** `DELIA-C3-ORCHESTRATOR-SEMANTIC-REFACTOR-FINITE-ROADMAP-01`
**DATA:** 2026-10-19
**ESTADO VIGENTE:** `OPTION_B_Q02_A_EXCEPTION_AUTHORIZED_FOR_I04_ONLY` (Product Master 2026-10-19; plano de seis pacotes preservado; Q01 não executado, Q02-B/C bloqueados). **Estado anterior** `PLANNED / PENDING_PHASE_GATE` foi supersedido somente para a entrada excepcional Q02-A.
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
- **Regra original histórica:** `Q01/Q02/Q03` ficam `PLANNED / NOT_AUTHORIZED` até G0. **Exceção vigente:** somente Q02-A `AUTHORIZED_FOR_I04_ONLY` pela seção 0, Q01/Q02-B/C/Q03 continuam bloqueados; ADR58 `ARCHITECTURE_DIRECTION=APPROVED` não concede `I04_ACCEPTED`.
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
