# Minha DELPI Copilot — AI Model Lifecycle e Capability Marketplace

**Status:** thematic MLOps/product/governance spec  
**Order authority:** [`16-execution-master-plan.md`](./16-execution-master-plan.md)  
**Model Router:** [`42-model-router-and-compute-policy.md`](./42-model-router-and-compute-policy.md)  
**Control Tower:** [`59-ai-control-tower-and-digital-workforce-governance.md`](./59-ai-control-tower-and-digital-workforce-governance.md)

## 1. Decisão

A DELPI deve governar o ciclo de vida de **todos os modelos de IA relevantes**, não apenas LLMs, e oferecer uma evolução controlada para descoberta/reuso de capabilities aprovadas.

Separar:

```text
MODEL LIFECYCLE
= build/evaluate/approve/deploy/monitor/rollback models

CAPABILITY MARKETPLACE
= discover/install/enable governed reusable capabilities/assets
```

## 2. Model families

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

## 3. Model registry metadata

```text
modelId/version
family/provider
owner
purpose
training/source lineage when DELPI-owned
approved data classes
runtime/deployment refs
quality metrics
eval suite/version
latency/cost profile
risk tier
status
approved environments
createdAt/approvedAt
rollbackRef
```

Provider-hosted models still require bounded registry/projection metadata.

## 4. Lifecycle

```text
DRAFT/EXPERIMENT
→ EVALUATED
→ APPROVED
→ DEPLOYED
→ MONITORED
→ DEGRADED | DEPRECATED | REVOKED
→ ROLLED_BACK/RETIRED
```

Promotion requires evidence appropriate to risk.

## 5. Drift and performance

Track by model type:

```text
quality drift
input/data drift
calibration drift
latency
availability
cost
error rate
human correction rate
business outcome correlation
```

No single generic “AI score” is sufficient.

## 6. Dataset/eval governance

Where DELPI owns training/eval datasets:

- dataset owner/version;
- source/licensing/privacy;
- train/eval separation;
- leakage controls;
- representativeness;
- sensitive attribute governance;
- retention;
- reproducibility.

Biometric/people-related models remain under stricter rules from `54`.

## 7. Deployment governance

Deployment can target:

```text
central cloud/runtime
provider API
batch worker
Automation Hub
Edge device/runtime
```

Each deployment has version, environment, cohort, health, rollback and kill switch.

## 8. Marketplace scope

Potential reusable assets:

```text
Expertise Packs
Domain Playbooks
Watches
Automation capabilities
Connector packs
MCP server integrations
A2A agent integrations
Analysis templates
Artifact templates
Semantic metric packs
Frontline skills
approved model packages
```

Marketplace is catalog/governance, not permission bypass.

## 9. Marketplace lifecycle

```text
DRAFT
→ REVIEW
→ APPROVED
→ PUBLISHED
→ DEPRECATED
→ REVOKED
```

Install/enable can still require local owner/configuration/RBAC.

## 10. Package manifest candidate

```text
assetId/version/type
name/description
owner/publisher
required capabilities
required permissions/scopes
data classifications
config schema
dependencies
compatibility
risk tier
evals/tests
release notes
signature/hash?
```

No package may smuggle broad credentials or hidden permissions.

## 11. Supply-chain security

- trusted publisher/owner;
- package hash/signature when applicable;
- dependency inventory;
- vulnerability/license checks;
- sandbox/review for executable assets;
- revocation path;
- no automatic production activation from external marketplace.

## 12. Model Router integration

Model Router chooses among **approved/available** models under Compute Policy. It cannot select revoked/unapproved model because it is cheaper/faster.

## 13. Control Tower integration

Control Tower consumes registry/deployment/marketplace metadata and exposes:

```text
inventory
health
risk
cost
usage
quality
incidents
rollout
kill switches
ownership
```

## 14. C0 inventory

Inventariar:

- existing model providers/accounts;
- local ML models/notebooks/services;
- model registries/MLOps tooling;
- CI/CD for models;
- datasets/eval suites;
- Edge model deployment mechanisms;
- current templates/plugins/catalogs;
- artifact/package signing;
- software supply-chain controls;
- ownership/approval process.

## 15. Phase mapping

```text
C0 → model/tooling/dataset/catalog/supply-chain inventory and lifecycle contracts
C3 → model registry projection/eval lineage foundations
C4/C5 → model use tied to Evidence/Outcome and risk policy
C6 → Control Tower model views + Marketplace draft/review/catalog UX
C7 → mature deployment/drift/rollback, Edge rollout and governed marketplace publish/enable
```

## 16. Acceptance

- every production model is version/owner traceable;
- revoked model cannot be newly selected;
- model rollback is reproducible/auditable;
- drift can degrade/disable capability truthfully;
- Marketplace asset declares dependencies/permissions/data scopes;
- installing asset cannot grant permission by itself;
- malicious/untrusted executable package is blocked from production;
- Edge and cloud versions are traceable independently.

## 17. North Star

> **A DELPI deve tratar modelos, skills, automações e integrações como ativos digitais governados: versionados, avaliados, observáveis, reutilizáveis e revogáveis.**
