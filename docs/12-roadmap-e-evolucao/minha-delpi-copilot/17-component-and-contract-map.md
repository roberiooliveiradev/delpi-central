# Minha DELPI Copilot — Mapa de Componentes, Contratos e Ownership

**Status:** arquitetura executável  
**Regra:** uma responsabilidade possui um owner canônico. Projeções podem indexar dados, mas não viram segunda fonte de verdade.

## 1. Mapa de componentes

| Componente | Owner | Produz | Consome | Não deve fazer |
|---|---|---|---|---|
| `portal` Shell | experiência da plataforma | rotas autorizadas em uso, workspace ativo, execução de Platform Commands | `/me/apps`, comandos tipados | regra de negócio server-side, inventar permissões |
| `CopilotBridge` no Portal | Platform Actions | `PlatformCommandResult` | `PlatformCommand`, rotas autorizadas | aceitar URL arbitrária, bypassar Core |
| `IframeBridge` no Portal | adapter seguro Portal ↔ iframe | handshake, contexto normalizado, observations de comandos visuais | app/route autorizado, mensagens tipadas do iframe | transmitir JWT, aceitar origin/source arbitrários, executar Business Action por clique |
| iframe bridge adapter/SDK | integração visual do app iframe | contexto bounded, capabilities visuais declaradas, command results | protocolo do Portal | conceder RBAC, executar business logic central, enviar secret |
| `plugins/minha-delpi-chat` | UX conversacional | input do usuário, eventos UI, confirmations visuais | send/stream/renderPlan/platform commands | escolher endpoint, autorizar write |
| `minha-delpi-ai-api` | inteligência transversal | goals/plans, capability selection, synthesis, policy orchestration | Action Catalog, workspace context, RAG, identity | catálogo técnico por app/endpoint |
| Action Catalog | contrato operacional OpenAPI materializado | actions autorizáveis com schemas | OpenAPI providers | semântica hardcoded externa ao OpenAPI |
| Capability Projection | índice semântico autorizado | visão unificada de capabilities | Action Catalog + Portal capabilities + internal tools | duplicar contrato técnico como nova authority |
| Core API | governança de apps/RBAC | `/me`, `/me/apps`, permissões efetivas | Keycloak + dados Core | delegar segurança real ao frontend |
| APIs de domínio | negócio | OpenAPI, use cases, dados/outcomes | identidade/integrações | depender do Copilot para regra de negócio |
| MFEs | experiência especializada | workspace context, entity refs, view commands suportados | APIs + Shell | implementar segurança real só na UI |
| apps iframe | experiência encapsulada/legada | contexto e commands somente quando bridge suportado | Shell/SSO/APIs próprias | ser tratado como API de negócio pelo Copilot |
| RAG/Knowledge | conhecimento documental | evidências autorizadas | documentos/scopes | executar ação de negócio |
| Policy/Safety | governança de execução | allow/deny/confirm/sensitivity | identity + capability/action metadata | obedecer instrução do LLM para relaxar policy |
| Observability | evidência operacional | traces/metrics/audit | eventos do pipeline | persistir CoT, secrets ou JWT |

## 2. Contratos v1 propostos

Os nomes abaixo são contratos conceituais. Em C0.S0 o Cursor deve procurar equivalentes existentes e reutilizá-los antes de criar novos schemas.

### 2.1 `PlatformCommandV1`

```json
{
  "version": 1,
  "commandId": "uuid",
  "type": "portal.open_route",
  "target": {
    "appId": "commercial",
    "routeId": "orders"
  },
  "context": {},
  "issuedAt": "ISO-8601"
}
```

Regras:

- `type` pertence a allowlist de Platform Actions genéricas;
- `target` usa IDs canônicos, não URL arbitrária;
- Portal resolve IDs para rota atual autorizada;
- `commandId` suporta trace/dedup quando aplicável;
- não carregar token/secret.

### 2.2 `PlatformCommandResultV1`

```json
{
  "version": 1,
  "commandId": "uuid",
  "status": "succeeded",
  "resolved": {
    "appId": "commercial",
    "routeId": "orders"
  },
  "errorCode": null
}
```

Status mínimos: `succeeded`, `rejected`, `not_found`, `unauthorized`, `failed`.

### 2.3 `WorkspaceContextV1`

```json
{
  "version": 1,
  "appId": "commercial",
  "routeId": "customer-detail",
  "entityRefs": [
    {"type": "customer", "id": "000123", "label": "Empresa XYZ"}
  ],
  "filters": {"branch": "01"},
  "selection": [],
  "dateRange": null,
  "visibleDataRefs": [],
  "source": "mfe",
  "updatedAt": "ISO-8601"
}
```

Regras:

- bounded size;
- allowlist/sanitização de campos;
- `source` pode ser `mfe`, `iframe` ou `portal` sem mudar a semântica do contrato;
- dados explicitamente atuais prevalecem sobre memória antiga;
- não é authority de permissão;
- não carregar dataset inteiro.

### 2.4 `CapabilityProjectionV1`

