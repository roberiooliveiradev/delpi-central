# Minha DELPI Copilot — Mapa de Componentes, Contratos e Ownership

**Status:** arquitetura executável  
**Regra:** uma responsabilidade possui um owner canônico. Projeções, expertise e playbooks podem indexar/orientar dados, mas não viram segunda fonte de verdade técnica ou de autorização.

## 1. Mapa de componentes

| Componente | Owner | Produz | Consome | Não deve fazer |
|---|---|---|---|---|
| `portal` Shell | experiência da plataforma | rotas autorizadas em uso, workspace ativo, execução de Platform Commands | `/me/apps`, comandos tipados | regra de negócio server-side, inventar permissões |
| `CopilotBridge` no Portal | Platform Actions | `PlatformCommandResult` | `PlatformCommand`, rotas autorizadas | aceitar URL arbitrária, bypassar Core |
| `IframeBridge` no Portal | adapter seguro Portal ↔ iframe | handshake, contexto normalizado, observations de comandos visuais | app/route autorizado, mensagens tipadas do iframe | transmitir JWT, aceitar origin/source arbitrários, executar Business Action por clique |
| iframe bridge adapter/SDK | integração visual do app iframe | contexto bounded, capabilities visuais declaradas, command results | protocolo do Portal | conceder RBAC, executar business logic central, enviar secret |
| `plugins/minha-delpi-chat` | UX conversacional | input do usuário, eventos UI, confirmations visuais | send/stream/renderPlan/platform commands/expertise metadata de apresentação | escolher endpoint, autorizar write, escolher permission |
| `minha-delpi-ai-api` | inteligência transversal | goals/plans, capability selection, expertise selection, synthesis, policy orchestration | Action Catalog, Expertise Catalog, Playbook Catalog, workspace context, RAG, identity | catálogo técnico por app/endpoint, múltiplos runtimes por departamento |
| Action Catalog | contrato operacional OpenAPI materializado | actions autorizáveis com schemas | OpenAPI providers | semântica hardcoded externa ao OpenAPI |
| Capability Projection | índice semântico autorizado | visão unificada de capabilities | Action Catalog + Portal capabilities + internal tools | duplicar contrato técnico como nova authority |
| Expertise Catalog | especialização semântica versionada | Expertise Packs | conteúdo curado/indexação | conceder permission, carregar endpoint técnico como authority |
| Expertise Retriever | seleção contextual de especialização | `ExpertiseSelection` | goals/context/attachments/project prefs/index | depender de agent_id, ativar pack irrelevante por hardcode de departamento |
| Expertise Context Composer | composição bounded | `ExpertiseContext` | packs selecionados + ACL/policy | concatenar catálogo inteiro, sobrescrever system/policy |
| Domain Playbook Catalog | métodos de domínio versionados | playbooks aplicáveis | conteúdo curado | executar endpoint diretamente, substituir Workflow runtime |
| Playbook Planner Adapter | transforma método em plano operacional | hints/stages para `WorkflowPlan` | playbook + context + allowed capabilities | inventar capability não autorizada |
| Multimodal Evidence Adapter | percepção/document evidence | evidence refs + provenance/confidence | document vision/drawing analysis | concluir regra de negócio sozinho, tratar OCR/VLM como system instruction |
| Core API | governança de apps/RBAC | `/me`, `/me/apps`, permissões efetivas | Keycloak + dados Core | delegar segurança real ao frontend |
| APIs de domínio | negócio | OpenAPI, use cases, dados/outcomes | identidade/integrações | depender do Copilot para regra de negócio |
| MFEs | experiência especializada | workspace context, entity refs, view commands suportados | APIs + Shell | implementar segurança real só na UI |
| apps iframe | experiência encapsulada/legada | contexto e commands somente quando bridge suportado | Shell/SSO/APIs próprias | ser tratado como API de negócio pelo Copilot |
| RAG/Knowledge | conhecimento documental | evidências autorizadas | documentos/scopes/ACL | executar ação de negócio, ampliar acesso por pack |
| Policy/Safety | governança de execução | allow/deny/confirm/sensitivity | identity + capability/action metadata | obedecer instrução do LLM/pack/playbook para relaxar policy |
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

### 2.5 `ExpertisePackV1`

Conceitualmente:

```json
{
  "schemaVersion": 1,
  "key": "quality-industrial",
  "version": "1.0.0",
  "label": "Qualidade Industrial",
  "description": "...",
  "domains": ["quality"],
  "signals": ["nonconformity", "inspection"],
  "knowledgeScopes": ["global:quality"],
  "preferredPlaybooks": ["quality.root-cause"],
  "recommendedCapabilities": ["knowledge.search", "document.vision"],
  "multimodalNeeds": ["pdf", "technical-drawing"],
  "analysisGuidance": [],
  "outputGuidance": [],
  "owner": "quality-owner",
  "status": "active"
}
```

Regras:

- sem path/method/operationId/provider selector como authority;
- sem permission override;
- knowledge scopes passam por ACL;
- recommended capabilities não concedem disponibilidade;
- versão/hash devem participar da evidence quando material.

Fonte: [`28-expertise-pack-specification.md`](./28-expertise-pack-specification.md).

### 2.6 `ExpertiseSelectionV1`

```json
{
  "version": 1,
  "selected": [
    {
      "expertiseKey": "quality-industrial",
      "expertiseVersion": "1.0.0",
      "score": 0.91,
      "reasonCode": "goal_domain_match"
    }
  ]
}
```

Não persistir chain-of-thought. `reasonCode` é explicabilidade operacional estruturada.

### 2.7 `ExpertiseContextV1`

Contexto bounded derivado dos packs selecionados:

