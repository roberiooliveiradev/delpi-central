# Minha DELPI Copilot — Organizational Knowledge e Aprendizagem Governada

**Status:** thematic spec  
**Order authority:** [`16-execution-master-plan.md`](./16-execution-master-plan.md)  
**Runtime phase:** C6, após Evidence/Case foundations estarem estáveis.

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

Compartilhar infraestrutura é possível; semântica/owner/lifecycle permanecem explícitos.

## 2. Reference Knowledge

RAG tradicional com:

- owner;
- scope/ACL;
- version/freshness;
- provenance;
- retention.

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
C0 → provenance/lifecycle/retention semantics
C2 → Reference Knowledge + ACL integration
C5 → Cases generate structured resolution evidence
C6 → Decision/Experience/Solution Pattern + governed learning
C7 → rollout optimization only
```

## 13. Gate

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