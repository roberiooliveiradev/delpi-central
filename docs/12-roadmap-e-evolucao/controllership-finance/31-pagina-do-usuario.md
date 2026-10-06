# 31 — Página do Usuário

## Estado

**TARGET / DOCUMENTATION_GATE PASS / READY_FOR_IMPLEMENTATION_BRIEF**

Runtime do Portal Controladoria & Finanças: **NOT_IMPLEMENTED**.

Este documento especifica a primeira superfície transversal do Portal a ser preparada para implementação:

```text
/apps/controllership-finance/users/{userId}
```

A página de usuário **não** é um novo item da topbar. Ela é uma deep route do Portal, acessada principalmente pela identidade/avatar do usuário e, futuramente, por links de pessoas em superfícies que possuam vínculo real com usuários.

## Decisões congeladas

Decisões de produto aprovadas em 06/10/2026:

```text
D1 = B
Usuário com controllership-finance.access pode consultar o perfil corporativo
básico de outro usuário com acesso ao mesmo Portal.

D2 = A
No próprio perfil, mostrar label amigável + código técnico das permissões
controllership-finance.access e controllership-finance.manage.
```

Consequências:

- permissões/capacidades de outro usuário **não** são expostas;
- `MANAGE` não implica `ACCESS`;
- usuário com apenas `controllership-finance.manage`, sem `controllership-finance.access`, não ganha leitura de perfis do Portal por consequência administrativa;
- não criar permission específica para perfil, usuário, contato, foto ou rota;
- não criar busca/listagem de usuários como parte desta página;
- ampliar os dados exibidos para além do perfil corporativo básico exige nova evidência/decisão.

## Objetivo

Permitir que um usuário autorizado do Portal:

1. consulte a própria identidade corporativa;
2. consulte a identidade corporativa básica de outro usuário do mesmo Portal;
3. acesse atalhos permitidos para a própria sessão;
4. use canais de contato corporativos disponíveis;
5. visualize, **somente no próprio perfil**, as capacidades e permission codes efetivos relevantes ao Portal;
6. edite foto, cargo e contatos pelo **Meu Perfil da Minha DELPI**, sem duplicar ownership no Portal Controladoria & Finanças.

## Ownership

### Core API

Owner de:

- diretório de usuários;
- nome;
- e-mail;
- person profile;
- cargo;
- telefone;
- celular;
- WhatsApp;
- foto;
- apps autorizados;
- effective permissions;
- RBAC.

Contratos S2S de leitura já existentes que devem ser revalidados no HEAD da implementação:

```text
POST /integrations/directory/users/lookup
GET  /integrations/directory/users/by-app
GET  /integrations/person-profiles/{userId}
GET  /integrations/person-profiles/{userId}/photo
```

O **Portal principal Minha DELPI** já é a superfície canônica de autoedição do perfil e usa a Core API diretamente para o usuário autenticado:

```text
GET    /core-api/me/person-profile
PATCH  /core-api/me/person-profile
GET    /core-api/me/person-profile/photo
PUT    /core-api/me/person-profile/photo
DELETE /core-api/me/person-profile/photo
```

No runtime atual, essa superfície permite ao próprio usuário editar **cargo e contatos** e adicionar/trocar/remover a própria foto. Nome e e-mail vêm da conta corporativa e permanecem somente leitura nessa tela.

### controllership-finance-api

Owner da composição do produto:

- validação AuthN/AuthZ server-side;
- política D1;
- confirmação de que o target pertence ao Portal;
- composição Directory + Person Profile;
- exposição apenas dos campos necessários;
- projeção self-only de capabilities/permission codes;
- tradução de indisponibilidade em estados honestos;
- proxy autorizado da foto quando necessário.

### plugins/controllership-finance

Owner de:

- composição visual;
- navegação;
- labels/copy PT-BR;
- estados da experiência;
- deep link;
- contato via `mailto:`, `tel:` e link de WhatsApp quando houver dado;
- redirecionamento para o Meu Perfil da Minha DELPI.

