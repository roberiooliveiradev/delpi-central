# Minha DELPI Copilot — Analysis Sandbox e Artifact Workspace

**Status:** thematic product/security/architecture spec  
**Order authority:** [`16-execution-master-plan.md`](./16-execution-master-plan.md)  
**Evidence:** [`38-evidence-provenance-and-epistemic-ux.md`](./38-evidence-provenance-and-epistemic-ux.md)  
**Security:** [`08-security-autonomy-audit.md`](./08-security-autonomy-audit.md)

## 1. Decisão de produto

O Copilot não deve se limitar a texto conversacional. Ele deve poder executar análises temporárias governadas e produzir **artefatos de trabalho editáveis e rastreáveis**.

Separar:

```text
ANALYSIS SANDBOX
= ambiente efêmero para cálculo/análise

ARTIFACT WORKSPACE
= objetos de trabalho persistíveis/versionáveis
```

## 2. Analysis Sandbox target

Capacidades possíveis, conforme policy:

```text
Python
SQL por adapters aprovados
DataFrames
estatística
forecasting
optimization
chart generation
CSV/Excel parsing
bounded file transforms
```

Não é shell corporativo irrestrito.

## 3. Sandbox isolation

Required:

- isolated runtime/container/session;
- no unrestricted host/network access;
- approved egress only;
- mounted inputs are bounded/copy-on-read where appropriate;
- no provider/core secrets injected unless specific adapter requires and shields them;
- CPU/memory/time/storage quotas;
- file type/size limits;
- package/library policy;
- malware/safe file ingestion;
- deterministic/reproducible environment metadata;
- cleanup/expiry.

## 4. Data access

Sandbox receives data through authorized capabilities/exports, not arbitrary database credentials.

```text
authorized read
→ bounded dataset/artifact
→ sandbox
→ calculation
→ Evidence/Artifact
```

Row/resource-level permissions remain enforced before data enters sandbox.

## 5. Reproducibility

Material analysis stores enough metadata to reproduce when policy requires:

```text
analysisRunId
input SourceRefs/EvidenceRefs
code/notebook/artifact hash bounded
runtime image/version
library versions
timezone/locale
parameters
outputs
createdAt
owner
retention class
```

No hidden chain-of-thought required.

## 6. Artifact Workspace target

Supported artifact families can include:

```text
report/document
spreadsheet/table
presentation
PDF/export
chart/dashboard snapshot
process map/BPMN candidate
A3 / 8D / FMEA candidate
checklist
procedure draft
project plan
decision memo
meeting minutes
data analysis package
```

Exact formats are capability-driven, not hardcoded into planner logic.

## 7. Artifact lifecycle

```text
DRAFT
→ REVIEWED
→ APPROVED/PUBLISHED when applicable
→ SUPERSEDED/ARCHIVED
```

Not every artifact needs approval. Policy depends on type/impact.

## 8. Source lineage

Artifact must preserve material provenance:

```text
artifactId/version
owner
sourceRefs/evidenceRefs
analysisRunRef?
createdBy user/service/Copilot
status
createdAt
updatedAt
sensitivity
retention
```

A generated report cannot hide which sources/calculations supported material claims.

## 9. Editability and human collaboration

User can edit generated artifact. After material manual edits, distinguish:

```text
AI-generated content
human-edited content
recomputed sections
stale source-dependent sections
```

Do not silently overwrite human changes on regeneration.

## 10. Artifact actions

Artifact can enter workflow:

```text
create draft
→ review/comment
→ attach to Case/Task/Room/Meeting
→ export/share under ACL
→ publish if governed
```

External share/email/Teams send remains separate governed action.

## 11. Analysis safety

Generated code/query is untrusted execution input. Required checks include:

- sandbox boundary;
- file/path restrictions;
- query timeout/row budgets;
- no arbitrary DDL/DML through read analysis connector;
- redaction of secrets;
- output size limits;
- user-visible failure instead of fabricated result.

## 12. C0 inventory

Inventariar:

- existing Python/Jupyter/code-execution services;
- container sandbox infrastructure;
- BI/query engines;
- document/spreadsheet/presentation generation utilities;
- object/file storage;
- antivirus/file scanning;
- artifact collaboration/versioning systems;
- export/share policies;
- data science packages/modeling platforms.

## 13. Phase mapping

```text
C0 → sandbox/security/storage/artifact-owner inventory and contracts
C3 → safe analysis execution foundation and artifact primitive decisions
C4 → read-only analysis with Evidence and reproducibility pilots
C5 → artifact generation/versioning/workflow integration; external send remains governed
C6 → full Artifact Workspace UX/collaboration/templates
C7 → advanced optimization/simulation workloads and scaled sandbox pools
```

## 14. Acceptance

- sandbox cannot reach blocked internal targets;
- read analysis cannot mutate source system;
- unauthorized data never enters sandbox;
- analysis result is reproducible or clearly marked non-reproducible;
- artifact preserves source lineage;
- human edit is not silently overwritten;
- generated file can be attached/exported under ACL;
- failure never becomes fabricated numerical result.

## 15. North Star

> **O Copilot deve transformar perguntas complexas em análises reproduzíveis e trabalho entregue — planilhas, relatórios, apresentações, mapas e documentos — não apenas em mensagens de chat.**
