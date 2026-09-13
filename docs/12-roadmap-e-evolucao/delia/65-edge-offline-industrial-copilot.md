# Minha DELPI Copilot — Edge/Offline Industrial Copilot

**Status:** thematic industrial/reliability/security spec  
**Order authority:** [`16-execution-master-plan.md`](./16-execution-master-plan.md)  
**Industrial/Frontline:** [`53-multimodal-meeting-frontline-and-industrial-copilot.md`](./53-multimodal-meeting-frontline-and-industrial-copilot.md)  
**Autonomous Operations:** [`57-event-driven-autonomous-operations-and-automation-execution-hub.md`](./57-event-driven-autonomous-operations-and-automation-execution-hub.md)

## 1. Decisão

O Copilot industrial não deve assumir conectividade cloud contínua. O target deve suportar **Edge/Offline assistance** para cenários aprovados, preservando o Copilot central como authority de produto/governança.

```text
Cloud Copilot
+ governed Edge Runtime
```

Edge não é um segundo Copilot autônomo irrestrito.

## 2. Edge capabilities possíveis

Conforme hardware/policy:

```text
cached current procedures/drawings
bounded local search/index
local STT/TTS optional
vision inference
anomaly/classifier inference
machine telemetry reads via approved adapters
FAST PATH rules
frontline UI/local session support
event buffering
store-and-forward sync
```

## 3. Offline modes

```text
ONLINE
DEGRADED
OFFLINE_READ_ONLY
OFFLINE_BOUNDED_ACTIONS when explicitly approved
SYNCING
```

Modo deve ser visível ao usuário. Não apresentar dado antigo como atual.

## 4. Cache/freshness

Todo conteúdo offline material possui:

```text
sourceRef
version/revision
syncedAt
validUntil?
retention
signature/hash where relevant
```

Procedimento/desenho stale deve ser bloqueado ou sinalizado conforme criticidade.

## 5. Offline authorization

C0/C7 devem decidir quais proofs podem existir offline. Por default:

- session/user identity cannot be invented;
- cached permission is not indefinite authority;
- high-risk action requires fresh central/domain validation unless explicit bounded offline policy exists;
- biometric candidate still does not grant authorization;
- OT safety remains independent.

## 6. Event buffering

```text
local event
→ validate/classify
→ append bounded buffer
→ dedupe/idempotency key
→ sync when link returns
→ central EventEnvelope/Workflow
```

Ordering, duplicate delivery and clock drift need explicit handling.

## 7. Edge model deployment

Model/package deployment requires:

```text
modelRef/version
approved device class
runtime compatibility
hash/signature
rollout cohort
rollback version
health
last sync
```

No uncontrolled model download from public source to production device.

## 8. Device management

Need inventory for:

```text
deviceRef
class/location
owner
OS/runtime
hardware accelerators
network zone
allowed capabilities
current package/model versions
health
last seen
```

Device identity != user identity.

## 9. Security

- signed artifacts/packages where applicable;
- encrypted local data at rest when sensitive;
- no long-lived broad secrets on device;
- remote revoke/disable where feasible;
- physical tamper risk considered;
- network segmentation respected;
- local logs bounded/redacted;
- offline data cleared according to retention/user switch policy.

## 10. Industrial boundary

Edge Copilot may observe/explain/recommend. Physical control stays with approved industrial/safety systems.

```text
Edge LLM/vision
-X→ free-form machine command
```

Any future bounded actuation needs separate industrial safety initiative and deterministic contract.

## 11. C0 inventory

Inventariar:

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
- offline business continuity requirements.

## 12. Phase mapping

```text
C0 → device/network/OT/offline/edge inventory and trust boundaries
C3 → Edge contracts/package/model/device projection foundations
C4 → read-only cached knowledge/telemetry pilots
C6 → Frontline offline assistance, buffering, sync and device admin pilots
C7 → scaled Edge deployment, local models, bounded offline actions only if separately approved
```

## 13. Acceptance

- offline mode visibly declared;
- stale revision detected;
- user switch clears local personal context;
- buffered events sync idempotently;
- revoked package/model cannot continue after enforcement point;
- edge model/version traceable;
- no unrestricted local secret exposure;
- loss of cloud does not silently widen authority;
- safety command boundary remains enforced.

## 14. North Star

> **O Copilot deve continuar útil no chão de fábrica mesmo com conectividade limitada, sem sacrificar atualização, identidade, segurança ou autoridade industrial.**
