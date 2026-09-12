# Minha DELPI Copilot — Baseline de Integração com a Plataforma

**Status:** `CANONICAL_BASELINE` de evidências para integração  
**Escopo:** Portal, Core API, Gateway, APIs, MFEs, plugin-ui e infraestrutura  
**Ordem:** [`16-execution-master-plan.md`](./16-execution-master-plan.md)

## 1. Objetivo

Registrar fatos observados no repositório antes da implementação do Copilot standalone. Este arquivo não substitui o inventário C0.S0: ele estabelece a baseline arquitetural já comprovada que C0 deve revalidar no HEAD de execução.

## 2. Portal é Shell e Host de aplicações

O Portal atual possui React/Vite e separação em `auth/components/data/hooks/layout/pages/routes/state/ui/ui-kit/utils`.

O `AuthContext`:

- obtém token do Keycloak;
- consulta Core API;
- carrega usuário e apps autorizados;
- agrega rotas fornecidas pelos apps;
- fornece `getAccessToken`, user, apps/routes, favorites e notifications.

Consequência:

> Copilot não implementa login/RBAC no frontend. Ele é hospedado pelo Portal e recebe a identidade/token pelo contrato normal do host.

## 3. AppHost suporta três modos

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

## 4. AppLauncher/Menu são Core-driven

`AppLauncher` usa `apps` e `routes` do `AuthContext`, logo o app registrado na Core API aparece/navega conforme manifesto e permissões.

Não criar catálogo manual do Copilot dentro do Portal.

## 5. Manifestos de apps

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

## 6. Module Federation compartilhada

`plugins/vite/federation.shared.ts` define:

- React/ReactDOM singleton e strict version;
- remote `@delpi/plugin-ui`;
- aliases de testes;
- convenções reutilizadas pelos MFEs.

**Decisão:** o Copilot MFE seguirá essa infraestrutura desde o primeiro commit.

## 7. plugin-ui é Design System compartilhado

`plugins/plugin-ui` possui remoteEntry, documentação, componentes e lifecycle próprios.

**Decisão:** UI do Copilot reutiliza `@delpi/plugin-ui`; não duplica componentes já existentes e não importa source privado do Portal/Chat.

Se um componente Copilot for genuinamente transversal, promoção para `plugin-ui` é decisão separada com consumidores comprovados.

## 8. Core API é authority de plataforma

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

## 9. APIs dedicadas são padrão do monorepo

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

## 10. api-delpi é backend-only corporativo

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

## 11. Gateway é entrada única

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

## 12. Infra/Compose confirma serviços independentes

`infra/docker-compose.dev.yml` organiza Core/Portal/Gateway/Keycloak, PostgreSQL e apps por serviços/profiles.

O Chat possui profile e containers próprios. O Copilot deverá possuir service/profile próprios, podendo reutilizar PostgreSQL/shared infra conforme decisão de C0, mas sem compartilhar runtime lógico com Chat.

## 13. SSO e autorização

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

## 14. Comunicação MFE → Copilot API

Padrão alvo:

```text
Copilot MFE
→ typed API client
→ /apps/minha-delpi-copilot-api/...
→ Gateway
→ Copilot API
```

Sem chamadas diretas do browser aos serviços internos, salvo contrato de plataforma existente explicitamente permitido.

## 15. Comunicação Copilot API → Core

Necessidades iniciais:

- resolver usuário/contexto;
- apps autorizados;
- rotas autorizadas;
- permission/capability context;
- avatar/user metadata quando UX exigir;
- notifications somente quando Core for owner apropriado.

A API do Copilot não cacheia autorização indefinidamente; define freshness/revalidation por policy.

## 16. Comunicação Copilot API → APIs de domínio

Preferência:

```text
OpenAPI/contract canônico
→ discovery/index
→ allowed capability projection
→ generic HTTP adapter
```

O Copilot não cria client/service especializado por endpoint apenas para ensinar o planner.

Adapters específicos só são permitidos quando a API exige protocolo/semântica não representável no executor genérico e isso for provado em C0/C3.

## 17. Eventos, sockets e notificações

A plataforma já possui:

- Core Socket.IO;
- APIs com WebSocket/socket quando necessário;
- notifications no Core/Portal;
- workers/schedulers em alguns serviços.

C0.S0 deve inventariar esses owners antes de criar event bus, inbox delivery ou notification transport do Copilot.

Regra:

```text
Copilot owns work/watch semantics
Core/Portal may own shared notification delivery/presentation
```

Não confundir semantic state do Copilot com canal de notificação.

## 18. Salas de interação

O manifesto do Portal Comercial expõe rota `/apps/commercial/interaction-rooms`.

C0 deve mapear implementação e contracts dessas salas antes de construir Interaction Rooms do Copilot.

Possibilidades permitidas após evidence:

```text
REUSE owner existente
EXTEND contrato existente
ADAPTER para owner existente
CREATE_REQUIRED somente se gap comprovado
```

## 19. Superfícies do Copilot no Portal

O produto deve possuir duas experiências sem duplicar runtime:

### App/full page

Registrado como MFE normal e acessível pelo launcher/menu/rota.

### Global surface

Botão/side panel persistente no Shell, implementado como host/adapter mínimo que monta o mesmo MFE ou um módulo federado específico do mesmo pacote.

Exemplo de exports possíveis, a confirmar em C1:

```text
./App
./Panel
```

ou um único `mount` parametrizado por `surface`.

A escolha precisa ser congelada por contrato antes de implementação.

## 20. Inventário obrigatório complementar em C0.S0

Mesmo com esta baseline, C0 precisa revisar:

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
- Portal global layouts/overlays para side panel;
- existing rooms/cases/requests;
- API docs/actions úteis ao Copilot.

## 21. Conclusão da baseline

A plataforma atual já fornece as fundações corporativas para uma aplicação autônoma:

```text
Keycloak       → SSO
Core API       → governance/RBAC/apps/routes
Portal         → Shell/host/context/navigation
Gateway        → routing
plugin-ui      → design system
Module Federation → MFE integration
Domain APIs    → business data/rules
Infra          → deploy/network/storage
```

O Copilot deve nascer **sobre** essas fundações, mas seu runtime inteligente é totalmente próprio.