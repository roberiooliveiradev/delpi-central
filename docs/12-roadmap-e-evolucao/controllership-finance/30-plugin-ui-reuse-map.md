# 30 — Mapa de Reuso do @delpi/plugin-ui

## Estado

**TARGET / IMPLEMENTATION AUTHORITY FOR UI REUSE**

## Princípio

O Portal Controladoria & Finanças segue `plugin-ui first`.

Antes de criar componente reutilizável ou chrome local, verificar o catálogo público em:

```text
plugins/plugin-ui/src/index.ts
plugins/plugin-ui/docs/component-catalog.md
```

Runtime de MFE federado:

```ts
import { ... } from "@delpi/plugin-ui/index";
await import("@delpi/plugin-ui/styles");
```

Não usar o bare import `@delpi/plugin-ui` em build federado novo; o remote canônico expõe `./index`.

## Bootstrap / Module Federation

O MFE deve usar o padrão vigente da plataforma:

```ts
import { pluginUiRemote, FEDERATION_SHARED_REACT } from "../vite/federation.shared";
```

e preparar o remote conforme o bootstrap canônico antes de carregar o App.

Não bundlar/copy local do `plugin-ui` como implementação nova.

## Matriz por página

| Página | Reuso principal | Import runtime | Natureza |
|---|---|---|---|
| Início | `createDashboardPageHero`, `createDashboardEventsSection`, `createDashboardCatalogSearchBar`, `createDashboardRecentAccessStrip`, `createDashboardSectionRouteCard`, TopBar/Search/Favorites factories | `@delpi/plugin-ui/index` | **Home family comum** |
| Visão geral | `KpiCard`, `MetricKpiCard`, `ChartCard`, `QuickPeriodSelector`, `createDashboardFiltersKit`, charts, `DataTableSection` | `@delpi/plugin-ui/index` | kit analítico reutilizável |
| Central de Fechamento / Cockpit | PagePath/PageHero/SectionCard, `StatusBadge`, `ProgressTracker`, `MetricStrip`, `AlertQueue`, `WorklistItem`, `Timeline` | `@delpi/plugin-ui/index` | composição de cockpit reutilizável |
| Central de Fechamento / Checklist e Documentos | `ResizableColumns`, `DataTableSection`, `DataRecordCard`, attachment kit, forms, `Timeline`, modals/notices | `@delpi/plugin-ui/index` | master-detail operacional reutilizável |
| Central de Fechamento / Estoque e Conciliação | `MetricKpiCard`, `ProgressTracker`, `AlertQueue`, `DetailFieldGrid`, `DataTableSection`, `Timeline`, state/confirm feedback | `@delpi/plugin-ui/index` | mesa de conciliação/readiness reutilizável |
| Central de Fechamento / Classificações e Pendências | `ResizableColumns`, `DataTableSection`, `DataRecordCard`, filters, `DetailFieldGrid`, forms, `Timeline`, state/confirm feedback | `@delpi/plugin-ui/index` | master-detail operacional com decisão humana |
| Sala de interação | `InteractionRoomPage`, `INTERACTION_ROOM_PAGE_LABELS_PT`, `PluginErrorBoundary` | `@delpi/plugin-ui/index` | **full-page reusable** |
| Minhas tarefas | `TaskWorkspacePage`, `TaskWorklistSection`, `TaskItemsTable`, `TaskSearchField`, `TaskEmptyState` | `@delpi/plugin-ui/index` | **workspace reusable** |
| Administração | PageHero/PagePath, SectionRouteCard, DataTableSection, forms, Modal/Confirm/Notice/Status | `@delpi/plugin-ui/index` | composição reutilizável; sem full page pronta |
| Ajuda | `createDashboardUserManual`, PageHero/PagePath/SectionCard, help primitives | `@delpi/plugin-ui/index` | **manual kit reusable** |
| Página do usuário | `createDashboardPortalUserProfilePage`, `portalUserProfileAccessBemClasses`, `StatusBadge`, state/loading primitives | `@delpi/plugin-ui/index` | **full-page reusable** |

## Início

### Família visual

```text
HOME FAMILY
= Hero
→ Eventos e interações
→ busca de caminhos
→ Últimos acessos
→ SectionRouteCards
```

### Import preferencial

