# I00 — Aceite independente da baseline de contexto conversacional e conhecimento MCP

**DATA:** 2026-10-17  
**TRACK:** `DELIA-C3-MCP-CONTEXTUAL-INTELLIGENCE-AND-ORCHESTRATOR-QUALITY-01`  
**REVIEWED_HEAD:** `ef8d555100a79d1aa926232d9df9ef8f81d4f7d5`  
**VERDICT:** `ACCEPT_WITH_RESIDUAL` **somente para revisão e baseline I00**; não implica aceite funcional de K2 nem autorização de I01.

## Escopo e evidências

Revisão remota read-only no GitHub de [44 — avaliação K1–K4](../conversational-intelligence-c3/44-specialist-knowledge-utilization-eval.md), `plugins/delia/src/App.tsx`, `plugins/delia/src/api/interactionClient.ts`, `delia-api/app/interfaces/http/interaction_routes.py`, `delia-api/app/application/interaction/handle_interactive_turn.py`, `delia-api/app/application/model_invocation/contracts.py` e `delia-api/app/application/capability_provision/orchestration.py`. Sem SSH, reexecução do modelo, testes, deploy ou alteração de runtime nesta revisão.

**Caminho factual de contexto:**
- Frontend: `App.tsx` mantém `turns` em React `useState`, chama `buildInteractionContext(turns)` antes de `submitInteractionTurn`; guarda também `provenance`, `groundingStatus` e `presentation` na UI, mas não os envia como referências estruturadas ao construir `context`.
- Cliente: `buildInteractionContext` seleciona pares recentes `USER_INPUT/DELIA_RESULT` de `content` e `epistemic_class`, com teto agregado de 16.384 caracteres; janela recente sem sumarização.
- Backend HTTP: `_parse_context` valida apenas `kind`, `content`, `epistemic_class`; conteúdo vindo do cliente é dado não confiável.
- Application: `HandleInteractiveTurn._validate_prior_context` valida alternância, classe epistemológica e orçamento, cria uma `InteractionSession` **request-scoped** e passa `prior_turns` ao orquestrador. Contrato `ConversationContextTurn` não transporta EvidenceRef/SourceRef/EntityRef/autorização.
- Orquestrador: possui `_understand_goal`, `_prior_continuation_attempt`, `_synthesize_content` e `_resolve_missing_inputs`; continuidade pode reutilizar apresentação anterior, mas jamais qualifica resultado passado como novo FACT ou AuthZ.

**Avaliação K1–K4 (executor-reported, não reexecutada):** K1 TÉO `PASS_WITH_LIMITATION` (guia consultado, síntese `skip_budget`); K2 TÉO `FAIL` (`prior_evidence_sufficient=false`, reconsulta, replay literal e 30014ms); K3 VISTA `PASS_WITH_LIMITATION` (guia consultado e resposta bruta/truncada); K4 DAVI `PASS_WITH_LIMITATION` (discovery legítimo sem candidata compatível). ACT material reportado=0.

## Decisão e limites

- `I00_REVIEW=ACCEPT_WITH_RESIDUAL`; `I00_BASELINE_COMPLETE=YES` para os arquivos inspecionados.
- `FRONTEND_TRANSIENT_TURN_STATE=PROVEN`; `CLIENT_CONTEXT_PROPAGATION=PROVEN`; `BACKEND_CONTEXT_VALIDATION=PROVEN`; `BACKEND_INTERACTION_SESSION_PERSISTENCE=NO_IN_EXAMINED_FLOW`.
- `STRUCTURED_MCP_KNOWLEDGE_CONTEXT=NOT_IMPLEMENTED_IN_EXAMINED_CONTEXT_CONTRACT`. Não extrapolar para todo subsistema de retenção/persistência da plataforma: `OTHER_STORAGE=TO_INVENTORY`.
- A falha K2 é `PROVEN` pela avaliação reportada, mas o efeito causal exato da perda de payload estruturado permanece `TO_INVENTORY`; não atribuir automaticamente o erro a isso.
- `EXISTING_EQUIVALENT=YES` (mecanismos existentes de goal/continuity/synthesis); `REUSE_DECISION=EXTEND_CANDIDATE`, condicionado ao contrato/CP-RQ e prova RED antes de implementação.
- Não criar memória global de MCP, cópia de base de conhecimento, segundo orquestrador ou persistência sem autoridade documental.
- Preservar `GLOBAL_TURN_BUDGET_SECONDS=30`, `MODEL_AUTHORED_FACTUAL_PROSE=NONE`, `GUIDANCE != DOMAIN_FACT`, `PRIOR_CONTEXT != AUTHZ`, `MESSAGE != ACT`.

```text
I00_INDEPENDENT_REVIEW=ACCEPT_WITH_RESIDUAL
I00_BASELINE_COMPLETE=YES
I01_STATUS=PLANNED_NOT_AUTHORIZED
NEXT=I01_CONTRACT_AND_BOUNDED_IMPLEMENTATION_GATE
C3_EXECUTED=NO
C4_AUTHORIZED=NO
C5_AUTHORIZED=NO
PRODUCTION_READINESS=NOT_PROVEN
```
