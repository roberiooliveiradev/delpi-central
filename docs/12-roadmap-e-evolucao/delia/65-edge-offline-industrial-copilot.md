# DÉLIA — Edge/Offline Industrial

**Status:** `TARGET` — thematic industrial/reliability/security spec  
**Order authority:** [`16-execution-master-plan.md`](./16-execution-master-plan.md)  
**Industrial/Frontline:** [`53-multimodal-meeting-frontline-and-industrial-copilot.md`](./53-multimodal-meeting-frontline-and-industrial-copilot.md)  
**Autonomous Operations:** [`57-event-driven-autonomous-operations-and-automation-execution-hub.md`](./57-event-driven-autonomous-operations-and-automation-execution-hub.md)

## 1. Decisão

A DÉLIA industrial não deve assumir conectividade cloud contínua. A visão alvo pode incluir **Edge/Offline assistance** para cenários aprovados, sem criar um segundo produto autônomo nem ampliar authority pela perda de conectividade.

```text
DÉLIA central governance/intelligence
+
governed Edge capability/runtime when proven necessary
```

Edge é deployment/runtime boundary potencial, não permission authority, business owner ou safety controller.

## 2. Edge capabilities possíveis

Candidates, conforme hardware/policy/owner reais:

```text
cached current procedures/drawings
bounded local search/index
local STT/TTS optional
vision inference
anomaly/classifier inference
machine telemetry reads via approved adapters
FAST deterministic rules
frontline UI/local session support
event buffering
store-and-forward sync
```

A lista é `TARGET`; não prova runtime, devices, models ou package manager existentes.

## 3. Offline modes

Estados candidatos, a congelar somente se houver lifecycle real:

```text
ONLINE
DEGRADED
OFFLINE_READ_ONLY
OFFLINE_BOUNDED_ACTIONS only when separately approved
SYNCING
```

Modo deve ser visível quando material. Dado stale não é apresentado como current fact.

## 4. Cache/freshness

Conteúdo offline material deve manter source/version/freshness/retention suficientes para evitar uso enganoso.

Candidate refs:

```text
sourceRef
version/revision
syncedAt
validUntil?
retention
signature/hash where relevant
```

Procedimento/desenho stale deve ser bloqueado ou sinalizado conforme owner/policy/criticidade.

## 5. Offline authorization

C0 deve inventariar requisitos reais de continuidade; qualquer future offline authority precisa de policy explícita e boundary própria.

Defaults:

- loss of cloud never widens permission;
- session/user identity cannot be invented;
- cached permission is not indefinite authority;
- high-risk action requires live central/domain validation unless a separately approved bounded offline contract exists;
- biometric candidate does not authenticate/authorize;
- provider/model/device state does not grant business permission;
- OT safety remains independent.

## 6. Event buffering

Target, quando necessário:

```text
local event
→ validate/classify
→ bounded durable buffer
→ dedupe/idempotency metadata
→ sync when authorized link returns
→ central EventEnvelope processing
```

Ordering, duplicates, clock drift, retention e reconciliation precisam de contrato explícito. Buffered event não autoriza ACT.

## 7. Edge model/package deployment

Candidate metadata:

```text
model/package ref + version
approved device class
runtime compatibility
hash/signature
rollout cohort
rollback ref
health
last sync
owner
```

Model/package deployment é capability técnica governada. Instalar modelo não concede permission nem altera policy.

No uncontrolled public-source download to production devices.

## 8. Device management

Se device projection/registry for necessário, C0 deve provar owner/source/consumer antes da criação.

Candidate fields:

```text
deviceRef
class/location
owner
OS/runtime
hardware accelerators
network zone
allowed technical capabilities
current package/model versions
health
last seen
```

Device identity != user identity. Technical device capability != business authority.

## 9. Security

Quando aplicável:

- signed artifacts/packages;
- encrypted local sensitive data;
- no long-lived broad secrets;
- protected device/service identity;
- remote revoke/disable where feasible;
- physical tamper considerations;
- network segmentation respected;
- bounded/redacted logs;
- local personal/session data cleanup;
- no secrets in prompts/models/ordinary telemetry.

## 10. Industrial boundary

DÉLIA/Edge may observe, explain and recommend. Physical control stays with approved industrial/safety systems.

```text
free-form Edge LLM/vision/voice
-X→ PLC/CNC/robot/machine command
```

Any future physical actuation requires a separate industrial safety initiative with deterministic typed commands, independent interlocks, approved owner, risk assessment, testing/simulation, fail-safe and audit.

Enterprise autonomy level never implies physical authority.

## 11. C0 inventory

Inventariar factual:

- factory connectivity/reliability;
- current Edge platforms/gateways;
- production PCs/tablets/kiosks;
- GPU/NPU/CPU capabilities;
- local storage;
- MDM/device management;
- OT segmentation/firewalls;
- local inference runtimes/models;
- procedure/drawing distribution;
- time synchronization;
- credential/device identity patterns;
- offline business continuity requirements;
- industrial safety owners/boundaries.

Sem evidence suficiente = `TO_INVENTORY`.

## 12. Phase mapping

```text
C0 → device/network/OT/offline/edge inventory + trust/safety boundary decisions
C3 → minimal Edge/device/package contracts only when justified
C4 → read-only cached knowledge/telemetry pilots
C6 → Frontline offline assistance, buffering/sync and device-admin pilots
C7 → scaled Edge/local models and bounded offline ACT only if separately authorized; L5/enterprise autonomy does not grant OT authority
```

## 13. Acceptance

Quando implementado, provar:

- offline/degraded state is explicit;
- stale revision is detected and handled by policy;
- user switch clears personal/session state;
- buffered events reconcile idempotently;
- revoked package/model is unavailable after defined enforcement point;
- edge model/package/device versions are traceable;
- no unrestricted local secret exposure;
- loss of cloud does not widen authority;
- device/model metadata cannot grant permission;
- safety command boundary remains enforced.

Sem prova obrigatória: `PENDING`/`INCONCLUSIVE`.

## 14. North Star

> **DÉLIA deve continuar útil em ambientes industriais com conectividade limitada sem transformar Edge/offline em authority paralela, permissão ampliada ou caminho para contornar segurança industrial.**
