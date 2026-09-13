# 04 — Platform Actions

## 1. Objetivo

Platform Actions permitem à DÉLIA operar a experiência da Minha DELPI por comandos tipados e autorizados, sem inventar URLs nem manipular DOM.

## 2. Authority

```text
Core API authorized apps/routes
→ Portal Shell
→ Platform Capability Projection
→ DÉLIA
```

Core permanece authority de apps/routes/RBAC/governance; Portal executa navegação/view. A DÉLIA não mantém lista paralela de apps/URLs nem transforma contexto em autorização.

## 3. Contracts

Reutilizar os primitives aprovados em C0, se comprovados/congelados:

- `PlatformCommand`;
- `PlatformCommandResult`;
- `EntityRef`;
- `WorkspaceContext`;
- correlation context.

Não criar command schema diferente por app. A presença dos nomes neste documento é TARGET, não prova de implementação.

## 4. CopilotBridge / bridge de plataforma

O nome histórico `CopilotBridge` pode permanecer como referência técnica até C0.S1, se existir/for aprovado. Semântica de ownership:

Portal owner de:

- schema validation da fronteira de host;
- target resolution;
- authorization/revalidation de rota/app;
- generic command dispatch;
- navigation/view execution;
- typed observation/result;
- trace/audit de navegação.

DÉLIA apenas solicita Platform Actions permitidas; não ganha authority sobre Portal internals.

## 5. Ações genéricas

### `portal.open_app`

```json
{"appId":"portal-suprimentos"}
```

### `portal.open_route`

```json
{"appId":"portal-suprimentos","routeId":"purchase-requests"}
```

### `portal.open_entity`

Usa `EntityRef` compartilhado quando o contract estiver congelado:

```json
{
  "entityRef": {
    "entityType":"purchaseRequest",
    "entityId":"SC-00123",
    "sourceSystem":"my-requests"
  }
}
```

Entity→route resolution é declarativa no app/Portal, não LLM hardcode.

### `portal.set_view_context`

Aplica filtros/view state suportados, sem alterar negócio.

### `portal.focus`

Foca/destaca visualmente.

### `portal.select_tab`

Seleciona view/aba suportada.

### `portal.back`

Navegação anterior quando suportada.

## 6. Result

Exemplo conceitual:

```json
{
  "status":"succeeded",
  "commandId":"uuid",
  "resolved":{"appId":"portal-suprimentos","routeId":"purchase-requests"},
  "errorCode":null
}
```

Status seguem o contract C0 quando definido; evitar enums diferentes por adapter.

## 7. Segurança

Antes da execução:

1. capability/target existem na visão atual autorizada;
2. payload/schema válido;
3. permission/route revalidada pelo owner correto;
4. sem URL arbitrária;
5. Platform Action não bypassa backend de negócio;
6. context/view command não vira write;
7. props/metadata do frontend não substituem Core/domain authorization.

## 8. MFE view capabilities

MFE pode declarar suporte visual, mas o core genérico deve preferir **verbos compartilhados**.

Exemplo:

```text
view.open_entity
view.set_view
view.set_filters
view.set_selection
view.focus_entity
view.refresh
```

O MFE mapeia o comando genérico para sua implementação local.

Não criar no core:

```text
customer.open-special-tab
supplier.click-approve
commercial.apply-x
```

## 9. Iframe

Iframe integrado usa o mesmo princípio via `IframeBridge` quando esse contract existir/aprovado:

```text
PlatformCommand
→ Portal
→ IframeBridge
→ generic visual command
→ observation
```

Business Actions permanecem fora do bridge.

## 10. Events

Eventos de Portal devem reutilizar `EventEnvelope`/contrato tipado somente quando materialmente o mesmo conceito for persistido/roteado e C0 comprovar esse primitive. Eventos locais de UI podem continuar internos ao Portal, mas precisam ownership/schema claro quando atravessam boundaries.

## 11. Exemplo

> “Abra o cliente DELPI e vá para pedidos em aberto.”

Possível plano:

```text
business.read customer search
→ EntityRef(customer)
→ portal.open_app
→ portal.open_entity(EntityRef)
→ portal.select_tab(open-orders)
```

Lookup é negócio; navegação é experiência.

## 12. Fallback

Sem view capability avançada:

- open app/route continua se o contract básico estiver disponível;
- explicar limitação;
- não usar DOM selector silenciosamente.

## 13. Generalization

Novo app/route/view compatível deve funcionar por registration/contracts sem adicionar `if appId == ...` no AI core/bridge genérico.
