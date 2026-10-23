# 128 — Revisão de produto: inteligência reutilizável, RPA e capacidades transversais

**Data:** 2026-10-23. **STATUS:** ARCHITECTURE_REVIEW / PLANNED, não implementado. **Produto:** DÉLIA standalone. **Correlação:** plano de modularização [125](./125-orchestration-complete-refactoring-finite-plan.md), estabilização funcional em execução independente. **Sem alteração de fase ou de runtime.**

## 1. Autoridades revalidadas e fatos

16 (sequência), 50 (boundary standalone), 17 (ownership/contratos), 49 (patterns), 51 (baseline), 52 (bootstrap), 21 (estado), 20 (testes), 25 (rastreabilidade), 24 (product spec), 03 (capability model), 60 (interop MCP/A2A) e ledger devem ser reabertos no HEAD de toda execução. Revisão de conteúdo diretamente em 16/17/24/49/50/03/60; docs restantes consultados para baseline de existência/precedência, não certificados como inspeção exaustiva. Nenhuma fonte de chat substitui autoridade.

**PROVEN na documentação:** DÉLIA é inteligência/Policy/Decision/Work/orquestração; Automation Hub é owner semântico de execução técnica (17 §§12–13, 24 §11, 49 §19); Domain API é autoridade de negócio; Core é RBAC/approval; Keycloak identidade; MCP/A2A interoperability não authority (60); planner consome capability semântica, não RPA clicks, selectors, packages ou operationId (03/17/49); executor preferido API oficial→integração nativa→função determinística→RPA→computer-use governado→Human Task (24). Repeating Work e scheduling (24 §11.1; CP-311–316) são TARGET; execution runtime físico do Automation Hub é `TO_INVENTORY/DEFERRED`, não declarar PROVEN. AI Control Tower e Process Intelligence são previsões de produto, não autorização para segundo planner/estado de execução.

## 2. Questão arquitetural

A modularização do `orchestration.py` só estará preparada para o produto futuro se separar capacidades de Application da interface conversacional, de providers e de mecanismos técnicos. Reutilização deve ocorrer dentro da DÉLIA por módulos coesos e para outros bounded contexts **somente por contratos externos autorizados**. `Chat/MFE`, `Recurring Work`, `Event-driven Watch` e consumidores corporativos são potenciais entrypoints; não devem importar implementação privada do orchestrator, contornar Core/domain AuthZ nem ler DB da DÉLIA.

## 3. Capability portfolio e ownership

| Capability / família | Owner canônico | Estado documental | Consumer potencial / regra |
|---|---|---|---|
| Contextualização, goal e seleção semântica | DÉLIA Application | existente/planejada por fase, confirmar runtime | conversa, Work, eventos; a proposta LLM nunca vira FACT/permission |
| Capability discovery/projection/registry governado | DÉLIA via contracts, fontes Core/Domain/providers | existente parcialmente; não inventar registry novo | planner/consumers autorizados, fresh source |
| Evidence/provenance/outcome verification | DÉLIA Evidence/Outcome; facts na Domain API | existente parcialmente + TARGET | todos os workflows, status técnico != business outcome |
| Policy/Decision e governança de writes | DÉLIA gates + Core/Domain authority | definido normativamente; fase a revalidar | PREPARE/ACT, revalidar identidade/autorização live |
| Work e ocorrência/continuidade | DÉLIA | TARGET/phase-dependent | chat, schedule, signals; persist intent ≠ permission |
| Automation/RPA technical execution | Automation Hub/executor boundary | TARGET físico TO_INVENTORY | execução de automações sob contrato; sem planner paralelo |
| RPA bot packages, queue/lease/worker/retry técnico | Automation Hub/owner de RPA | TO_INVENTORY | DÉLIA só recebe status/provenance/technical result |
| Recurring Work scheduler mechanics | scheduler legítimo a inventariar | TARGET | occurrences; agenda não concede write |
| MCP tools/A2A agents | providers externos via adapters | integração existente em parte, expansão TARGET | discovery != approval; results untrusted |
| Human Task / governed computer-use | executor owner/sandbox, human owner | TARGET | fallback autorizado, nunca livre sobre OT safety |
| Process Intelligence / Knowledge / predictions | owners por capability conforme produto | TARGET / fase dependente | decisões baseadas em evidência, prediction != FACT |
| AI Control Tower | plano de governança | TARGET | audita modelos, RPAs, execs; não duplica DÉLIA Work |

