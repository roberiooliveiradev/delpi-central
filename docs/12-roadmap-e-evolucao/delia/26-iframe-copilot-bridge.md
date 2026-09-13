# DÉLIA — Iframe Bridge

**Status:** thematic spec / TARGET  
**Order authority:** [`16-execution-master-plan.md`](./16-execution-master-plan.md)  
**Foundation:** `PlatformCommand`, `WorkspaceContext`, `EntityRef` e bridge envelope são targets a confirmar/congelar em C0; runtime de integração entra em C2 somente após gates.

> `CopilotBridge` pode continuar aparecendo como identificador técnico/histórico de bridge até C0.S1; não é nome do produto.

## 1. Objetivo

Integrar apps `iframe` à DÉLIA standalone sem DOM automation, bypass de origem/RBAC ou duplicação de Business Actions.

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
DÉLIA API/MFE
→ PlatformCommand
→ Portal bridge host
→ IframeBridge
→ generic visual command
→ observation

Negócio:
DÉLIA API
→ Action Catalog/OpenAPI
→ Core/domain authorization + Policy/Decision Gate
→ Domain API/use case
→ Outcome/Evidence
```

Nunca usar click/DOM para substituir Business Action. Automation Hub/RPA não é atalho para bridge visual quando API autoritativa existe.

## 4. Handshake

Target:

```text
iframe HELLO
→ Portal valida origin + event.source + appId + authorized route + protocol/version
→ capability intersection
→ BRIDGE_READY + opaque session correlation
```

`sessionId` do bridge não é credential de negócio.

## 5. Envelope

Usar `IframeBridgeEnvelope` somente se C0 comprovar/congelar esse foundation:

```text
protocol/version
sessionId
requestId quando aplicável
message type
typed payload
```

Não criar envelope por app.

## 6. Context

Iframe I1+ pode publicar `EntityRef[]`, view/presentation state, filters, selection, date range e visible-data refs quando esses contracts estiverem aprovados. Portal valida/sanitiza e transporta para o mesmo `WorkspaceContext` target usado por MFEs.

Payload do iframe é untrusted data para policy/system. Portal aggregation não transforma view state em source of truth de negócio.

## 7. Comandos visuais genéricos

```text
view.open_entity
view.set_view
view.set_filters
view.set_selection
view.focus_entity
view.refresh
```

Não criar comandos app-specific no core/Portal/DÉLIA.

## 8. Result

Observation/result é correlacionado por requestId e bridge session. Comando visual não produz Outcome de negócio fictício.

## 9. Capability discovery

Target flow, condicionado a contratos reais:

```text
Core authorized apps/routes
→ app/route autorizado

registration/manifest
→ render/origin metadata

runtime handshake
→ visual capabilities suportadas

Domain OpenAPI / DÉLIA Capability Projection
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
- current permission revalidation via canonical owner.

Threat tests incluem malicious origin/source/appId, stale session, replay, undeclared command, context injection, token exfiltration e permission revocation.

## 12. Apps legados/external

Sem adaptação interna:

```text
class = PORTAL_ONLY
```

DÉLIA pode abrir app/rota e usar APIs disponíveis, mas não promete cross-origin DOM reading, internal entity/filter discovery ou form clicking.

Se alguma operação legada material exigir RPA/computer-use, isso pertence ao Automation Hub technical-execution boundary, separado do IframeBridge.

## 13. SDK futuro

Se C0 provar ausência de helper reutilizável e houver 2+ consumers reais, C6 AI-ready ecosystem pode fornecer package compartilhado para handshake, envelope/types, context publisher, command handler, lifecycle cleanup e fixtures.

SDK não contém business logic/RBAC. Deve passar Abstraction Gate antes de ser criado.

## 14. Implementation mapping

```text
C0 → inventory + bridge contracts/security semantics
C1 → prova do DÉLIA MFE/Portal host standalone
C2 → PORTAL_ONLY + handshake/context/view runtime
C3 → intelligence understands contextual capabilities
C4 → Business reads via Domain APIs, never bridge click
C5 → governed ACT via Domain APIs/approved execution boundaries, never bridge click
C6 → shared SDK/readiness onboarding when justified
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
- lógica da DÉLIA dentro do Portal;
- RPA/computer-use mechanics dentro do bridge.
