# Minha DELPI Copilot — Migração de Agents para Expertise

**Status:** `SUPERSEDED / REFERENCE_ONLY`  
**Order authority:** [`16-execution-master-plan.md`](./16-execution-master-plan.md)  
**Standalone boundary:** [`50-standalone-copilot-application-architecture.md`](./50-standalone-copilot-application-architecture.md)

## Decisão atual

Este documento descrevia uma estratégia antiga em que o Copilot seria obtido por evolução/migração do Minha DELPI Chat e de seu modelo de agents.

Essa estratégia foi **substituída**.

O Copilot atual:

```text
não migra AgentSpecializationService
não migra ChatWorkspaceAgentActivationService
não migra ChatSoftAgentHandoffService
não migra ChatSkillRegistry
não migra agent_id/chat_mode/sessions do Chat
não faz cutover do Chat
```

A nova aplicação implementa nativamente:

```text
single Copilot runtime
+ Expertise Packs
+ Domain Playbooks
+ Capability Projection
+ Knowledge/Multimodal
+ Copilot-owned conversations/work state
```

## Relação com o Minha DELPI Chat

Chat permanece produto separado. Qualquer modernização dos agents atuais pertence ao roadmap próprio do Chat e não bloqueia esta iniciativa.

O Copilot pode estudar o Chat durante `C0.S0` para:

- identificar anti-patterns;
- comparar UX/flows;
- reconhecer libraries realmente neutras;
- evitar repetir bugs/acoplamentos.

Isso não autoriza dependência de runtime.

## Requisitos históricos

Os requisitos relacionados foram preservados em `25-requirements-traceability.md` como:

```text
CP-080 OUT_OF_SCOPE_WITH_DECISION
CP-081 OUT_OF_SCOPE_WITH_DECISION
CP-082 OUT_OF_SCOPE_WITH_DECISION
CP-085 OUT_OF_SCOPE_WITH_DECISION
```

Os IDs não são apagados nem reutilizados.

## Conceito ainda válido

A decisão conceitual de **um Copilot + expertise componível**, em vez de agentes departamentais, continua válida. A implementação está especificada em `27`, `28`, `29`, `33` e nas fases C3/C6 do Plano Mestre.

## Regra

Nenhum Cursor/implementador deve usar este arquivo para executar migration/cutover. Ele existe somente para explicar por que referências antigas a agents do Chat podem aparecer no histórico da documentação.