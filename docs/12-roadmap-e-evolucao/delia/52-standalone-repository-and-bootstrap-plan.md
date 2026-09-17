# DÉLIA — Estrutura de Repositório e Bootstrap Standalone

**Status:** `CANONICAL_AUTHORITY` para criação física inicial da aplicação  
**Order authority:** [`16-execution-master-plan.md`](./16-execution-master-plan.md)  
**Boundary:** [`50-standalone-copilot-application-architecture.md`](./50-standalone-copilot-application-architecture.md)  
**Baseline:** [`51-platform-integration-baseline.md`](./51-platform-integration-baseline.md)  
**Multimodal/Meeting/Frontline:** [`53-multimodal-meeting-frontline-and-industrial-copilot.md`](./53-multimodal-meeting-frontline-and-industrial-copilot.md)

> Este documento é `TARGET/PLANNED`: não prova que API, MFE, migrations, manifesto, rotas, containers ou serviços da DÉLIA já existam. A criação física só começa após os gates de C0 definidos em `16`.

## 1. Objetivo

Definir a organização física esperada **antes** de criar runtime, evitando reestruturações precoces do backend/frontend.

A aplicação deve nascer preparada arquiteturalmente para Global/Workspace/Meeting/Frontline, porém C1 implementa somente o bootstrap necessário; não antecipar media/runtime/features de C3/C6.

Os nomes finais foram aceitos pelo `ARCHITECTURE_REVIEW_C0_S1` (`REVIEWED_HEAD=c822f0e72495256c3459a4b36b9c37a3bba95cbb`; authority `68`); paths abaixo são `PLANNED / FROZEN_ACCEPTED` e só mudam por evidence/ADR futuro. Não criar pastas nesta etapa.

## 2. Estrutura macro alvo

```text
delpi-central/
├── delia-api/                       # FROZEN_ACCEPTED (C0.S1)
│   ├── app/
│   │   ├── domain/
│   │   ├── application/
│   │   ├── interfaces/
│   │   ├── infrastructure/
│   │   ├── composition/
│   │   └── create_app.py | main.py
│   ├── migrations/                  # CONDITIONAL: only when DÉLIA-owned persisted state exists (see §4)
│   ├── tests/
│   ├── docs/
│   ├── scripts/
│   ├── Dockerfile.dev
│   ├── Dockerfile.prod
│   ├── requirements.txt
│   └── pytest.ini
│
├── plugins/
│   ├── delia/                       # FROZEN_ACCEPTED (C0.S1); one product, one MFE
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

Histórico supersedido (não criar como runtime ativo): `minha-delpi-copilot-api/`, `plugins/minha-delpi-copilot/`.

Não criar source code da DÉLIA dentro de `minha-delpi-ai-api` ou `plugins/minha-delpi-chat`.

Não criar por default:

```text
delia-panel/
delia-workspace/
delia-meeting/
delia-frontline/
meeting-ai-api/
frontline-ai-api/
operator-agent-runtime/
```

Meeting/Frontline/Global/Workspace são surfaces do mesmo produto/MFE, salvo gap futuro comprovado e ADR. C1 pode escolher `./App` + `./Panel` versus mount parametrizado — não congelado em C0.S1.

## 3. Backend package rules

### domain

Somente:

- entities/aggregates realmente pertencentes à DÉLIA;
- value objects;
- lifecycle/state-machine semantics;
- pure policies/specifications;
- domain errors/events quando houver domínio próprio.

Sem Flask, SQLAlchemy, HTTP, provider SDK, Core client, LLM/media client.

### application

Subáreas candidatas, criadas somente quando a fase exigir e o Abstraction Gate aprovar:

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
automation_hub/
```

Só criar subdiretórios quando houver implementação real, owner/contract comprovados e Abstraction Gate aprovado.

### composition

Composition Root único ou módulos de wiring coerentes com o padrão confirmado em C0.

Provider/media/automation SDKs são construídos aqui/infrastructure, nunca dentro de use cases/domain.

## 4. Banco e migrations

A DÉLIA terá migration chain própria **somente para state/lifecycles que C0/C1 (ou fase posterior) provar que são owned**.

### OWN_MIGRATION_CHAIN — applicability

```text
OWN_MIGRATION_CHAIN applicability:
- NOT_APPLICABLE while no persisted DÉLIA-owned state exists
- REQUIRED once persisted DÉLIA-owned state is introduced
```

C1 Product Master decision (`C1-T6D1`):

```text
OWN_MIGRATION_CHAIN = NOT_APPLICABLE_AT_C1
Reason: C1 introduces no DÉLIA-owned persisted state.
```

`NOT_APPLICABLE_AT_C1` means:

- no DÉLIA-owned durable business/state model was introduced in C1;
- no legitimate schema/table owned by DÉLIA exists yet;
- no migration chain should be created only to satisfy a checklist;
- empty migration scaffolding is **forbidden**;
- Chat migrations must not be reused;
- Core/domain/provider schemas must not be treated as DÉLIA ownership.

It does **not** mean DÉLIA never needs migrations, that persistence is forbidden later, that DÉLIA may write foreign schemas without ownership, or that future state can bypass migration requirements.

### Future trigger (mandatory)

The **first** bounded task that introduces persisted state owned by DÉLIA MUST make `OWN_MIGRATION_CHAIN` applicable and **REQUIRED**, transitioning:

```text
NOT_APPLICABLE_AT_C1
→ REQUIRED
→ PASS only after implementation + evidence
```

That task cannot be accepted unless it proves, as applicable:

- owner = DÉLIA;
- persisted state need is real;
- canonical state/lifecycle is identified;
- logical namespace/schema ownership is defined;
- migration root is `delia-api/migrations/` unless a later canonical ADR supersedes it;
- migration chain is independent from Chat;
- migration changes only DÉLIA-owned schema/tables;
- forward migration test exists;
- rollback/down migration or rollback strategy is evidenced where supported;
- compatibility impact is classified;
- startup/deploy behavior with migrations is defined;
- observability/failure behavior is defined;
- no direct writes to foreign-owned DB tables;
- no empty placeholder migrations.

Evidence, not documentation existence alone, is required for `PASS`.

### Ownership rule (unchanged)

```text
DÉLIA migration
→ alters only schema/tables under DÉLIA ownership
```

Não editar migrations do Chat para atender DÉLIA.

Se um cluster PostgreSQL compartilhado for reutilizado fisicamente, manter separação lógica clara por tables/schema/ownership, constraints e migration chain próprias.

Raw audio/video não vira tabela/blob persistido por default; media storage e metadata só entram após C0/C3 provar need/policy.

C0 congela boundaries antes de migrations. Empty scaffolding to “fechar gate” viola Abstraction Gate e esta seção.

## 5. Frontend package rules

O MFE segue Clean Architecture pragmática do frontend.

```text
ui/
→ componentes/páginas/surfaces visuais

state/
→ local/conversation/workspace/media-session client state

data/
→ API da DÉLIA client/cache/adapters

features/
→ composição por capability de produto

contracts/
→ types DTO/host/media contracts

adapters/
→ Portal host/WorkspaceContext/federation/device/browser boundaries
```

Durable business/media metadata state permanece backend-owned quando persistência é necessária.

Browser mic/camera/screen permission state permanece client/platform state e não concede Business Action permission.

## 6. Module Federation

Baseline atual comprova a existência de `plugins/vite/federation.shared.ts`, `@delpi/plugin-ui`, `FEDERATION_SHARED_REACT` e helper de federation. O uso pela DÉLIA é `PLANNED`, sujeito a contract/conformance em C0/C1.

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
DeliaRoot
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

C1 não implementa STT/Vision/realtime. O frontend apenas deve evitar decisões que impeçam C3/C6.

Regras:

- media permission handling fica atrás de adapter/hook bounded quando necessário;
- nenhuma capture inicia no mount;
- reload não reinicia capture automaticamente;
- UI suporta feature/capability detection;
- accessible fallback existe como princípio;
- provider SDK não entra diretamente nos componentes.

## 9. Manifesto alvo

Shape conceitual, **não contrato congelado nem arquivo para registro ainda**:

```json
{
  "schemaVersion": "1.0.0",
  "id": "delia",
  "name": "DÉLIA",
  "type": "microfrontend",
  "basePath": "/apps/delia",
  "entry": "/apps/delia/assets/remoteEntry.js",
  "permissions": [{"code": "delia.access", "module": "delia"}],
  "routes": [{"path": "/apps/delia", "permission": "delia.access"}],
  "backend": {
    "required": true,
    "serviceName": "delia-api",
    "baseUrl": "/apps/delia-api",
    "validateJwt": true
  },
  "ui": {"renderMode": "federated"}
}
```

`id=delia`, paths e `serviceName=delia-api` são freeze aceito C0.S1. Manifest source owner = DÉLIA; app/route/RBAC registry owner = Core. Navegação vigente permanece `/me/apps` → `apps[].routes` (não recriar `/me/routes`).

**C1-T4D1 Product Master decision (APPROVED):** `delia.access` é a permission canônica de bootstrap/platform-access da DÉLIA — visibilidade do app, filtragem Core `/me/apps`, navegação Portal e acesso ao shell/rota raiz `/apps/delia`. **Não** autoriza Domain API, Evidence, Decision, Work, PREPARE, ACT, provider/tool, side effects externos ou OT. Códigos de capability de negócio (`delia.work.*`, `delia.decision.*`, etc.) permanecem não inventados. Core live registration e atribuição RBAC continuam PENDING até a etapa de publicação.

