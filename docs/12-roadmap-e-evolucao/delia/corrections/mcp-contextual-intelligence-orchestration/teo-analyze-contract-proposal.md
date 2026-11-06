# Proposta contratual — TÉO analyze (aguardando aprovação do owner)

TASK_ID: DELIA-C3-TEO-ANALYZE-CONTRACT-CLARIFICATION-AND-B2-VALIDATION-01
BASE_HEAD: 8c69509340b9c97f23231c534fce318b690e1270
OWNER: TÉO (transformometro-api) | CONSUMER: DÉLIA via MCP

## Fase A — matriz de requisitos (comprovada no código)

`dashboard_view_scope_service.py:61-95` — resolver de escopo analítico:

| Escopo (view) | Obrigatório | Proibido | Erro runtime |
|---|---|---|---|
| consolidated (default) | — | — | — |
| filial | filial_id | setor_id | "visão filial exige filial_id" |
| department | filial_id + setor_id | — | "visão departamento exige filial_id e setor_id" |

Views nominais do analyze (server.py:131-151): snapshot meta|summary|
processes|instances|rows; dashboard_*; processo-scoped (processo_id);
revision-scoped (revisao_id); impact_effort_matrix (3 ids aceitos);
meeting_minute_transcript (minute_id). Descrição atual lista nomes mas
NÃO declara o requisito filial+setor do escopo department — PROVEN_GAP.

## Fase B — proposta mínima (texto, sem schema/assinatura)

Acrescentar à descrição publicada (server.py:134-151), após o trecho de
snapshot views, uma linha de escopo:

"Scope resolution: consolidated (default, sem ids) | filial exige
filial_id e rejeita setor_id | departamento exige filial_id e setor_id.
Scoped views exigem o id correspondente."

Compatibilidade: texto apenas, zero impacto; consumidores: DÉLIA/agentes.

## Fase C — schema condicional

inputSchema é gerado pela assinatura FastMCP (todos filtros Optional) —
if/then/oneOf exigiria schema manual fora do gerador; suporte do
provider a conditional schemas é incerto. SCHEMA_CONDITIONAL =
UNSUPPORTED na cadeia atual → descrição é o canal correto e mínimo.

## Fase D — GATE DE APROVAÇÃO

CONTRACT_CHANGE_PROPOSAL:
  OWNER: TÉO | CAPABILITY: analyze
  CHANGE: descrição apenas; SCHEMA_CHANGE: NO; BACKWARD_COMPAT: total
  ROLLBACK: revert do texto
  OWNER_APPROVAL: PENDING — mecanismo verificável indisponível

STATUS: ARCHITECTURE_DECISION_REQUIRED — implementação bloqueada
até aprovação explícita do owner TÉO. Nenhuma alteração funcional.
