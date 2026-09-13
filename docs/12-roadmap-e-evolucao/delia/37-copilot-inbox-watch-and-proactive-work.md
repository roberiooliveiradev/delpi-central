# DÉLIA — Inbox, Watch e Trabalho Proativo

**Status:** thematic spec  
**Order authority:** [`16-execution-master-plan.md`](./16-execution-master-plan.md)  
**Standalone boundary:** [`50-standalone-copilot-application-architecture.md`](./50-standalone-copilot-application-architecture.md)  
**Foundation:** `EventEnvelope` é TARGET a congelar em C0; Durable Workflow em C5 após gates; Inbox/Watch product runtime em C6.

## 1. DÉLIA Inbox

Inbox materializa o que requer atenção:

```text
AGUARDANDO VOCÊ → Decision Gates, approvals, input faltante
TRABALHANDO     → Tasks/Cases/Workflows em andamento/espera
CONCLUÍDO       → resultados recentes relevantes
ALERTAS         → Watch/events/riscos
```

Cada item referencia Task/Case/Workflow/Decision/Watch/Entity, sem criar novo engine.

## 2. Watch

Watch representa condição futura monitorada de forma governada, por exemplo pedido atrasar, estoque atingir limite, nova revisão de desenho, fornecedor ultrapassar SLA, ação vencer ou evidência chegar ao Case.

Watch não é permissão nem executor. Ele detecta/avalia condição e encaminha o próximo passo segundo Policy/Decision/Work.

## 3. Event-first

Target:

```text
Domain/Platform/Provider EventEnvelope
→ validate/authenticate/dedupe
→ Watch matching
→ permission/policy revalidation
→ OBSERVE | ADVISE | PREPARE | ACT when phase/policy allows
```

Polling somente com gap provado e owner/frequency/cost claros.

## 4. Modes

```text
OBSERVE → atualiza/audita estado sem side effect material
ADVISE  → alerta/recomendação/Inbox item
PREPARE → prepara candidate action/arguments/preview sem side effect
ACT     → solicita/executa capability governada conforme Policy/Decision/Work e execution boundary
```

Phase semantics:

```text
C6 Watch default = OBSERVE | ADVISE | PREPARE
C6 Watch autonomous ACT = BLOCKED
C5 governed ACT = may already exist for explicit capabilities through authorized/confirmed flows
C7 selected Watch autonomous ACT = allowed only after explicit capability/autonomy gates
```

Portanto “Watch ACT em C7” significa **Watch disparando ACT autonomamente**, não que toda ação material do produto seja proibida até C7.

## 5. Watch/Event contracts

Reutilizar `EntityRef` e `EventEnvelope` somente se C0 os congelar. Watch pode conter owner/subject refs, entity scope, structured condition, mode, policy/autonomy ref, status, cooldown/dedupe policy e expiry.

Não armazenar prompt livre/código arbitrário como condição executável.

`wait_event` e Watch devem convergir para o mesmo EventEnvelope contract se esse primitive for aprovado; não criar `WatchEvent` paralelo.

## 6. Watch + Graph/Workflow

```text
event entity
→ authorized Graph traversal
→ Domain API reads
→ Evidence
→ advice/PREPARE/action planning
```

Case/Workflow pode aguardar evidence/approval/status/prazo/revisão; evento correlacionado retoma `wait_event` após revalidation.

## 7. Inbox behavior

Item deve explicar o que ocorreu, por que importa, source/evidence, work item, available authorized actions e se decisão é requerida. Ler item não executa write.

## 8. Dedupe/noise

- dedupe event/watch/subject;
- cooldown;
- grouping when safe;
- severity;
- expiry;
- quiet-hours/preferences quando policy permitir;
- resolved state quando semântica suportar.

## 9. Segurança

- owner claro;
- permission revalidated no trigger;
- revoked source não permanece exposto;
- event payload = untrusted data;
- event never grants permission;
- PREPARE has no material side effect;
- ACT revalida live AuthZ/policy/Decision/idempotency/audit;
- replay não duplica effect;
- autonomous ACT requires capability-scoped autonomy and kill switch;
- Automation Hub technical execution, when used, does not become Watch/permission authority.

## 10. Audit

Registrar watch lifecycle, source event/ref, match/dedupe, policy outcome, advice, PREPARE, workflow resume, action execute/reject, authoritative Outcome e acknowledge/dismiss.

## 11. Phase mapping

```text
C0 → EventEnvelope/Watch semantics + events/notifications inventory
C5 → Durable Workflow + wait_event foundation + governed ACT capability gates
C6.S1–S4 → Task/Case/Room/Inbox foundation consumers
C6 → Watch OBSERVE/ADVISE/PREPARE conforme substeps canônicos de 16
C7 → selected Watch autonomous ACT conforme 16/20/25
```

Este documento não redefine substep numbering; `16` é authority de ordem.

## 12. Delivery boundary

DÉLIA owns Inbox/Watch semantics and Work correlation. Core/Portal shared notification infrastructure may be used via adapter for delivery/presentation when C0 confirms compatibility.

Portal does not own Watch matching or workflow decisions. Notification delivery does not prove business Outcome.

## 13. Execution boundary

When a Watch-authorized action requires technical automation execution:

```text
Watch condition
→ DÉLIA Policy/Decision/Work
→ semantic capability
→ Automation Hub contract
→ technical execution
→ authoritative Outcome verification
```

DÉLIA does not embed RPA/computer-use mechanics in Watch definitions.

## 14. Independence

Inbox/Watch state belongs to DÉLIA runtime when implemented and does not use Minha DELPI Chat notifications/sessions as product authority.

## 15. Anti-patterns

- cron/polling app-specific without gap;
- prompt as condition code;
- parallel EventEnvelope;
- alert without dedupe/budget;
- permission evaluated only at creation;
- event payload as permission;
- PREPARE with hidden side effect;
- Watch autonomous ACT before C7 gates;
- ACT after permission/policy revocation;
- Inbox as workflow engine;
- RPA clicks/selectors inside Watch;
- fallback to Chat runtime.

## 16. Gate C6/C7

Watch/Inbox require correlatable/deduped events, preserved source permissions, safe workflow resume and noise controls.

C6 passes only if Watch `OBSERVE|ADVISE|PREPARE` works without autonomous side effects. C7 may unlock selected Watch autonomous ACT only with capability/context/risk-scoped autonomy, explicit identity, live revalidation, limits/budgets, idempotency, audit, kill switch and verified Outcome.
