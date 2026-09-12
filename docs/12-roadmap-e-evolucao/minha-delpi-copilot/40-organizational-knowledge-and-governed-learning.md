# Minha DELPI Copilot — Organizational Knowledge e Aprendizagem Governada

**Status:** arquitetura proposta  
**Objetivo:** separar conhecimento documental, conhecimento operacional, decisões e experiência histórica, criando um ciclo seguro de melhoria.

## 1. Classes de conhecimento

```text
Reference Knowledge
→ documentos, normas, procedimentos, manuais

Operational Knowledge
→ como processos da DELPI funcionam

Decision Knowledge
→ decisões tomadas, contexto e justificativas

Experience Knowledge
→ casos anteriores, causas, ações, resultados

Semantic Knowledge
→ entidades, conceitos e relações do Business Graph
```

Essas classes podem compartilhar infraestrutura, mas não devem ser semanticamente confundidas.

## 2. Reference Knowledge

RAG tradicional continua útil para:

- procedimentos;
- normas;
- políticas;
- manuais;
- documentação técnica;
- guias internos.

Toda fonte deve possuir scope, owner, version/freshness e política de acesso.

## 3. Operational Knowledge

Representa práticas e processos estáveis:

- como tratar uma não conformidade;
- quem deve aprovar determinado processo;
- quais etapas um fluxo corporativo possui;
- terminologia interna;
- critérios de aceitação.

Preferencialmente materializado como Domain Playbooks, regras ou documentação governada, não como memória informal do LLM.

## 4. Decision Knowledge

Uma decisão relevante pode registrar:

```text
decisionId
case/task
question
options considered
selected option
decision owner/date
approved evidence refs
constraints
outcome refs
```

Não persistir chain-of-thought do modelo. Registrar justificativa operacional aprovada e evidências.

## 5. Experience Knowledge

Permite responder:

> “Já tivemos esse problema antes?”

Um caso encerrado pode gerar um `ExperienceRecord`:

```text
problem signature
context/entity types
confirmed root causes
actions taken
verification/result
applicable constraints
evidence refs
case ref
```

Promoção para Experience Knowledge deve ser governada; nem toda conversa/caso vira conhecimento confiável.

## 6. Solution Patterns

Padrões validados podem ser promovidos para catálogo reutilizável:

```text
candidate
→ expert review
→ eval
→ published pattern
→ usage/feedback
→ version update/deprecate
```

Exemplo: padrão de solução para trinca causada por determinado processo/material.

## 7. Governed Learning Loop

O produto aprende por evolução de artefatos governados, não por alteração invisível do modelo a cada correção.

```text
feedback/correction
→ telemetry
→ recurring issue detection
→ improvement proposal
→ edit Expertise/Playbook/Knowledge/Rule
→ tests/evals
→ approval
→ versioned publish
→ canary
```

## 8. Sinais de melhoria

- usuário corrige entidade frequentemente;
- expertise escolhida incorretamente;
- playbook pede informação desnecessária;
- mesma capability falha em binding;
- mesma recomendação é rejeitada;
- perguntas repetidas sem resposta;
- solution pattern recorrente;
- source stale/contraditório.

## 9. Feedback

Tipos úteis:

```text
helpful / not_helpful
wrong_fact
wrong_entity
wrong_action
wrong_method
missing_source
unsafe_suggestion
outdated_knowledge
better_solution
```

Feedback não substitui evidence nem altera produção automaticamente.

## 10. Retenção e LGPD

- minimizar conteúdo persistido;
- separar dados pessoais de conhecimento reutilizável;
- redigir/anonymizar quando possível;
- respeitar delete/retention policies;
- não promover dado pessoal de caso para conhecimento global sem base legal/policy.

## 11. Métricas

- knowledge hit usefulness;
- outdated knowledge rate;
- correction recurrence;
- solution pattern reuse;
- expertise/playbook version success;
- time to resolve repeated cases;
- proportion of conclusions backed by evidence.

## 12. Não fazer

- “auto-treinar” com toda conversa;
- transformar resposta do LLM em norma corporativa;
- esconder origem/versionamento;
- usar decisão antiga fora de contexto como regra universal;
- manter conhecimento sem owner.

## 13. Gate

Uma fonte só é considerada `published organizational knowledge` se possuir owner, scope, provenance, lifecycle e regras de acesso.