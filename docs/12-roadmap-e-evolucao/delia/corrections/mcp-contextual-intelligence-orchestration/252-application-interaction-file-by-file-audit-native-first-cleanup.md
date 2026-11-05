# 252 — DÉLIA · Auditoria integral de application/interaction e limpeza native-first

**TASK_ID:** DELIA-C3-APPLICATION-INTERACTION-FILE-BY-FILE-CLEANUP-01  
**DATE:** 2026-11-05  
**SOURCE_HEAD:** `603d50c0db341af1536d701ba690ab5d4204de22`  
**SCOPE:** `delia-api/app/application/interaction/` — 13/13 arquivos lidos integralmente no SHA via GitHub API  
**STATUS:** AUDIT / PLANNED, no source code modified; TEST_NOT_RUN  
**RELATED:** docs 239–251, especialmente 244–246/249–250; canonical authorities/ledger  
**PRODUCTION_DEPLOY:** NOT_AUTHORIZED.

## 1. Diagnóstico e limites

A pasta implementa o **contrato de interação**, não apenas um motor semântico substituível por Pydantic AI. Há código legítimo de AuthZ context, Evidence lineage, write PREPARE/ACT, argumento com JSON Schema, deadline, progress NDJSON, observabilidade, apresentação e contexto de workspace. Reduzir especificamente lógica semântica residual e duplicações com o Agent nativo, preservando gates e postconditions. `handle_interactive_turn.py` é o maior candidato à redução; `argument_validation.py` deve perder acoplamento a `outcome_assessment.py` quando doc245 for executado.

**EXISTING_EQUIVALENT:** YES para native Pydantic AI `Agent`/typed output, JSON Schema/Pydantic validação de instâncias, contratos existentes de Interaction/SourceRef/Policy, deadlines, observabilidade e bounded pending writes. TO_INVENTORY para equivalência exata JSON Schema do owner, mecanismos de observabilidade reutilizáveis e integração com SDK. **REUSE_DECISION:** REUSE/SHRINK; DELETE apenas lógica/arquivo com consumidores mapeados e substituição provada. Não gerar novo interaction engine, planner, formatter, policy engine ou store.

**Reancoragem obrigatória pré-implementação:** git status/HEAD/origin → Project Instructions/.cursor → docs 16→50→17→49→51→52→21→20→25 → arquitetura/product spec → spec temática → ledger e docs 239–252. Esta auditoria apenas leu código pela API GitHub: status local, authorities integrais, testes e runtime não foram verificados; não declarar prova onde há TO_INVENTORY.

## 2. Matriz arquivo a arquivo (13/13)

| Arquivo | Linhas extraídas | Responsabilidade / símbolos | Direção |
|---|---:|---|---|
| `__init__.py` | 8 | docstring do pacote e boundary Interaction | KEEP; atualizar texto stale se runtime mudou |
| `activity.py` | 346 | `ActivityEvent`, `ActivityEventSink`, estados de progress e NDJSON semantic activity | KEEP/SHRINK: consolidar apenas campos/observation comprovadamente duplicados |
| `argument_validation.py` | 654 | `normalize_arguments`, `apply_evidence_bound_selections`, `validate_arguments`, `validate_untyped_arguments`, `_check_value`, validação bounded de JSON Schema e completude | PRIORITY SHRINK/DECOUPLE; importer de Outcome legado; Pydantic AI não é authorization/owner argument verification |
| `capability_attempt.py` | 253 | `GovernedCapabilityStatus`, `GovernedCapabilityAttempt`, `GovernedCapabilityBinding`, `SupportsGovernedCapabilityAttempt`, tradução segura de estados | KEEP/SHRINK: contrato crítico entre Orchestration e Interaction |
| `contracts.py` | 306 | `InteractiveTurnRequest`, `GovernedCapabilityProvenance`, `VerifiedCompositeEvidence`, `InteractiveTurnResult`, enums/constants do Turn | KEEP; revisar campos antigos CRI apenas após consumers comprovadamente eliminados |
| `errors.py` | 31 | `InteractionError`, códigos semânticos | KEEP; nenhuma economia material |
| `handle_interactive_turn.py` | 1739 | `HandleInteractiveConversationTurn` com `execute`, `_execute_observed`, `_grounded_result`, `_grounded_composite_result`, `_write_lifecycle_result`, `_invoke`, `_validate_result`, `serialize_result` | **MAJOR SHRINK**: retirar redundâncias de resposta/conversa/CRI após migrar native structured output; manter acesso, prior context, binding, evidence, terminal & writes |
| `instruction.py` | 78 | `DELIA_INTERACTION_INSTRUCTION`, `interaction_instruction_lineage` | REVIEW/SHRINK: comparar com instrução canônica do Agent native e lineage; remover instrução paralela somente depois de provar duplicação e consumers |
| `pending_proposals.py` | 142 | `PendingWrite`, `PendingWriteStore`, TTL, digest, atomic take-if-current | KEEP SECURITY-CRITICAL; revisar process-local persistence somente se owner/phase decidir |
| `presentation.py` | 160 | `compose_presentation`, typed allowed interactions, plain vs markdown-safe projection v1/v2 | KEEP/SHRINK; não converter HTML/Markdown bruto em conteúdo trusted |
| `turn_budget.py` | 101 | `TurnDeadline`, `TurnBudgetExhausted`, `remaining_budget` | KEEP; shared monotonic turn deadline, não substituído por timeouts per-call do SDK |
| `turn_observability.py` | 597 | `ModelCallLedger`, `ModelCallObservation`, `OperationalCallObservation`, `aggregate_usage`, `build_turn_observability`, recovery counters | PRIORITY SHRINK/REUSE: tokens/durations reais, não inventados; verificar duplicação com SDK PydanticAI e trace; remover observação de CRI/assessor extintos após consumers |
| `workspace_context.py` | 214 | `WorkspaceContext`, `WorkspaceEntityRef`, `parse_workspace_context` | KEEP; cliente é untrusted context, nunca Core/Domain authorization |

