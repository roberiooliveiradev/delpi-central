# Minha DELPI Copilot — Inbox, Watch e Trabalho Proativo

**Status:** thematic spec  
**Order authority:** [`16-execution-master-plan.md`](./16-execution-master-plan.md)  
**Foundation:** `EventEnvelope` em C0; Inbox usa refs de Work/Decision/Watch existentes.

## 1. Copilot Inbox

Inbox materializa o que requer atenção:

```text
AGUARDANDO VOCÊ
→ Decision Gates, approvals, input faltante

TRABALHANDO
→ Tasks/Cases/Workflows em andamento/espera

CONCLUÍDO
→ resultados recentes relevantes

ALERTAS
→ Watch/events/riscos
```

Cada item referencia sua source (`TaskRef`, `CaseRef`, workflow/decision/watch/entity), sem criar novo engine.

## 2. Watch

Watch representa condição futura monitorada de forma governada.

Exemplos:

- pedido atrasar;
- estoque cair abaixo do limite;
- nova revisão de desenho;
- fornecedor ultrapassar SLA;
- ação vencer;
- indicador ultrapassar threshold;
- evidência chegar ao Case.

## 3. Event-first

Preferência:

```text
domain/platform EventEnvelope
→ validate/dedupe
→ Watch matching
→ permission/policy revalidation
→ OBSERVE | ADVISE | ACT
```

Polling somente com gap provado e owner/frequency/cost claros.

## 4. Modes

```text
OBSERVE
→ atualiza/audita estado

ADVISE
→ alerta/recomendação/Inbox item

ACT
→ executa capability allowlisted sob autonomy/Decision Gate
```

C6 libera OBSERVE/ADVISE. ACT somente C7.

## 5. Watch contract

Reutilizar `EntityRef` e Event semantics C0.

Campos conceituais:

```text
watchId
owner/subject ref
entity scope refs
condition ref/structured condition
mode
policy/autonomy ref
status
cooldown/dedupe policy
expiresAt?
createdAt/updatedAt
```

Não armazenar prompt livre ou código arbitrário como condição executável.

## 6. EventEnvelope

Watch e `wait_event` usam o **mesmo** EventEnvelope compartilhado:

```text
eventId
eventType
source
entityRefs[]
occurredAt
payloadRef/payload bounded
correlation
schemaVersion
```

Não criar `WatchEvent` paralelo.

## 7. Watch + Graph

Ao disparar:

```text
event entity
→ authorized Graph traversal
→ source API reads
→ Evidence
→ advice/action planning
```

Graph não concede permissão.

## 8. Watch + Durable Workflow

Case/Workflow pode aguardar:

- evidence;
- approval;
- status externo;
- prazo;
- revisão.

Evento correlacionado pode retomar `wait_event` após revalidation.

## 9. Inbox behavior

Item deve explicar:

- o que ocorreu;
- por que importa;
- source/evidence;
- qual work item originou;
- ações autorizadas;
- se decisão é requerida.

Ler item não executa write.

## 10. Dedupe/noise

Obrigatório:

- dedupe event/watch/subject;
- cooldown;
- grouping quando seguro;
- severity;
- expiry;
- quiet-hours/preferences quando policy permitir;
- resolved state quando semântica suportar.

## 11. Segurança

- owner claro;
- permission revalidated no trigger;
- source access revogado não fica exposto pela Inbox;
- event payload é untrusted data;
- Watch ACT revalida policy/Decision Gate/idempotency;
- duplicate/replayed event não duplica effect.

## 12. Audit

Registrar:

```text
watch create/update/disable
source event/ref
match/dedupe outcome
policy outcome
advice emitted
work resumed
action prepared/executed/rejected
user acknowledged/dismissed
```

## 13. Implementation mapping

Não executar `PW*` como roadmap independente.

```text
C0 → EventEnvelope/Watch semantics + inventory de events/notifications
C5 → Inbox sobre Durable Work/Decisions
C6 → Watch OBSERVE/ADVISE
C7 → Watch ACT selected
```

## 14. Anti-patterns

- cron/polling app-specific no core sem gap;
- prompt livre como condition code;
- outro EventEnvelope;
- alerta sem dedupe/budget;
- permission avaliada somente na criação;
- ACT porque “Watch já existia” apesar de policy revogada;
- Inbox como workflow engine.

## 15. Gate

Watch/Inbox só passam quando:

- events são correlacionáveis/deduped;
- source permission é preservada;
- no alert fatigue baseline;
- workflow resume é seguro;
- ACT permanece inacessível antes da fase/policy correta.