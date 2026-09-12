# Minha DELPI Copilot — Expertise Studio

**Status:** thematic admin spec  
**Order authority:** [`16-execution-master-plan.md`](./16-execution-master-plan.md)  
**Runtime phase:** C6, após Expertise/Playbook runtime C2 e operational cutover C4 estarem estáveis.

## 1. Conceito

Expertise Studio é a superfície de governança para:

- Expertise Packs;
- Domain Playbooks;
- terminology/glossary;
- knowledge refs/scopes;
- output guidance/schemas;
- examples/eval datasets;
- lifecycle/versioning;
- owners/reviewers;
- rollout/rollback.

**Não é criador de agentes.**

## 2. Lifecycle

```text
DRAFT
→ REVIEW
→ TESTING
→ APPROVED
→ PUBLISHED
→ DEPRECATED
→ RETIRED
```

Mudança material publicada cria versão/candidate novo e passa por evals.

## 3. Roles

Conforme RBAC administrativo real:

- Expertise Author;
- Domain Reviewer;
- AI/Platform Reviewer;
- Security Reviewer quando necessário;
- Publisher/Admin.

Admin de conteúdo não concede business permission ao Copilot.

## 4. Pack editor

Pode editar campos permitidos pelo `ExpertisePack` foundation:

- identity/version;
- domains/signals;
- terminology;
- analysis/output guidance;
- Evidence expectations;
- knowledge refs;
- playbook refs;
- multimodal needs;
- eval refs;
- owner/reviewers.

Não cadastrar path/method/operationId como API catalog.

## 5. Playbook editor

Pode editar:

- purpose/applicability;
- stages;
- Evidence requirements;
- decision criteria;
- completion criteria;
- optional/required stages;
- artifact/output guidance;
- evals/owner.

Não embutir HTTP executor.

## 6. Preview/eval

Antes de publicar:

- compile/validate content;
- refs exist/authorized structurally;
- run positive/sibling/negative/safety cases;
- compare current vs candidate;
- measure token/context footprint;
- detect secret/technical authority violations;
- review semantic diff.

## 7. Versioning

Scheme final depende do owner, mas precisa distinguir compatible vs material change e registrar version/hash no runtime/audit.

## 8. Rollout

```text
published candidate
→ internal/canary
→ metrics/domain review
→ wider rollout
```

Rollback para versão anterior deve existir.

## 9. Metrics

- selection precision;
- task completion;
- correction rate;
- Evidence coverage;
- clarification efficiency;
- review/approval rate;
- latency/token impact;
- unsafe/blocked outcomes.

## 10. Governed Learning integration

```text
candidate improvement
→ author/reviewer decision
→ edit
→ eval
→ publish
```

Feedback não publica mudança automaticamente.

## 11. Implementation mapping

```text
C0 → Pack/Playbook contracts/lifecycle semantics
C2 → runtime catalog/retrieval outside Studio UX
C6 → Studio admin capability + governance workflows
C7 → optimization/rollout refinements
```

Não iniciar “MVP Studio storage” antes de C6 só porque a UI ainda não existe; C0/C2 owners devem ser reutilizados, não duplicados.

## 12. Anti-patterns

- arbitrary prompt publish sem review;
- Expertise as permission;
- agentId por pack;
- secrets;
- endpoint technical catalog;
- publish após um único manual example;
- Studio repository paralelo ao Expertise Catalog canônico;
- lifecycle próprio diferente do runtime catalog.

## 13. Gate

Studio só passa quando administra o **mesmo** Pack/Playbook owner usado pelo runtime, com RBAC, versioning, eval, audit e rollback.