**TOTAL: 4.629 linhas extraídas** (8+346+654+253+306+31+1739+78+142+160+101+597+214). Os maiores módulos somam ~2.990 linhas (`handle_interactive_turn`+`argument_validation`+`turn_observability`). Contar `wc -l` no worktree do executor para baseline formal.

## 3. Achados técnicos e ações de limpeza

### 3.1 handle_interactive_turn.py (1739)

O wrapper de Interaction reúne acesso e turno, classificação de admission, prior context, invocação conversacional por `InvokeModel`, consentimento PREPARE/ACT, projeção de Evidence, reuso de observabilidade, resultado final, serialização. Se a interpretação/produção de resposta for absorvida pelo Pydantic AI nativo docs245/246/249, remover **somente** branches paralelos de inteligência e composição CRI; não cortar `_require_access`, `_validate_input`, `_validate_prior_context`, `_validate_turn_command`, `_validate_execution_ceiling`, `_grounded_result`, `_grounded_composite_result`, `_write_lifecycle_result`, `_emit_terminal`, `_validate_result`, `serialize_result`.

É importador direto de `_comparison_records` em `capability_provision/outcome_assessment.py` (linhas ~44–46); adicionar ao inventário doc245. `_prior_continuation_result`, `_honest_terminal_result`, `_conversational_budget_result`, `_source_terminal_result`, `_invoke`: diferenciar responsabilidade semântica antiga versus fallback legítimo, error handling e budget. Remover duplicações, não TODO equivalente por estética.

### 3.2 argument_validation.py (654)

Valida argumentos **propostos pelo modelo** contra schema real anunciado pelo owner; limita profundidade, número de nodes/keys/items, strings e tamanho JSON; rejeita controle de orquestração do modelo (candidate_token, proposal_handle, confirmation, idempotency_key, commit_now), preserva owner validation como autoridade final. Isso não pode ser delegado ao modelo nem a `output_validator` sem verificação independente. A função `validate_arguments` e `_check_value` implementam bounded subset de JSON Schema. **Candidatos:** simplificar subset com validador JSON Schema/Pydantic já instalado somente após provar equivalência de `anyOf`, defaults owner-declared, `additionalProperties`, size caps, parameter completeness, nested business payloads e forçamento de fail-closed. Não criar novo parser caseiro. `apply_evidence_bound_selections` exige ref verificável, nunca model-supplied source unchecked.

**CRITICAL:** importa `MAX_MISSING_INPUTS`, `_canonical_key`, `_entity_payload_slot`, `_extract_owner_entity_schemas`, `_value_present` de `outcome_assessment.py`; esses consumers faltaram nas matrizes iniciais doc245/246 e devem ser migrados para owner real, sem copiar 600 linhas ou trocar deterministic validation por texto LLM. **Doc245 implementation blocked until this import is corrected.**

### 3.3 turn_observability.py (597)

Registra `ModelInvocationResult` real (usage e duration), chamadas operacionais, timeout, composition, recovery attempt e decision fingerprints. É metadata de execução com limites e `ContextVar` request-scoped, não FACT. Possível sobreposição com telemetria/uso do Pydantic AI: `aggregate_usage` deve conservar os tokens efetivamente reportados por stage, sem contar fallback como medição. `record_composition` atualmente descreve seleção/render CRI e `record_assessment_decision` mantém observações de assessor; revisar se ficam órfãos após doc245. Se SDK nativo já fornece trace/usage, reutilizar apenas com contrato consistente e granularidade necessária para UI, evitando dupla contagem. `model output != FACT`.

### 3.4 activity.py (346)

`ActivityPhase`, `ActivityState`, `ActivityOutcomeStatus`, `ActivityEvent.to_record`, `ActivityEventSink.emit`. Contrato de eventos progressivos requer honestidade de etapas efetivamente executadas, não etapas planejadas; consumidores no orchestration e handler, wire em interfaces HTTP. KEEP; eliminar subclasses/enum alias somente se consumers ausentes. Nunca mover fila/Flask para Application.

