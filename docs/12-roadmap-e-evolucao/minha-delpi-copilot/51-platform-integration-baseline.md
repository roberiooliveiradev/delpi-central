# Minha DELPI Copilot — Baseline de Integração com a Plataforma

**Status:** `CANONICAL_BASELINE` de evidências para integração  
**Escopo:** Portal, Core API, Gateway, APIs, MFEs, plugin-ui, infraestrutura e gaps a inventariar para media/Meeting/Frontline/OT  
**Ordem:** [`16-execution-master-plan.md`](./16-execution-master-plan.md)  
**Multimodal/Meeting/Frontline:** [`53-multimodal-meeting-frontline-and-industrial-copilot.md`](./53-multimodal-meeting-frontline-and-industrial-copilot.md)

## 1. Objetivo

Registrar fatos observados no repositório antes da implementação do Copilot standalone e separar claramente **fato comprovado** de **item ainda `TO_INVENTORY`**.

Este arquivo não substitui C0.S0. Ele estabelece a baseline já comprovada que C0 deve revalidar no HEAD de execução e lista novos gaps de mídia/device/industrial que **não podem ser preenchidos por suposição**.

## 2. Portal é Shell e Host de aplicações — PROVEN

O Portal atual possui React/Vite e separação em `auth/components/data/hooks/layout/pages/routes/state/ui/ui-kit/utils`.

O `AuthContext`:

- obtém token do Keycloak;
- consulta Core API;
- carrega usuário e apps autorizados;
- agrega rotas fornecidas pelos apps;
- fornece `getAccessToken`, user, apps/routes, favorites e notifications.

Consequência:

> Copilot não implementa login/RBAC no frontend. Ele é hospedado pelo Portal e recebe a identidade/token pelo contrato normal do host.

## 3. AppHost suporta três modos — PROVEN

O contrato do Portal possui:

```text
embedded
external
federated
```

Para `federated`, o `AppHost`:

1. resolve `remoteEntry`;
2. inicializa share scope;
3. carrega módulo exposto;
4. exige `mount()`;
5. passa propriedades de host.

Props observadas:

```text
getAccessToken
basePath
pathname
search
alternateEntry
appRoutes
routeLabel
permissions
isSuperadmin
```

**Decisão:** Copilot será MFE `federated`.

`iframe` não é o modo alvo do próprio Copilot; iframe bridge é apenas integração do Copilot com outros apps iframe.

## 4. AppLauncher/Menu são Core-driven — PROVEN

`AppLauncher` usa `apps` e `routes` do `AuthContext`, logo o app registrado na Core API aparece/navega conforme manifesto e permissões.

Não criar catálogo manual do Copilot dentro do Portal.

## 5. Manifestos de apps — PROVEN

Manifestos atuais provam o padrão:

```json
{
  "id": "commercial",
  "type": "microfrontend",
  "basePath": "/apps/commercial",
  "entry": "/apps/commercial/assets/remoteEntry.js",
  "permissions": [],
  "routes": [],
  "ui": {"renderMode": "federated"}
}
```

O Minha DELPI Chat também é MFE federado, mas seu manifesto acopla backend `minha-delpi-ai-api`. Esse vínculo é específico do Chat e **não será reutilizado pelo Copilot**.

O Copilot terá manifesto próprio.

## 6. Module Federation compartilhada — PROVEN

`plugins/vite/federation.shared.ts` define:

- React/ReactDOM singleton e strict version;
- remote `@delpi/plugin-ui`;
- aliases de testes;
- convenções reutilizadas pelos MFEs.

**Decisão:** o Copilot MFE seguirá essa infraestrutura desde o primeiro commit.

## 7. plugin-ui é Design System compartilhado — PROVEN

`plugins/plugin-ui` possui remoteEntry, documentação, componentes e lifecycle próprios.

**Decisão:** UI do Copilot reutiliza `@delpi/plugin-ui`; não duplica componentes já existentes e não importa source privado do Portal/Chat.

Se um componente Copilot for genuinamente transversal, promoção para `plugin-ui` é decisão separada com consumidores comprovados.

## 8. Core API é authority de plataforma — PROVEN

A estrutura observada do Core segue Clean Architecture:

```text
app/domain
app/application
app/interfaces
app/infrastructure
app/create_app.py
```

Core permanece owner de:

- usuários e contexto de plataforma;
- apps;
- rotas;
- permissions/RBAC;
- manifesto/registro;
- notifications/presence/app usage quando aplicável.

O Copilot não cria tabelas paralelas para essas authorities.

## 9. APIs dedicadas são padrão do monorepo — PROVEN

O repositório possui serviços pares dedicados, entre outros:

```text
api-delpi/
commercial-api/
customer-experience-api/
financial-api/
cipa-api/
comite-etica-conduta-api/
...
```