```ts
import {
  formatPortalGreeting,
  createDashboardPageHero,
  createDashboardTitleWithHelp,
  createDashboardStatusBadge,
  createDashboardEventsSection,
  createDashboardScopeChipBar,
  createDashboardWorklistItem,
  createDashboardLoadingActivityCard,
  createDashboardCatalogSearchBar,
  createDashboardRecentAccessStrip,
  createDashboardSectionRouteCard,
  createDashboardNavigationCard,
  createDashboardCommandPalette,
  createDashboardTopBar,
  createDashboardTopBarSearchTrigger,
  createDashboardTopBarFavoritesStrip,
  createDashboardTopBarUtilityCluster,
  createDashboardTopBarUserIdentity,
  ActionButton,
  EmptyState,
  StateBanner,
} from "@delpi/plugin-ui/index";
```

Contrato detalhado:
- [32-inicio-home.md](./32-inicio-home.md)

O Portal fornece catálogo, conteúdo, dados operacionais e AuthZ. O kit owns chrome, foco, responsividade e tema.

**DO NOT RECREATE:** TopBar, Command Palette, PageHero, EventsSection, worklist item, CatalogSearchBar, RecentAccessStrip, SectionRouteCard, NavigationCard, FavoritesStrip ou generic state/loading/empty chrome.

## Visão geral

### Família analítica canônica

```text
PageHero compact
→ QuickPeriodSelector + Filters
→ KPI grid
→ ChartCards
→ DataTableSection drilldown
```

### Import preferencial

```ts
import {
  createDashboardPageHero,
  createDashboardSectionCard,
  KpiCard,
  createDashboardKpiCard,
  MetricKpiCard,
  ChartCard,
  QuickPeriodSelector,
  createDashboardQuickPeriodSelector,
  createDashboardFiltersKit,
  FilterBarShell,
  LineSeriesChart,
  AreaSeriesChart,
  BarSeriesChart,
  ComparativeAreaChart,
  MultiTypeSeriesChart,
  createDashboardChartToolbarKit,
  DataTableSection,
  EmptyState,
  StateBox,
  StateBanner,
  LoadingState,
  createDashboardLoadingActivityCard,
  ActionButton,
} from "@delpi/plugin-ui/index";
```

Contrato detalhado:
- [25-visao-geral-indicadores-financeiros.md](./25-visao-geral-indicadores-financeiros.md).

O tipo de KPI/chart depende do contrato do indicador. O Portal não cria visual porque um componente existe.

**DO NOT RECREATE:** PageHero, KPI card, ChartCard, period selector, filter chrome, chart toolbar, chart primitive, DataTableSection ou feedback genérico.

## Central de Fechamento — Cockpit da Competência

### Import preferencial

```ts
import {
  createDashboardPagePath,
  createDashboardPageHero,
  createDashboardSectionCard,
  StatusBadge,
  ProgressTracker,
  MetricStrip,
  AlertQueue,
  WorklistItem,
  Timeline,
  StateBanner,
  StateBox,
  EmptyState,
  LoadingState,
  HelpTooltip,
  ActionButton,
} from "@delpi/plugin-ui/index";
```

Contrato visual detalhado:
- [08-p1-cockpit-da-competencia.md](./08-p1-cockpit-da-competencia.md)

O Cockpit deve compor os três eixos independentes e navegar aos owners. O kit fornece chrome; P2/P3/P4/P5 continuam owners de suas regras.

## Central de Fechamento — Checklist e Documentos

### Import preferencial

```ts
import {
  createDashboardPagePath,
  createDashboardPageHero,
  createDashboardSectionCard,
  ResizableColumns,
  DataTableSection,
  DataRecordCard,
  createDashboardFiltersKit,
  StatusBadge,
  Timeline,
  StateBanner,
  StateBox,
  FileDropzone,
  AttachmentFileList,
  AttachmentPreviewStrip,
  SelectField,
  TextAreaField,
  ReadOnlyField,
  ModalShell,
  ConfirmModalPanel,
  FloatingNoticeStack,
  ActionButton,
  BackLink,
  HelpTooltip,
  EmptyState,
  LoadingState,
} from "@delpi/plugin-ui/index";
```

Contrato visual detalhado:
- [09-p2-checklist-e-documentos.md](./09-p2-checklist-e-documentos.md)

Desktop usa master-detail com `ResizableColumns`; mobile usa lista → detalhe full-width. Evidências usam o attachment kit público. O Portal continua owner dos contracts, estados, AuthZ e regras de validação.

## Central de Fechamento — Estoque e Conciliação

### Import preferencial

```ts
import {
  createDashboardPagePath,
  createDashboardPageHero,
  createDashboardSectionCard,
  MetricKpiCard,
  StatusBadge,
  ProgressTracker,
  AlertQueue,
  DetailFieldGrid,
  DataTableSection,
  Timeline,
  StateBanner,
  StateBox,
  ModalShell,
  ConfirmModalPanel,
  FloatingNoticeStack,
  ActionButton,
  HelpTooltip,
  EmptyState,
  LoadingState,
} from "@delpi/plugin-ui/index";
```

