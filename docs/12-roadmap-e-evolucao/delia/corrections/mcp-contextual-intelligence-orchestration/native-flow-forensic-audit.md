# Auditoria forense — fluxo nativo Pydantic AI vs mecanismos locais

TASK_ID: DELIA-C3-PYDANTIC-AI-NATIVE-FLOW-FORENSIC-AUDIT-01
BASE_HEAD: 28ffd610ac7575194eec1808bb9085de9c061d0d
FUNCTIONAL_CODE_CHANGED: NO | REAL_MODEL_CALLS: 0

## Matriz de responsabilidades (pydantic_ai_investigation.py)

| Componente | Linha | Classificação | Decisão |
|---|---|---|---|
| build_openai_compatible_investigation_model | 90 | ADAPTER_REQUIRED (provider config) | KEEP |
| _build_native_mcp_toolset | 174 | ADAPTER (native MCPToolset por grupo) | KEEP |
| _EnvelopeHintedToolset | 189 | POTENTIAL_DUPLICATION — hint de envelope p/ tools planas; utilidade não comprovada | TO_INVENTORY |
| InvestigationDeps | 261 | NATIVE deps (usa mecanismo do framework) | KEEP |
| _bounded_json | 295 | LEGITIMATE_DELIA (sanitização bounded) | KEEP |
| _declared_container_only | 364 | guard tipos declarados (proven) | KEEP |
| _attempt_projection | 377 | LEGITIMATE_DELIA — projeção governada (evidence_citable, sanitização, observações) | KEEP |
| uncovered_user_identifiers | 511 | LEGITIMATE_DELIA (coverage empresarial) | KEEP |
| focus_arguments_on_next_identifier | 532 | ADAPTER (binding query) | KEEP |
| _invocation_fingerprint + non_progress_calls | 578 | anti-loop fingerprint — SEM equivalente nativo | KEEP/EXTEND (decisão pendente) |
| _prior_message_history | 619 | usa message_history nativo | KEEP |
| _trim_overflow + ProcessHistory | 1571 | usa ProcessHistory nativo; política local de trim | KEEP |
| _governed_invoke | 1035 | ADAPTER_REQUIRED — ponte única tool→gates governados | KEEP |
| _governed_mcp_hook | 1340 | REQUIRED — process_tool_call nativo delegando à governança | KEEP |
| declare_investigation_goal / compose / request_clarification | 1255/1438/1487 | LEGITIMATE_DELIA (ferramentas de governança) | KEEP |
| output_validator _investigation_answer_shape | 1593 | native output_validator + ModelRetry bounded | KEEP |

## Veredictos

INFORMATION_LOSS: NOT_PROVEN (task anterior — projeção completa)
LOCAL_SEMANTIC_INTERFERENCE: NOT_PROVEN — nenhum componente
  seleciona tool, filtra capabilities sem governança, reescreve args
  além do binding documentado, nem executa retry paralelo.
B1 (H4): limitação do MODELO — confirmada; nenhum código local
  impediu a estratégia correta.

NO_LOCAL_REDUNDANCY_PROVEN para a causal B1.
Único candidato a simplificação: _EnvelopeHintedToolset
  (TO_INVENTORY — remover requer prova de que hints não afetam o
  modelo; não demonstrado nesta task).

FILES_TO_KEEP: todos exceto _EnvelopeHintedToolset (inventário)
FILES_TO_REMOVE: nenhum comprovado