`commercial-api` demonstra organização com:

```text
application
composition
core
domain
infrastructure
interface
middleware
startup
```

**Decisão:** uma Copilot API dedicada é compatível com a organização atual e deve seguir Clean Architecture/Ports & Adapters desde a criação.

## 10. api-delpi é backend-only corporativo — PROVEN

Seu manifesto declara:

```text
type = backend-only
basePath = /apps/api-delpi
validateJwt = true
requiredPermissionsHeader = x-user-permissions
healthEndpoint = /health
```

O Copilot deve consumir `api-delpi` como sistema owner de integrações DELPI/TOTVS quando necessário, por contratos autorizados.

Nunca copiar a lógica TOTVS para dentro do Copilot.

## 11. Gateway é entrada única — PROVEN

O Nginx atual roteia serviços por prefixos `/apps/<service>/...` e Core por `/core-api/`.

Exemplos observados:

```text
/core-api/                    → core-api:8000
/apps/minha-delpi-ai/api/     → Chat AI API
/apps/commercial-api/         → commercial-api:8000
/apps/requests-api/           → requests-api:8000
/apps/supplies-api/           → supplies-api:8000
/apps/customer-experience-api/→ customer-experience-api:8000
```

**Decisão:** Copilot API terá rota própria no Gateway, sem reutilizar `/apps/minha-delpi-ai/api/`.

## 12. Infra/Compose confirma serviços independentes — PROVEN

`infra/docker-compose.dev.yml` organiza Core/Portal/Gateway/Keycloak, PostgreSQL e apps por serviços/profiles.

O Chat possui profile e containers próprios. O Copilot deverá possuir service/profile próprios, podendo reutilizar PostgreSQL/shared infra conforme decisão de C0, mas sem compartilhar runtime lógico com Chat.

## 13. SSO e autorização — TARGET derivado da plataforma comprovada

Fluxo alvo:

```text
Keycloak
→ Portal recebe access token
→ Copilot MFE usa getAccessToken
→ Gateway
→ Copilot API valida JWT
→ Copilot API consulta Core para contexto/autorização da plataforma
→ Domain API revalida operação de negócio
```

Não transportar lista definitiva de permissions como trust boundary apenas porque o MFE recebeu props de permissions.

## 14. Comunicação MFE → Copilot API — TARGET

```text
Copilot MFE
→ typed API client
→ /apps/minha-delpi-copilot-api/...
→ Gateway
→ Copilot API
```

Sem chamadas diretas do browser aos serviços internos, salvo contrato de plataforma existente explicitamente permitido.

## 15. Comunicação Copilot API → Core — TARGET

Necessidades iniciais:

- resolver usuário/contexto;
- apps autorizados;
- rotas autorizadas;
- permission/capability context;
- avatar/user metadata quando UX exigir;
- notifications somente quando Core for owner apropriado.

A API do Copilot não cacheia autorização indefinidamente; define freshness/revalidation por policy.

## 16. Comunicação Copilot API → APIs de domínio — TARGET

Preferência:

```text
OpenAPI/contract canônico
→ discovery/index
→ allowed capability projection
→ generic HTTP adapter
```

O Copilot não cria client/service especializado por endpoint apenas para ensinar o planner.

Adapters específicos só são permitidos quando a API exige protocolo/semântica não representável no executor genérico e isso for provado em C0/C3.

## 17. Eventos, sockets e notificações — PARTIAL PROVEN / TO_INVENTORY

A plataforma já possui:

- Core Socket.IO;
- APIs com WebSocket/socket quando necessário;
- notifications no Core/Portal;
- workers/schedulers em alguns serviços.

C0.S0 deve inventariar owners e contratos concretos antes de criar event bus, inbox delivery ou notification transport do Copilot.

Regra:

```text
Copilot owns work/watch semantics
Core/Portal may own shared notification delivery/presentation
```

## 18. Salas de interação — EXISTENCE PROVEN / CONTRACT TO_INVENTORY

O manifesto do Portal Comercial expõe rota `/apps/commercial/interaction-rooms`.

C0 deve mapear implementação, API, storage, sockets e authorization antes de construir Interaction Rooms do Copilot.

Possibilidades permitidas após evidence:

```text
REUSE owner existente
EXTEND contrato existente
ADAPTER para owner existente
CREATE_REQUIRED somente se gap comprovado
```

## 19. Superfícies do Copilot no Portal — TARGET

O produto evolui sem duplicar runtime:

```text
GLOBAL
WORKSPACE
MEETING
FRONTLINE
```

### Global/Workspace

Portal/full-page host do mesmo MFE.

### Meeting/Frontline

Também pertencem ao mesmo `plugins/minha-delpi-copilot` e mesma Copilot API; layouts/device capabilities podem variar.

