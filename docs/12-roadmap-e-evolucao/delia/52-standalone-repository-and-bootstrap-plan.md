# Minha DELPI Copilot — Estrutura de Repositório e Bootstrap Standalone

**Status:** `CANONICAL_AUTHORITY` para criação física inicial da aplicação  
**Order authority:** [`16-execution-master-plan.md`](./16-execution-master-plan.md)  
**Boundary:** [`50-standalone-copilot-application-architecture.md`](./50-standalone-copilot-application-architecture.md)  
**Baseline:** [`51-platform-integration-baseline.md`](./51-platform-integration-baseline.md)  
**Multimodal/Meeting/Frontline:** [`53-multimodal-meeting-frontline-and-industrial-copilot.md`](./53-multimodal-meeting-frontline-and-industrial-copilot.md)

## 1. Objetivo

Definir a organização física esperada **antes** de o Cursor criar arquivos, para evitar reestruturações precoces do backend/frontend.

A aplicação deve nascer preparada arquiteturalmente para Global/Workspace/Meeting/Frontline, porém C1 implementa somente o bootstrap necessário; não antecipar media/runtime/features de C3/C6.

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

Não criar por default:

```text
meeting-ai-api/
frontline-ai-api/
operator-agent-runtime/
```

Meeting/Frontline são módulos/surfaces do mesmo produto, salvo gap futuro comprovado e ADR.

## 3. Backend package rules

### domain

Somente:

- entities/aggregates realmente pertencentes ao Copilot;
- value objects;
- lifecycle/state-machine semantics;
- pure policies/specifications;
- domain errors/events quando houver domínio próprio.

Sem Flask, SQLAlchemy, HTTP, provider SDK, Core client, LLM/media client.

### application

Subáreas candidatas, criadas somente quando a fase exigir:

```text
conversation/
capabilities/
planning/
expertise/
knowledge/
evidence/
platform/
actions/
media/
meetings/
frontline/
workflows/
cases/
watch/
admin/
```

Não criar packages vazios antecipadamente.

Application contém use cases, ports e orchestration. Meeting/Frontline usam os mesmos Action/Policy/Evidence/Workflow contracts.

### interfaces

```text
http/
streaming/     # somente quando escolhido
media/         # somente quando transport boundary real existir
events/        # somente quando necessário
schemas/
```

Controllers/transport handlers traduzem transporte para use cases.

### infrastructure

Adapters concretos possíveis:

```text
persistence/
core_api/
domain_api/
openapi/
llm/
embeddings/
knowledge_store/
multimodal/
speech/
media/
device_context/
events/
storage/
observability/
```

Só criar subdiretórios quando houver implementation real e Abstraction Gate aprovado.

### composition

Composition Root único ou módulos de wiring coerentes com o padrão confirmado em C0.

Provider/media SDKs são construídos aqui/infrastructure, nunca dentro de use cases/domain.

## 4. Banco e migrations

O Copilot possui migrations próprias.

Regra:

```text
Copilot migration
→ altera somente schema/tabelas sob ownership Copilot
```

Não editar migrations do Chat para atender Copilot.

Se o cluster `postgres-plugins` for reutilizado fisicamente, manter separação lógica clara por tables/schema/ownership, constraints e migration chain próprias.

Raw audio/video não vira tabela/blob persistido por default; media storage e metadata só entram após C0/C3 provar need/policy.

## 5. Frontend package rules

O MFE segue Clean Architecture pragmática do frontend.

```text
ui/
→ componentes/páginas/surfaces visuais

state/
→ local/conversation/workspace/media-session client state

data/
→ Copilot API client/cache/adapters

features/
→ composição por capability de produto

contracts/
→ types DTO/host/media contracts

adapters/
→ Portal host/WorkspaceContext/federation/device/browser boundaries
```

Durable business/media metadata state permanece na Copilot API quando persistência é necessária.

Browser mic/camera/screen permission state permanece client/platform state e não concede Business Action permission.

## 6. Module Federation

Reutilizar:

```text
@originjs/vite-plugin-federation
plugins/vite/federation.shared.ts
@delpi/plugin-ui
FEDERATION_SHARED_REACT
federationReactProxyFixPlugin
```

Módulo mínimo esperado em C1:

```text
./App → full-page mount
```

Surface global:

- preferir um segundo export `./Panel` **ou** um mount parametrizado;
- escolher em C1 após verificar lifecycle e bundle sharing;
- ambos pertencem ao mesmo MFE e usam o mesmo state/API contracts.

Meeting/Frontline futuras:

- preferir `surface`/feature composition dentro do mesmo MFE;
- export específico só se lifecycle/bundle justificar;
- não criar app federado separado por surface sem ADR.

## 7. Surface composition target

Conceitualmente:

```text
CopilotRoot
├─ GlobalSurface
├─ WorkspaceSurface
├─ MeetingSurface      # C6
└─ FrontlineSurface    # C6
```

Compartilham:

```text
api client
auth host contract
WorkspaceContext
conversation/work refs
Evidence/Decision contracts
media capability adapter
```

Não compartilhar global mutable state entre usuários/devices.

## 8. Media/browser adapter baseline

C1 não implementa STT/Vision/realtime, mas o frontend deve evitar decisões que impeçam C3/C6.

Regras:

- media permission handling fica atrás de adapter/hook bounded quando necessário;
- nenhuma capture inicia no mount;
- reload não reinicia capture automaticamente;
- UI suporta feature/capability detection;
- accessible fallback existe como princípio;
- provider SDK não entra diretamente nos componentes.

## 9. Manifesto alvo

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

Meeting/Frontline não exigem manifests independentes por default.

## 10. Gateway target

Conceitualmente:

```nginx
location ^~ /apps/minha-delpi-copilot-api/ {
  ...
}
```

Dev/prod precisam permanecer simétricos.

Streaming/SSE/WebSocket/WebRTC-related tuning só altera buffering/timeouts/proxy settings se o transport escolhido realmente exigir e testes provarem necessidade.

## 11. Compose target

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

Speech/Vision/media provider não precisa ser container próprio se for serviço externo; C0/C3 decide por evidence, não por antecipação.

## 12. Shared code policy

Antes de extrair package compartilhado:

```text
há 2+ consumers reais?
contrato é neutro de produto?
owner compartilhado está claro?
versão/testes independentes são justificáveis?
```

Se não, manter implementação dentro do Copilot.

Não transformar o Chat em biblioteca compartilhada.

## 13. Shared-device rule

Não criar “user singleton” no MFE pensando em terminal individual.

A arquitetura deve permitir:

```text
user login/session A
→ use
→ logout/switch
→ clear local context/media cache
→ user login/session B
```

sem vazamento.

Device/workstation metadata é separado de user identity.

## 14. Primeira vertical slice após Foundation Freeze

A primeira implementação runtime não será “chat inteligente”, Meeting ou Frontline.

Será **bootstrap de integração**, pequena e verificável:

```text
1. criar Copilot API skeleton
2. /health
3. JWT validation
4. Core client / current-user context
5. criar Copilot MFE skeleton
6. plugin-ui/federation
7. responsive/accessibility/media-permission baseline
8. manifest draft/registration path
9. gateway dev/prod
10. compose dev/prod
11. Portal AppHost mount
12. authorized route smoke
13. independent shutdown/rollback
```

Só depois o Intelligence Core começa.

## 15. Por que bootstrap vem antes de inteligência

Isso prova cedo:

- app independente existe;
- deploy independente funciona;
- auth correto;
- Core/RBAC correto;
- Portal hosting correto;
- federation/plugin-ui corretos;
- routing correto;
- observabilidade/health mínimos;
- frontend pode evoluir para diferentes surfaces sem duplicar produto;
- media permissions não iniciam capture por acidente;
- nenhum vínculo com Chat.

Sem isso, construir planner/RAG/media antes seria feature-first em uma fundação ainda não integrada.

## 16. Build sequence recomendada

```text
C0 — Architecture/Foundation + Media/Privacy/OT Freeze
↓
C1 — Standalone Application Bootstrap + Portal/Core/Gateway integration
↓
C2 — Workspace/Operational Context + Platform Commands
↓
C3 — Intelligence Core + Multimodal Foundations
↓
C4 — Business Reads + Business Graph
↓
C5 — Governed Writes + Durable Work foundation
↓
C6 — Cases/Inbox/Watch + Meeting/Frontline + Ecosystem/Learning
↓
C7 — Advanced Realtime + Autonomy/Simulation/Model Routing/Rollout
```

O Plano Mestre `16` é única authority.

## 17. Definition of Bootstrap Done

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
RESPONSIVE_ACCESSIBILITY_BASELINE = PASS
MEDIA_CAPTURE_NOT_AUTO_STARTED = PASS
NO_CHAT_RUNTIME_DEPENDENCY = PASS
DEV_PROD_ROUTE_PARITY = PASS
HEALTH = PASS
ROLLBACK_INDEPENDENT = PASS
```

Somente então liberar C2/C3 conforme `16`.