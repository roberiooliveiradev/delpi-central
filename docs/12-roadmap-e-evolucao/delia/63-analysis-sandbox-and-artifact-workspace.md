# DÉLIA — Analysis Sandbox e Artifact Workspace

**Status:** `TARGET` — thematic product/security/architecture spec  
**Order authority:** [`16-execution-master-plan.md`](./16-execution-master-plan.md)  
**Evidence:** [`38-evidence-provenance-and-epistemic-ux.md`](./38-evidence-provenance-and-epistemic-ux.md)  
**Security:** [`08-security-autonomy-audit.md`](./08-security-autonomy-audit.md)

## 1. Decisão de produto

A DÉLIA não deve se limitar a texto conversacional. A visão alvo inclui análises temporárias governadas e artefatos de trabalho editáveis/rastreáveis.

Separar:

```text
ANALYSIS SANDBOX
= ambiente efêmero/bounded para cálculo e análise

ARTIFACT WORKSPACE
= lifecycle governado de objetos de trabalho
```

A documentação não prova que sandbox, workspace, storage ou generators já existam.

## 2. Analysis Sandbox target

Capabilities candidatas, conforme C0 provar owner/runtime/security:

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

Sandbox nunca é shell corporativo irrestrito nem caminho alternativo para burlar Domain APIs, Core, provider scopes ou network policy.

## 3. Sandbox isolation

Quando implementado, exigir conforme risco:

- isolated runtime/container/session;
- no unrestricted host/private-network access;
- approved egress only;
- bounded/copy-on-read inputs where appropriate;
- no broad source/provider credentials;
- secrets protected behind approved adapters when strictly required;
- CPU/memory/time/storage quotas;
- file type/size limits;
- package/library policy;
- malware/safe-file ingestion controls;
- deterministic/reproducible environment metadata where required;
- cleanup/expiry.

Generated code/query is untrusted execution input.

## 4. Data access

Target:

```text
authorized read through source owner contract
→ bounded dataset/artifact
→ sandbox
→ calculation
→ Evidence/Artifact candidate
```

Row/resource-level permissions are enforced before data enters the sandbox. Sandbox does not receive arbitrary production DB credentials or authorization authority.

## 5. Reproducibility

Candidate metadata, only if needed by consumers:

```text
analysisRunRef
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

Do not create schema/repository unless C0/Abstraction Gate proves need. No hidden chain-of-thought is required for reproducibility.

## 6. Artifact Workspace target

Artifact families can include:

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

Exact formats/capabilities are contract-driven and do not become planner branches.

## 7. Artifact lifecycle

Possible lifecycle semantics:

```text
DRAFT
→ REVIEWED
→ APPROVED/PUBLISHED when applicable
→ SUPERSEDED/ARCHIVED
```

This is a candidate, not a universal state machine. Reuse owner lifecycle when one already exists; do not create parallel document authority.

## 8. Source lineage

Artifact material should preserve enough refs to reconstruct provenance without copying source truth unnecessarily:

```text
artifactRef/version
owner/source authority
sourceRefs/evidenceRefs
analysisRunRef?
createdBy actor/service
status
createdAt/updatedAt
sensitivity
retention
```

Generated content never hides which sources/calculations support material claims.

## 9. Editability and human collaboration

Human edits are first-class. Regeneration must not silently overwrite them.

When material, distinguish:

```text
AI-generated content
human-edited content
recomputed sections
stale source-dependent sections
```

## 10. Artifact actions

Artifact can enter governed Work:

```text
create draft
→ review/comment
→ attach/reference in Task/Case/Room/Meeting
→ export/share under ACL
→ publish via owner contract when applicable
```

External share/email/Teams send remains separate governed action. `draft != send`.

## 11. Analysis safety

Required controls when applicable:

- sandbox boundary;
- file/path restrictions;
- query timeout/row budgets;
- no arbitrary DDL/DML via read-analysis connector;
- no unrestricted shell/network;
- secret redaction;
- output size/classification limits;
- truthful failure instead of fabricated result;
- source permissions revalidated outside the generated code.

## 12. C0 inventory

Inventariar factual:

- existing Python/Jupyter/code-execution services;
- container sandbox infrastructure;
- BI/query engines;
- document/spreadsheet/presentation generation utilities;
- object/file storage;
- antivirus/file scanning;
- artifact collaboration/versioning systems;
- export/share policies;
- data science/modeling platforms;
- existing owner lifecycles for documents/artifacts.

Sem evidence suficiente = `TO_INVENTORY`.

## 13. Phase mapping

```text
C0 → sandbox/security/storage/artifact-owner inventory + contract decisions
C3 → minimal safe analysis/artifact primitives only when justified
C4 → read-only analysis pilots with Evidence/reproducibility
C5 → artifact generation/versioning/Work integration; external send remains separately governed
C6 → Artifact Workspace UX/collaboration/templates where validated
C7 → scaled/advanced optimization and simulation workloads under same isolation boundaries
```

## 14. Acceptance

Quando implementado, provar:

- sandbox cannot reach blocked internal targets;
- read analysis cannot mutate source systems;
- unauthorized data never enters sandbox;
- generated code cannot widen permissions;
- analysis result is reproducible when required or clearly marked otherwise;
- artifact preserves source lineage;
- human edit is not silently overwritten;
- generated file uses ACL/retention/export policy;
- failure never becomes fabricated numerical result.

Sem prova obrigatória: `PENDING`/`INCONCLUSIVE`.

## 15. North Star

> **DÉLIA deve transformar problemas complexos em análises reproduzíveis e artefatos úteis sem ganhar shell irrestrito, credenciais amplas, source authority ou lifecycle paralelo.**
