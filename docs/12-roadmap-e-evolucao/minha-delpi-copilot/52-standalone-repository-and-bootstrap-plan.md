# Minha DELPI Copilot — Estrutura de Repositório e Bootstrap Standalone

**Status:** `CANONICAL_AUTHORITY` para criação física inicial da aplicação  
**Order authority:** [`16-execution-master-plan.md`](./16-execution-master-plan.md)  
**Boundary:** [`50-standalone-copilot-application-architecture.md`](./50-standalone-copilot-application-architecture.md)  
**Baseline:** [`51-platform-integration-baseline.md`](./51-platform-integration-baseline.md)

## 1. Objetivo

Definir a organização física esperada **antes** de o Cursor criar arquivos, para evitar reestruturações precoces do backend/frontend.

Os nomes finais são congelados em C0.S1; os paths abaixo são o target recomendado e só podem mudar por evidence/ADR.

## 2. Estrutura macro alvo

```text
delpi-central/
├── minha-delpi-copilot-api/
│   ├── app/
│   │   ├── domain/
│   │   ├── application/
│   │   ├── interfaces/
│   │   ├── infrastructure/
│   │   ├── composition/
│   │   └── create_app.py | main.py
│   ├── migrations/
│   ├── tests/
│   ├── docs/
│   ├── scripts/
│   ├── Dockerfile.dev
│   ├── Dockerfile.prod
│   ├── requirements.txt
│   └── pytest.ini
│
├── plugins/
│   ├── minha-delpi-copilot/
│   │   ├── src/
│   │   │   ├── ui/
│   │   │   ├── state/
│   │   │   ├── data/
│   │   │   ├── features/
│   │   │   ├── contracts/
│   │   │   ├── adapters/
│   │   │   └── bootstrap.tsx
│   │   ├── tests/
│   │   ├── delpi.manifest.json
│   │   ├── vite.config.ts
│   │   ├── package.json
│   │   └── Dockerfile
│   ├── plugin-ui/
│   └── vite/
│
├── portal/
├── core-api/
├── gateway/
└── infra/
```

Não criar source code do Copilot dentro de `minha-delpi-ai-api` ou `plugins/minha-delpi-chat`.

## 3. Backend package rules

### domain

Somente:

- entities/aggregates realmente pertencentes ao Copilot;
- value objects;
- lifecycle/state-machine semantics;
- pure policies/specifications;
- domain errors/events quando houver domínio próprio.

Sem Flask, SQLAlchemy, HTTP, provider SDK, Core client ou LLM client.

### application

Subáreas iniciais candidatas:

```text
conversation/
capabilities/
planning/
expertise/
knowledge/
evidence/
platform/
actions/
workflows/
cases/
watch/
admin/
```

Não criar todas como packages vazios no primeiro commit. Criar conforme fase liberada.

Application contém use cases, ports e orchestration.

### interfaces

```text
http/
streaming/
events/       # somente quando necessário
schemas/
```

Controllers traduzem transporte para use cases.

### infrastructure

Adapters concretos, por exemplo:

```text
persistence/
core_api/
domain_api/
openapi/
llm/
embeddings/
knowledge_store/
multimodal/
events/
storage/
observability/
```

Só criar subdiretórios quando houver implementation real.

### composition

Composition Root único ou módulos de wiring coerentes com o padrão confirmado em C0.

## 4. Banco e migrations

O Copilot possui migrations próprias.

Regra:

```text
Copilot migration
→ altera somente schema/tabelas sob ownership Copilot
```

Não editar migrations do Chat para atender Copilot.

Se o cluster `postgres-plugins` for reutilizado fisicamente, manter separação lógica clara por tables/schema/ownership, constraints e migration chain próprias.

## 5. Frontend package rules

O MFE segue Clean Architecture pragmática do frontend.

```text
ui/
→ componentes/páginas puramente visuais

state/
→ local/conversation/workspace/client state

data/
→ Copilot API client/cache/adapters

features/
→ composição por capability de produto

contracts/
→ types DTO/host contracts

adapters/
→ Portal host/WorkspaceContext/federation boundaries
```

Durable business state permanece na Copilot API.

## 6. Module Federation

Reutilizar:

```text
@originjs/vite-plugin-federation
plugins/vite/federation.shared.ts
@delpi/plugin-ui
FEDERATION_SHARED_REACT
federationReactProxyFixPlugin
```

Módulo mínimo esperado:

```text
./App → full-page mount
```

Surface global:

- preferir um segundo export `./Panel` **ou** um mount parametrizado;
- escolher em C1 após verificar lifecycle e bundle sharing;
- ambos pertencem ao mesmo MFE e usam o mesmo state/API contracts.

## 7. Manifesto alvo

Shape conceitual, não arquivo para registro ainda:

```json
{
  "schemaVersion": "1.0.0",
  "id": "minha-delpi-copilot",
  "name": "Minha DELPI Copilot",
  "type": "microfrontend",
  "basePath": "/apps/minha-delpi-copilot",
  "entry": "/apps/minha-delpi-copilot/assets/remoteEntry.js",
  "permissions": [],
  "routes": [],
  "backend": {
    "required": true,
    "serviceName": "minha-delpi-copilot-api",
    "baseUrl": "/apps/minha-delpi-copilot-api",
    "validateJwt": true
  },
  "ui": {"renderMode": "federated"}
}
```

Permission codes e rotas finais são definidos durante C0/C1, não inventados antecipadamente sem capability model.

## 8. Gateway target

Conceitualmente:

```nginx
location ^~ /apps/minha-delpi-copilot-api/ {
  ...
}
```

Dev/prod precisam permanecer simétricos.

Streaming/SSE/WebSocket só deve alterar buffering/timeouts se o transport escolhido realmente exigir.

## 9. Compose target

Services conceituais:

```text
minha-delpi-copilot-api
minha-delpi-copilot
```

Dependências mínimas esperadas:

```text
Copilot API:
- postgres-plugins ou storage aprovado
- keycloak/Core connectivity
- provider connectivity quando habilitado

Copilot MFE:
- plugin-ui
- Copilot API via Gateway em runtime
```

Não declarar dependência `depends_on: minha-delpi-ai-api` nem `depends_on: minha-delpi-chat`.

## 10. Shared code policy

Antes de extrair package compartilhado:

```text
há 2+ consumers reais?
contrato é neutro de produto?
owner compartilhado está claro?
versão/testes independentes são justificáveis?
```

Se não, manter implementação dentro do Copilot.

Não transformar o Chat em biblioteca compartilhada.

## 11. Primeira vertical slice após Foundation Freeze

A primeira implementação runtime não será “chat inteligente”.

Será **bootstrap de integração**, pequena e verificável:

```text
1. criar Copilot API skeleton
2. /health
3. JWT validation
4. Core client / current-user context
5. criar Copilot MFE skeleton
6. plugin-ui/federation
7. manifest draft/registration path
8. gateway dev/prod
9. compose dev/prod
10. Portal AppHost mount
11. authorized route smoke
12. independent shutdown/rollback
```

Só depois o Intelligence Core começa.

## 12. Por que bootstrap vem antes de inteligência

Isso prova cedo:

- app independente existe;
- deploy independente funciona;
- auth correto;
- Core/RBAC correto;
- Portal hosting correto;
- federation/plugin-ui corretos;
- routing correto;
- observabilidade/health mínimos;
- nenhum vínculo com Chat.

Sem isso, construir planner/RAG antes seria feature-first em uma fundação ainda não integrada.

## 13. Build sequence recomendada

```text
C0 — Architecture/Foundation Freeze
↓
C1 — Standalone Application Bootstrap + Portal/Core/Gateway integration
↓
C2 — Workspace Context + Platform Commands
↓
C3 — Intelligence Core + Evidence + Expertise + Knowledge
↓
C4 — Business Reads + Business Graph
↓
C5 — Governed Writes + Durable Work foundation
↓
C6 — Cases/Inbox/Watch/Ecosystem/Learning
↓
C7 — Autonomy/Simulation/Model Routing/Rollout
```

O Plano Mestre `16` é atualizado para essa ordem e continua única authority.

## 14. Definition of Bootstrap Done

```text
API_FOLDER_INDEPENDENT = PASS
MFE_FOLDER_INDEPENDENT = PASS
OWN_MIGRATION_CHAIN = PASS
OWN_MANIFEST = PASS
OWN_GATEWAY_ROUTE = PASS
OWN_COMPOSE_SERVICE = PASS
JWT_VALIDATION = PASS
CORE_CONTEXT = PASS
FEDERATED_MOUNT = PASS
PLUGIN_UI = PASS
NO_CHAT_RUNTIME_DEPENDENCY = PASS
DEV_PROD_ROUTE_PARITY = PASS
HEALTH = PASS
ROLLBACK_INDEPENDENT = PASS
```

Somente então liberar Intelligence Core.