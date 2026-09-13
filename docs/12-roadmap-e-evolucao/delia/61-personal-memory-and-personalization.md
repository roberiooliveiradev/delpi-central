# DÉLIA — Memória Pessoal e Personalização

**Status:** `TARGET` — thematic product/privacy/architecture spec  
**Order authority:** [`16-execution-master-plan.md`](./16-execution-master-plan.md)  
**State:** [`21-data-and-state-model.md`](./21-data-and-state-model.md)  
**Privacy/Security:** [`08-security-autonomy-audit.md`](./08-security-autonomy-audit.md)

## 1. Decisão de produto

A DÉLIA deve distinguir claramente:

```text
ORGANIZATIONAL KNOWLEDGE
!=
PERSONAL MEMORY
!=
CONVERSATION HISTORY
!=
WORKSPACE/SESSION CONTEXT
```

Personal Memory existe para adaptar experiência/relevância ao usuário. Não é business authority, não concede permission e não vira conhecimento corporativo automaticamente.

## 2. Candidates para memória pessoal

Conforme policy, finalidade e controles do usuário, podem existir candidates como:

```text
preferências de formato/idioma
assuntos/projetos acompanhados
notification preferences
preferred analysis/report formats
user-confirmed work facts
private continuity refs
followed topics
```

Responsabilidades, papéis ou fatos de negócio devem referenciar fontes oficiais; memory não os torna verdade autoritativa.

## 3. O que não deve virar memória pessoal automaticamente

- sensitive personal attributes;
- inferred personality/emotion/trustworthiness;
- disciplinary/employee scoring;
- health or other sensitive inference;
- raw biometric templates;
- provider credentials/tokens/secrets;
- secret content from other users;
- temporary external content with no retention purpose;
- chain-of-thought;
- unsupported inference presented as user fact.

## 4. Memory classes

Classes abaixo são candidate semantics até C0 congelar owner, lifecycle, storage e controls:

```text
USER_PREFERENCE
USER_CONFIRMED_FACT
WORK_CONTINUITY_REF
FOLLOWED_TOPIC
PRIVATE_KNOWLEDGE_REF
TEMPORARY_PERSONAL_CONTEXT
```

Não criar repository/schema/registry apenas porque esta lista existe na documentação.

## 5. Memory write semantics

Target:

```text
candidate memory
→ relevance/privacy/policy check
→ user control/approved rule
→ persisted memory only when lifecycle is authorized
```

Correção do usuário prevalece sobre a versão ativa. A arquitetura deve evitar que valor antigo continue influenciando respostas após correção/deletion conforme retention policy.

## 6. User controls

Quando Memory estiver implementada, a UX deve permitir controles coerentes com policy, incluindo inspeção/resumo, correção, delete/forget, disable/pause personalization e transparência de influência material quando apropriado.

A existência de controles específicos depende do contrato congelado; este documento não prova UI/runtime existente.

## 7. Personalization model

Personalization pode influenciar:

- presentation;
- prioritization;
- reminders;
- proactive briefings;
- preferred analysis/report formats;
- suggested next actions.

Nunca pode bypassar:

```text
Core RBAC
Domain authorization
Policy/Decision
provider scopes
source ACL
risk/autonomy policy
```

## 8. Daily/operational briefing

Target:

```text
live authorized facts/tasks/cases/watches
+ user preferences/followed topics
→ personalized briefing
```

Memory fornece preferência/relevância; live authoritative sources fornecem estado factual.

## 9. Shared devices

Personal Memory não pode vazar entre usuários em terminal compartilhado. User switch/logout deve invalidar projeções/cache local de personalização conforme contrato de device/session.

## 10. Privacy and data minimization

- private memory is user-scoped by default;
- private memory != Organizational Knowledge;
- no hidden employment profile;
- minimum useful representation;
- deletion/revocation must propagate to derived indexes/projections as required;
- memory never grants authorization.

## 11. Organizational Knowledge boundary

Personal Memory só pode originar organizational knowledge candidate quando houver purpose explícito e fluxo governado:

```text
personal/session evidence
→ organizational knowledge candidate
→ owner/review
→ eval/privacy/licensing checks
→ version
→ publish
```

Nunca auto-promote.

## 12. C0 inventory

Inventariar factual:

- existing user preference/profile stores;
- Core user/profile fields;
- notification preferences;
- favorites/recent usage;
- privacy/retention owner;
- deletion/export requirements;
- shared-device constraints;
- existing personalization mechanisms.

Sem evidence suficiente = `TO_INVENTORY`.

## 13. Phase mapping

```text
C0 → owner/classes/privacy/retention/control contract decisions
C3 → minimal memory/personalization foundations only if justified
C4 → relevance/personalized reads without authority change
C6 → user-facing controls, briefing and continuity experiences
C7 → advanced personalization optimization under privacy/eval controls
```

## 14. Acceptance

Quando implementada, provar:

- user A memory never appears for user B;
- user can exercise required correction/deletion/disable controls;
- memory cannot grant permission;
- stale memory cannot override live domain fact;
- personal memory never auto-promotes to Organizational Knowledge;
- sensitive inference is blocked;
- shared-device user switch clears personalized projections;
- material memory influence can be explained without exposing hidden reasoning.

Sem prova obrigatória: `PENDING`/`INCONCLUSIVE`.

## 15. North Star

> **DÉLIA deve adaptar relevância e experiência ao usuário sem transformar personalização em vigilância, autorização ou verdade corporativa.**