Exports concretos (`./App`, `./Panel`, mount parametrizado etc.) são congelados em C1 após C0 evidence.

Não criar `meeting-ai-api`/`frontline-ai-api` por conveniência.

## 20. Baseline factual de mídia/realtime — TO_INVENTORY

Até a execução formal de C0.S0, **não considerar comprovados**:

- provider STT/TTS corporativo disponível;
- provider Vision/VLM corporativo disponível para o Copilot;
- WebRTC/realtime transport já padronizado;
- media/object storage adequado a gravações;
- gravação/transcrição de reunião já existente;
- browser permission wrapper compartilhado;
- quotas/custos/latência aceitáveis;
- política corporativa de retenção de raw áudio/vídeo;
- hardware de sala integrado ao Portal.

C0.S0 deve localizar evidence ou marcar `NOT_PROVEN`/`COPILOT_IMPLEMENT_NEW`/`EXTEND_PLATFORM_CONTRACT`.

## 21. Baseline factual de devices/Frontline — TO_INVENTORY

Não considerar comprovados sem C0 evidence:

- tablets industriais padronizados;
- kiosks/terminais com browser compatível;
- microfone/câmera disponíveis nos postos;
- device identity service;
- kiosk/shared-terminal session policy;
- connectivity/latency no chão de fábrica;
- headset/wearable;
- current production-terminal app contract.

C0 deve mapear hardware/processo real antes de escolher transport/UX específico.

## 22. Contexto operacional — TO_INVENTORY por domínio

A arquitetura define o modelo:

```text
WorkspaceContext + EntityRef
```

Mas C0 precisa provar owners/IDs/contracts reais para:

```text
productionOrder
operation
machine
workstation
product/revision
lot
material
tool
```

Não inventar IDs ou source systems.

## 23. Industrial/OT — TO_INVENTORY e NO-ACTUATION default

Até C0 mapear a realidade, não assumir:

- PLC/CNC/robot vendors/protocols;
- SCADA/MES ownership;
- telemetry access;
- command APIs;
- network reachability;
- safety architecture;
- interlock contracts.

Mesmo que C0 encontre uma interface de comando, isso **não autoriza** o Copilot a executá-la.

Default arquitetural:

```text
approved telemetry/read → pode ser candidato a Adapter
free-form Copilot/LLM machine actuation → BLOCK
```

Qualquer atuação OT futura exige initiative/safety gate separado conforme `53`.

## 24. Privacy/consent/retention — TO_INVENTORY

C0 deve mapear políticas e owners reais para:

- captura de áudio;
- gravação/transcrição;
- câmera/vídeo;
- screen share;
- employee/workplace privacy;
- retenção/deleção;
- LGPD/data classification;
- provider processing;
- export/download.

Até haver evidence, nenhuma raw-media retention deve ser assumida.

## 25. Training/procedures — TO_INVENTORY

C0 deve mapear fontes oficiais de:

- instruções de trabalho;
- procedimentos;
- desenhos/revisões;
- vídeos de treinamento;
- qualification/certification state;
- owners e freshness/versioning.

Frontline training assistance deve referenciar essas authorities, não criar conteúdo operacional como truth sem owner.

## 26. Inventário obrigatório complementar em C0.S0

Mesmo com esta baseline, revisar:

### Plataforma existente
- todos os manifests ativos;
- todas as APIs e OpenAPIs disponíveis;
- auth middleware de APIs representativas;
- patterns de HTTP clients;
- notifications/events/workers;
- app registration scripts;
- Gateway dev/prod;
- Compose dev/prod;
- env vars;
- migrations/storage patterns;
- plugin-ui exports;
- federation contract/mount/unmount;
- Portal global layouts/overlays;
- existing rooms/cases/requests.

### Nova visão multimodal/industrial
- media/browser APIs;
- speech/vision providers;
- storage/retention;
- realtime transport;
- shared devices;
- meeting hardware/process;
- production context sources;
- training/procedures;
- OT telemetry/interfaces;
- industrial safety owners.

## 27. Conclusão da baseline

**Comprovado:** a plataforma atual já fornece as fundações corporativas para uma aplicação autônoma:

```text
Keycloak       → SSO
Core API       → governance/RBAC/apps/routes
Portal         → Shell/host/context/navigation
Gateway        → routing
plugin-ui      → design system
Module Federation → MFE integration
Domain APIs    → business data/rules
Infra          → deploy/network/storage foundations
```

**Ainda não comprovado:** detalhes de media/realtime/devices/factory hardware/OT/privacy policies. Esses itens pertencem explicitamente ao C0.S0 e não podem ser inferidos.

O Copilot deve nascer **sobre** as fundações comprovadas; seu runtime inteligente/multimodal é próprio.