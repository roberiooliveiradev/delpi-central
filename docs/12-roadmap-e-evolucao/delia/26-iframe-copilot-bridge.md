# Minha DELPI Copilot — Iframe Copilot Bridge

**Status:** thematic spec  
**Order authority:** [`16-execution-master-plan.md`](./16-execution-master-plan.md)  
**Foundation:** `PlatformCommand`, `WorkspaceContext`, `EntityRef` e bridge envelope em C0; runtime de integração em C2.

## 1. Objetivo

Integrar apps `iframe` ao Copilot standalone sem DOM automation, bypass de origem/RBAC ou duplicação de Business Actions.

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
Copilot API/MFE
→ PlatformCommand
→ Portal CopilotBridge
→ IframeBridge
→ generic visual command
→ observation

Negócio:
Copilot API
→ Copilot Action Catalog/OpenAPI
→ RBAC/policy/Decision Gate
→ Domain API/use case
→ Outcome/Evidence
```

Nunca usar click/DOM para substituir Business Action.

## 4. Handshake

```text
iframe HELLO
→ Portal valida origin + event.source + appId + authorized route + protocol/version
→ capability intersection
→ BRIDGE_READY + opaque session correlation
```

`sessionId` do bridge não é credential de negócio.

## 5. Envelope

Usar `IframeBridgeEnvelope` foundation:

```text
protocol/version
sessionId
requestId quando aplicável
message type
typed payload
```

Não criar envelope por app.

## 6. Context

Iframe I1+ pode publicar `EntityRef[]`, view/presentation state, filters, selection, date range e visible-data refs. Portal valida/sanitiza e converte para o mesmo `WorkspaceContext` usado por MFEs.

Payload do iframe é untrusted data para policy/system.

## 7. Comandos visuais genéricos

```text
view.open_entity
view.set_view
view.set_filters
view.set_selection
view.focus_entity
view.refresh
```

Não criar comandos app-specific no core/Portal/Copilot.

## 8. Result

Observation/result é correlacionado por requestId e bridge session. Comando visual não produz outcome de negócio fictício.

## 9. Capability discovery

```text
Core /me/apps
→ app/route autorizado

registration/manifest
→ render/origin metadata

runtime handshake
→ visual capabilities suportadas

Domain OpenAPI/Copilot Action Catalog
→ Business Actions
```

Handshake não concede app access nem business permission.

## 10. SSO

Preferência:

```text
Portal → Keycloak
Iframe app → Keycloak/SSO compatível
Bridge → context/visual commands only
```

Proibido token em query string, JWT/refresh token em postMessage ou credential técnica compartilhada pelo bridge.

## 11. Security

- origin allowlist;
- `event.source` validation;
- authorized app/route binding;
- protocol/version/schema validation;
- capability allowlist/intersection;
- bounded payload;
- lifecycle/session invalidation;
- timeout/correlation;
- rate/budget quando necessário;
- secret redaction;
- CSP/frame policy;
- current permission revalidation.

Threat tests incluem malicious origin/source/appId, stale session, replay, undeclared command, context injection, token exfiltration e permission revocation.

## 12. Apps legados/external

Sem adaptação interna:

```text
class = PORTAL_ONLY
```

Copilot pode abrir app/rota e usar APIs disponíveis, mas não promete cross-origin DOM reading, internal entity/filter discovery ou form clicking.

## 13. SDK futuro

Se C0 provar ausência de helper reutilizável, C6 AI-ready ecosystem pode fornecer package compartilhado para handshake, envelope/types, context publisher, command handler, lifecycle cleanup e fixtures.

SDK não contém business logic/RBAC.

## 14. Implementation mapping

```text
C0 → inventory + bridge contracts/security semantics
C1 → prova do Copilot MFE/Portal host standalone
C2 → PORTAL_ONLY + handshake/context/view runtime
C3 → intelligence understands contextual capabilities
C4 → Business reads via Domain APIs, never bridge click
C5 → governed writes via Domain APIs, never bridge click
C6 → shared SDK/readiness onboarding
C7 → rollout/coverage refinements
```

## 15. Promotion gates

```text
I0→I1: handshake + security + context lifecycle
I1→I2: generic declared commands + typed observations + negatives
I2→I3: Business Actions via OpenAPI + RBAC/policy/Decision Gate/evals
```

`postMessage` funcionando não significa AI_READY.

## 16. Generalization

Segundo iframe com outro appId/origin/capability set deve funcionar sem branch app-specific ou planner patch.

## 17. Anti-patterns

- DOM automation;
- cross-origin workaround;
- `eval`/script injection;
- `targetOrigin='*'` para mensagem sensível;
- JWT/refresh token no bridge;
- app-specific commands;
- Business Action como click;
- handshake como RBAC;
- context como system instruction;
- lógica do Copilot dentro do Portal.