O MFE não é authority de permissions nem decide acesso final.

## Não objetivos

Esta página não cria:

- cadastro de usuário;
- edição local de identidade;
- storage local de foto;
- tabela/migration de perfil;
- permission por página;
- permission por filial/unidade;
- grupos, roles ou permission detail de outro usuário;
- busca global de pessoas;
- gestão de equipe;
- atribuição de responsabilidades;
- responsável/validator agregados de P2/P4/P6;
- preferências de usuário próprias do Portal nesta primeira versão.

Responsabilidades operacionais podem ser adicionadas futuramente somente quando existir contract user-centric comprovado pelos owners correspondentes.

## Rota

### MFE

```text
/apps/controllership-finance/users/{userId}
```

A rota é interna ao MFE e não adiciona entrada à topbar.

### BFF

TARGET:

```text
GET /apps/controllership-finance-api/users/{userId}/profile
GET /apps/controllership-finance-api/users/{userId}/profile/photo
```

Nenhum write de person profile pertence ao BFF do Controladoria nesta versão.

Proibido criar:

```text
PATCH  /users/{userId}/profile
PUT    /users/{userId}/profile/photo
DELETE /users/{userId}/profile/photo
```

Edição de identidade continua no **Meu Perfil da Minha DELPI**, que já escreve na Core API pelos contratos `/core-api/me/person-profile` e `/core-api/me/person-profile/photo`. O Portal Controladoria & Finanças permanece somente leitura para esses dados.

## Fluxo canônico de leitura e edição

A separação de responsabilidades é obrigatória:

```text
VISUALIZAÇÃO NO PORTAL CONTROLADORIA & FINANÇAS
plugins/controllership-finance
→ controllership-finance-api
→ Core Directory / Person Profile / Effective Permissions
→ render read-only

EDIÇÃO DO PRÓPRIO PERFIL
Portal principal Minha DELPI / Meu Perfil
→ Core API /core-api/me/person-profile
→ PATCH cargo/contatos
→ Core persistence

FOTO DO PRÓPRIO PERFIL
Portal principal Minha DELPI / Meu Perfil
→ Core API /core-api/me/person-profile/photo
→ PUT/DELETE foto
→ Core avatar storage + metadata
```

Consequências arquiteturais:

- o botão **Editar no Meu Perfil** sempre sai da superfície de Controladoria e navega para a experiência global da Minha DELPI;
- `plugins/controllership-finance` não renderiza inputs de cargo/telefone/celular/WhatsApp nem upload de foto;
- `controllership-finance-api` não implementa proxy de write para esses contratos;
- não duplicar validação E.164, regras de upload, storage ou self-edit policy no produto;
- após o usuário editar o perfil global e retornar, a página do Controladoria deve recarregar os dados do Core; não manter cópia persistida localmente;
- a experiência de Controladoria pode exibir dados atualizados, mas não se torna owner deles.

## AuthZ

### Leitura do perfil

Regra server-side:

```text
authenticated
AND effective_permission(controllership-finance.access)
AND target_user_has_app_access(controllership-finance)
```

Resultado:

- ator sem `controllership-finance.access` → `403`;
- target inexistente ou sem acesso ao Portal → `404`;
- falha ao resolver effective permission → fail-closed;
- falha estrutural do Core necessária para localizar o target → erro de downstream, nunca lista vazia nem perfil sintético.

A UI esconder link não substitui esta regra.

### Próprio perfil

`isSelf` é calculado pelo BFF/consumer a partir da identidade autenticada e do `userId` solicitado.

Somente quando `isSelf=true` podem ser retornados/exibidos:

- `isSuperadmin`, quando aplicável;
- capability `access`;
- capability `manage`;
- permission codes do Portal.

### Perfil de outro usuário

Nunca retornar/exibir:

- roles;
- groups;
- permission codes;
- apps efetivos completos;
- superadmin;
- capabilities administrativas;
- qualquer dado de acesso que não seja necessário para provar membership do target no Portal.

## Contrato TARGET

### Response principal

Shape lógico esperado:

