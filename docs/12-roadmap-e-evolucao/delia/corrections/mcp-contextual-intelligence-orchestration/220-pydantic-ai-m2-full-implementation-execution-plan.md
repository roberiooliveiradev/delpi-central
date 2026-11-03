# DÉLIA — M2 Full Implementation: Pydantic AI Unified Intelligence Runtime

**TASK_ID:** `DELIA-C3-PYDANTIC-AI-UNIFIED-RUNTIME-M2-FULL-IMPLEMENTATION-01`  
**STATE:** AUTHORIZED_FOR_IMPLEMENTATION (coordenação; não é aceite da implementação).  
**Owner:** DÉLIA Application (contratos/gates) + Infrastructure (Pydantic AI adapter). **Executor:** Devin.  
**Reference:** M1 doc 219, commit `d78ecb763c`. HEAD de referência na leitura: `301f9cbead46c6c53005b627e45f8e57c746e322`; revalidar `origin/main`, worktree e authorities antes de agir.  
**Scope:** M2 **integral** (todos os estágios de inferência aprovados), não apenas admission. Implementar, integrar e provar em código; sem nova fase preparatória de inventário.  
**No production deploy, no production cutover, no M5 removal:** M2 prepara o caminho Pydantic AI plenamente funcional e isolado para M3 de paridade e M4 cutover, sem dois planners públicos em produção.

## 0. Decisão e hierarquia de autoridade

O usuário aprovou substituir mecanismos concorrentes de IA pela infraestrutura Pydantic AI. M1 foi aceito com residuais **não bloqueantes**; não criar M1.1, novo inventário, nova task de readiness ou pedir autorização intermediária para mudanças técnicas bounded. O plano CRI-semantic `33bed6a3` está **subsumido** pela migração, não revogado silenciosamente; suas invariantes permanecem. Toda execução reancora: HEAD/status/origin, Project Instructions/.cursor, documentos 16→50→17→49→51→52→21→20→25, arquitetura técnica, product spec, specs IA/CRI/MCP, ledger, doc 219. Identificar fase/NEXT/CP/RQ no HEAD. Conflito com autoridade superior ou owner legítimo: STOP `ARCHITECTURE_DECISION_REQUIRED` ou `EXECUTION_DRIFT` no trecho afetado; continuar partes independentes seguras.

## 1. Resultado implementável exigido de M2

Construir **um caminho Pydantic AI integrado e exercitável** para todas as propostas de modelo atualmente feitas por outros mecanismos, atrás dos ports/contratos existentes, com testes RED→GREEN e eval real, sem modificar a autoridade de domínio:

1. Admission e interpretação do objetivo (`interaction_class`, `owner_required`, incerteza).
2. Seleção semântica do grupo elegível (model proposal, allowed groups e validação).
3. Target/capability selection e resolução de ambiguidade (model proposal, revalidação).
4. Argument generation via `pydantic_arggen` existente (reusar provider/model setup; preservar schema e validação final).
5. Continuidade investigativa e recovery **apenas da inferência**: propostas tipadas para next step, bounded clarification, resolver, fanout etc. Estado, limites, dedup, deadlines, gating e subobjectives persistem na Application.
6. Interpretação/síntese comunicativa semântica para CRI via proposal ancorada a `EvidenceFacts`/`OutcomeVerdict`; fatos e formatação definitiva seguem determinísticos.
7. Compatibilidade da sequência oficial com caminhos alternativos existentes, sem iniciar segundo planner/graph. LangGraph antigo apenas baseline/rollback até M3–M5; **não criar Agent livre que execute MCP**.

**Abstraction gate, por stage:** `EXISTING_EQUIVALENT=YES|NO|TO_INVENTORY`, `REUSE_DECISION=REUSE|EXTEND|NEW`. M1 comprova infraestrutura arggen existente; estender capacidades por ports coesos, não sobrecarregar `pydantic_arggen.py` monoliticamente. NEW só para gap real, com contrato e owner, nunca engine/registry paralelo.