Meeting/Frontline não exigem manifests independentes por default.

## 10. Gateway target

Conceitualmente:

```nginx
location ^~ /apps/delia-api/ {
  ...
}
```

MFE/assets usam o padrão genérico `/apps/<app>/assets/...` → `delpi-<app>` (alvo: `/apps/delia`, container `delpi-delia`).

Dev/prod precisam permanecer simétricos.

Streaming/SSE/WebSocket/WebRTC-related tuning só altera buffering/timeouts/proxy settings se o transport escolhido realmente exigir e testes provarem necessidade.

## 11. Compose target

Services conceituais:

```text
delia-api          # container: delpi-delia-api
delia              # container: delpi-delia
```

Dependências mínimas candidatas, a confirmar em C0/C1:

```text
DÉLIA API:
- storage/persistence aprovado
- Keycloak/Core connectivity
- Domain APIs
- Automation Hub/executor contracts quando fase exigir
- provider connectivity quando habilitado

DÉLIA MFE:
- plugin-ui/federation foundation confirmada
- DÉLIA API via Gateway em runtime
```

Não declarar dependência de `minha-delpi-ai-api` nem `minha-delpi-chat`.

Speech/Vision/media provider não precisa ser container próprio se for serviço externo; C0/C3 decide por evidence, não por antecipação.

## 12. Shared code policy

Antes de extrair package compartilhado:

```text
há 2+ consumers reais?
contrato é neutro de produto?
owner compartilhado está claro?
versão/testes independentes são justificáveis?
```

Se não, manter implementação no bounded context dono. Não transformar o Chat em biblioteca compartilhada.

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
1. criar API da DÉLIA skeleton
2. /health
3. JWT validation
4. Core client / current-user context
5. criar MFE da DÉLIA skeleton
6. plugin-ui/federation
7. responsive/accessibility/media-permission baseline
8. manifest draft/registration path
9. gateway dev/prod
10. compose dev/prod
11. Portal AppHost mount
12. authorized route smoke
13. independent shutdown/rollback
```

Cada item só pode usar contrato/owner comprovado no baseline atualizado. Se uma dependência não estiver provada, volta para `TO_INVENTORY`/ADR; não inventar compatibilidade.

Só depois o Intelligence Core começa.

## 15. Por que bootstrap vem antes de inteligência

Isso deve provar cedo:

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

Até esses testes existirem, são critérios de aceite `PLANNED`, não fatos.

## 16. Build sequence

A única sequência válida é a do Plano Mestre `16`:

```text
C0 — Foundation Freeze factual/arquitetural
↓
C1 — Standalone Application Bootstrap
↓
C2 — Portal + Operational Context + Platform Commands
↓
C3 — Intelligence Core + Capability Foundations
↓
C4 — Governed Reads + Graph/Semantics/Analysis/Predictive Discovery
↓
C5 — Governed Writes + Executors + Durable Work + Artifacts/Prescriptive Prepare
↓
C6 — Product Work + Process Intelligence + Control Tower + Meeting/Frontline + Ecosystem
↓
C7 — Advanced Autonomy + Operational Twin/Edge/Marketplace/Optimization + Scale/Rollout
```

Este documento não cria ordem paralela.

## 17. Definition of Bootstrap Done

```text
API_FOLDER_INDEPENDENT = PASS
MFE_FOLDER_INDEPENDENT = PASS
OWN_MIGRATION_CHAIN = PASS | NOT_APPLICABLE_AT_C1
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

### OWN_MIGRATION_CHAIN acceptance semantics

```text
PASS:
  C1 introduced persisted DÉLIA-owned state and the independent migration chain
  was implemented and proven with evidence.

NOT_APPLICABLE_AT_C1:
  C1 introduced no persisted DÉLIA-owned state, so creating migrations would
  violate the persistence ownership rule (§4) and the Abstraction Gate.
```

`NOT_APPLICABLE_AT_C1` is **not** a waiver for future persisted state.

The first bounded task introducing DÉLIA-owned persistence MUST transition:

```text
NOT_APPLICABLE_AT_C1
→ REQUIRED
→ PASS only after implementation/evidence
```

Product Master C1-T6D1 decision: `OWN_MIGRATION_CHAIN = NOT_APPLICABLE_AT_C1` (no DÉLIA-owned persisted state in C1).

Nenhum item vira `PASS` por existência documental ou skeleton isolado. É necessária evidência válida para SHA/config, wiring real e teste aplicável. `NOT_APPLICABLE_AT_C1` exige rationale + ausência comprovada de estado owned persistido (não checklist vazio).

Somente então liberar C2/C3 conforme `16`.