### 3.5 capability_attempt.py (253) e contracts.py (306)

São tipados e centrais: `GovernedCapabilityAttempt` representa status/provenance, `VerifiedCompositeEvidence` contém SourceRefs validados e fan-in; `InteractiveTurnResult` é contrato terminal. Doc245 exige output_type do Agent **mapeado para esses contratos**, não status paralelo autoautorizado pelo LLM. `VerifiedCompositeEvidence` requer prova de origem real dos subs, especialmente E4 fan-in; não inventar refs no terminal. KEEP os contracts e remover campos obsoletos apenas após AST consumers.

### 3.6 pending_proposals.py (142)

Back-end-only process-local TTL store de PREPARE→ACT, com lock `RLock`, identity/session-bound digest e `take_if_current` para consumo atômico. Um path WRITE não pode ser removido sob argumento de que o Pydantic AI controla o fluxo. KEEP. Validar autorização final live, idempotency, replay/revoke e limites de memória em testes. Store em memória é contrato atual, não inferir escalabilidade/durabilidade sem roadmap.

### 3.7 presentation.py (160)

Composição determinística da apresentação v1/v2. Monta `blocks` a partir de campos de `InteractiveTurnResult` governados, semantic_kind e allowed_interactions. Marca `markdown_safe` apenas se o renderer governado originou o conteúdo. Pydantic structured output não substitui renderer/projeção para UI; manter fronteira de safe markdown, não reautorizar texto bruto do owner/model.

### 3.8 turn_budget.py (101)

`TurnDeadline.start`, `remaining_seconds`, `stage_timeout`, `check` e `remaining_budget`; controle de deadline total, independente dos timeouts pontuais do PydanticAI/HTTP. KEEP; comparar duplicação com `ModelSettings.timeout` somente como teto redutor, sem perda de prazo total.

### 3.9 workspace_context.py (214)

Parsing e bound de contexto enviado pelo Portal, entidades e contexto de tela. É **UNTRUSTED** e ajuda modelo a resolver demonstrativos, não autoriza capabilities. KEEP. Não promover `grants_authorization` nem workspace identity a Core RBAC.

### 3.10 instruction.py (78)

Texto de instrução e `InstructionLineage` da interação; comparar se é usado para fallback conversacional à parte e instruções de agent Pydantic. Se for duplicação após doc245/249, retirar com owner legítimo e hash/lineage preservados; não eliminar governança do prompt.

### 3.11 errors.py (31) e __init__.py (8)

KEEP; classes/contrato pequenos e sem duplicação identificada.

## 4. Dependências, testes e execução

**PROVEN imports**: `handle_interactive_turn.py` e `argument_validation.py` importam `capability_provision/outcome_assessment.py`; `capability_attempt.py` depende de capability contracts, Activity, Deadline e Workspace; `contracts.py` incorpora SourceRef/EpistemicClass e Workspace. `orchestration.py` importa múltiplos módulos interaction e o handler é composto em `root_composer.py`. Os arquivos 13/13 foram lidos no HEAD GitHub. A lista de consumers é parcial e exige `rg`/AST global.

**TO_INVENTORY:** status local, documentação superior e ledger, todos os consumers transitivos/dinâmicos, código efetivamente exercitado por admission/CRI e native Agent, import graph, testes por fase e eval E01–E10.

**TEST_NOT_RUN:** nenhuma suíte, integration/NDJSON, security ou E2E executada nesta auditoria.

**IMPLEMENTATION ORDER:**
1. Reanchor autoridade completa e checar se documentos 244–251 já tiveram implementação no novo HEAD.
2. Symbol callgraph e imports de cada arquivo, negative tests para Core AuthZ, owner evidence, malformed input, replay, PREPARE/ACT e fenced outputs.
3. Migrar os consumidores de `outcome_assessment.py` (handler + argument validation) junto doc245; usar native `output_type` tipado e validator para decisões semânticas, não permitir self-certified FACT.
4. Unificar branching de respostas no Agent nativo; reduzir `handle_interactive_turn.py` sem eliminar terminal serialization/interaction/policy. Revisar old CRI instruction, presentation e observability.
5. Avaliar JSON Schema nativo para argument validation somente com paridade e security tests; sem introduzir abstração/engine adicional.
6. Revisar observability/usage e Activity: evitar duplicação de contagem e estados de progress fabricados; preservar user-facing NDJSON.
7. Executar suíte inteira, eval local E01–E10 e provas de fan-in SourceRefs, partial/completeness, no false-grounded, cancellation, retries, model timeout, AuthZ, write gates e idempotency.
8. Residual search, contar LOC before/after, documentar status, SHA/config/evidence/owner/contracts, atualizar docs 245/246/249/250/252 e ledger, commit/rebase/push main, no production deploy.

**Review:** KEEP/SHRINK dos bounded contracts. Não há evidência para deletar a pasta inteira. Priorizar `handle_interactive_turn.py`, `argument_validation.py`, `turn_observability.py`. Confirmação de remoção física requer teste e runtime; esta é documentação-only, não código alterado.
