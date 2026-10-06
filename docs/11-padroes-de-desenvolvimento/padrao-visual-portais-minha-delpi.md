# Padrão Visual dos Portais Minha DELPI

> **Status:** padrão transversal de referência — outubro/2026
>
> **Escopo:** microfrontends federados de Portais da Minha DELPI.
>
> Este documento consolida a linguagem visual comum comprovada no Portal Comercial e no `@delpi/plugin-ui`. Ele complementa, sem substituir, as instruções oficiais e as regras `.cursor` de frontend/design system.

## 1. Objetivo

Todo Portal deve parecer parte da mesma plataforma.

O domínio muda. O chrome, a navegação, as superfícies comuns, os estados de experiência, a responsividade, o tema e os componentes compartilhados não devem ser redesenhados a cada produto.

Princípio:

```text
HOST MINHA DELPI
→ PORTAL SHELL COMUM
→ PÁGINAS COMUNS
→ PÁGINAS DE DOMÍNIO
```

e:

```text
plugin-ui first
+ thin portal adapters
+ domain composition
= portal consistente
```

## 2. Autoridade e evidência

Aplicar em conjunto com:

- `docs/11-padroes-de-desenvolvimento/instrucoes-oficiais-gpt-arquiteto-delpi-central.md`;
- `.cursor/rules/platform-frontend-mfe-experience.mdc`;
- `.cursor/rules/plugins-reusable-components.mdc`;
- `.cursor/rules/plugins-visual-design-system.mdc`;
- `plugins/plugin-ui/docs/component-catalog.md`;
- `plugins/plugin-ui/docs/module-federation.md`;
- implementação atual de `plugins/commercial` como referência de composição madura.

Classificação da evidência usada nesta consolidação:

| Evidência | Classificação | Uso |
|---|---|---|
| screenshots do Portal Comercial em claro/escuro | OBSERVED | confirmar comportamento e paridade visual |
| `plugins/commercial/src/app/PluginShell.tsx` | PROVEN | shell/topbar/search/favoritos/perfil |
| `plugins/commercial/src/app/commercialUi.ts` | PROVEN | adapters finos sobre plugin-ui |
| Home/Overview/MyDay/Interaction/Admin/Help/UserProfile do Comercial | PROVEN | famílias visuais comuns |
| `plugins/plugin-ui/src/styles/**` | PROVEN | chrome, responsividade e temas compartilhados |
| docs/rules do plugin-ui | PROVEN | contrato de consumo e proibição de CSS duplicado |

Screenshot não substitui código. Código não autoriza copiar regras de negócio do Comercial.

## 3. Três camadas visuais

### 3.1 Host Minha DELPI

O host é responsável por identidade global, shell global da plataforma, tema e montagem do MFE.

O Portal não recria:

- sidebar global do host;
- seletor global de tema;
- autenticação;
- perfil global `/profile`;
- catálogo global de apps.

### 3.2 Shell comum do Portal

Todo Portal possui um shell próprio, visualmente alinhado ao padrão da plataforma.

Responsabilidades:

- TopBar;
- navegação principal;
- Buscar;
- Favoritos;
- identidade/avatar do usuário;
- Command Palette;
- badges de navegação quando suportados;
- Page transitions;
- root visual e tokens do MFE.

### 3.3 Páginas de domínio

Páginas específicas do produto compõem componentes do kit sobre contratos de domínio.

Elas podem variar em conteúdo e fluxo, mas devem escolher uma família visual canônica deste documento antes de criar layout novo.

## 4. Root e integração federada

Todo MFE novo usa root escopado:

```text
.dashboard-{portal-id}
```

e container externo:

```text
dashboard-{portal-id} dashboard-page
```

Import de runtime federado:

```ts
import { ... } from "@delpi/plugin-ui/index";
```

O bootstrap deve seguir `plugins/plugin-ui/docs/module-federation.md`, incluindo `preparePluginUiRemote()` antes de carregar o App. O CSS compartilhado é carregado pelo remote (`@delpi/plugin-ui/styles`).

Não usar bare import `@delpi/plugin-ui` em build federado novo.

## 5. Adapter visual do Portal

Cada Portal deve possuir um adapter fino equivalente ao padrão comprovado em `plugins/commercial/src/app/commercialUi.ts`.