## 2. Ownership e separação estrita

- Keycloak identidade; Core RBAC/AuthZ live; Domain APIs dados/regras/autoridade; MCP/A2A interop untrusted; Automation Hub execução técnica; DÉLIA Application coordena capabilities/Policy/Decision/Work/Evidence/Outcome.
- `pydantic_ai`, clients, SDK e prompts/provider mechanics **apenas em Infrastructure**. Domain/Application usam ports/DTOs neutros e validações próprias, sem imports framework/DB/HTTP.
- Modelo **propõe**, nunca autoriza; output != FACT; metadata, tool result e prompt de provider são dados não confiáveis.
- Writes materiais: identity → Core AuthZ → Domain authority → capability → Policy/Decision → confirmação → idempotência → audit → execution → authoritative postcondition; READ≠WRITE; PREPARE≠ACT; simulate≠apply.
- Nunca expor tokens, candidate_tokens, JWT ou segredos no prompt, logs/telemetria, frontend ou evidence cache. `candidate_token` é encadeado por contrato governado, não escolhido livremente pelo modelo.
- Manter FAST e OPERATIONAL sem chamada LLM desnecessária. Deadline, budget, cancelamento e erro honesto.

## 3. Contratos e integração por estágio (M1 doc 219)

Registrar em código e testes interfaces neutras para:
- `AdmissionProposal`: classificação permitida/none, `owner_required`, unknown/clarification; output validado/rejeitado, sem reclassificar acesso.
- `CapabilityGroupProposal`: referência exata ao grupo do catálogo **elegível atual**, ou abstain; validação determinística.
- `TargetProposal`: referência exata à capability aprovada da seleção, ou abstain; revalidação contra fresh projection, sem provider branch.
- `ArgumentsProposal`: schema-bounded args usando implementação Pydantic AI existente; validação final `_validate_instance`; preserve strings e campos obrigatórios; argumentos não são permissão.
- `ContinuationProposal`: objetivo/subobjetivo/next-semantic-capability/clarify por contexto autorizado; a aplicação mantém progress, replay, limits e outcome.
- `CommunicationProposal`: intenção comunicativa/proposta de introdução opcional + refs existentes; nenhuma contagem/fato novo; limitações, partiality, owner provenance e texto empresarial permanecem controlados por Evidence/Outcome e renderer.

Os nomes acima são **formas conceituais**, não autorização para criar classes duplicadas. Primeiro procurar contratos equivalentes; se houver, estender e demonstrar. Cada output inválido, ausente, alucinado ou fora da allowlist deve produzir fallback bounded, não execução livre nem transformação em FACT. Estado de comunicação não deve inventar shapes/owners/quantity.

## 4. Código e remoção planejada

Inspecionar imports/consumers reais dos pontos já conhecidos:
- `delia-api/app/application/capability_provision/orchestration.py`
- `delia-api/app/infrastructure/arggen/pydantic_arggen.py`
- `delia-api/app/application/capability_provision/outcome_assessment.py`
- `delia-api/app/application/capability_provision/conversational_response.py`
- `delia-api/app/application/capability_provision/generic_evidence_renderer.py`
- `langgraph_engine` e entrypoints/config do engine identificados no HEAD.
- tests `test_unified_evidence_presentation.py`, `test_cri_unified_presentation.py`, `test_cri_e3_conversational_presentation.py`, `test_c3_*`.

Migrar as inferências hand-rolled (como `_propose`) para o adapter Pydantic AI por extensão dos ports existentes, **sem reescrever os gates do orchestrator**. Reutilizar model/provider factory quando comprovada. Não assumir API de biblioteca sem verificar versão instalada e docs correspondentes. Propostas tipadas são validadas em Application antes de qualquer chamada real; modelo não invoca actions diretamente.