```json
{
  "userId": "uuid",
  "name": "Nome do usuário",
  "email": "usuario@empresa.com",
  "jobTitle": "Cargo ou null",
  "phone": "+55...",
  "mobile": "+55...",
  "whatsapp": "+55...",
  "hasPhoto": true,
  "isSelf": true,
  "isSuperadmin": false,
  "capabilities": {
    "access": true,
    "manage": false
  },
  "permissions": [
    "controllership-finance.access"
  ],
  "sources": {
    "directory": "AVAILABLE",
    "personProfile": "AVAILABLE"
  }
}
```

Regras:

- `isSuperadmin`, `capabilities` e `permissions` devem ser `null` ou omitidos para outro usuário;
- labels PT-BR das permissions pertencem ao frontend/content, não ao contrato do Core;
- `permissions` contém apenas os códigos deste Portal;
- null de campo pessoal significa "não informado" **somente** quando `sources.personProfile=AVAILABLE`;
- se Person Profile estiver indisponível, não interpretar null como ausência real.

O contrato físico final deve entrar no OpenAPI do BFF quando o serviço for implementado. Este markdown define semântica e acceptance, não substitui OpenAPI runtime.

### Source states

Valores mínimos:

```text
AVAILABLE
UNAVAILABLE
```

A primeira versão não deve inventar freshness quando o Core não expõe timestamp confiável para a fonte.

## Estados da experiência

A página deve distinguir:

```text
LOADING
SUCCESS
PARTIAL
ERROR
FORBIDDEN
NOT_FOUND
```

### LOADING

- manter PagePath navegável quando possível;
- usar loading do `@delpi/plugin-ui`;
- não renderizar valores placeholder como se fossem dados.

### SUCCESS

Directory e Person Profile disponíveis.

Campos realmente vazios podem usar:

```text
Não informado
```

### PARTIAL

Exemplo:

```text
Directory = AVAILABLE
Person Profile = UNAVAILABLE
```

A UI mantém nome/e-mail confiáveis e apresenta aviso explícito de que cargo/contatos estão temporariamente indisponíveis.

Não mostrar:

```text
Cargo: Não informado
Celular: Não informado
```

quando a fonte falhou.

### ERROR

Usar quando a identidade mínima não puder ser composta com segurança, incluindo falha de Directory/Core necessária para localizar o target.

Oferecer retry quando o erro for recuperável.

### FORBIDDEN

Ator autenticado sem `controllership-finance.access`.

Não transformar 403 em 404 local nem em empty.

### NOT_FOUND

Target inexistente ou sem acesso ao Portal.

Evitar detalhar na mensagem se foi "usuário inexistente" ou "sem acesso ao app" quando isso ampliar enumeração desnecessária.

## Foto

A foto continua sendo propriedade do Core Person Profile.

Fluxo:

```text
MFE
→ controllership-finance-api
→ Core /integrations/person-profiles/{userId}/photo
```

Regras:

- sem storage no Portal;
- sem migration;
- sem upload local;
- ausência real de foto → avatar por iniciais;
- falha no binário da foto não derruba a página;
- fallback visual para iniciais não deve ser usado como evidência de que o usuário não possui foto.

## Reuso obrigatório de @delpi/plugin-ui

Existe uma **full-page reusable** canônica para este caso.

Import preferencial:

```ts
import {
  createDashboardPortalUserProfilePage,
  portalUserProfileAccessBemClasses,
  createDashboardSectionCard,
  StatusBadge,
  StateBanner,
  LoadingState,
} from "@delpi/plugin-ui/index";
```

Estilos/runtime:

```ts
await import("@delpi/plugin-ui/styles");
```

A página deve usar primeiro:

```text
createDashboardPortalUserProfilePage
```

Essa full page já owns:

- `PagePath`;
- `PageHero` em density comfortable;
- badge "Você";
- CTA "Editar no Meu Perfil";
- grid Identidade | Atalhos;
- avatar/foto/iniciais;
- campos de identidade;
- slots para sections de domínio;
- responsividade;
- acessibilidade estrutural.

