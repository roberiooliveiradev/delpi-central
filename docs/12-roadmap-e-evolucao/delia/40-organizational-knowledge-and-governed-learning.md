# DÉLIA — Organizational Knowledge e Aprendizagem Governada

**Status:** `TARGET` — thematic spec  
**Order authority:** [`16-execution-master-plan.md`](./16-execution-master-plan.md)  
**Standalone boundary:** [`50-standalone-copilot-application-architecture.md`](./50-standalone-copilot-application-architecture.md)  
**Multimodal/Meeting/Frontline:** [`53-multimodal-meeting-frontline-and-industrial-copilot.md`](./53-multimodal-meeting-frontline-and-industrial-copilot.md)

## 1. Classes

```text
Reference Knowledge
→ normas, procedimentos, manuais

Operational Knowledge
→ processos/métodos governados, frequentemente Playbooks

Decision Knowledge
→ decisões aprovadas, contexto, constraints, Evidence/Outcome refs

Experience Knowledge
→ casos, reuniões e experiências operacionais revisadas

Semantic Knowledge
→ relações/significados derivados de sources governadas
```

Essas classes não implicam stores separados nem ownership automático da DÉLIA. C0 deve identificar owner, source canônica, consumers, lifecycle, retention e ACL.

## 2. Reference Knowledge

Target de retrieval/RAG da DÉLIA sobre fontes autorizadas, com:

- owner;
- scope/ACL;
- version/freshness;
- provenance;
- retention.

A DÉLIA não se torna owner do documento/procedure original por indexá-lo ou referenciá-lo.

C0 pode identificar infraestrutura neutra reaproveitável. Runtime/storage próprio só deve ser criado quando boundary/consumer/lifecycle real justificar.

## 3. Operational Knowledge

Preferir representação governada como:

- Domain Playbook;
- policy/rule;
- documentação versionada;
- terminology/glossary;
- standard work/instruction mantido pelo owner oficial.

DÉLIA não substitui procedure/policy owner.

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

Não persistir chain-of-thought. Ata/resumo inferido não vira decisão aprovada sem confirmação/lifecycle apropriado.

## 5. Experience Knowledge

Case resolvido, reunião concluída ou experiência operacional pode gerar **candidate** quando houver finalidade e Evidence adequadas.

```text
Evidence
→ candidate
→ owner/review
→ eval
→ version
→ publish
```

Candidate não é published knowledge automaticamente.

## 6. Conhecimento tácito no chão de fábrica

Fala/observação autorizada pode gerar candidate practice/insight, nunca regra universal automática.

```text
observation/source
+ operational context
+ existing Evidence when available
→ candidate
→ domain owner review
→ validation/eval
→ procedure/playbook/knowledge candidate
→ formal publish by correct owner
```

## 7. Process observation

Observação de processo por câmera, vídeo, eventos ou dados pode gerar hipóteses/candidates como gargalo, espera, retrabalho ou prática operacional.

Nunca:

```text
one observation → automatic standard-work update
operator behavior → hidden individual performance score
```

Human Observation usa fatos observáveis do processo; não infere personalidade, honestidade, emoção como verdade, saúde, atributos sensíveis ou valor profissional.

## 8. Solution Patterns

```text
candidate
→ expert review
→ eval/generalization
→ published pattern
→ usage/feedback
→ version/deprecate
```

Um único caso bem-sucedido não prova generalização.

## 9. Governed Learning Loop

```text
feedback/case/meeting/frontline/process outcome
→ Evidence
→ recurring issue/candidate
→ change proposal
→ edit candidate
→ tests/evals
→ correct owner review/approval
→ versioned publish
→ canary/monitor
```

Nunca auto-promover conversation, public page, successful automation ou user correction para policy/procedure/conhecimento corporativo.

## 10. Feedback taxonomy

Feedback é sinal, não truth/evidence por si só.

## 11. Provenance e refs

Reutilizar refs canônicos somente se C0 os congelar. Não criar modelos paralelos por knowledge class/surface.

Personal Memory permanece separada de Organizational Knowledge e nunca concede authorization.

## 12. Security/LGPD/worker privacy

- source ACL;
- minimize/redact/anonymize;
- retention/delete/export owner;
- no silent globalization of sensitive Case/Meeting/Frontline content;
- external/generated content = untrusted;
- raw audio/video is not Knowledge by default;
- no hidden employee surveillance/scoring;
- access to derived Experience Knowledge does not imply original-source access.

## 13. Quality gate para conhecimento operacional

Antes de promover candidate ligado a processo fabril, verificar conforme aplicável:

```text
owner
source/evidence
scope/sample
reproducibility
conflicting evidence
safety impact
quality impact
engineering/process approval
training/certification impact
version/effective date
rollback/deprecation path
```

## 14. Metrics

Medir usefulness, freshness, correction recurrence, pattern reuse, eval/version outcomes e verified process improvement. Não usar “obediência ao AI” como produtividade/qualidade individual.

## 15. Mapping

```text
C0 → owner/provenance/lifecycle/retention/media/privacy boundaries
C3 → reference retrieval foundation only when unlocked and justified
C4 → Graph/Semantic/source correlation
C6 → Decision/Experience/Solution Pattern + Governed Learning product lifecycle
C7 → scale/optimization only
```

## 16. Independence

Nenhum RAG store, conversation memory ou agent knowledge do Minha DELPI Chat é authority da DÉLIA. Reuso exige componente neutro real com owner/contract/consumers comprovados.

## 17. Gate

Published organizational knowledge exige owner, version, scope/ACL, provenance, review/eval, lifecycle/status, retention e approvals aplicáveis. Sem isso, permanece candidate/reference.