Exemplo conceitual:

```text
{Portal}Ui
├── UI_PREFIX
├── PORTAL_SCOPE
├── TopBar
├── PageHero
├── PagePath
├── SectionCard
├── StatusBadge
├── Filters
├── Tables
├── Feedback
└── domain-neutral labels
```

O adapter:

- configura `prefix`, labels e scope;
- mapeia tokens;
- pode escolher densidade padrão;
- não reimplementa componente;
- não copia CSS interno do kit;
- não contém regra de negócio.

## 6. TopBar obrigatória

A TopBar é a navegação primária do Portal.

Estrutura:

```text
┌────────────────────────────────────────────────────────────────────┐
│ navegação principal              Buscar | Favoritos | avatar/nome │
└────────────────────────────────────────────────────────────────────┘
```

### 6.1 Lado esquerdo

Os Portais devem manter, quando a capability existir, esta ordem conceitual:

```text
Início
Visão geral
Sala de interação
Minhas tarefas
[itens de domínio realmente top-level]
Administração
Ajuda
```

Não promover toda página de domínio para a TopBar.

### 6.2 Lado direito

Obrigatório no padrão de Portal:

- **Buscar** com Command Palette e atalho Ctrl/Cmd+K;
- **Favoritos**;
- **identidade do usuário** com avatar e nome.

Exports/factories canônicos incluem:

```text
createDashboardTopBar
createDashboardTopBarSearchTrigger
createDashboardTopBarFavoritesStrip
createDashboardTopBarUtilityCluster
createDashboardTopBarUserIdentity
createDashboardCommandPalette
```

### 6.3 Comportamento

- item ativo usa underline/accent canônico;
- badges de contagem são permitidos quando representam dado real;
- TopBar pode ser sticky;
- em viewport estreita, labels de Buscar/Favoritos/nome podem ficar visually-hidden, preservando ícones/avatar e accessible name;
- alvos touch permanecem adequados;
- keyboard/focus visível obrigatório.

## 7. Página de usuário obrigatória

Todo Portal deve possuir página de usuário do Portal.

Rota conceitual:

```text
/apps/{portal-id}/users/{userId}
```

O avatar na TopBar deve permitir acessar o perfil do Portal.

Componente canônico:

```text
createDashboardPortalUserProfilePage
```

Hierarquia:

```text
PagePath
→ PageHero
→ Identidade | Atalhos
→ seções de domínio do Portal
→ acesso/capabilities quando aplicável
```

Regras:

- identidade básica é read-only no Portal;
- edição de foto/cargo/contatos aponta para o perfil global da Minha DELPI (`/profile`);
- o Portal pode adicionar grupos, equipes, carteiras, responsabilidades ou acessos próprios;
- não duplicar editor de perfil global;
- a página usa a mesma TopBar e tema do Portal.

## 8. Páginas comuns entre Portais

As páginas abaixo pertencem à mesma família visual em todos os Portais. O conteúdo muda; a estrutura visual e os componentes-base não.

### 8.1 Início

Referência comprovada: `plugins/commercial/src/features/home/HomePage.tsx` + Hero do `PluginShell`.

Gramática:

```text
TopBar
→ PageHero de entrada
→ Eventos e interações
→ Busca de caminhos/funcionalidades
→ Últimos acessos
→ cards de seções/rotas
```

Componentes preferenciais:

- `createDashboardPageHero`;
- `createDashboardEventsSection`;
- `createDashboardCatalogSearchBar`;
- `createDashboardRecentAccessStrip`;
- `createDashboardSectionRouteCard`;
- `createDashboardNavigationCard`;
- `createDashboardWorklistItem`;
- `createDashboardScopeChipBar`.

O Início é launcher e orientação. Não deve duplicar uma página analítica inteira.

### 8.2 Visão geral

Referência comprovada: `plugins/commercial/src/features/overview/OverviewPage.tsx`.

Gramática:

```text
TopBar
→ PageHero compacto
   → título/descrição/refresh
   → período rápido
   → FilterBar
→ seção de KPIs
→ gráficos
→ tabelas/drilldowns quando aplicável
```

Componentes:

