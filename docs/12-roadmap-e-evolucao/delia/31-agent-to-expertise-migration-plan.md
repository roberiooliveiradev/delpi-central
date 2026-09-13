# DÉLIA — Histórico de Migração de Agents para Expertise

**Status:** `SUPERSEDED / REFERENCE_ONLY`  
**Order authority:** [`16-execution-master-plan.md`](./16-execution-master-plan.md)  
**Standalone boundary:** [`50-standalone-copilot-application-architecture.md`](./50-standalone-copilot-application-architecture.md)

## Decisão atual

Este documento registra uma estratégia antiga em que o produto seria obtido por evolução/migração do Minha DELPI Chat e de seu modelo de agents.

Essa estratégia foi **substituída**. DÉLIA é aplicação standalone nova.

DÉLIA:

```text
não migra AgentSpecializationService
não migra ChatWorkspaceAgentActivationService
não migra ChatSoftAgentHandoffService
não migra ChatSkillRegistry
não migra agent_id/chat_mode/sessions do Chat
não faz cutover do Chat
```

O target standalone pode implementar nativamente, quando fases/gates permitirem:

```text
single DÉLIA product/runtime identity
+ Expertise Packs
+ Domain Playbooks
+ Capability Projection
+ Knowledge/Multimodal
+ DÉLIA-owned conversation/work state only where ownership is proven
```

Nenhum item acima é evidência de runtime implementado.

## Relação com o Minha DELPI Chat

Chat permanece produto separado. Qualquer modernização dos agents atuais pertence ao roadmap próprio do Chat e não bloqueia DÉLIA.

DÉLIA pode estudar o Chat durante C0.S0 somente para inventory/anti-patterns/reuse neutral comprovado. Isso não autoriza runtime dependency.

## Requisitos históricos

IDs históricos permanecem preservados em `25-requirements-traceability.md`; não apagar/reutilizar IDs.

## Conceito ainda válido

A decisão conceitual de uma DÉLIA com expertise componível, em vez de agentes departamentais user-facing, continua válida. Implementação real segue `16`, `27`, `28`, `29`, `49` e gates aplicáveis.

## Regra

Nenhum implementador deve usar este arquivo para executar migration/cutover. Ele existe somente para explicar referências históricas a agents do Chat.