```json
{
  "capabilityId": "...",
  "kind": "business.read",
  "label": "Consultar estoque",
  "description": "...",
  "source": {
    "type": "action_catalog",
    "refId": "action-id"
  },
  "availability": "allowed",
  "risk": "read",
  "requiresConfirmation": false,
  "provenance": {}
}
```

A projeção pode conter metadata necessária para retrieval/UX, mas o executor volta ao `source.refId` canônico para contrato técnico e policy.

### 2.5 Confirmation

```json
{
  "confirmationId": "uuid",
  "actionRef": "action-id",
  "summary": "Atualizar ...",
  "argumentsPreview": {},
  "sensitivity": "write",
  "expiresAt": "ISO-8601"
}
```

Decision:

```json
{
  "confirmationId": "uuid",
  "decision": "confirmed",
  "decidedAt": "ISO-8601"
}
```

Regras:

- preview deve refletir os argumentos que serão executados;
- alteração material nos argumentos invalida confirmação anterior;
- confirmação não substitui RBAC/policy no momento da execução.

### 2.6 `WorkflowPlanV1`

Não armazenar raciocínio privado. Registrar somente plano operacional explicável:

```json
{
  "workflowId": "uuid",
  "goal": "Analisar atraso e criar solicitação",
  "steps": [
    {
      "stepId": "s1",
      "capabilityRef": "...",
      "dependsOn": [],
      "mode": "read",
      "status": "planned"
    }
  ]
}
```

### 2.7 `IframeBridgeEnvelopeV1`

Fonte detalhada: [`26-iframe-copilot-bridge.md`](./26-iframe-copilot-bridge.md).

Envelope conceitual:

```json
{
  "protocol": "delpi-iframe-copilot",
  "version": 1,
  "sessionId": "opaque-id",
  "requestId": "uuid",
  "type": "command",
  "payload": {}
}
```

Handshake esperado:

```text
iframe HELLO
→ Portal valida origin/source/appId/autorização/protocolo
→ Portal retorna BRIDGE_READY
→ troca de context/commands/results tipados
```

Regras:

- `sessionId` não é credencial de negócio;
- `postMessage` não transporta JWT/refresh token;
- capability visual declarada pelo iframe não concede autorização;
- Portal intersecta declaration + app/route autorizado + allowlist do protocolo;
- commands são visuais/genéricos;
- Business Actions continuam fora do bridge.

## 3. Producer → consumer graph

```text
Keycloak
  → Core API identity

Core API /me/apps
  → Portal AuthContext/apps/routes
  → Authorized Portal Capability Projection
  → Minha DELPI AI retrieval/planner
  → PlatformCommand
  → Chat transport
  → CopilotBridge
  → Router/AppHost/MFE/IframeBridge

Iframe app
  → HELLO + declared visual capabilities
  → IframeBridge validation
  → context.changed
  → WorkspaceContext normalization
  → Portal Context Store
  → AI turn input

Copilot/Portal
  → visual command
  → IframeBridge
  → iframe handler
  → command.result / observation
  → Portal/Copilot feedback

Business OpenAPI
  → importer/index
  → Action Catalog
  → allowed actions
  → Business Capability Projection
  → retrieval/planner
  → validator/policy/confirmation
  → ExecuteExternalActionUseCase
  → HTTP gateway
  → domain API
  → normalized result
  → presentation/synthesis

MFE
  → WorkspaceContext publisher
  → Portal Context Store
  → AI turn input
  → grounding/planning
```

## 4. Ownership por dado

| Dado | Authority |
|---|---|
| identidade | Keycloak + Core integration |
| permissões efetivas | Core API |
| apps/rotas autorizados | Core API `/me/apps` |
| path/method/operationId/schema de business action | OpenAPI + Action Catalog |
| disponibilidade para agente | binding/allowed actions |
| workspace visual atual | Portal/MFE/iframe context contract |
| iframe origin/render registration | manifesto/Core/Portal registration real a confirmar em C0.S0 |
| visual capabilities do iframe em runtime | handshake validado + allowlist do protocolo |
| policy/sensitivity/confirmation | policy layer server-side |
| conversa/memória | Minha DELPI AI persistence |
| navegação atual | Portal Router/Shell |
| resultado de negócio | API/use case de domínio |
| presentation | AI API render decision + MFE render |

## 5. Pontos a inventariar antes de implementar

Marcar `TO_INVENTORY` até C0.S0 provar:

- schema real retornado por `/me/apps` e IDs estáveis disponíveis;
- existência de route ID além de path;
- eventos SSE já reutilizáveis para PlatformCommand;
- mecanismo atual de confirmation;
- deep-link conventions existentes por MFE;
- shared package adequado para tipos Portal/MFE;
- persistence atual de turn metadata/context;
- idempotency support nas APIs de write;
- policy/sensitivity metadata atual no Action Catalog;
- lista real de apps `iframe` e `external`;
- onde origin/entry/renderMode são authority hoje;
- se algum iframe já usa `postMessage`/bridge;
- SSO/auth atual de cada iframe;
- CSP/frame policies atuais;
- lifecycle de iframe no `AppHost`/Portal.

Não preencher esses pontos por inferência.
