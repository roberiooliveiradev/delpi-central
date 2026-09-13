# Minha DELPI Copilot — Organizational Knowledge e Aprendizagem Governada

**Status:** thematic spec  
**Order authority:** [`16-execution-master-plan.md`](./16-execution-master-plan.md)  
**Standalone boundary:** [`50-standalone-copilot-application-architecture.md`](./50-standalone-copilot-application-architecture.md)  
**Multimodal/Meeting/Frontline:** [`53-multimodal-meeting-frontline-and-industrial-copilot.md`](./53-multimodal-meeting-frontline-and-industrial-copilot.md)  
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
→ casos, reuniões e experiências operacionais revisadas com outcomes/evidence

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

Fontes podem incluir procedimentos, instruções de trabalho, normas, manuais, desenhos/documentos e materiais de treinamento, sempre respeitando owner/version/ACL.

C0 pode identificar infraestrutura neutra reaproveitável, mas C3 implementa o runtime de retrieval do Copilot.

## 3. Operational Knowledge

Preferir representação governada como:

- Domain Playbook;
- policy/rule;
- documentação versionada;
- terminology/glossary;
- standard work/instruction mantido pelo owner oficial.

Não depender de “memória informal do LLM”.

Copilot não substitui o owner do procedimento apenas porque ajudou a identificar uma melhoria.

## 4. Decision Knowledge

Registro conceitual pode referenciar:

```text
decision/case/task/meeting refs
question/options
selected option
actor/date
Evidence refs
constraints
Outcome refs
```

Não persistir chain-of-thought. Armazenar justificativa operacional aprovada quando necessária.

Ata/resumo de reunião não vira `Decision Knowledge` apenas porque o LLM inferiu uma decisão; é necessário estado humano/operacional confirmado conforme o workflow aplicável.

## 5. Experience Knowledge

Case resolvido, reunião concluída ou experiência operacional pode gerar **candidate** Experience quando houver finalidade e evidence adequadas.

Exemplo conceitual:

```text
problem/practice signature
context/entity types
source = case|meeting|frontline|validated feedback
confirmed causes or practice statement
verified actions/outcomes when available
constraints
Evidence refs
Case/Meeting/Frontline refs
```

Candidate não é published knowledge automaticamente.

Uma fala de operador ou observação de câmera, isoladamente, não é corporate truth.

## 6. Conhecimento tácito no chão de fábrica

O Copilot pode ajudar a capturar conhecimento que hoje fica apenas na experiência individual.

Exemplo:

> “Quando esse material vem desse fornecedor eu verifico primeiro esta região porque já tivemos rebarba.”

Fluxo permitido:

```text
fala/observação autorizada
+ OP/produto/material/máquina context
+ Evidence existente quando disponível
→ candidate practice/insight
→ domain owner review
→ buscar confirmação histórica/medição se necessário
→ eval
→ accepted Experience/Playbook/procedure change candidate
→ formal publish pelo owner correto
```

O Copilot deve preservar quem disse/observou, em qual contexto e qual grau de evidência existe, sem transformar experiência tácita em regra universal.

## 7. Process observation

Observação de processo por câmera, vídeo, eventos ou dados pode gerar candidatos como:

- possível gargalo;
- espera recorrente;
- ajuste manual repetido;
- possível causa de retrabalho;
- prática útil do operador;
- divergência entre instrução e execução real.

Mas o pipeline é:

```text
observation
→ Evidence/Hypothesis
→ validation with source/process owner
→ candidate improvement
→ review/eval
```

Nunca:

```text
one visual observation
→ automatic standard-work update
```

Nem:

```text
operator behavior
→ hidden individual performance score
```

## 8. Solution Patterns

```text
candidate
→ expert review
→ eval
→ published pattern
→ usage/feedback
→ version/deprecate
```

Padrão precisa provar sibling/generalization; não memorizar um único caso literalmente.

## 9. Governed Learning Loop

```text
feedback
case resolution
meeting outcome
frontline assistance outcome
validated process observation
        ↓
telemetry + Evidence
        ↓
recurring issue/candidate
        ↓
change proposal
        ↓
edit Expertise/Playbook/Knowledge/Rule/procedure candidate
        ↓
tests/evals
        ↓
review/approval by correct owner
        ↓
versioned publish
        ↓
canary/monitor
```

Nunca:

```text
user correction → automatic production behavior change
meeting transcript → automatic corporate policy
operator observation → automatic work instruction
```

## 10. Feedback taxonomy

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
wrong_transcript
wrong_visual_finding
wrong_meeting_summary
unsafe_frontline_guidance
```

Feedback é sinal, não truth/evidence por si só.

## 11. Provenance e shared refs

Usar:

```text
EntityRef
SourceRef
EvidenceRef
OutcomeRef
CaseRef
TaskRef
Meeting/Frontline refs when persisted
Decision refs
MediaRef when C0 approves it
```

Não criar modelos paralelos por knowledge class ou surface.

## 12. Security/LGPD/worker privacy

- user/source ACL;
- minimize/redact/anonymize;
- no PII promotion sem policy/base;
- delete/retention;
- no sensitive Case/Meeting/Frontline content globalized silently;
- malicious prior record não altera system/policy;
- raw audio/video is not Knowledge by default;
- no facial/emotion analytics by default;
- no hidden employee surveillance/scoring;
- access to Experience Knowledge does not imply access to original protected media/source.

## 13. Quality gate para conhecimento operacional

Antes de promover candidate ligado a processo fabril, verificar conforme aplicável:

```text
owner
source/evidence
sample/context scope
reproducibility
conflicting evidence
safety impact
quality impact
engineering/process approval
training/certification impact
version/effective date
rollback/deprecation path
```

Sugestão útil não substitui change management oficial.

## 14. Metrics

- knowledge usefulness;
- stale/outdated rate;
- correction recurrence;
- solution pattern reuse;
- version success;
- repeated-case resolution time;
- evidence coverage;
- candidate→published precision;
- rejected candidate reasons;
- meeting/frontline candidate usefulness;
- unsafe/unsupported candidate rate;
- process improvement outcome after approved publish.

Não usar “quanto o operador obedeceu ao Copilot” como proxy automático de qualidade/produtividade.

## 15. Mapping

```text
C0 → provenance/lifecycle/retention + media/privacy/storage boundaries
C3 → Reference Knowledge/RAG + ACL/provenance integration
C4 → Semantic Knowledge/Business Graph source correlation
C6.S2 → Cases produce structured resolution evidence
C6.S6 → Organizational/Decision/Experience/Solution Pattern runtime
C6.S7 → Governed Learning Loop incl. Meeting/Frontline/process candidates
C6.S10–S11 → Meeting/Frontline produce candidates and outcomes, not auto-published knowledge
C7 → rollout/performance optimization only
```

## 16. Independence

Nenhum knowledge namespace, RAG store, conversation memory ou agent knowledge do Minha DELPI Chat é authority do Copilot. Reuso só é permitido quando C0 comprovar componente neutro com owner compartilhado e contrato independente.

## 17. Gate

Published organizational knowledge exige:

```text
owner
version
scope/ACL
provenance
review/eval
lifecycle/status
retention
source/media access separation when applicable
safety/process approval when applicable
```

Sem esses itens, continua candidate/reference, não corporate truth.