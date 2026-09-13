# Minha DELPI Copilot — Memória Pessoal e Personalização

**Status:** thematic product/privacy/architecture spec  
**Order authority:** [`16-execution-master-plan.md`](./16-execution-master-plan.md)  
**State:** [`21-data-and-state-model.md`](./21-data-and-state-model.md)  
**Privacy/Security:** [`08-security-autonomy-audit.md`](./08-security-autonomy-audit.md)

## 1. Decisão de produto

O Copilot deve distinguir claramente:

```text
ORGANIZATIONAL KNOWLEDGE
!=
PERSONAL COPILOT MEMORY
!=
CONVERSATION HISTORY
!=
WORKSPACE CONTEXT
```

Personal Memory existe para adaptar a experiência ao usuário sem transformar preferências em authority de negócio ou compartilhá-las implicitamente com a organização.

## 2. O que pode compor memória pessoal

Conforme policy e consentimento:

```text
preferências de formato/idioma
áreas e projetos acompanhados
assuntos recorrentes
responsabilidades declaradas/derivadas de fonte oficial
pessoas/equipes frequentemente relacionadas ao trabalho
preferred dashboards/metrics
working style preferences bounded
notification preferences
user-confirmed facts
private reminders/continuity refs
```

## 3. O que não deve virar memória pessoal automaticamente

- sensitive personal attributes;
- inferred personality/emotion/trustworthiness;
- disciplinary/employee scoring;
- raw biometric templates;
- provider credentials/tokens;
- secret content from other users;
- temporary external content with no retention purpose;
- chain-of-thought;
- unsupported inference presented as user fact.

## 4. Memory classes

```text
USER_PREFERENCE
USER_CONFIRMED_FACT
WORK_CONTINUITY_REF
FOLLOWED_TOPIC
PRIVATE_KNOWLEDGE_REF
TEMPORARY_PERSONAL_CONTEXT
```

Cada item possui source/provenance/confidence/createdAt/lastUsed/retention/status quando aplicável.

## 5. Memory write semantics

Personal Memory write é explícito ou policy-approved; não é efeito colateral invisível de qualquer conversa.

```text
candidate memory
→ relevance/privacy/policy check
→ auto-save if low-risk and user-enabled OR ask user when material
→ versioned memory item
```

Correção do usuário prevalece e gera audit de alteração, sem manter valor incorreto como ativo.

## 6. User controls

UX deve permitir:

```text
view memory summary
search/browse memory
correct
forget/delete
pause/disable personalization
set retention/preferences
see why a memory influenced an answer when material
```

## 7. Personalization model

Personalization may influence:

- presentation;
- prioritization;
- reminders;
- proactive briefings;
- preferred analysis/report formats;
- suggested next actions.

It must not bypass:

```text
Core RBAC
Domain authorization
Decision Gate
external scopes
source ACL
risk/autonomy policy
```

## 8. Daily/operational briefing

Target example:

```text
user responsibilities + followed topics + Tasks/Cases/Watches + authorized sources
→ personalized briefing
→ changes / risks / pending decisions / upcoming meetings
```

Briefing is computed from live authorities; memory provides preference/relevance, not stale business truth.

## 9. Shared devices

Personal memory is never cached across users on shared terminal. User switch/logout must clear local personalized projections.

## 10. Privacy and data minimization

- personal memory owner = user unless explicit organizational policy says otherwise;
- private memory is not organizational Knowledge;
- no hidden profile used for employment decisions;
- retain only minimum useful representation;
- deletion/revocation propagates to derived indexes as policy requires.

## 11. C0 inventory

Inventariar:

- existing user preference/profile stores;
- Core user/profile fields;
- notification preferences;
- favorites/recent usage;
- privacy/retention owner;
- deletion/export requirements;
- shared-device constraints;
- existing personalization mechanisms.

## 12. Phase mapping

```text
C0 → memory classes/ownership/privacy/retention/control contracts
C3 → memory candidate/read/write foundations and personalization policy
C4 → personalized relevance for reads/briefing without authority change
C6 → user-facing memory controls, proactive briefing and continuity
C7 → advanced personalization optimization under eval/privacy controls
```

## 13. Acceptance

- user A memory never appears for user B;
- user can inspect/correct/delete memory;
- memory cannot grant permission;
- stale memory cannot override live domain fact;
- personal memory never auto-promotes to organizational Knowledge;
- sensitive inference is blocked;
- shared-device user switch clears local personalized state;
- answer can identify material memory influence without exposing hidden reasoning.

## 14. North Star

> **O Copilot deve conhecer como cada usuário prefere trabalhar e o que acompanha, sem transformar personalização em vigilância, permissão ou verdade corporativa.**
