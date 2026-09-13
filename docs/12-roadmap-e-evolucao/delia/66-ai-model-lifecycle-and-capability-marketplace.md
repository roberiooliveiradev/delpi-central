# DÉLIA — AI Model Lifecycle e Capability Marketplace

**Status:** `TARGET` — thematic MLOps/product/governance spec  
**Order authority:** [`16-execution-master-plan.md`](./16-execution-master-plan.md)  
**Model Router:** [`42-model-router-and-compute-policy.md`](./42-model-router-and-compute-policy.md)  
**Control Tower:** [`59-ai-control-tower-and-digital-workforce-governance.md`](./59-ai-control-tower-and-digital-workforce-governance.md)

## 1. Decisão

A visão alvo prevê governança do ciclo de vida dos modelos de IA relevantes e um catálogo governado de capabilities/assets reutilizáveis.

Separar:

```text
MODEL LIFECYCLE
= owner-specific build/evaluate/approve/deploy/monitor/rollback/revoke

CAPABILITY MARKETPLACE
= governed discovery/review/publish/enable experience over reusable assets
```

Marketplace não é permission authority, deployment owner universal nem mecanismo de auto-instalação em produção.

## 2. Model families

Candidates:

```text
LLM
embedding
vision
speech
classifier
forecast
anomaly detection
optimization model
quality model
other approved ML/AI models
```

A lista é `TARGET`; não prova modelos, registries ou pipelines existentes.

## 3. Model registry/projection metadata

Se C0 provar necessidade de registry/projection, representar refs do owner sem duplicar seu master.

Candidate metadata:

```text
modelRef/version
family/provider
owner/sourceRef
purpose
training/source lineage when applicable
approved data classes
runtime/deployment refs
quality/eval refs
latency/cost profile
risk tier
status
approved environments
rollback/revoke refs
```

Provider-hosted models também exigem governance metadata suficiente, mas isso não transforma DÉLIA em owner do provider lifecycle.

## 4. Model lifecycle

Estados abaixo são candidate semantics, não universal state machine:

```text
DRAFT/EXPERIMENT
→ EVALUATED
→ APPROVED
→ DEPLOYED
→ MONITORED
→ DEGRADED | DEPRECATED | REVOKED
→ ROLLED_BACK/RETIRED
```

Reuse owner lifecycle when one exists. Promotion/deployment requires evidence appropriate to risk.

## 5. Drift and performance

Medidas podem incluir, conforme model type:

```text
quality drift
input/data drift
calibration drift
latency
availability
cost
error rate
human correction rate
verified business outcome correlation
```

No single generic “AI score” proves fitness.

## 6. Dataset/eval governance

Where DELPI owns or governs training/eval datasets, require source/owner/version/licensing/privacy, train/eval separation, leakage controls, representativeness, sensitive-data governance, retention and reproducibility as applicable.

Biometric/people-related models remain under stricter boundaries from `54`.

## 7. Deployment governance

Potential technical targets:

```text
central runtime
provider API
batch worker
Automation Hub technical executor when applicable
Edge runtime/device
```

Deployment metadata does not grant business authority. Every deployment keeps owner/version/environment/cohort/health/rollback/revoke refs where applicable.

## 8. Marketplace scope

Potential reusable assets:

```text
Expertise Packs
Domain Playbooks
Watches
Automation capability definitions
Connector packs
MCP/A2A integrations
Analysis templates
Artifact templates
Semantic metric packs
Frontline skills
approved model packages
```

Marketplace is catalog/governance experience over owner-controlled assets. `publish != enable`, `enable != permission`, `install != authorization`.

## 9. Marketplace lifecycle

Possible candidate semantics:

```text
DRAFT
→ REVIEW
→ APPROVED
→ PUBLISHED
→ DEPRECATED
→ REVOKED
```

Do not create parallel lifecycle when asset owner already has one. Local enablement may still require owner configuration, compatibility, RBAC, Policy and Decision gates.

## 10. Package manifest candidate

```text
assetRef/version/type
name/description
owner/publisher
required capabilities
required permissions/scopes
required data classifications
config schema
dependencies
compatibility
risk tier
eval/test refs
release notes
signature/hash refs when applicable
```

Declared permissions are requirements, not grants. No package may carry broad credentials or silently expand scopes.

## 11. Supply-chain security

Executable assets require controls appropriate to risk, including:

- trusted publisher/owner;
- integrity/hash/signature where applicable;
- dependency inventory;
- vulnerability/license review;
- sandbox/review for executable assets;
- explicit revoke/rollback path;
- no automatic external-marketplace activation into production.

Package/tool metadata remains untrusted for system/policy.

## 12. Model Router integration

Model Router chooses only among **approved and currently available** model refs under Compute Policy. It cannot make revoked/unapproved model usable because it is cheaper/faster.

Router selection != model approval.

## 13. Control Tower integration

Control Tower may project inventory/health/risk/cost/usage/quality/incidents/rollout/kill-switch/ownership refs from authoritative owners. It does not become deployment or model lifecycle authority by projection.

## 14. C0 inventory

Inventariar factual:

- existing model providers/accounts;
- local ML models/notebooks/services;
- model registries/MLOps tooling;
- CI/CD/deployment paths for models;
- datasets/eval suites;
- Edge model deployment mechanisms;
- current templates/plugins/catalogs;
- artifact/package signing;
- software supply-chain controls;
- ownership/approval processes.

Sem evidence suficiente = `TO_INVENTORY`.

## 15. Phase mapping

```text
C0 → model/tooling/dataset/catalog/supply-chain inventory + owner/lifecycle contracts
C3 → model/eval-lineage projections only when justified
C4/C5 → approved model use tied to Evidence/Decision/Outcome and risk policy
C6 → Control Tower model views + Marketplace draft/review/catalog UX
C7 → mature deployment/drift/rollback/revoke, Edge rollout and governed publish/enable; L5 remains separately scoped
```

## 16. Acceptance

Quando implementado, provar:

- every active production model is traceable to owner/version/eval/deployment refs;
- revoked/unapproved model cannot be newly selected;
- rollback/revoke reaches authoritative deployment owner;
- drift can truthfully degrade/disable affected capability;
- Marketplace asset declares dependencies/required permissions/data scopes without granting them;
- install/publish/enable cannot grant business permission;
- malicious/untrusted executable package is blocked;
- Edge/cloud deployments remain independently traceable;
- Marketplace/Control Tower do not become second planner or execution authority.

Sem prova obrigatória: `PENDING`/`INCONCLUSIVE`.

## 17. North Star

> **A DELPI deve tratar modelos e reusable capabilities como ativos digitais governados, versionados, avaliados, observáveis e revogáveis sem permitir que catálogo, pacote, modelo ou deployment amplie authority por conta própria.**