- `createDashboardPageHero`;
- `createDashboardQuickPeriodSelector`;
- `createDashboardFiltersKit` / `FilterBarShell`;
- `createDashboardKpiCard` / `MetricKpiCard`;
- `SectionCard` / `ChartCard`;
- charts compartilhados;
- `DataTableSection` quando houver drilldown tabular.

Filtros dentro do Hero seguem regra de **uma moldura**: FilterBar tem chrome; FiltersRow interno fica flush.

### 8.3 Minhas tarefas

Referência comprovada: `plugins/commercial/src/features/my-day/MyDayPage.tsx`.

Família canônica:

```text
TaskWorkspacePage
├── PageHero
│   ├── status/badge
│   ├── 3 highlights operacionais
│   └── chips de escopo/fila
├── Worklist
│   ├── ações
│   ├── busca
│   └── itens/empty
└── Editor quando aplicável
```

Componentes:

- `TaskWorkspacePage`;
- `TaskWorklistSection`;
- `TaskItemsTable`;
- `TaskSearchField`;
- `TaskEmptyState`;
- `TaskEditorFrame`;
- `StatusBadge`;
- `ScopeChipBar`.

O kit é owner do chrome. Cada Portal é owner das tarefas/projeções, callbacks e AuthZ.

### 8.4 Sala de interação

Referência comprovada: `InteractionRoomWorkspace` do Comercial + collaboration family do plugin-ui.

Estados:

```text
desktop sem seleção → inbox
desktop com sala     → inbox | thread em ResizableColumns
mobile               → inbox OU thread
```

Gramática de inbox:

```text
busca
→ filtros/chips
→ lista de salas
→ estado selecionado
```

Componentes preferenciais:

- `InteractionRoomPage` e primitives da família collaboration;
- `ResizableColumns`;
- `RoomInboxPanel` / `RoomInboxList`;
- `RoomConversationShell`;
- `MessageThread`;
- `MentionComposer`;
- `StateBanner` para falha de realtime/conexão.

A Sala pode usar layout fill-viewport. No mobile, não manter split comprimido.

### 8.5 Ajuda

Referência comprovada: `plugins/commercial/src/features/help/UserManualPage.tsx`.

Gramática:

```text
PagePath
→ PageHero
→ nota de escopo
→ layout TOC + conteúdo
   ├── conceitos
   ├── Quero... → vá em...
   ├── FAQ
   └── glossário
```

Componente canônico:

```text
createDashboardUserManual
```

Família:

`Frame`, `Scope`, `Layout`, `Section`, `Concepts`, `GuideTable`, `Faq`, `Glossary`, `Eyebrow`.

Help é sincronizada com feature user-facing.

### 8.6 Administração

Administração tem conteúdo por domínio, mas gramática comum:

```text
PagePath
→ UnderlineNav de subseções
→ PageHero compacto
→ KPIs/resumo quando útil
→ SectionCards
→ ações rápidas / listas / formulários
```

Referência comprovada: `AdministrationHomePage` do Comercial.

Não criar uma permission por aba administrativa. O backend continua authority.

## 9. Famílias visuais para páginas de domínio

Antes de desenhar página nova, escolher uma família.

### 9.1 Lista / bancada de dados

Referência: Pedidos em aberto do Comercial.

```text
PageHero compacto
├── freshness + Atualizar
├── highlights
├── chips de foco
└── FilterBar
→ DataTableSection
   ├── view toggle quando necessário
   ├── export quando autorizado
   ├── font/columns quando aplicável
   └── DataTable
→ paginação
```

Usar para filas, cadastros operacionais, listagens e consultas.

### 9.2 Master-detail

```text
PageHero/Context
→ filtros
→ ResizableColumns
   ├── lista
   └── detalhe
```

No mobile: lista → detalhe full-width.

Usar quando seleção contínua entre registros é parte central do trabalho.

### 9.3 Analítica / indicadores

```text
PageHero + período/filtros
→ KPI grid
→ ChartCards
→ drilldowns/tabelas
```

Não escolher gráfico pela disponibilidade do componente; o contrato do indicador decide a representação.

### 9.4 Cockpit / processo

```text
contexto
→ blockers
→ estados/eixos
→ pendências
→ histórico
```

Usar quando a página precisa responder situação, bloqueios e navegação para owners.

