# 24 — Início e Navegação Principal

## Estado

**TARGET / DOCUMENTED**

Este documento define a arquitetura de informação da topbar do **Portal Controladoria & Finanças**.

## Topbar canônica

A navegação principal do Portal contém exatamente:

```text
Início
Visão geral
Sala de interação
Minhas tarefas
Administração
Ajuda
```

Não adicionar nova entrada de topbar sem decisão explícita de produto.

## Rotas lógicas

Seguindo o padrão atual dos Portais Comercial e Suprimentos:

| Item | Rota TARGET | Permission |
|---|---|---|
| Início | `/apps/controllership-finance` | `controllership-finance.access` |
| Visão geral | `/apps/controllership-finance/overview` | `controllership-finance.access` |
| Sala de interação | `/apps/controllership-finance/interaction-rooms` | `controllership-finance.access` |
| Minhas tarefas | `/apps/controllership-finance/my-tasks` | `controllership-finance.access` |
| Administração | `/apps/controllership-finance/administration` | `controllership-finance.manage` |
| Ajuda | `/apps/controllership-finance/help` | `controllership-finance.access` |

Identifiers técnicos são em inglês; labels de UX permanecem PT-BR.


## Reuso obrigatório de `@delpi/plugin-ui`

Esta página não deve recriar chrome de navegação, cards de launcher ou estados genéricos.

Import canônico em MFE federado:

```ts
import {
  createDashboardTopBar,
  createDashboardSectionRouteCard,
  createDashboardNavigationCard,
  createDashboardRecentAccessStrip,
  createDashboardPageHero,
  EmptyState,
  LoadingState,
} from "@delpi/plugin-ui/index";
```

Estilos/runtime do kit:

```ts
await import("@delpi/plugin-ui/styles");
```

Uso esperado:

| Necessidade | Reuso canônico |
|---|---|
| topbar principal | `createDashboardTopBar` |
| launcher de funcionalidades com subrotas | `createDashboardSectionRouteCard` |
| card simples de entrada em uma funcionalidade | `createDashboardNavigationCard` |
| acessos recentes, quando habilitados | `createDashboardRecentAccessStrip` |
| hero/cabeçalho da página | `createDashboardPageHero` |
| loading/empty genéricos | `LoadingState` / `EmptyState` |

`SectionRouteCard` e `NavigationCard` recebem conteúdo de domínio do Portal; o kit controla chrome, foco e acessibilidade.

**DO NOT RECREATE:** TopBar, underline/nav chrome, launcher-card chrome, recent-access chrome, loading/empty genéricos. Para a deep route de usuário, também não recriar o `PortalUserProfilePage` do `@delpi/plugin-ui`.

## Modelo de permissions

O Portal usa somente:

```text
controllership-finance.access
controllership-finance.manage
```

Não criar permission por página, botão, endpoint, CRUD, filial, unidade, indicador ou funcionalidade interna.

`ACCESS` autoriza o uso normal do Portal.

`MANAGE` autoriza administração/configuração. Não deve ser usado para fragmentar a navegação operacional.

## Unit scope / filial

Para este Portal:

```text
BRANCH_PERMISSION_CODES = NO
UNIT_SCOPE_PERMISSION_MODEL = NOT_APPLICABLE
```

Filial/unidade pode existir como dimensão de dados, filtro ou contexto do processo quando a fonte exigir, mas não como permission code dedicado do Portal.

AuthZ continua server-side e fail-closed.


## Página do usuário — deep route transversal

A página de usuário não altera a topbar canônica.

Rota TARGET:

```text
/apps/controllership-finance/users/{userId}
```

Fonte detalhada:
- [31-pagina-do-usuario.md](./31-pagina-do-usuario.md)

Política congelada:
- viewer com `controllership-finance.access` pode consultar o perfil corporativo básico de outro usuário com acesso ao mesmo Portal;
- perfil de outro usuário não expõe permissions/capabilities;
- no próprio perfil, labels + códigos técnicos `controllership-finance.access/manage` podem ser exibidos;
- identidade/foto pertencem ao Core;
- a rota não cria permission nova.

A identidade/avatar da topbar pode navegar para o perfil self somente quando a sessão possui ACCESS. Uma sessão apenas MANAGE não recebe ACCESS implicitamente; o avatar pode continuar apontando ao Meu Perfil global da Minha DELPI.

Atalhos dentro do perfil devem refletir **runtime implementado + autorização do viewer**, nunca roadmap futuro isoladamente.

## Papel do Início

`Início` é a Home/root do produto e funciona como launcher operacional.

Contrato completo:
- [32-inicio-home.md](./32-inicio-home.md)

O padrão visual é comum aos Portais:

```text
TopBar comum
→ Hero/saudação
→ Eventos e interações
→ Caminhos e funcionalidades
→ Últimos acessos
→ cards/seções do Portal
```

A Central de Fechamento permanece a primeira funcionalidade e agrupa P1–P5, mas a Home não duplica o Cockpit.

P1–P5 continuam fora da topbar principal e entram como rotas do launcher somente quando estiverem implementadas no runtime e autorizadas ao viewer.

Favoritos, busca e recentes seguem o contrato de [32-inicio-home.md](./32-inicio-home.md).

Estados dinâmicos degradam de forma independente: erro de tasks/blockers/favoritos não deve inutilizar o catálogo de rotas autorizado.

## Central de Fechamento

A Central de Fechamento é a primeira funcionalidade do Portal, não uma entrada adicional da topbar.

Ela agrupa:

| Página interna | Documento |
|---|---|
| Cockpit da Competência | [08-p1-cockpit-da-competencia.md](./08-p1-cockpit-da-competencia.md) |
| Checklist e Documentos | [09-p2-checklist-e-documentos.md](./09-p2-checklist-e-documentos.md) |
| Estoque e Conciliação | [10-p3-estoque-cutoff-e-conciliacao.md](./10-p3-estoque-cutoff-e-conciliacao.md) |
| Classificações e Pendências | [11-p4-classificacoes-e-pendencias.md](./11-p4-classificacoes-e-pendencias.md) |
| Pacote e Envio | [12-p5-pacote-finalizacao-e-envio.md](./12-p5-pacote-finalizacao-e-envio.md) |

Administração permanece transversal ao Portal e é documentada em [28-administracao.md](./28-administracao.md).

## Critério de aceite documental

```text
TOPBAR = [Início, Visão geral, Sala de interação, Minhas tarefas, Administração, Ajuda]
```

e:

```text
P1–P5 ∈ Central de Fechamento
P1–P5 ∉ topbar principal
```