`portalUserProfileAccessBemClasses` fornece o chrome transversal do bloco de acesso.

### DO NOT RECREATE

- shell da página de perfil;
- hero;
- identidade;
- avatar;
- grid identidade/atalhos;
- badge "Você";
- CTA self;
- access chrome;
- `SectionCard`;
- `StatusBadge`;
- loading/error chrome;
- CSS do `PortalUserProfilePage`.

O MFE pode criar somente layout de página/composição e conteúdo específico do Portal. CSS de componente do kit permanece exclusivamente no `plugin-ui`.

## Copy TARGET

### Hero

Eyebrow:

```text
Portal Controladoria & Finanças
```

Título:

```text
{nome do usuário}
```

Descrição:

```text
{cargo}
```

Fallback da descrição:

```text
{e-mail}
```

### Identidade

```text
Identidade
Dados do cadastro corporativo.
```

Nota:

```text
Foto, cargo e contatos são gerenciados no Meu Perfil da Minha DELPI.
```

### Atalhos

```text
Atalhos
Navegação permitida para você e canais de contato disponíveis.
```

Essa copy é deliberadamente orientada ao **viewer**, para não sugerir que os atalhos de navegação representam permissões do usuário observado.

### Acesso no Portal

Somente self:

```text
Acesso no Portal
Permissões e capacidades efetivas desta sessão.
```

Labels:

```text
Acesso ao Portal
Administração
Acessar Portal Controladoria & Finanças
Administrar Portal Controladoria & Finanças
```

Códigos técnicos visíveis conforme D2:

```text
controllership-finance.access
controllership-finance.manage
```

## Atalhos

### Navegação do Portal

Mostrar somente rotas que estejam simultaneamente:

```text
IMPLEMENTED_IN_RUNTIME
AND authorized_for_viewer
```

Não renderizar página futura apenas porque existe no roadmap.

Candidatos conforme disponibilidade real:

- Início;
- Visão geral;
- Sala de interação;
- Minhas tarefas;
- Administração — somente se o viewer possui `manage` e a rota está implementada;
- Ajuda.

### Contato

Quando o dado existir:

- e-mail → `mailto:`;
- telefone/celular → `tel:`;
- WhatsApp → link externo seguro.

Não adicionar "atribuir tarefa", "tornar validator", "mudar responsável" ou equivalentes sem caso de uso owner explícito.

## Integração com a topbar

A identidade/avatar da topbar pode navegar para:

```text
/apps/controllership-finance/users/{currentUserId}
```

somente quando a sessão possui `controllership-finance.access`.

Se a sessão tiver apenas `controllership-finance.manage`, a identidade global continua podendo levar ao Meu Perfil da Minha DELPI; isso não deve conceder `ACCESS` implicitamente.

A topbar canônica permanece exatamente:

```text
Início | Visão geral | Sala de interação | Minhas tarefas | Administração | Ajuda
```

Perfil não entra nessa lista.

## Wireframe — desktop / próprio usuário