### 9.5 Administração / catálogo

```text
PagePath
→ UnderlineNav
→ PageHero
→ resumo
→ DataTable/Forms
→ Modal/Confirm para writes
→ audit/history
```

## 10. PageHero

`PageHero` é o cabeçalho visual padrão.

Possui:

- eyebrow;
- título;
- descrição;
- badge;
- ações;
- highlights;
- body para filtros/chips.

### Densidade

**Compact** é o default recomendado para páginas operacionais, listas, overview e administração.

**Comfortable** pode ser usado deliberadamente em landing/entrada com forte papel editorial.

Não criar segundo hero local.

## 11. PagePath e navegação secundária

`PagePath` é padrão em páginas profundas, detalhes e administração.

`UnderlineNav` é padrão para subseções irmãs.

Não usar breadcrumb pesado no Início quando não há hierarquia profunda.

Subnav deve permanecer horizontal/scrollável ou responsiva conforme kit, sem tabs locais redesenhadas.

## 12. SectionCard e superfícies

`SectionCard` é a moldura padrão de blocos de conteúdo.

Use para:

- painéis;
- grupos de ações;
- gráficos;
- tabelas;
- histórico;
- conteúdo de ajuda.

Evitar card dentro de card sem razão semântica.

## 13. KPIs e métricas

Preferir:

- `MetricKpiCard` para métrica simples;
- `KpiCard`/`createDashboardKpiCard` para meta, score e contexto mais rico;
- `MetricStrip` para resumo compacto dentro de outra superfície.

Regras:

- card não calcula regra de negócio;
- unidade/período/contexto explícitos;
- erro/indisponível não vira zero;
- loading inicial e refreshing são estados diferentes;
- KPI clicável precisa de foco/keyboard e drilldown real.

## 14. Filtros

Filtros seguem o kit.

Regra de borda:

```text
FiltersRow sozinho        → chrome próprio
FiltersRow em FilterBar   → só FilterBar
FilterBar em PageHero     → FilterBar mantém a única moldura
```

Não empilhar molduras.

Filtros relevantes devem ser shareable por URL quando a jornada exigir F5/deep link.

## 15. Tabelas

Usar `DataTable` / `DataTableSection`.

Características do padrão:

- header semântico;
- ordenação acessível;
- hover/focus;
- seleção/expansão quando suportada;
- dark mode pelo kit;
- estados danger/warning via tone;
- coluna configurável/export/font size apenas quando a jornada justificar;
- mobile: cards ou scroll horizontal intencional; nunca corte silencioso.

Não recriar tabela com CSS local.

## 16. Estados de experiência

Toda página considera:

```text
INITIAL / LOADING
REFRESHING
SUCCESS
EMPTY
PARTIAL
UNAVAILABLE_SOURCE
VALIDATION_ERROR
ERROR
FORBIDDEN
NOT_FOUND
```

Princípios:

- initial loading não mostra dados inventados;
- refreshing mantém conteúdo anterior quando seguro;
- partial mantém dado confiável e expõe o que falhou;
- indisponível != zero;
- empty só após consulta bem-sucedida;
- 403 não vaza conteúdo;
- erro oferece recovery quando possível.

Componentes preferenciais:

`LoadingActivityCard`, `LoadingState`, `EmptyState`, `SoftEmptyState`, `StateBox`, `StateBanner`, `FloatingNoticeStack`, `PluginErrorBoundary`.

## 17. Light e Dark

Claro e escuro são **o mesmo produto e a mesma árvore de componentes**.

```text
SAME DOM
+ SAME COMPONENTS
+ SAME INFORMATION HIERARCHY
+ THEME TOKENS
= LIGHT / DARK PARITY
```

### 17.1 Tokens

O root do Portal mapeia tokens do host para tokens locais e `--delpi-ui-*`.

Base:

```text
--primary
--secundary
--surface
--surface-2
--text
--text-muted
--border
--app-canvas
```

e mapeia para:

```text
--delpi-ui-accent
--delpi-ui-surface
--delpi-ui-surface-elevated
--delpi-ui-surface-soft
--delpi-ui-text
--delpi-ui-title
--delpi-ui-text-muted
--delpi-ui-border
```

Dark mode usa:

```text
:root[data-theme="dark"] .dashboard-{portal-id}
```

Nunca `prefers-color-scheme` como authority do MFE.

### 17.2 Observação dos temas

Light:

- canvas claro;
- superfícies brancas/soft;
- título/brand escuro ou accent;
- Hero com tint azul leve;
- bordas discretas;
- accent azul para ativo/CTA/link.

Dark:

- canvas e surfaces escuros;
- texto claro;
- accent azul preservado;
- Hero com gradiente azul/escuro mais intenso;
- bordas translúcidas;
- tabela e hover usam mistura de accent + surface.

Não hardcodear versões light/dark de componentes do kit.

## 18. Spacing, densidade e responsividade

Baseline observada/comprovada no Comercial, sem substituir defaults do kit:

| Elemento | Desktop | Mobile |
|---|---|---|
| page padding | `clamp(16px, 2vw, 28px)` | ~12–16px |
| section gap | ~20–24px | ~12px |
| grid gap | ~16px | ~8–10px |
| control target | ≥44px | ≥44px |

Regras:

- `>1100px`: grids completos quando houver espaço;
- `≤1100px`: reduzir colunas;
- `≤900px`: highlights/charts/splits começam a empilhar conforme componente;
- `≤768px`: experiência mobile; toolbars/grids empilham;
- `≤720px`: labels utilitários da TopBar podem virar icon-only visualmente;
- `≤480px`: métricas/cards devem suportar uma coluna.

Breakpoints específicos de componente pertencem ao `plugin-ui` sempre que o kit controla o chrome.

## 19. Acessibilidade

Obrigatório:

- semântica HTML;
- headings corretos;
- labels/aria;
- teclado;
- foco visível;
- target touch;
- contraste;
- estado não dependente de cor;
- conteúdo essencial não depende de hover;
- dialog com focus management;
- reduced motion respeitado.

## 20. Ícones

Biblioteca canônica: `lucide-react`.

Referência:

- navegação: ~16px;
- botão/toolbar: ~16px;
- KPI: ~22px;
- ícone decorativo maior somente quando a composição justificar.

Não usar emoji como substituto de ícone de interface.

## 21. Favoritos, busca e recentes

Não confundir:

```text
Favoritos    = TopBar / persistência de favorito
Buscar       = Command Palette
Recentes     = Início / RecentAccessStrip
```

Favoritos não devem ser movidos para dentro de `RecentAccessStrip`.

## 22. CSS permitido no MFE

Permitido:

- tokens do Portal;
- mapping `--delpi-ui-*`;
- layout de página;
- grids/stacks entre componentes;
- CSS de visual específico de domínio que não existe no kit.

Proibido:

- `.delpi-ui-*` override;
- espelho BEM local de componente do kit;
- copiar CSS do Comercial;
- fix light/dark do kit dentro do Portal;
- `body`, `:root` global, `*` global;
- componente compartilhável novo sem inventário do kit.

Bug visual do componente compartilhado deve ser corrigido no `plugins/plugin-ui`.

## 23. Matriz de componentes comuns

| Necessidade | Componente/factory |
|---|---|
| TopBar | `createDashboardTopBar` |
| Buscar | `createDashboardTopBarSearchTrigger` + `createDashboardCommandPalette` |
| Favoritos | `createDashboardTopBarFavoritesStrip` |
| Usuário na TopBar | `createDashboardTopBarUserIdentity` |
| Perfil do Portal | `createDashboardPortalUserProfilePage` |
| Hero | `createDashboardPageHero` |
| Breadcrumb/path | `createDashboardPagePath` |
| Subnav | `createDashboardUnderlineNav` |
| Section | `createDashboardSectionCard` |
| Início/launcher | `createDashboardSectionRouteCard`, `createDashboardNavigationCard` |
| Busca de features | `createDashboardCatalogSearchBar` |
| Recentes | `createDashboardRecentAccessStrip` |
| Eventos | `createDashboardEventsSection` |
| Tasks | `TaskWorkspacePage` family |
| Interaction | `InteractionRoomPage` + collaboration family |
| Help | `createDashboardUserManual` |
| KPI | `MetricKpiCard`, `createDashboardKpiCard` |
| Filtros | `createDashboardFiltersKit`, `FilterBarShell` |
| Tabela | `DataTable`, `DataTableSection` |
| Master-detail | `ResizableColumns` |
| Status | `StatusBadge` |
| Loading | `LoadingActivityCard`, `LoadingState` |
| Empty | `EmptyState`, `SoftEmptyState` |
| Partial/error | `StateBanner`, `StateBox` |
| Modal/confirm | `ModalShell`, `ConfirmModalPanel` |

