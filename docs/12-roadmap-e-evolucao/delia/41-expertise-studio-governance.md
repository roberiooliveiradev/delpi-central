# DÉLIA — Expertise Studio

**Status:** `TARGET` — thematic admin spec  
**Order authority:** [`16-execution-master-plan.md`](./16-execution-master-plan.md)  
**Standalone boundary:** [`50-standalone-copilot-application-architecture.md`](./50-standalone-copilot-application-architecture.md)

## 1. Conceito

Expertise Studio é uma **surface target de governança**, não prova de runtime, catalog, repository ou storage existente.

Pode administrar, se C0/C3 congelarem esses contracts/owners:

- Expertise Packs;
- Domain Playbooks;
- terminology/glossary refs;
- knowledge refs/scopes;
- output guidance/schemas;
- examples/eval datasets;
- lifecycle/versioning;
- owners/reviewers;
- rollout/rollback.

**Não é criador de agentes.**

## 2. Lifecycle

Candidate lifecycle, sujeito ao owner canônico:

```text
DRAFT
→ REVIEW
→ TESTING
→ APPROVED
→ PUBLISHED
→ DEPRECATED
→ RETIRED
```

Não criar lifecycle paralelo se o owner corporativo aprovado já possuir um equivalente compatível.

## 3. Roles

Roles dependem do RBAC real do Core e separation-of-duties aplicável. Admin de conteúdo não concede business permission à DÉLIA nem provider scope.

## 4. Pack editor

Só pode editar fields permitidos pelo contract canônico. Não cadastrar endpoint/path/method/operationId, secrets ou permission overrides.

## 5. Playbook editor

Pode administrar method/evidence/criteria/output guidance conforme contract aprovado. Não embute HTTP/RPA executor nem technical worker state.

## 6. Preview/eval

Antes de publicar:

- validate schema/refs;
- positive/sibling/negative/safety evals;
- current vs candidate diff;
- token/context footprint quando aplicável;
- secret/technical-authority checks;
- semantic review;
- task outcome/generalization proof para mudanças de IA.

## 7. Versioning

Scheme final depende do owner. Deve distinguir mudança material/compatível quando isso for relevante e registrar version/hash auditável.

## 8. Rollout

```text
approved candidate
→ canary/internal
→ metrics/domain review
→ broader publish
```

Rollback/revoke precisam existir quando asset material puder afetar comportamento.

## 9. Metrics

Selection precision, task outcome, correction rate, Evidence coverage, review/approval rate, latency/cost impact e unsafe/blocked outcomes, sem employee scoring.

## 10. Governed Learning integration

```text
candidate improvement
→ owner/reviewer decision
→ edit
→ eval
→ versioned publish
```

Feedback não publica mudança automaticamente.

## 11. Implementation mapping

```text
C0 → decide owners/contracts/lifecycle/persistence boundaries
C3 → minimal Expertise/Playbook runtime only if unlocked
C6 → Studio/admin capability when real consumers/governance need exists
C7 → scale/rollout refinements only
```

Não iniciar “Studio storage” ou repository antecipadamente. A surface deve administrar o mesmo owner/catalog aprovado pelo runtime, não criar fonte paralela.

## 12. Independence

Studio não migra, edita nem publica Agents/Skills do Minha DELPI Chat.

## 13. Anti-patterns

- arbitrary prompt publish;
- Expertise as permission;
- agentId por pack;
- secrets;
- endpoint technical catalog;
- publish após um único example;
- repository/lifecycle paralelo;
- CRUD de Agent legado disfarçado;
- admin role como business authorization.

## 14. Gate

PASS somente quando a surface administrar o owner/contract real com Core RBAC, versioning, eval, audit, rollback/revoke e runtime proof no SHA/config avaliado.