```text
┌──────────────────────────────────────────────────────────────────────────────┐
│ Início | Visão geral | Sala | Minhas tarefas | Administração | Ajuda       │
│                                      Buscar | Favoritos | [avatar] Usuário │
└──────────────────────────────────────────────────────────────────────────────┘

← Portal Controladoria & Finanças / Nome do usuário

┌──────────────────────────────────────────────────────────────────────────────┐
│ PORTAL CONTROLADORIA & FINANÇAS                                             │
│                                                                              │
│ Nome do usuário                  [Você]              [Editar no Meu Perfil]  │
│ Cargo ou e-mail                                                             │
└──────────────────────────────────────────────────────────────────────────────┘

┌────────────────────────────────────┐  ┌────────────────────────────────────┐
│ IDENTIDADE                         │  │ ATALHOS                           │
│ Dados do cadastro corporativo.     │  │ Navegação permitida para você... │
│                                    │  │                                    │
│ [ FOTO ] Nome                      │  │ [Início] [Visão geral]            │
│          Nome do usuário           │  │ [Sala de interação]               │
│                                    │  │ [Minhas tarefas]                  │
│          E-mail                    │  │ [Administração]* [Ajuda]          │
│          usuario@empresa.com       │  │                                    │
│                                    │  │ [Enviar e-mail]                   │
│          Cargo                     │  │ [Ligar]* [WhatsApp]*              │
│          ...                       │  │                                    │
│                                    │  │ * quando aplicável                │
│          Telefone / Celular        │  │                                    │
│          WhatsApp                  │  │                                    │
│                                    │  │                                    │
│ Foto, cargo e contatos são         │  │                                    │
│ gerenciados no Meu Perfil.         │  │                                    │
└────────────────────────────────────┘  └────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────────────────┐
│ ACESSO NO PORTAL                                                            │
│ Permissões e capacidades efetivas desta sessão.                             │
│                                                                              │
│ Capacidades                                                                  │
│ [Acesso ao Portal] [Administração]*                                         │
│                                                                              │
│ Permissões RBAC                                                              │
│ Acessar Portal Controladoria & Finanças      controllership-finance.access  │
│ Administrar Portal Controladoria & Finanças  controllership-finance.manage  │
└──────────────────────────────────────────────────────────────────────────────┘
```

## Wireframe — desktop / outro usuário

```text
← contexto anterior / Nome do usuário

┌──────────────────────────────────────────────────────────────────────────────┐
│ PORTAL CONTROLADORIA & FINANÇAS                                             │
│                                                                              │
│ Nome do usuário                                                             │
│ Cargo ou e-mail                                                             │
└──────────────────────────────────────────────────────────────────────────────┘

┌────────────────────────────────────┐  ┌────────────────────────────────────┐
│ IDENTIDADE                         │  │ ATALHOS                           │
│ Dados do cadastro corporativo.     │  │ Navegação permitida para você... │
│                                    │  │                                    │
│ [ FOTO ] Nome / e-mail / contatos  │  │ [voltar ao contexto]             │
│                                    │  │ [Enviar e-mail]                   │
│                                    │  │ [Ligar]* [WhatsApp]*              │
└────────────────────────────────────┘  └────────────────────────────────────┘

Não renderizar:
- badge "Você";
- "Editar no Meu Perfil";
- capabilities;
- permission codes;
- roles/groups;
- administração do target.
```

## Wireframe — mobile

```text
TOPBAR COMPACTA

← Portal

┌─────────────────────────────┐
│ Nome do usuário      [Você] │
│ Cargo                       │
│                             │
│ [Editar no Meu Perfil]      │
└─────────────────────────────┘

┌─────────────────────────────┐
│ Identidade                  │
│                             │
│ [foto]                      │
│ Nome                        │
│ E-mail                      │
│ Cargo                       │
│ Telefone                    │
│ Celular                     │
│ WhatsApp                    │
└─────────────────────────────┘

┌─────────────────────────────┐
│ Atalhos                     │
│                             │
│ [Início                 ]   │
│ [Visão geral            ]   │
│ [Sala de interação      ]   │
│ [Minhas tarefas         ]   │
│ [Administração          ]*  │
│ [Ajuda                  ]   │
│ [Enviar e-mail          ]   │
│ [WhatsApp               ]*  │
└─────────────────────────────┘

┌─────────────────────────────┐
│ Acesso no Portal            │
│ self only                   │
└─────────────────────────────┘
```

Para outro usuário, remover self chrome e seção de acesso.

## Wireframe — PARTIAL

```text
[!] Alguns dados do perfil estão temporariamente indisponíveis.
    Nome e e-mail estão atualizados pelo diretório.
    Cargo e contatos não puderam ser consultados agora.

┌────────────────────────────────────┐
│ IDENTIDADE                         │
│ [foto/iniciais] Nome               │
│                 E-mail             │
│                                    │
│ Cargo      Indisponível no momento │
│ Telefone   Indisponível no momento │
│ Celular    Indisponível no momento │
│ WhatsApp   Indisponível no momento │
└────────────────────────────────────┘
```

