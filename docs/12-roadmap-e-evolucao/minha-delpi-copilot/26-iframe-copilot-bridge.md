# Minha DELPI Copilot — Iframe Copilot Bridge

**Status:** thematic spec  
**Order authority:** [`16-execution-master-plan.md`](./16-execution-master-plan.md)  
**Foundation:** `PlatformCommand`, `WorkspaceContext`, `EntityRef` e bridge envelope compartilhados em C0.

## 1. Objetivo

Integrar apps `iframe` ao Copilot sem DOM automation, bypass de origem/RBAC ou duplicação de Business Actions.

## 2. Classes

```text
I0 PORTAL_ONLY
→ abre app/rota autorizados

I1 CONTEXTUAL
→ I0 + publica WorkspaceContext bounded

I2 INTERACTIVE
→ I1 + recebe comandos visuais genéricos declarados

I3 AI_READY
→ I2 + Business Actions relevantes por API/OpenAPI governada
```

## 3. Regra arquitetural

```text
Visual/context:
Copilot
→ PlatformCommand
→ CopilotBridge
→ IframeBridge
→ generic visual command
→ observation

Negócio:
Copilot
→ Action Catalog/OpenAPI
→ RBAC/policy/Decision Gate
→ domain API/use case
→ Outcome/Evidence
```

Nunca usar click/DOM para substituir Business Action.

## 4. Handshake

Conceitualmente:

```text
iframe HELLO
→ Portal valida origin + event.source + appId + authorized route + protocol/version
→ capability intersection
→ BRIDGE_READY + opaque session correlation
```

`sessionId` do bridge não é credential de negócio.

## 5. Envelope

Usar `IframeBridgeEnvelope` foundation, com:

```text
protocol/version
sessionId
requestId quando aplicável
message type
typed payload
```

Não criar envelope específico por app.

## 6. Context

Iframe I1+ pode publicar:

- `EntityRef[]`;
- viewId/presentation state;
- filters;
- selection;
- date range;
- visible data refs.

Portal valida/sanitiza e normaliza para o mesmo `WorkspaceContext` usado por MFE.

Payload do iframe é **untrusted data** para policy/system.

## 7. Comandos visuais genéricos

Preferir verbos compartilhados:

```text
view.open_entity
view.set_view
view.set_filters
view.set_selection
view.focus_entity
view.refresh
```

Não criar no core:

```text
click_totvs_button
open_commercial_customer
select_supplier_screen_x
```

## 8. Command result

Observation/result correlacionado por requestId e estado do bridge.

Command visual não pode produzir outcome de negócio fictício.

## 9. Capability discovery

Combina:

```text
Core /me/apps
→ app/route autorizado

registration/manifest
→ render/origin metadata real

runtime handshake
→ visual capabilities suportadas

OpenAPI/Action Catalog
→ Business Actions
```

Handshake não concede app access nem business permission.

## 10. SSO

Preferência:

```text
Portal → Keycloak
Iframe app → Keycloak/SSO compatível
Bridge → somente context/visual commands
```

Proibido por padrão:

- token em query string;
- JWT/refresh token em `postMessage`;
- shared technical credential via bridge.

## 11. Security

Obrigatório:

- origin allowlist;
- `event.source` validation;
- authorized app/route binding;
- protocol/version;
- schema validation;
- capability allowlist/intersection;
- bounded payload;
- lifecycle/session invalidation;
- timeout/correlation;
- rate/budget quando necessário;
- secret redaction;
- CSP/frame policy coerente;
- current permission revalidation.

Threat tests:

- malicious origin;
- wrong source/window;
- fake appId;
- unauthorized app;
- stale session;
- oversized/invalid payload;
- replay;
- undeclared command;
- context injection;
- token exfiltration;
- permission revoked after handshake.

## 12. Apps legados/external

Sem adaptação interna:

```text
class = PORTAL_ONLY
```

Copilot pode abrir app/rota e usar APIs externas disponíveis, mas não promete:

- cross-origin DOM reading;
- current internal entity;
- internal filters;
- form filling/clicking.

Apps `external` fora do Shell exigem canal explícito/auditado para níveis I1+.

## 13. SDK futuro

Se C0 provar ausência de helper reutilizável, C6 AI-ready ecosystem pode fornecer SDK/shared package para:

- handshake;
- envelope/types;
- context publisher;
- visual command handler;
- lifecycle cleanup;
- test fixtures.

SDK não contém business logic/RBAC.

## 14. Implementation mapping

```text
C0 → inventory + bridge contract/security semantics
C1 → PORTAL_ONLY + handshake/context/view foundation
C3/C4 → Business parity via APIs, never bridge click
C6 → shared SDK/readiness onboarding
C7 → rollout/coverage refinements
```

## 15. Promotion gates

```text
I0→I1
handshake + security + context lifecycle

I1→I2
generic declared commands + typed observations + negatives

I2→I3
Business Actions via OpenAPI + RBAC/policy/Decision Gate/evals
```

`postMessage` funcionando não significa AI_READY.

## 16. Generalization

Segundo iframe com outro appId/origin/capability set deve funcionar sem `if appId == ...`, command app-specific ou planner patch.

## 17. Anti-patterns

- DOM automation;
- cross-origin workaround;
- `eval`/script injection;
- `targetOrigin='*'` em mensagem sensível;
- JWT/refresh token no bridge;
- app-specific commands no core;
- Business Action como click;
- handshake como RBAC;
- context como system instruction.