Contrato visual detalhado:
- [10-p3-estoque-cutoff-e-conciliacao.md](./10-p3-estoque-cutoff-e-conciliacao.md)

A divergência é a métrica monetária de maior destaque, mas o estado de readiness depende também de cutoff, revalidação e disponibilidade/freshness das sources. O kit fornece chrome; os contracts de source, regra e estado canônico continuam nos owners.

## Central de Fechamento — Classificações e Pendências

### Import preferencial

```ts
import {
  createDashboardPagePath,
  createDashboardPageHero,
  createDashboardSectionCard,
  ResizableColumns,
  DataTableSection,
  DataRecordCard,
  createDashboardFiltersKit,
  DetailFieldGrid,
  ReadOnlyField,
  SelectField,
  TextAreaField,
  StatusBadge,
  AlertQueue,
  Timeline,
  StateBanner,
  StateBox,
  ModalShell,
  ConfirmModalPanel,
  FloatingNoticeStack,
  ActionButton,
  BackLink,
  HelpTooltip,
  EmptyState,
  LoadingState,
} from "@delpi/plugin-ui/index";
```

Contrato visual detalhado:
- [11-p4-classificacoes-e-pendencias.md](./11-p4-classificacoes-e-pendencias.md)

Desktop usa master-detail com `ResizableColumns`; mobile usa lista → detalhe full-width. A fila usa `DataTableSection`/ `DataRecordCard`, o detalhe compõe primitives do kit e o histórico usa `Timeline`.

A sugestão de IA não ganha chrome de decisão concluída: deve permanecer dentro da composição existente (`SectionCard`/detail primitives), com confirmação humana separada quando autorizada.

**DO NOT RECREATE:** master-detail, fila responsiva, filtros, badges, state chrome, detail fields, formulários, modal/confirm, notices, timeline ou HelpTooltip.

P4 continua dono apenas do estado próprio do fechamento; regra upstream/CC, effective permissions e sources permanecem nos owners definidos pelos contracts.

## Sala de interação

### Full-page canônica

```ts
import {
  InteractionRoomPage,
  INTERACTION_ROOM_PAGE_LABELS_PT,
  RoomInboxPanel,
  RoomInboxList,
  RoomHeader,
  RoomContextPanel,
  RoomSidePanel,
  RoomMessageFindPanel,
  RoomSharedItemList,
  RoomConversationShell,
  MessageThread,
  MentionComposer,
  ReactionBar,
  ReactionQuickBar,
  ConversationFileDropLayer,
  ResizableColumns,
  StateBanner,
  EmptyGuidance,
} from "@delpi/plugin-ui/index";
```

Contrato detalhado:
- [26-sala-de-interacao.md](./26-sala-de-interacao.md)

Usar `InteractionRoomPage` como primeira opção. Primitives só entram para extensão comprovada do contrato.

**DO NOT RECREATE:** inbox, split, header, thread, composer, mention, reaction, shared panel, context panel, find-in-chat, attachment chrome ou CSS do kit.

O Portal fornece:
- rooms/messages;
- context mapping;
- callbacks;
- AuthZ;
- profile/mention adapters;
- attachment/realtime/notification adapters.

## Minhas tarefas

### Workspace canônico

```ts
import {
  TaskWorkspacePage,
  TaskWorklistSection,
  TaskItemsTable,
  TaskSearchField,
  TaskEmptyState,
  buildTaskWorkspaceHighlights,
  createDashboardPageHero,
  createDashboardScopeChipBar,
  StatusBadge,
  StateBanner,
  LoadingState,
  ActionButton,
} from "@delpi/plugin-ui/index";
```

Capability existente mas deliberadamente não usada na V1:

```ts
import {
  TaskEditorFrame,
} from "@delpi/plugin-ui/index";
```

Contrato detalhado:
- [27-minhas-tarefas.md](./27-minhas-tarefas.md)

A V1 é self-only e projeta trabalho de P2/P4/P5 conditional. A única action genérica é `Abrir`; owner pages executam o negócio.

`buildTaskWorkspaceHighlights` deve ser usado com due buckets desabilitados enquanto não houver SLA/due global.

**DO NOT RECREATE:** workspace, worklist, task table, search, empty, status chrome ou editor frame.

Se as colunas fixas de `TaskItemsTable` forem inadequadas para self-only/no-due, evoluir o `plugin-ui` em vez de criar tabela local.

## Administração

Não existe `AdministrationPage` full-page pública no kit.

### Composição canônica

