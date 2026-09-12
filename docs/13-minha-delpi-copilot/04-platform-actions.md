# 04 — Platform Actions

## 1. Objetivo

Platform Actions permitem que o Copilot opere a experiência da Minha DELPI sem inventar URLs nem manipular diretamente o DOM. São comandos tipados, validados pelo Portal Shell e limitados ao conjunto de apps/rotas autorizados.

## 2. Fonte do catálogo

A fonte primária deve ser o estado autorizado já conhecido pelo Portal, derivado do Core API.

```text
Core API
→ apps/rotas autorizados
→ Portal Shell
→ Platform Capability Catalog
→ Copilot
```

O Copilot não deve possuir uma lista hardcoded paralela de apps.

## 3. CopilotBridge

O Portal deve possuir um `CopilotBridge` responsável por:

- receber comandos estruturados;
- validar schema;
- verificar que o alvo existe na visão autorizada do usuário;
- executar navegação/ação visual;
- retornar observation estruturada;
- registrar telemetria/auditoria quando aplicável.

## 4. Ações mínimas

### `portal.open_app`

Abre um app autorizado.

Entrada conceitual:

```json
{
  "appId": "portal-suprimentos"
}
```

### `portal.open_route`

Abre uma rota autorizada de um app.

```json
{
  "appId": "portal-suprimentos",
  "routeId": "purchase-requests"
}
```

### `portal.open_entity`

Abre uma entidade em um app capaz de representá-la.

```json
{
  "entityType": "purchaseRequest",
  "entityId": "SC-00123"
}
```

A resolução entidade → rota deve ser declarativa no contrato do app, não hardcoded no LLM.

### `portal.set_view_context`

Aplica contexto visual suportado pela tela.

```json
{
  "filters": {
    "branch": "01",
    "product": "90264238"
  }
}
```

### `portal.focus`

Destaca um elemento sem executar negócio.

### `portal.select_tab`

Muda uma aba declaradamente suportada.

### `portal.back`

Retorna ao estado de navegação anterior.

## 5. Contrato de resposta

O bridge deve responder com observações, por exemplo:

```json
{
  "status": "completed",
  "command": "portal.open_route",
  "appId": "portal-suprimentos",
  "routeId": "purchase-requests",
  "workspaceContextVersion": 42
}
```

Em erro:

```json
{
  "status": "rejected",
  "reason": "route_not_authorized"
}
```

## 6. Segurança

Antes de executar uma Platform Action:

1. confirmar que a capability está autorizada;
2. validar o payload;
3. confirmar que app/rota continuam presentes no estado atual;
4. nunca confiar em URL arbitrária produzida pelo modelo;
5. nunca usar Platform Action para bypassar um backend protegido.

## 7. Registro por app

Um MFE pode declarar UI capabilities próprias, por exemplo:

```text
customer.open
customer.select-tab
customer.apply-view-filter
dashboard.change-view
interaction-room.open
```

Regras:

- somente comportamento visual/local;
- sem duplicar write/read de negócio que já deveria ser API;
- schema versionado;
- capability descoberta pelo Shell;
- app desmontado = capability indisponível.

## 8. Fluxo de exemplo

Usuário:

> “Abra o Portal Comercial no cliente DELPI e vá para pedidos em aberto.”

Plano possível:

```text
1. business.read customer.search("DELPI")
2. portal.open_app(portal-comercial)
3. portal.open_entity(customer, 000123)
4. portal.select_tab(open-orders)
```

O lookup do cliente é negócio; abrir app/entidade/aba é experiência.

## 9. Eventos Portal ↔ Copilot

Sugestão de eventos tipados:

```text
copilot:command
copilot:command-result
workspace:context-changed
workspace:entity-selected
workspace:view-changed
capability:availability-changed
```

Evitar EventBus genérico sem contratos. Eventos devem ter schema e ownership.

## 10. Fallback

Se uma página não implementa uma UI capability específica:

- ainda deve ser possível abrir app/rota autorizada;
- o Copilot explica a limitação;
- não deve começar a usar seletores DOM como fallback silencioso.
