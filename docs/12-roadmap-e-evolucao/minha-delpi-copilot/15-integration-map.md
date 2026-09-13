# 15 — Mapa de integração com a Minha DELPI

**Ordem:** [`16-execution-master-plan.md`](./16-execution-master-plan.md)  
**Boundary:** [`50-standalone-copilot-application-architecture.md`](./50-standalone-copilot-application-architecture.md)  
**Internet/External Connectors:** [`55-internet-research-and-external-connectors.md`](./55-internet-research-and-external-connectors.md)

## 1. Mapa macro

```text
                           ┌──────────────┐
                           │   Keycloak   │
                           └──────┬───────┘
                                  │
                                  ▼
┌───────────┐     ┌────────────────────────────┐     ┌──────────────┐
│  Portal   │────▶│ Minha DELPI Copilot MFE    │────▶│   Gateway    │
└─────┬─────┘     └────────────────────────────┘     └──────┬───────┘
      │                                                      │
      ▼                                                      ▼
┌───────────┐                                     ┌──────────────────────┐
│ Core API  │◀────────────────────────────────────│ Copilot Standalone API│
└───────────┘                                     └───────┬──────────────┘
                                                         │
       ┌──────────────────────┬───────────────────────────┼────────────────────────┐
       ▼                      ▼                           ▼                        ▼
 Domain APIs/OpenAPI     Public Internet           External Providers       AI/Media/Biometric
 business authority     search + safe fetch        OAuth/API/Webhooks       providers/stores
       │                      │                           │                        │
       └──────────────────────┴───────────────────────────┴────────────────────────┘
                                                         │
                                                         ▼
                                            Evidence / Graph / Durable Work
```

## 2. Portal ↔ Copilot

Portal hospeda/navega/contextualiza. Copilot MFE recebe host contract e conversa somente com a Copilot API para intelligence/work/external features.

Portal não contém planner, connector tokens, provider SDKs, search logic ou secret storage.

## 3. Copilot ↔ Core

Core continua authority de apps/routes/RBAC/user context. External provider scope não modifica Core permissions.

## 4. Copilot ↔ Domain APIs

```text
OpenAPI
→ Action Catalog
→ authorized capability
→ Planner/Policy
→ generic executor
→ Domain API
→ Outcome/Evidence
```

## 5. Copilot ↔ Public Internet

```text
Research intent
→ SearchProviderPort
→ search results
→ SafeWebFetchPort
→ SourceRef/EvidenceRef
→ synthesis
```

Regras:

- egress validation;
- protected/internal destinations blocked;
- external content untrusted;
- freshness/provenance;
- no arbitrary unrestricted HTTP from LLM.

## 6. Copilot ↔ External Providers

```text
User/Admin connect
→ OAuth/API authorization
→ ExternalConnection
→ protected secretRef
→ Provider Adapter
→ semantic connector capabilities
```

Provider examples when approved:

```text
Microsoft 365 / Outlook / OneDrive / SharePoint / Teams
Google Workspace / Gmail / Calendar / Drive
WhatsApp Business Platform
Slack
GitHub
other future providers
```

## 7. External Reads

```text
semantic capability
→ connection/scope check
→ provider adapter
→ normalized resource
→ SourceRef/EvidenceRef
```

No mailbox/Drive master copy inside Copilot.

## 8. External Writes

```text
intent
→ draft/preview
→ Policy/Decision Gate
→ connection/scope revalidation
→ provider adapter
→ verified Outcome
```

`draft != send`.

## 9. Provider Events

```text
Provider webhook/push/subscription
→ interface/provider validation
→ EventEnvelope
→ dedupe/correlation
→ Watch/Inbox/Workflow
```

Subscription renewal/reconciliation/permission revocation are explicit lifecycle responsibilities.

## 10. Secret/Vault integration

```text
Copilot ExternalConnection
→ secretRef
→ approved Secret/Vault owner
→ credential used only inside provider adapter boundary
```

Credential never goes to LLM/MFE/ordinary log.

## 11. Source/Evidence integration

Internal and external information converge on shared provenance contracts:

```text
Domain API result    ─┐
Public web source     ├→ SourceRef → EvidenceRef → synthesis/Case/Knowledge
External email/file  ┤
Media/biometric      ┘
```

Source authority/freshness remains explicit.

## 12. Graph integration

Business Graph can relate external SourceRefs to EntityRefs/Case/Task without copying external master data or granting source access through graph membership.

## 13. Meeting/Frontline

Meeting can query internal + authorized external sources. Frontline may use external reference material only as supplemental context; official internal procedure/revision remains authority when defined.

## 14. External Knowledge promotion

```text
SourceRef/Evidence
→ transient use OR candidate
→ privacy/freshness/licensing review
→ owner/eval/version
→ publish
```

Personal external source never auto-promotes to organizational Knowledge.

## 15. Failure boundaries

Distinguish:

```text
Core/Domain unavailable
external connection missing/expired/revoked
provider unavailable/rate-limited
resource not found
web research blocked
subscription stale
Decision required
```

Do not narrate provider failure as absence of business data.

## 16. Kill switches

Independent controls for:

```text
Internet Research
provider
connection
external writes/messaging
webhook ingestion
background sync/watch
browser automation future
Copilot writes generally
OT integration
```

## 17. Anti-pattern integration graph

```text
Portal ─X→ provider token
LLM ─X→ unrestricted HTTP
Planner ─X→ if Gmail/Outlook/WhatsApp
Webhook ─X→ direct write
Personal connection ─X→ org-wide source automatically
Draft ─X→ implicit send
External provider ─X→ Core permission grant
Copilot ─X→ Chat runtime
Copilot ─X→ direct free-form machine actuation
```

## 18. C0 inventory requirement

C0.S0 must map actual repo evidence for egress, OAuth, secret management, existing provider integrations, webhook/subscriptions, privacy owners and provider app registrations before any connector implementation.