## 24. Padrão de página — decisão rápida

```text
É página comum?
├─ Início           → Home family
├─ Visão geral      → Overview family
├─ Minhas tarefas   → TaskWorkspace family
├─ Sala interação   → Interaction family
├─ Ajuda            → UserManual family
├─ Usuário          → PortalUserProfile family
└─ Administração    → Admin grammar

É página de domínio?
├─ muita linha/filtro      → data-list family
├─ lista + detalhe         → master-detail family
├─ KPIs/gráficos           → analytics family
├─ status/blockers/process → cockpit family
└─ configuração            → admin/catalog family
```

## 25. Definition of Done visual

Um slice frontend só fecha com evidência de:

```text
VISUAL_FAMILY
PLUGIN_UI_COMPONENTS_REUSED
LOCAL_UI_CREATED
WHY_LOCAL_UI_WAS_NECESSARY
PLUGIN_UI_GAP_FOUND
LIGHT_THEME
DARK_THEME
DESKTOP
MOBILE
KEYBOARD_FOCUS
LOADING_EMPTY_ERROR_PARTIAL_403_404
DEEP_LINK_F5 quando aplicável
BUILD_TESTS
FEDERATED_SMOKE quando material
HELP_SYNC
```

Se smoke federado não puder rodar: `INCONCLUSIVE`, nunca PASS inferido.

## 26. Anti-padrões

Reprovar:

- redesenhar Início/Overview/Tasks/Interaction/Help/Profile por Portal;
- omitir Buscar/Favoritos/identidade da TopBar sem decisão de plataforma;
- criar perfil local sem `PortalUserProfilePage`;
- criar Hero/KPI/Table/Filter/Modal já existentes no kit;
- duplicar CSS do kit;
- light e dark com layouts diferentes;
- dark mode testado só em standalone;
- ocultar ação/estado importante apenas por cor;
- modal como substituto de ficha completa quando deep link é a jornada correta;
- topbar saturada com todas as rotas internas;
- autorização baseada em visibilidade de UI.

## 27. Aplicação ao Portal Controladoria & Finanças

Os documentos já planejados do Portal Controladoria & Finanças devem ser revisitados contra este padrão antes da implementação frontend.

Classificação:

| Documento/página | Próxima revisão |
|---|---|
| Início | alinhar integralmente à Home family |
| Visão geral | alinhar integralmente à Overview family |
| Sala de interação | alinhar à Interaction family |
| Minhas tarefas | alinhar à TaskWorkspace family |
| Administração | alinhar à gramática Admin |
| Ajuda | alinhar à UserManual family |
| Página do usuário | **ADICIONAR** usando PortalUserProfilePage |
| P1 Cockpit | revisar shell/Hero/sections/states contra este padrão |
| P2 Checklist e Documentos | revisar master-detail/filters/states contra este padrão |
| P3 Estoque e Conciliação | revisar Hero/KPI/readiness/table contra este padrão |
| P4 Classificações e Pendências | definir após aplicar família worklist/master-detail |
| P5 Pacote e Envio | definir após aplicar família process/detail |

Essa revisão não reabre regras de negócio já congeladas. O objetivo é alinhar composição visual e reuso.

## 28. Regra final

```text
IDENTIFY PAGE FAMILY
→ INVENTORY PLUGIN-UI
→ COMPOSE SHARED CHROME
→ ADD DOMAIN CONTENT
→ MAP THEME TOKENS
→ VALIDATE LIGHT/DARK
→ VALIDATE DESKTOP/MOBILE
→ VALIDATE KEYBOARD/STATES
→ FEDERATED SMOKE
```

Não fazer:

```text
DESIGN FROM SCRATCH
→ COPY CSS FROM ANOTHER PORTAL
→ FIX DARK MODE AFTER
```