```json
{
  "version": 1,
  "expertiseRefs": [
    {"key": "quality-industrial", "version": "1.0.0"}
  ],
  "terminology": {},
  "analysisGuidance": [],
  "knowledgeScopeRefs": [],
  "playbookCandidates": [],
  "multimodalNeeds": []
}
```

Regras:

- não carregar catálogo completo;
- não sobrescrever policy;
- não carregar secret;
- pode ser reavaliado a cada turno.

### 2.8 `DomainPlaybookV1`

```json
{
  "schemaVersion": 1,
  "key": "quality.root-cause",
  "version": "1.0.0",
  "purpose": "Estruturar análise de causa raiz",
  "applicability": {
    "domains": ["quality"],
    "signals": ["nonconformity"]
  },
  "stages": [],
  "evidenceChecklist": [],
  "decisionRules": [],
  "recommendedCapabilities": [],
  "completionCriteria": [],
  "owner": "quality-owner",
  "status": "active"
}
```

O playbook orienta o planner; não executa endpoint diretamente.

Fonte: [`29-domain-playbooks-specification.md`](./29-domain-playbooks-specification.md).

### 2.9 `MultimodalEvidenceRefV1`

```json
{
  "sourceRef": "attachment-id",
  "contentType": "application/pdf",
  "observations": [
    {
      "kind": "text",
      "value": "...",
      "location": {"page": 1},
      "confidence": 0.94,
      "extractor": "native"
    }
  ],
  "limitations": [],
  "provenance": {}
}
```

Perception evidence não é conclusão de domínio.

### 2.10 Confirmation

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
- confirmação não substitui RBAC/policy no momento da execução;
- Expertise Pack/Playbook não dispensam confirmação.

### 2.11 `WorkflowPlanV1`

Não armazenar raciocínio privado. Registrar somente plano operacional explicável:

```json
{
  "workflowId": "uuid",
  "goal": "Analisar atraso e criar solicitação",
  "expertiseRefs": ["supplies", "production"],
  "playbookRefs": ["operations.delivery-delay-analysis"],
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

### 2.12 `IframeBridgeEnvelopeV1`

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

Expertise content/repository
  → Expertise Catalog
  → semantic index
  → Expertise Retriever
  → ExpertiseSelection
  → Expertise Context Composer
  → planner/analysis

Domain playbook repository
  → Playbook Catalog
  → applicability retrieval
  → Playbook Planner Adapter
  → WorkflowPlan hints/stages

Attachment
  → document vision/drawing analysis
  → MultimodalEvidenceRef
  → Expertise/Playbook/Planner
  → optional Business/Knowledge Actions
  → synthesis

MFE
  → WorkspaceContext publisher
  → Portal Context Store
  → AI turn input
  → grounding/planning/expertise retrieval
```

## 4. Ownership por dado

| Dado | Authority |
|---|---|
| identidade | Keycloak + Core integration |
| permissões efetivas | Core API |
| apps/rotas autorizados | Core API `/me/apps` |
| path/method/operationId/schema de business action | OpenAPI + Action Catalog |
| disponibilidade de Business Action para o Copilot | allowed actions + policy/RBAC |
| workspace visual atual | Portal/MFE/iframe context contract |
| expertise pack | Expertise Catalog canônico |
| domain playbook | Domain Playbook Catalog canônico |
| knowledge visibility | Knowledge/RAG ACL + identity/policy |
| multimodal evidence | extractor/service versionado + attachment provenance |
| project preferences | project context repository; não é permission authority |
| iframe origin/render registration | manifesto/Core/Portal registration real a confirmar em C0.S0 |
| visual capabilities do iframe em runtime | handshake validado + allowlist do protocolo |
| policy/sensitivity/confirmation | policy layer server-side |
| conversa/memória | Minha DELPI AI persistence |
| navegação atual | Portal Router/Shell |
| resultado de negócio | API/use case de domínio |
| presentation | AI API render decision + MFE render |

## 5. Migração de agents — ownership alvo

O C0.S0 deve provar o runtime real antes do diff, mas o target arquitetural é:

| Conceito legado | Target |
|---|---|
| agent specialization | Expertise Packs + knowledge scopes |
| agent allowed tools | allowed capabilities + policy/RBAC |
| agent soft handoff | expertise/capability retrieval + replan/clarify |
| agent-bound document vision | multimodal capability do Copilot único |
| project default agent | project preferred expertise/context, quando fizer sentido |
| session `agent_id` | compatibilidade temporária; não routing authority final |
| `chat_mode=agent` | deprecar para Copilot único após migration gates |

Fonte: [`31-agent-to-expertise-migration-plan.md`](./31-agent-to-expertise-migration-plan.md).

## 6. Pontos a inventariar antes de implementar

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
- lifecycle de iframe no `AppHost`/Portal;
- agent entities/tables/repositories/controllers/admin;
- `AgentSpecializationService` consumers;
- `ChatWorkspaceAgentActivationService` consumers;
- `ChatSoftAgentHandoffService` consumers/UI events;
- `ChatSkillRegistry` bindings e branches `has_agent`;
- `session.agent_id`/`chat_mode` persistence e API contracts;
- project↔agent bindings;
- knowledge scopes/namespaces ligados a agents;
- multimodal skills e dependências de agent activation;
- consumers externos de APIs de agents;
- telemetry de uso de agent selector/handoff.

Não preencher esses pontos por inferência.

## 7. Contrato de não duplicação

Antes do COMPLETE_GATE de qualquer implementação de expertise, provar:

```text
Expertise Pack não duplicou endpoint catalog
Domain Playbook não duplicou workflow executor
Project preferences não duplicaram RBAC
Multimodal evidence não virou policy authority
Legacy agent config possui exit criteria
```