Se LangGraph participa apenas de sequenciamento operacional, substituir a parte de inferência, **não** mover governança ou estados duráveis para Pydantic AI. Marcar exatamente os pontos substituíveis no mapa M5. **Não remover a versão legada no M2**; preservar rollback temporário isolado, sem ambos executarem writes ou responderem simultaneamente.

## 5. Execução contínua por blocos (não etapas burocráticas)

**M2-A Admission** — RED contrato atual → implementar adapter tipado → GREEN em conversation, surface inquiry, operational, ambiguous, none, failures; preservar deadline e guard.

**M2-B Selection** — RED group/target com catálogos dinâmicos e authorized projection → adapter tipado → GREEN; casos unknown owner, no candidate, prompt injection em metadata, fresh revalidation.

**M2-C Args e provider-neutral** — integrar `pydantic_arggen` ao caminho novo sem duplicar provider client. Testar schema nested, enum, required, string codes com zeros à esquerda, malformed model output, tokens opacos, discover→execute, schema drift e retries bounded.

**M2-D Continuity/recovery** — adapter de proposta somente, conservar Application state/logic; RED→GREEN para multi-step, resolver, fanout, dedup, clarification, context truncation, deadline, no infinite loop, write gating.

**M2-E CRI semantic** — conservar `compose_cri_response`, `generic_evidence_renderer`, `OutcomeVerdict`, vocab v7, `structure_found` e isolamento de metadata; proposta contextual só se informação não obtida de stage existente; zero chamada extra por default. RED→GREEN para hierarquia raiz+2PI+4MP com MP repetida, `90260921`, coleções, comparação, insuficiência, partial, empty legítimo vs owner error. Não codificar por produto ou provider.

**M2-F End-to-end integration** — um único caminho selecionável por **configuração de rollout local/teste** usando ports existentes, não dois planners ativos na mesma requisição. Testes completos de orquestração, tool adapters, streaming/API, frontend contract e regressões. Recuperação de provider 4xx/5xx/timeout não pode virar coleção vazia artificial; não mexer no owner api-delpi fora desta task.

Cada bloco deve concluir implementação e testes no mesmo trabalho M2, salvo STOP material. Não fazer outro inventário/review intermediário apenas por falta de dados de benchmark; medir durante implementação.

## 6. Evals e critérios de aceitação

### Contratos/funcional
- Admission, group/target, args, continuity, CRI com testes RED→GREEN e comparação ao M1.
- Sem regressão de segurança, autorização, evidência, provenance e execução.
- Unknown/new capability: catálogo dinâmico, sem branches de provider. DAVI discovery→execute `get_product_structure` via `candidate_token` encadeado; TÉO/VISTA e outros owners autorizados quando realmente disponíveis.
- Estrutura `90260148` (root+2PI+4MP e ocorrências repetidas), `90260921`, `90260147`, `90260862`; casos de regressão, **não regras**. Separar dados de fixture e E2E real com identidade autorizada.
- Texto técnico `entity/shape/has_more` não vira fato de negócio; `root` preservado; sem cardinalidade universal enganosa.
- Failure/status != empty; technical success != business outcome.

### Generalization + adversarial
- Definir **antes do tuning** pelo menos três holdouts independentes cobrindo owners/shapes/objetivos distintos, além de cenários unknown/novel.
- Prompt injection em MCP metadata, descriptions, response payload, Markdown; AuthZ deny; PREPARE/ACT sem confirmação; invalid tokens; timeout, provider 402/5xx; mixed query/multiturn; incomplete evidence.
- Teste de output estruturado incorreto/adversarial, revalidation fail-closed, no secrets.
- Não considerar GREEN de mocks como business outcome.

### Performance/observability
- Medir por SHA/model/provider/config: total e por stage chamadas LLM, input/output tokens efetivos, latência p50/p95 quando amostra permitir, falhas, retries, deadline, outcome. Baseline M1 ~7 calls / ~11k input / ~200 output / 15–30s é referência reportada, **não comparador pareado formal**.
- Registre medição com workload idêntico pré/pós quando possível; sem números inventados. Não criar telemetria paralela se instrumentação existente for suficiente.
- Zero chamadas adicionais injustificadas; overhead só se ganho de outcome explicitamente demonstrado.

