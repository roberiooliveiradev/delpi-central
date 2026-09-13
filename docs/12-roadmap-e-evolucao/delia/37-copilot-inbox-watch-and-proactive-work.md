# Minha DELPI Copilot — Inbox, Watch e Trabalho Proativo

**Status:** thematic spec  
**Order authority:** [`16-execution-master-plan.md`](./16-execution-master-plan.md)  
**Standalone boundary:** [`50-standalone-copilot-application-architecture.md`](./50-standalone-copilot-application-architecture.md)  
**Foundation:** `EventEnvelope` em C0; Durable Workflow em C5; Inbox/Watch product runtime em C6.

## 1. Copilot Inbox

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

## 3. Event-first

```text
Domain/Platform EventEnvelope
→ validate/dedupe
→ Watch matching
→ permission/policy revalidation
→ OBSERVE | ADVISE | ACT
```

Polling somente com gap provado e owner/frequency/cost claros.

## 4. Modes

```text
OBSERVE → atualiza/audita estado
ADVISE  → alerta/recomendação/Inbox item
ACT     → executa capability allowlisted sob autonomy/Decision Gate
```

C6 libera OBSERVE/ADVISE. ACT somente C7.

## 5. Watch/Event contracts

Reutilizar `EntityRef` e `EventEnvelope` C0. Watch pode conter owner/subject refs, entity scope, structured condition, mode, policy/autonomy ref, status, cooldown/dedupe policy e expiry.

Não armazenar prompt livre/código arbitrário como condição executável.

`wait_event` e Watch usam o mesmo EventEnvelope; não criar `WatchEvent` paralelo.

## 6. Watch + Graph/Workflow

```text
event entity
→ authorized Graph traversal
→ Domain API reads
→ Evidence
→ advice/action planning
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
- ACT revalida policy/Decision/idempotency;
- replay não duplica effect.

## 10. Audit

Registrar watch lifecycle, source event/ref, match/dedupe, policy outcome, advice, workflow resume, action prepare/execute/reject e acknowledge/dismiss.

## 11. Phase mapping

```text
C0 → EventEnvelope/Watch semantics + events/notifications inventory
C5 → Durable Workflow + wait_event foundation
C6.S1–S4 → Task/Case/Room/Inbox foundation consumers
C6.S5 → Watch OBSERVE/ADVISE
C7 → Watch ACT selected
```

## 12. Delivery boundary

Copilot API owns Inbox/Watch semantics. Core/Portal shared notification infrastructure may be used via adapter for delivery/presentation when C0 confirms compatibility.

Portal does not own Watch matching or workflow decisions.

## 13. Independence

Inbox/Watch state belongs to Copilot runtime and does not use Minha DELPI Chat notifications/sessions as product authority.

## 14. Anti-patterns

- cron/polling app-specific without gap;
- prompt as condition code;
- parallel EventEnvelope;
- alert without dedupe/budget;
- permission evaluated only at creation;
- ACT after permission/policy revocation;
- Inbox as workflow engine;
- fallback to Chat runtime.

## 15. Gate C6/C7

Watch/Inbox require correlatable/deduped events, preserved source permissions, safe workflow resume and noise controls. ACT remains inaccessible before C7 policy allows it.