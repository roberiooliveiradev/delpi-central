# Minha DELPI Copilot — Mapa de Componentes, Contratos e Ownership

**Status:** arquitetura executável  
**Regra:** uma responsabilidade possui um owner canônico. Projeções podem indexar dados, mas não viram segunda fonte de verdade.

## 1. Mapa de componentes

| Componente | Owner | Produz | Consome | Não deve fazer |
|---|---|---|---|---|
| `portal` Shell | experiência da plataforma | rotas autorizadas em uso, workspace ativo, execução de Platform Commands | `/me/apps`, comandos tipados | regra de negócio server-side, inventar permissões |
| `CopilotBridge` no Portal | Platform Actions | `PlatformCommandResult` | `PlatformCommand`, rotas autorizadas | aceitar URL arbitrária, bypassar Core |
| `plugins/minha-delpi-chat` | UX conversacional | input do usuário, eventos UI, confirmations visuais | send/stream/renderPlan/platform commands | escolher endpoint, autorizar write |
| `minha-delpi-ai-api` | inteligência transversal | goals/plans, capability selection, synthesis, policy orchestration | Action Catalog, workspace context, RAG, identity | catálogo técnico por app/endpoint |
| Action Catalog | contrato operacional OpenAPI materializado | actions autorizáveis com schemas | OpenAPI providers | semântica hardcoded externa ao OpenAPI |
| Capability Projection | índice semântico autorizado | visão unificada de capabilities | Action Catalog + Portal capabilities + internal tools | duplicar contrato técnico como nova authority |
| Core API | governança de apps/RBAC | `/me`, `/me/apps`, permissões efetivas | Keycloak + dados Core | delegar segurança real ao frontend |
| APIs de domínio | negócio | OpenAPI, use cases, dados/outcomes | identidade/integrações | depender do Copilot para regra de negócio |
| MFEs | experiência especializada | workspace context, entity refs, view commands suportados | APIs + Shell | implementar segurança real só na UI |
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
  → Router/AppHost/MFE

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
| workspace visual atual | Portal/MFE context contract |
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
- policy/sensitivity metadata atual no Action Catalog.

Não preencher esses pontos por inferência.