### Gates de status
- `PASS` somente com execução/evidência no SHA/config.
- `TEST_NOT_RUN` quando identidade/infra indisponível; `INCONCLUSIVE` quando não há comparabilidade.
- Se E2E empresarial real não for possível, implementar e testar M2 localmente e registrar impedimento em M3/M4; **não travar M2 por ausência de conta do usuário**, mas não declarar E2E PASS.
- Segurança crítica ou quebra de contract: `FAIL` e STOP na promoção.
- M2 não inclui produção, M4 cutover, M5 legacy removal. Flags locais de isolamento/rollback não autorizam produção.

## 7. Não objetivos e STOP

NÃO criar novo agent executor MCP com tools livres; segunda fonte de AuthZ; nova capability/registry/graph/engine paralela; import de API externa entre bounded contexts; dependência de tabelas Minha DELPI Chat; lógica lexicográfica específica de BOM; revisão de Remark; mudança de api-delpi SQL timeout; adaptação do planner a endpoint/click; ACT por comando livre de IA/OT.

Se conflito de autoridade/decisão congelada, schema incompatível com owner, mudança de owner, regresso material de segurança ou rota de write não governada: `EXECUTION_DRIFT` ou `ARCHITECTURE_DECISION_REQUIRED` com evidência e menor escopo seguro. Não redesenhar silenciosamente.

## 8. Done / entrega obrigatória

Para declarar `M2_IMPLEMENTED_PENDING_M3_PARITY`:
1. Todos os estágios M2-A..F integrados no **caminho Pydantic AI isolado**, executáveis, não só planos.
2. RED→GREEN por stage, suites existentes e regressões relevantes.
3. Ports/contracts preservados; Domain/Application sem dependência SDK.
4. Gate de AuthZ/Domain/Policy/Outcome demonstrado; nenhum write disparado por proposal.
5. Generalization + adversarial tests executados no SHA avaliado, lacunas explicitadas.
6. Métricas/model/config/latência/tokens capturados quando disponíveis; sem extrapolação falsa.
7. Listagem residual de runtime legado com consumers e critério de remoção M5.
8. Docs/ledger atualizados com fatos, commits pequenos, push main seguro (sem force-push).
9. Rollback local documentado, prod não alterada.

**Formato de report:** TASK_ID, BASE_SHA, FINAL_SHA, ORIGIN_MAIN, PUSH_VERIFIED, AUTHORITIES_REVALIDATED, PHASE_CP_RQ, EXISTING_EQUIVALENT, REUSE_DECISION, M2_A_B_C_D_E_F_STATUS, CONTRACT_PARITY, MODEL_STAGE_REUSED, PYDANTIC_AI_ADAPTERS, EXTRA_LLM_CALLS, CONFIG_MODEL_PROVIDER, LLM_CALLS_AND_TOKENS_BEFORE_AFTER, LATENCY_BEFORE_AFTER, RED_GREEN, GENERALIZATION_HOLDOUT, SECURITY_NEGATIVE_TESTS, EVIDENCE_OUTCOME_PARITY, LOCAL_RUNTIME_SHA, REAL_E2E, LEGACY_DEPENDENCIES, FILES_CHANGED, TESTS_NOT_RUN, OPEN_RESIDUALS, NEXT_M3_PARITY, PRODUCTION_DEPLOY=NOT_AUTHORIZED, REVIEW_VERDICT=PENDING_INDEPENDENT_REVIEW.

**Mandato:** executar M2 **por inteiro**, sem pedir outra task para começar admission, selection, continuity ou CRI. Os gates são para garantir correção durante a implementação, não para criar inventários infinitos. A coordenação revisará a entrega M2 para autorizar M3.