## 4. Contratos reutilizáveis a priorizar (SEM novos serviços por presunção)

**A. Semantic capability request**: entrada `identityRef`, `consumerRef`, `intent/goal typed`, `contextRef`, `source scope`, `budget`; saída `capabilityRef/version`, evidência da disponibilidade real, `preconditions`, `risk`, limites. Não incluir token em prompt nem permissões inferidas de JWT; Core/domain resolvem direitos efetivos no backend.

**B. Governed decision/prepare**: entrada request tipado + evidenceRefs + constraints + live permission result; saída preparação governada/needs-confirmation/denial + auditRefs. Sem executor side effects. Não criar novo Decision Engine se já existir contrato legítimo.

**C. Execution dispatch**: entrada semântica previamente autorizada + `executionRef/idempotencyKey`, `executor-bound request`, risco, timeout; saída `ACCEPTED/PENDING/TECHNICAL_FAILED/AMBIGUOUS` + correlation. Adaptador para Automation Hub e RPA mechanics fica no boundary legítimo, não no planner.

**D. Outcome verification**: entrada `executionRef`, `expected postcondition`, `authoritative sourceRef`, `provenance`; saída `VERIFIED_SUCCESS|VERIFIED_FAILURE|PENDING|INCONCLUSIVE`. Zero conclusões baseadas só em HTTP 200 ou status 'bot completed'.

**E. Intelligence consumer boundary**: entrypoint autorizado pode pedir observação, contextualização, recomendação, preparação ou ação conforme capabilities e policy vigentes. Contrato external HTTP/event/MCP-like *somente quando consumer/owner comprovado*; não publicar chamadas internas de `orchestration.py` como API pública. Contratos especificam owner, allowed operations, request/response, errors, AuthN/AuthZ, scopes, idempotência, cost/rate/time budgets, provenance, compatibility, observability e revocation. OpenAPI/operationId estável quando apropriado.

Nenhum A–E acima é DTO/endpoint existente comprovado apenas por estar desenhado. Antes de criar interface formal, `EXISTING_EQUIVALENT=YES|NO|TO_INVENTORY`, `REUSE_DECISION=REUSE|EXTEND|NEW`, consumer real, typed contract, stage gates e testes.

## 5. Arquitetura RPA — sequência e ownership

```text
User/Event/Schedule/Approved App
  → DÉLIA goal and capability (semantic, not executor names)
  → Live Core authorization + Domain rules/authority
  → DÉLIA Evidence + Policy/Decision (PREPARE/ACT)
  → DÉLIA Work orchestration and governed action binding
  → adapter contract to Automation Hub (when technical automation necessary)
  → approved RPA/Script/Computer-Use worker (sandboxed/identity bounded)
  → technical execution result (NOT business fact)
  → DÉLIA OutcomeVerifier queries authoritative Domain API
  → notification and learning candidate (never auto truth)
```

Para cada automation declarar: owner de bot/package/queue, consent/credential isolation, per-run idempotency, timeout/retry, ambiguous side-effect handling, cancel/rollback/escalation, approved allowlist, cost/rate, telemetry, authoritative postcondition. A execução RPA de produção não é automaticamente autorizada por este documento. API oficial sempre preferida se atende o contrato.

## 6. Reuso por aplicações externas — separação de superfícies

1. **Internal module reuse na DÉLIA**: capacidades puras compartilhadas entre conversa, Work, Watch, tasks; não criar `DeliaIntelligenceService` monolítico.
2. **External authorized composition**: outro aplicativo chama API/evento *oficial* exposto pelo owner DÉLIA somente após validação de consumers, RBAC, tenant/context, data minimization, idempotency e version compatibility. Alternativamente usar provider existente MCP/A2A quando contrato/semântica/segurança forem adequados; nunca é permission bridge.
3. **Shared DELPI platform capabilities**: se capability já pertence a Domain API/Core/Automation Hub/shared components, não migrar para DÉLIA como owner global. DÉLIA orquestra; demais aplicativos acessam o owner real e DÉLIA só para inteligência governada onde apropriado.
4. **No private import/DB sharing** entre bounded contexts. Package compartilhado só para contratos pure/DTO com version/consumers reais, nunca runtime da DÉLIA clonado ou Chat engine reutilizado.

