# Minha DELPI Copilot — Organizational Knowledge e Aprendizagem Governada

**Status:** thematic spec  
**Order authority:** [`16-execution-master-plan.md`](./16-execution-master-plan.md)  
**Standalone boundary:** [`50-standalone-copilot-application-architecture.md`](./50-standalone-copilot-application-architecture.md)  
**Runtime phase:** Reference Knowledge/RAG nasce na Copilot API em C3; Decision/Experience/Solution Pattern e Governed Learning entram em C6.

## 1. Classes

```text
Reference Knowledge
→ normas, procedimentos, manuais

Operational Knowledge
→ processos/métodos governados, frequentemente Playbooks

Decision Knowledge
→ decisões aprovadas, contexto, constraints, Evidence/Outcome refs

Experience Knowledge
→ casos resolvidos e resultados revisados

Semantic Knowledge
→ entidades/relacionamentos do Business Graph
```

Compartilhar infraestrutura neutra é possível; semântica, owner e lifecycle permanecem explícitos e pertencem ao Copilot ou ao owner corporativo correto, nunca ao Minha DELPI Chat por dependência implícita.

## 2. Reference Knowledge

RAG da própria Copilot API com:

- owner;
- scope/ACL;
- version/freshness;
- provenance;
- retention.

C0 pode identificar infraestrutura neutra reaproveitável, mas C3 implementa o runtime de retrieval do Copilot.

## 3. Operational Knowledge

Preferir representação governada como:

- Domain Playbook;
- policy/rule;
- documentação versionada;
- terminology/glossary.

Não depender de “memória informal do LLM”.

## 4. Decision Knowledge

Registro conceitual pode referenciar:

```text
decision/case/task refs
question/options
selected option
actor/date
Evidence refs
constraints
Outcome refs
```

Não persistir chain-of-thought. Armazenar justificativa operacional aprovada quando necessária.

## 5. Experience Knowledge

Case resolvido pode gerar **candidate** Experience:

```text
problem signature
context/entity types
confirmed causes
verified actions/outcomes
constraints
Evidence refs
Case ref
```

Candidate não é published knowledge automaticamente.

## 6. Solution Patterns

```text
candidate
→ expert review
→ eval
→ published pattern
→ usage/feedback
→ version/deprecate
```

Padrão precisa provar sibling/generalization; não memorizar um único caso literalmente.

## 7. Governed Learning Loop

```text
feedback/correction/case resolution
→ telemetry
→ recurring issue/candidate
→ change proposal
→ edit Expertise/Playbook/Knowledge/Rule
→ tests/evals
→ review/approval
→ versioned publish
→ canary
```

Nunca:

```text
user correction → automatic production behavior change
```

## 8. Feedback taxonomy

Exemplos:

```text
helpful/not_helpful
wrong_fact
wrong_entity
wrong_action
wrong_method
missing_source
unsafe_suggestion
outdated_knowledge
better_solution
```

Feedback é sinal, não truth/evidence.

## 9. Provenance e shared refs

Usar `EntityRef`, `EvidenceRef`, `OutcomeRef`, Case/Task/Decision refs compartilhados. Não criar modelos paralelos por knowledge class.

## 10. Security/LGPD

- user/source ACL;
- minimize/redact/anonymize;
- no PII promotion sem policy/base;
- delete/retention;
- no sensitive Case content globalized silently;
- malicious prior record não altera system/policy.

## 11. Metrics

- knowledge usefulness;
- stale/outdated rate;
- correction recurrence;
- solution pattern reuse;
- version success;
- repeated-case resolution time;
- evidence coverage.

## 12. Mapping

```text
C0 → provenance/lifecycle/retention + storage boundaries
C3 → Reference Knowledge/RAG + ACL/provenance integration
C4 → Semantic Knowledge/Business Graph source correlation
C6.S2 → Cases produce structured resolution evidence
C6.S6 → Decision/Experience/Solution Pattern runtime
C6.S7 → Governed Learning Loop
C7 → rollout/performance optimization only
```

## 13. Independence

Nenhum knowledge namespace, RAG store, conversation memory ou agent knowledge do Minha DELPI Chat é authority do Copilot. Reuso só é permitido quando C0 comprovar componente neutro com owner compartilhado e contrato independente.

## 14. Gate

Published organizational knowledge exige:

```text
owner
version
scope/ACL
provenance
review/eval
lifecycle/status
retention
```

Sem esses itens, continua candidate/reference, não corporate truth.