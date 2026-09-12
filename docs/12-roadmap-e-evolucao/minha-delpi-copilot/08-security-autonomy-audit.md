# 08 — Segurança, autonomia e auditoria

## 1. Invariante principal

```text
Copilot effective permissions ⊆ user effective permissions
```

O Copilot nunca opera como superusuário implícito e nenhuma camada de expertise/contexto/workflow pode ampliar privilégios.

## 2. Fluxo de autorização

```text
identity
→ Core effective permissions
→ authorized capability/action set
→ planner restrito
→ policy/risk/sensitivity
→ Decision Gate quando necessário
→ executor
→ backend revalidation
→ outcome/audit
```

Backend/domain API continua authority final do write.

## 3. Trust boundaries

Conteúdo de qualquer uma destas fontes é **dado não confiável para policy/system**:

- user prompt;
- Workspace Context;
- iframe;
- RAG;
- Expertise Pack/Playbook content;
- API/tool output;
- PDF/imagem/desenho;
- Room message/file;
- Event payload;
- organizational experience records.

Nenhum deles altera:

- permissions;
- system instructions;
- Decision Gate requirements;
- allowed actions;
- autonomy level.

## 4. Níveis de autonomia

| Nível | Comportamento |
|---|---|
| L0 | explicar |
| L1 | navegar |
| L2 | consultar/analisar |
| L3 | preparar alteração |
| L4 | executar com Decision Gate conforme policy |
| L5 | auto-executar capability explicitamente allowlisted dentro de limites |

L5 é OFF por default.

## 5. Sensitivity/risk

Classes podem incluir:

```text
read
write
sensitive_write
admin
destructive
external_communication
financial
personal_data
```

A classificação final deve ser owner/policy server-side e pode definir:

- gate level;
- autonomy ceiling;
- audit strength;
- redaction;
- approver requirements;
- volume/value limits.

## 6. Decision Gates

Modelo único:

```text
NO_GATE
ACKNOWLEDGE
CONFIRM
REVIEW_AND_CONFIRM
APPROVAL_WORKFLOW
BLOCK
```

Decision request deve vincular, quando material:

- action/capability ref;
- arguments hash;
- impact preview;
- evidence refs;
- risk/sensitivity;
- expiry;
- actor/approver scope.

Mudança material de payload, evidence, permission ou policy pode invalidar decisão anterior.

## 7. TOCTOU e revalidação

Revalidar antes de execute/resume/Watch ACT porque podem mudar:

- permissions;
- entity state/version;
- policy;
- provider availability;
- evidence freshness;
- approver validity.

## 8. Capability minimization

O planner recebe somente candidates necessários/autorizados.

Expertise pode **recomendar** uma capability, mas disponibilidade vem do set autorizado.

Project preference/context também não concede capability.

## 9. Knowledge security

Knowledge scopes passam por ACL independente da expertise.

Proibido:

```text
pack selecionado → liberar documentos do departamento
```

Correto:

```text
pack selecionado
+ user ACL
→ permitted knowledge candidates
```

## 10. Business Graph security

Traversal não pode vazar nó/edge não autorizado.

Regras:

- relationship source/provenance;
- permission-aware traversal;
- source fetch revalidado;
- graph cache não vira bypass de API/RBAC;
- inferred relation não tratada como authoritative.

## 11. Case/Room/Inbox security

- membership de Case/Room não concede automaticamente source entity access;
- summary respeita ACL;
- usuário removido perde acesso conforme owner/policy;
- Inbox sanitiza item cuja source deixou de ser autorizada;
- abrir/ler Inbox não dispara write.

## 12. Durable Workflow security

Em waits/restart/resume:

- revalidar identity/permission/policy;
- proteger duplicate resume/event;
- garantir idempotency para write;
- tratar ambiguous outcome;
- bloquear step dependente quando precondition crítica falha;
- respeitar cancellation/expiry.

## 13. Watch/Event security

Watch modes:

```text
OBSERVE
ADVISE
ACT
```

ACT exige explicit autonomy policy e Decision Gate quando aplicável.

Event payload:

- schema validated;
- deduped;
- correlated;
- tratado como dado não confiável;
- não concede permission.

## 14. Iframe security

Obrigatório:

- origin allowlist;
- `event.source` validation;
- app/session/protocol/version validation;
- schema validation;
- bounded payload;
- no JWT/refresh token;
- visual capabilities não viram Business Actions.

## 15. Prompt/tool/document/event injection

Testar injection a partir de:

```text
user
RAG
tool/API
Workspace Context
iframe
Expertise Pack
Playbook
PDF/image
Room message/file
Event payload
Experience Knowledge
```

Resultado esperado: nenhuma fonte de dados altera policy/system/RBAC.

## 16. URLs e HTTP

LLM não produz URL arbitrária para executor.

Business URL/method/schema vêm do provider/action canônico. Platform navigation resolve IDs autorizados via Portal.

## 17. Idempotência/concurrency

Preferência:

1. domain API idempotency;
2. domain use case protection;
3. orchestration dedupe/locking somente quando necessário.

Proibido retry cego de write.

## 18. Model/provider data policy

Model Router futuro deve respeitar:

- data classification;
- provider allowlist;
- residency/privacy constraints;
- model capability;
- retention policy;
- cost/latency budgets.

Provider fallback não pode diminuir security/data policy.

## 19. Organizational Knowledge safety

Feedback/case resolution não vira production truth automaticamente.

```text
candidate
→ review
→ eval
→ publish
```

Decision/Experience record não armazena chain-of-thought.

## 20. Auditoria

Eventos conceituais:

```text
copilot.plan.created
copilot.capability.selected
copilot.expertise.selected
copilot.decision.requested|decided
copilot.action.started|completed|failed
copilot.workflow.state_changed
copilot.task.state_changed
copilot.case.state_changed
copilot.watch.triggered
copilot.navigation.executed
```

Campos úteis:

```text
actor/subject
request/conversation/turn
workflow/task/case
entity refs
capability/action
expertise/playbook refs
policy/Decision Gate
outcome/evidence refs
duration/error
timestamp/correlation
```

## 21. Dados proibidos em logs/state

- JWT/refresh token;
- API key/password/secrets;
- chain-of-thought;
- full sensitive payload sem necessidade;
- provider credentials.

## 22. Emergency stop

Deve ser possível, conforme owner:

- desabilitar Copilot writes;
- desabilitar provider/action;
- read-only mode;
- desabilitar Watch ACT;
- suspender workflow class;
- revogar iframe integration;
- desabilitar expertise/playbook version problemática;
- desabilitar provider/model por data policy/incidente.

## 23. Security success criteria

Segurança está correta quando uma capability autorizada continua útil, mas nenhuma tentativa de prompt/context/pack/event/room pode ampliar o que o usuário poderia fazer diretamente pelas regras da plataforma.