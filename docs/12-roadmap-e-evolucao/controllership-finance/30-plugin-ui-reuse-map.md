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
| Início | `createDashboardTopBar`, `createDashboardSectionRouteCard`, `createDashboardNavigationCard`, `createDashboardRecentAccessStrip`, `createDashboardPageHero` | `@delpi/plugin-ui/index` | composição reutilizável |
| Visão geral | `KpiCard`, `MetricKpiCard`, `ChartCard`, `QuickPeriodSelector`, `createDashboardFiltersKit`, charts, `DataTableSection` | `@delpi/plugin-ui/index` | kit analítico reutilizável |
| Sala de interação | `InteractionRoomPage`, `INTERACTION_ROOM_PAGE_LABELS_PT`, `PluginErrorBoundary` | `@delpi/plugin-ui/index` | **full-page reusable** |
| Minhas tarefas | `TaskWorkspacePage`, `TaskWorklistSection`, `TaskItemsTable`, `TaskSearchField`, `TaskEmptyState` | `@delpi/plugin-ui/index` | **workspace reusable** |
| Administração | PageHero/PagePath, SectionRouteCard, DataTableSection, forms, Modal/Confirm/Notice/Status | `@delpi/plugin-ui/index` | composição reutilizável; sem full page pronta |
| Ajuda | `createDashboardUserManual`, PageHero/PagePath/SectionCard, help primitives | `@delpi/plugin-ui/index` | **manual kit reusable** |

## Início

### Import preferencial

```ts
import {
  createDashboardTopBar,
  createDashboardSectionRouteCard,
  createDashboardNavigationCard,
  createDashboardRecentAccessStrip,
  createDashboardPageHero,
} from "@delpi/plugin-ui/index";
```

O Portal fornece labels, rotas, badges e conteúdo de domínio.

## Visão geral

### Import preferencial

```ts
import {
  KpiCard,
  MetricKpiCard,
  ChartCard,
  QuickPeriodSelector,
  createDashboardFiltersKit,
  LineSeriesChart,
  AreaSeriesChart,
  BarSeriesChart,
  ComparativeAreaChart,
  DataTableSection,
} from "@delpi/plugin-ui/index";
```

O contract do indicador decide o componente adequado. Disponibilidade de chart no kit não cria KPI nem regra.

## Sala de interação

### Full-page canônica

```ts
import {
  InteractionRoomPage,
  INTERACTION_ROOM_PAGE_LABELS_PT,
  PluginErrorBoundary,
} from "@delpi/plugin-ui/index";
```

Usar `InteractionRoomPage` antes de compor primitives manualmente.

Primitives de colaboração estão disponíveis no mesmo index para extensões comprovadas: `RoomInboxPanel`, `RoomHeader`, `RoomContextPanel`, `RoomConversationShell`, `MessageThread`, `MentionComposer`, `ReactionBar` e correlatos.

Persistência, AuthZ, realtime adapters e business context continuam responsabilidade dos owners/Portal.

## Minhas tarefas

### Workspace canônico

```ts
import {
  TaskWorkspacePage,
  TaskWorklistSection,
  TaskItemsTable,
  TaskSearchField,
  TaskEmptyState,
  TaskEditorFrame,
  buildTaskWorkspaceHighlights,
} from "@delpi/plugin-ui/index";
```

O Portal fornece projeções e actions ligadas aos casos de uso owners; o kit não é owner do workflow.

## Administração

Não existe `AdministrationPage` full-page pública no kit.

Compor a página a partir de:

```ts
import {
  createDashboardPageHero,
  createDashboardPagePath,
  createDashboardSectionRouteCard,
  DataTableSection,
  createDashboardFiltersKit,
  FormGrid,
  FormActions,
  NativeTextField,
  NativeSelectField,
  NativeTextAreaField,
  ModalShell,
  ConfirmModalPanel,
  FloatingNoticeStack,
  StatusBadge,
} from "@delpi/plugin-ui/index";
```

Não criar um novo design-system administrativo dentro do Portal.

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
} from "@delpi/plugin-ui/index";
```

O conteúdo em PT-BR permanece no plugin consumidor.

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