## Tema e CSS

Root técnico do Portal:

```text
.portal-controllership-finance
```

O MFE deve mapear tokens `--delpi-ui-*` no root e manter CSS de componente no kit.

Não criar override local de:

```text
.delpi-ui-portal-user-profile*
```

Claro/escuro são validados via tokens do Portal, não por duplicação de CSS.

## Acessibilidade

Obrigatório:

- headings semânticos;
- PagePath operável por teclado;
- foco visível;
- avatar/foto com nome acessível;
- links de e-mail/telefone/WhatsApp com label explícito;
- status não dependente apenas de cor;
- CTA "Editar no Meu Perfil" com destino compreensível;
- retry focável;
- ordem mobile coerente;
- nenhum dado material apenas em tooltip/hover.

## Deep link / retorno

`/users/{userId}` deve sobreviver a F5.

Quando a navegação vier de outra superfície do Portal, preservar contexto de retorno por mecanismo seguro do próprio MFE, por exemplo `returnTo` validado dentro de `/apps/controllership-finance`.

Nunca aceitar open redirect.

Fallback:

```text
Portal Controladoria & Finanças
→ /apps/controllership-finance
```

## Help

Mudança user-facing nesta página exige sync da Ajuda no mesmo gate de implementação.

A Ajuda deve explicar:

- o que é a página de usuário;
- quais dados vêm do cadastro corporativo;
- onde editar foto/cargo/contatos;
- diferença entre "Não informado" e "temporariamente indisponível";
- que permissions/capabilities só aparecem no próprio perfil;
- que visualizar outro perfil não concede poder administrativo;
- que Administração depende de `manage`;
- como voltar ao contexto anterior.

Não publicar instruções de uso da página na Ajuda antes da rota estar implementada.

## RQ / AC

### RQ-USER-01 — rota transversal sem item de topbar

Aceite:

- deep route `/users/{userId}`;
- topbar permanece com seis itens canônicos;
- avatar self pode abrir a rota quando viewer possui ACCESS;
- F5 preserva rota.

### RQ-USER-02 — identidade vem do Core

Aceite:

- nome/e-mail do Directory;
- person profile do Core;
- zero tabela/migration/storage de identidade no Portal;
- foto não é persistida no BFF.

### RQ-USER-03 — D1 / leitura de outro usuário

Aceite:

- viewer com ACCESS abre target com acesso ao mesmo Portal;
- target sem acesso ao app resulta 404;
- viewer sem ACCESS resulta 403;
- nenhuma permission nova é criada.

### RQ-USER-04 — D2 / acesso self-only

Aceite:

- próprio perfil mostra labels + códigos `access`/`manage` efetivos;
- outro perfil não retorna nem renderiza permissions/capabilities;
- JWT/frontend não são authority final.

### RQ-USER-05 — edição pertence ao Meu Perfil

Aceite:

- CTA self abre o Meu Perfil do Portal principal Minha DELPI;
- cargo/contatos são editados pelo contrato Core `PATCH /core-api/me/person-profile`;
- foto é adicionada/trocada/removida pelos contratos Core `/core-api/me/person-profile/photo`;
- nome/e-mail permanecem conforme a conta corporativa e não são editados no Portal Controladoria & Finanças;
- não existe write de identidade nem proxy de write no `controllership-finance-api`;
- o MFE de Controladoria não contém form de edição/upload;
- ao retornar do Meu Perfil, os dados são recarregados do Core;
- outro usuário não recebe CTA de edição.

### RQ-USER-06 — estados honestos

Aceite:

- person profile unavailable → PARTIAL;
- null real com source disponível → "Não informado";
- Directory/Core estruturalmente indisponível → ERROR/downstream;
- 403 e 404 distintos.

### RQ-USER-07 — plugin-ui first

Aceite:

- `createDashboardPortalUserProfilePage` usado como full-page;
- nenhum clone local do chrome;
- nenhum CSS de componente do kit no MFE;
- claro/escuro/mobile/keyboard validados.