## 7. Impacto obrigatório no plano 125

Adicionar ao gate R0 (quando liberado): matriz `ENTRYPOINT → APPLICATION CAPABILITY → OWNER → CONTRACT → CONSUMERS → EXECUTION BOUNDARY → OUTCOME VERIFIER`, cobrindo pelo menos conversa, Work recorrente, evento, app externo, RPA e Human Task como **cenários de desenho**, não implementações declaradas. Identificar call-sites conversacionais que usam diretamente rendering/turn context e separar context adapter das capacidades puras só se equivalente/consumer legítimo. Provar que trocar RPA→API não muda planner/capability semântica. Não criar Hub/worker/client no refactor R0–R7; trabalho RPA exige contrato/ADR/phase próprio.

## 8. Critérios de aceite futuros

- AC-CROSS-01: mesma capability semântica pode ser usada de entrada distinta com contexto/identidade governados, sem lógica duplicada e sem converter permissões em estado cached.
- AC-CROSS-02: adapter trocável (RPA→API) preserva goal, Policy/Decision e outcome contract.
- AC-CROSS-03: provas negativas de permission denial/expired consent/side effect ambiguous/timeout/retry/idempotency; fail-closed material.
- AC-CROSS-04: status bot success não promove business Outcome sem Domain postcondition.
- AC-CROSS-05: source owner/consumer/contract para cada módulo compartilhado; import DAG acíclico; ausência de God Service.
- AC-CROSS-06: apps externas não importam o runtime DÉLIA e não recebem bearer/secrets/model internals.
- AC-CROSS-07: nenhum mecanismo de RPA executa PLC/CNC/OT commands livremente; safety industrial separado.
- AC-CROSS-08: capability phases e CP/RQ do HEAD preservados; `TARGET` não reportado como `PROVEN`.

## 9. Próxima decisão

**PLANNED/NO_IMPLEMENTATION.** Antes de expandir o plano de refactor 125, coordenação revisa esta matriz com latest 16+ledger e aprova somente extensão documental da baseline R0. A estabilização funcional em execução permanece separada. RPA runtime, provider/connector, interfaces cross-app e scheduler não são criados por esta revisão. Quando houver consumer e contrato legítimos, solicitar task bounded própria por boundary.


## 10. Contrato de implementação e riscos de reuso cross-app

A aplicação das diretrizes de reuso e RPA desta revisão fica vinculada ao [protocolo 129](./129-refactor-implementation-conformance-and-antipattern-gates.md) e à [seção 13 do plano 125](./125-orchestration-complete-refactoring-finite-plan.md). São constraints de revisão, **não autorização para criar runtime/serviço RPA, API/evento, Work scheduler ou registrar uma capability TARGET como PROVEN**.

Toda proposta futura de compartilhamento registra ENTRYPOINT → CAPABILITY → OWNER → CONTRACT → EXECUTION BOUNDARY → OUTCOME e prova consumidor real. Reuso interno usa application contracts sem dependência de ConversationTurn, Markdown ou MFE. Reuso entre aplicativos se faz por HTTP/event com AuthN/AuthZ/versioning aprovado, nunca por imports internos ou banco de outra aplicação. Shared/ corporativo exige 2+ consumidores reais e API estável, conforme platform-architecture-boundaries.mdc.

Bloqueadores específicos: DÉLIA como gateway universal; DÉLIA executar bots/schedulers/workers; Automation Hub virar segundo planner; RPA DONE como outcome empresarial; write sem live Core+Domain authority; side-effect retry cego; metadata MCP/A2A autorizar ou instruir; LLM/Work/Watch executar ACT indevido, OT/Safety sem gate industrial. Em conflito com authorities/decision frozen, STOP → ARCHITECTURE_DECISION_REQUIRED. Testes sentinela e matriz AP-01…AP-20 são os do protocolo 129.

**Estado preservado:** revisão arquitetural PLANNED, implementação cross-app/RPA TARGET/TO_INVENTORY conforme owners; R0–R7 não iniciados nem autorizados por esta referência.
