# Minha DELPI Copilot — Governança Documental e Revisão Arquitetural

**Status:** canônico para precedência documental  
**Revisão:** foundation-first + standalone + multimodal/biometric/external/industrial boundaries  
**Ordem:** [`16-execution-master-plan.md`](./16-execution-master-plan.md)

## 1. Objetivo

Evitar ordens, owners, contracts, patterns, security/privacy/external-data boundaries concorrentes.

## 2. Precedência

Em caso de conflito:

```text
1. instruções oficiais + .cursor rules
2. 16 — ordem/dependências
3. 50 — standalone product/runtime boundary
4. 17 — ownership/primitives/contracts
5. 49 — architecture/patterns
6. 51 — factual platform baseline
7. 52 — repository/bootstrap target
8. 21 — state/persistence
9. 20 — tests/gates
10. 25 — CP requirements
11. 02 — technical target
12. 24 — product target
13. thematic specs, including 53/54/55
14. ledger — execution evidence/status
```

Ledger registra estado; não redefine arquitetura.

## 3. Authorities operacionais

| Arquivo | Authority |
|---|---|
| `16` | única ordem C0–C7 |
| `50` | standalone boundary |
| `17` | owners/primitives/contracts |
| `49` | code architecture/patterns |
| `51` | factual platform baseline |
| `52` | physical/bootstrap target |
| `20` | tests/gates |
| `21` | state/persistence/media/biometric/external refs |
| `23` | Cursor master prompt |
| `25` | requirements `CP-001…CP-214` |
| ledger | current execution/evidence |

## 4. Specs temáticas relevantes

```text
53 multimodal/Meeting/Frontline/industrial
54 biometric identity/Human Observation
55 Internet Research/external connectors/OAuth/external learning
```

`55` não cria outra ordem, outro requirement matrix ou outro action executor. Sua implementação é materializada exclusivamente por `16`.

## 5. Findings arquiteturais já corrigidos

### F1 — Multiple execution authorities
`16` é única authority de ordem.

### F2 — Shared primitives tardios
Entity/Evidence/Decision/Workflow/Event antecipados para foundation.

### F3 — Chat tratado como base
Superseded: Copilot é standalone API/MFE/persistence/deploy próprios.

### F4 — Architecture inferred by feature
`49` congela layers/patterns/Abstraction Gate.

### F5 — Multimodal/Frontline tardio
Media/privacy/device/OT boundaries entram em C0.

### F6 — Biometric identity poderia virar auth paralela
`54`: biometric match é candidate association; Core/Keycloak continuam authority.

### F7 — Human Observation poderia virar worker profiling
`54`: somente sinais observáveis do processo; no sensitive/psychological inference or automatic employment decision.

### F8 — Internet poderia virar HTTP irrestrito
`55`: pesquisa passa por Search + Safe Fetch + egress policy; content externo é untrusted.

### F9 — Connectors poderiam hardcodar provider no planner
`55` + `49`: semantic connector capabilities + provider adapters; no `if gmail/outlook/whatsapp` no planner.

### F10 — OAuth scope poderia ser confundido com RBAC
Corrigido: provider scope é connection-specific e não altera Core permissions.

### F11 — Tokens poderiam contaminar state/LLM/MFE
Corrigido: Secret/Vault boundary + `secretRef`; credentials nunca são prompt/context/ordinary log data.

### F12 — Conta pessoal poderia virar source corporativo
Corrigido: USER_DELEGATED/ORG_MANAGED/SHARED_RESOURCE/SERVICE_CONNECTION possuem ownership e visibility distintos.

### F13 — Read e send poderiam convergir cedo demais
Corrigido: read/write capabilities separadas; `draft != send`; writes usam Policy/Decision/outcome verification.

### F14 — Webhooks poderiam virar action channel paralelo
Corrigido: provider event → validation → EventEnvelope → dedupe/reconciliation → Watch/Workflow. Event payload nunca autoriza write.

### F15 — “Aprender com internet” poderia auto-publicar truth
Corrigido: transient research ou Knowledge candidate; organizational publish exige governance/freshness/privacy/licensing.

### F16 — WhatsApp pessoal poderia induzir scraping frágil
Corrigido: target default usa contratos oficiais suportados, especialmente WhatsApp Business Platform quando aplicável.

## 6. Foundation invariants

Após C0.S7:

```text
one Copilot runtime/API
one Copilot MFE
Core = platform authorization authority
Keycloak = identity authority
Domain API = business authority
External provider = external resource authority
Portal = navigation/hosting authority
OpenAPI = business action technical source
SourceRef/EvidenceRef = cross-source provenance
ExternalConnection = explicit owner/scopes/lifecycle
Secret material = protected secret owner
Internet Research = safe egress + provenance
External content = untrusted
provider scope != Core permission
personal connection != organizational source
read != write
draft != send
provider event != write authorization
external Knowledge = candidate before publish
Chat runtime dependency = zero
OT free-form actuation = blocked
```

## 7. Reading minimization

### Sempre

```text
official rules
applicable .cursor rules
README
16
50
17
49
20 applicable section
25 applicable CPs
ledger
```

### C0/C1

```text
51
52
53/54/55 because C0 inventories all corresponding boundaries
```

### State/persistence

```text
21
```

### External feature step

```text
55
+ relevant 16 step
+ relevant 20 gate
+ relevant CPs 194–214
```

## 8. Future-doc rule

Every new doc declares status/order authority/standalone boundary and relevant thematic authority.

Thematic doc may not:

- create another phase sequence/CP matrix/test matrix/master prompt;
- redefine shared primitive silently;
- introduce Chat runtime dependency;
- create duplicate Core/domain/provider authority;
- move AI/connector intelligence into Portal;
- store credentials in normal state;
- create provider-specific planner routing;
- make personal source organizational implicitly;
- convert event/web content into action authority;
- weaken biometric/privacy/OT boundaries.

## 9. Current executable state

```text
C0.S0 platform/monorepo/media/device/biometric/external/OT inventory
→ C0.S1 standalone boundary/names
→ C0.S2 authorities
→ C0.S3 primitives/refs
→ C0.S4 architecture/persistence/privacy/egress/OAuth/secrets
→ C0.S5 integration contracts
→ C0.S6 RED harness including external negatives
→ C0.S7 FOUNDATION_FREEZE
→ C1.S1 standalone API skeleton
```

No runtime implementation before this sequence permits it.