### RQ-USER-08 — atalhos não antecipam roadmap

Aceite:

- navegação mostra somente rota implementada + autorizada ao viewer;
- Administração só quando `manage`;
- contatos apenas quando os dados existem;
- rota futura documentada não vira botão automaticamente.

### RQ-USER-09 — Help sincronizada

Aceite:

- Ajuda atualizada no mesmo gate;
- links/deep links válidos;
- conteúdo não promete feature antes do runtime.

## Matriz mínima de testes

### Positive

- self com ACCESS;
- self com ACCESS+MANAGE;
- outro usuário do Portal com viewer ACCESS;
- identidade completa;
- identidade sem foto;
- contato opcional ausente;
- deep link/F5;
- retorno ao contexto anterior.

### Sibling

- abrir usuário B não reutiliza nome/foto/contato de usuário A;
- alternar entre perfis não vaza permission codes do self;
- falha do Person Profile de um target não marca outro target como partial.

### Negative

- sem token;
- token inválido;
- viewer sem ACCESS;
- viewer somente MANAGE;
- target sem acesso ao Portal;
- target inválido;
- tentativa de obter permissions de outro usuário;
- Core effective permission indisponível → fail-closed;
- open redirect em `returnTo`;
- source unavailable tratado como "Não informado";
- link para rota futura não implementada.

### UI / experiência

- loading;
- partial;
- error + retry;
- 403;
- 404;
- desktop;
- mobile;
- tema claro;
- tema escuro;
- teclado/foco;
- status sem dependência exclusiva de cor;
- Help sincronizada.

## Evidência exigida na implementação

O report do Cursor deve incluir:

```text
BASE HEAD
FINAL HEAD
STATUS
FACTS PROVEN
TO_INVENTORY
EXECUTION_DRIFT
FILES INSPECTED/CHANGED
CONTRACT IMPACT
PLUGIN_UI_COMPONENTS_REUSED
LOCAL_UI_CREATED
WHY_LOCAL_UI_WAS_NECESSARY
PLUGIN_UI_GAP_FOUND
SECURITY CHECKS
RQ/AC COVERAGE
TESTS
FEDERATED SMOKE
RESIDUAL SEARCH
POSTCONDITION/OUTCOME
UNRESOLVED
NEXT STEP
```

Smoke federado não executado quando material = `INCONCLUSIVE`, nunca PASS inferido.

## Gate para implementação

Antes do diff runtime:

```text
HEAD reancorado
AND foundation do MFE/BFF existente ou explicitamente autorizada no mesmo slice
AND Core contracts revalidados no HEAD
AND effective permission adapter definido fail-closed
AND app membership lookup comprovado
AND plugin-ui full-page export revalidado
AND RQ-USER-01..09 selecionados
AND Help incluída no mesmo gate
```

Se qualquer premissa acima mudar materialmente:

```text
EXECUTION_DRIFT
→ STOP
→ não adaptar silenciosamente
```

## Sequência sugerida de implementação

```text
UP.S1 — BFF read-only profile composition + AuthZ + contract tests
→ UP.S2 — MFE route/page + plugin-ui full-page + states
→ UP.S3 — topbar/deep links + Help + UI tests
→ UP.S4 — build + federated smoke + acceptance evidence
```

A sequência é um handoff, não authority superior a contracts/runtime do HEAD.

## Definition of Done

A página só está pronta quando:

- D1 e D2 implementadas exatamente;
- Core permanece owner da identidade, person profile e foto;
- edição ocorre somente no Portal principal Minha DELPI usando a Core API;
- nenhuma persistência local de perfil foi criada;
- BFF autoriza server-side e fail-closed;
- outro usuário não vaza RBAC;
- `PortalUserProfilePage` é reutilizada;
- estados honestos cobertos;
- Help sincronizada;
- positive + sibling + negative verdes;
- deep link/F5 funciona;
- desktop/mobile, claro/escuro e teclado/foco validados;
- build verde;
- smoke federado executado quando material.