```ts
import {
  createDashboardPageHero,
  createDashboardPagePath,
  createDashboardSectionRouteCard,
  createDashboardUnderlineNav,
  DataTableSection,
  createDashboardFiltersKit,
  FormGrid,
  FormActions,
  NativeTextField,
  NativeSelectField,
  NativeTextAreaField,
  EditableSectionCard,
  ReadOnlyField,
  ModalShell,
  ConfirmModalPanel,
  FloatingNoticeStack,
  StatusBadge,
  StateBanner,
  EmptyState,
  LoadingState,
  Timeline,
  ActionButton,
} from "@delpi/plugin-ui/index";
```

Contrato detalhado:
- [28-administracao.md](./28-administracao.md)

Arquitetura visual:

```text
PagePath
→ UnderlineNav: Painel | Templates | Catálogos | Histórico
→ PageHero
→ SectionRouteCard / DataTableSection / forms
→ Modal/Confirm/Notice/Status
```

O Portal owns template lifecycle, catalog registry, effective dating, audit e contracts. O kit owns o chrome.

**DO NOT RECREATE:** subnav, hero/path, route cards, DataTableSection, filter chrome, form fields, editable/read-only cards, modal/confirm, notices, badges, timeline ou generic states.

Não criar uma aba/permission/componente visual diferente para cada catálogo.

## Ajuda

### Manual canônico

```ts
import {
  createDashboardUserManual,
  createDashboardPageHero,
  createDashboardPagePath,
  createDashboardSectionCard,
  HelpTooltip,
  FieldLabel,
  SectionHintLabel,
  ActionButton,
  StateBanner,
  EmptyState,
} from "@delpi/plugin-ui/index";
```

Contrato detalhado:
- [29-ajuda.md](./29-ajuda.md)

`createDashboardUserManual` fornece:

```text
Frame
Eyebrow
Scope
Layout / TOC
Section
Concepts
GuideTable
Faq
Glossary
classNames
```

O Portal fornece:
- conteúdo PT-BR;
- section registry;
- feature/permission gating;
- tool-link registry;
- contextual deep links;
- glossary/FAQ;
- sync com features.

O conteúdo é versionado no MFE. Não criar BFF/DB/CMS de Help na V1.

**DO NOT RECREATE:** manual frame, TOC, concepts, guide table, FAQ, glossary, tool-link chrome ou HelpTooltip.

Help contextual longo navega para `/help#manual-{sectionId}`; hints curtos usam `HelpTooltip`.

## Página do usuário

### Full-page canônica

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

Usar `createDashboardPortalUserProfilePage` antes de compor `PagePath`, `PageHero`, avatar, identidade ou atalhos manualmente.

A full page já owns:

```text
PagePath
→ PageHero comfortable
→ badge Você
→ CTA self
→ Identidade | Atalhos
→ avatar/iniciais
→ slots de seções
→ responsive/a11y
```

O Controladoria fornece dados, copy, navegação, AuthZ e a seção self-only de acesso.

Contrato detalhado:
- [31-pagina-do-usuario.md](./31-pagina-do-usuario.md)

**DO NOT RECREATE:** shell da página, hero, identidade, avatar, grid Identidade|Atalhos, self badge, self CTA, access chrome ou CSS `.delpi-ui-portal-user-profile*`.

## Feedback e estados

Para estados comuns, preferir os exports públicos do kit, conforme necessidade:

```ts
import {
  LoadingState,
  EmptyState,
  StateBox,
  StateBanner,
  StatusBadge,
  PluginErrorBoundary,
} from "@delpi/plugin-ui/index";
```

## Regra de criação de componente novo

```text
NEED UI
→ search plugin-ui catalog
→ reuse exported component
→ compose existing primitives
→ only then consider new reusable component
```

Se surgir um componente realmente reutilizável e inexistente, preferir adicioná-lo ao `plugins/plugin-ui` seguindo o processo de contribuição do kit, em vez de duplicá-lo localmente.

## Do not recreate

- TopBar e navegação underline;
- cards KPI e chart chrome;
- task workspace/list/search;
- interaction-room shell/thread/composer;
- manual/TOC/FAQ/glossary chrome;
- DataTable/DataTableSection;
- modal/confirm/notice shells;
- loading/empty/status genéricos;
- forms já exportados.

## Validação de implementação

Cada slice frontend deve reportar:

```text
PLUGIN_UI_COMPONENTS_REUSED
LOCAL_UI_CREATED
WHY_LOCAL_UI_WAS_NECESSARY
PLUGIN_UI_GAP_FOUND
```

Se `LOCAL_UI_CREATED` duplicar um export já existente no kit, o slice deve ser `REWORK`.
