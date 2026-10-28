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
| Central de Fechamento / Pacote, Finalização e Envio | `ResizableColumns`, `DataTableSection`, `DataRecordCard`, `ProgressTracker`, `DetailFieldGrid`, `Timeline`, state/confirm feedback | `@delpi/plugin-ui/index` | master-detail por destinatário; submit/review in-portal |
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

### Reuso efetivo verificado — UX-013 (28/10/2026)

Campos do catálogo administrativo de documentos **foram migrados de
controles nativos para exports reais do kit**, boundados no adaptador
`cf` (`src/app/controllershipFinanceUi.ts`):

| Consumidor `cf` | Export real do kit | Uso |
|---|---|---|
| `CfTextField` | `createDashboardTextField` + `textFieldBemClasses` | nome, identificador técnico, R-ID TOTVS, chave/entregável/ordem/finalidade do item |
| `CfTextAreaField` | `createDashboardTextAreaField` + `textAreaFieldBemClasses` | descrição, orientações, notas, motivo de devolução |
| `CfSelectField` | `createDashboardSelectField` + `selectFieldPacClasses` | 6 selects de Exigência + selects do diálogo de item (listbox acessível, não-native) |
| `CfDateField` | `createDashboardDateField` + `dateFieldBemClasses` | competência `type="month"` (vigência, publicação) |
| `CfTimeline` | `createTimeline` | eventos de auditoria e histórico do documento com tons semânticos por tipo |
| `CfActionButton` | `ActionButton` | CTA `primary`, secundárias `ghost`, gatilhos destrutivos ghost + `cf-action-btn--danger` |
| `ConfirmModalPanel`, `CfDialog`, `CfEmptyState`, `CfStatusBadge`, `DataTableSection` | já boundados | preservados |

Sem lacuna de kit identificada: todos os controles necessários existem
como export real. Campos numéricos simples (ordem do item) usam
`CfTextField` + parse — `NumberStepperControl` existe mas não foi
necessário para um campo opcional de ordenação.

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

## Central de Fechamento — Pacote, Finalização e Envio

### Import preferencial

```ts
import {
  createDashboardPagePath,
  createDashboardPageHero,
  createDashboardSectionCard,
  ResizableColumns,
  DataTableSection,
  DataRecordCard,
  DetailFieldGrid,
  ReadOnlyField,
  ProgressTracker,
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
- [12-p5-pacote-finalizacao-e-envio.md](./12-p5-pacote-finalizacao-e-envio.md)

Desktop usa master-detail por recipient package; mobile usa lista → detalhe full-width. `ProgressTracker` pode explicar finalize → submit for review → review, sem colapsar estados.

**DO NOT RECREATE:** master-detail, recipient cards/table, lifecycle/status chrome, detail fields, timeline, modal/confirm, notices ou HelpTooltip.

Não criar delivery UI externo. `Enviar para análise` e review states usam primitives já públicas; se o reviewer workflow provar gap real, contribuir primeiro no `plugin-ui`.

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

A V1 é self-only e projeta trabalho de P2/P4 e obrigações P5 por área para cada usuário elegível, sem criar TaskEntity. A única action genérica é `Abrir`; owner pages executam o negócio.

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
  StateBox,
  EmptyState,
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

### Loading centralizado do Portal (padrão vigente)

O adaptador canônico de carregamento do Portal é `CfLoadingCard`
(`src/app/controllershipFinanceUi.ts`), bound de
`createDashboardLoadingActivityCard` com prefixo `cf` — `role="status"`,
`aria-live="polite"`, `role="progressbar"` e spinner/token de tema do kit
(claro/escuro, movimento reduzido vêm do CSS `delpi-ui-loading-activity*`).

Regras de uso:

- **Carga de seção/conteúdo**: `<CfLoadingCard title="…" variant="compact" />`
  dentro do `CfSectionCard`; `variant="panel"` para bloco de página inteira
  (ex.: `HomePage`).
- **Tabela**: o `DataTableSection` já renderiza `CfLoadingCard` internamente
  nos estados inicial/refresh — passar apenas `loading` e nunca criar
  indicador paralelo.
- **Região de resultados**: envolver em `aria-busy={loading}` —
  **o wrapper deve carregar `cf-page-stack`** (`<div className="cf-page-stack"
  aria-busy={loading}>`). Um `<div>` intermediário sem a classe vira um único
  filho do stack e as `CfSectionCard` internas empilham coladas (o `gap` do
  pai não desce); verificado em produção em 21/10/2026.
- **Erro**: `CfStateBanner` + ação `Tentar novamente`; loading/erro/vazio/
  parcial continuam estados distintos.

### Grid de cards centralizado (padrão vigente)

O adaptador canônico de cards de indicadores/resumos é `CfMetricStrip`
(`src/app/controllershipFinanceUi.ts`), bound de
`createDashboardMetricStrip` — grid responsivo do kit (quebra por largura,
gap consistente entre cards, `tabular-nums`, `word-break` para valores
longos, `role="group"` com `aria-label`) com prefixo de classe `cf`.

Regras de uso:

- Indicadores e resumos (por tipo, por armazém, por moeda) usam
  `<CfMetricStrip aria-label="…" items=[{label, value, description, tone}]>`;
  `tone` cobre `warning`/`danger` para estados de atenção/ausência.
- Páginas novas **não** devem criar `<ul className="cf-…-summary">` ou
  grid de cards próprio; reutilizar `CfMetricStrip`.
- Tokens legados `--delpi-*` consumidos pelo MetricStrip do kit são
  boundados aos tokens `--cf-*` do Portal em `index.css` (tema claro/escuro).

### Mensagens centralizadas ao usuário (padrão vigente)

O adaptador canônico de mensagens é `CfFeedbackMessage`
(`src/app/cfFeedbackUi.ts`), bound de `CfStateBanner` — recebe intenção
semântica `info | warning | error | success` e mapeia às variantes reais
do kit (error/success/default); `warning`/`info` distinguem-se por ícone
(`⚠`/`ℹ`) sem inventar `variant` inexistente.

`CfQueryErrorBanner` é o catálogo único de falhas de consulta das duas
páginas: mapeia `{status, code}` tipado do BFF para título/orientação/ação
— `scope_unavailable` → "Consulta ainda não habilitada", `S2S_*` →
"Integração de dados pendente", `401` → "Sessão expirada", `403` →
"Acesso restrito", `503`/rede → "Origem indisponível"/"Falha de
comunicação", genérico expõe `error.message` real — sempre com
"Tentar novamente" quando aplicável.

Regras de uso:

- Nenhuma mensagem de operação aparece como `<p>`/`<div>` de texto solto;
  usar `CfFeedbackMessage` (informativa/aviso/dados parciais) ou
  `CfQueryErrorBanner` (erro de consulta).
- Uma mensagem, um contexto: não duplicar o mesmo erro em banner + tabela.
- `CfLoadingCard` nunca é apresentado como erro; loading/erro/vazio/
  parcial/snapshot-ausente permanecem estados distintos.
- Snapshot ausente é estado informativo específico ("Snapshot não
  encontrado"), nunca saldo zero.

### Hero das páginas da Central de Fechamento (padrão vigente)

`ClosingHero` (`src/app/ClosingHero.tsx`, doc 50) é a composição canônica
de hero — adaptador fino sobre `CfPageHero` (`createDashboardPageHero`,
density compact): eyebrow "Central de Fechamento", título (com
`CfTitleWithHelp`), subtítulo, ações = "Atualizado em DD/MM/AAAA, HH:mm"
(timestamp real do fetch, sem botão — refresh é único), corpo = grid de
KPIs `CfMetricKpiCard` + nota `CfFeedbackMessage` + painel de filtros
(`cf-hero-filters`) + linha de ações com "Limpar filtros" (ghost) +
"Atualizar consulta" (primary, `disabled` durante a consulta). Páginas
novas de consulta da Central devem usar `ClosingHero` em vez de
`CfSectionCard` para filtros. Timestamp só com data real de conclusão
da consulta; "Atualizar consulta" repete a consulta vigente e nunca
submete/valida filtros.

KPIs do hero usam `CfMetricKpiCard` (`createMetricKpiCard` bound em
`controllershipFinanceUi.ts`) — tile oficial com `icon` (ReactNode,
lucide-react), `label`, `value` em `<strong>`, `hint` e `tone`
(`warning` para indisponibilidade/parcialidade). O grid `cf-hero-kpis`
(auto-fit minmax 190px) quebra por largura. `CfMetricStrip` permanece o
padrão das seções de resumo fora do hero; em R03 os dois painéis
(tipo/armazém) são agrupados por `cf-summary-panels` (grid auto-fit
minmax 420px — lado a lado só quando a largura comporta).

`CfFeedbackMessage` carrega `cf-feedback--<intent>`; `warning` recebe
borda/fundo amber via tokens `--delpi-warning*` (avisos persistentes
como "Dados parcialmente disponíveis"), `info` permanece discreto.

### Células de tabela da Central de Fechamento (padrão vigente)

Células com hierarquia em duas linhas usam `cf-cell-primary` (peso 600) +
`cf-cell-secondary` (12px mutada) — documento, códigos com descrição
(natureza, tipo de movimento) e fornecedor/cliente (nome + código/loja).
Valores monetários usam `cf-cell-amount` (600 + `tabular-nums`);
ausências usam `cf-cell-muted` ("Não identificada").

Classificações com valor real do contrato usam `CfStatusBadge`
(neutral/info/success/warning/danger): Direção exibe o rótulo do `side`
consultado + código cru `paymentDirection` (doc48 D4 — sem
reclassificação), Vínculo `resolved`→success / `missing_*`→warning, Tipo
de produto em badge neutro. Semântica inventada (cores por tipo de
produto, percentuais) continua proibida. `mobileLabel` rotula colunas
abreviadas no modo responsivo do kit.

Colunas de texto longo usam `className: "cf-table__col--wrap"` — o kit
resolve para `delpi-ui-table__col--wrap` (min 8rem / max 16rem + quebra
de palavra), evitando coluna gigante sem inventar larguras locais.
`__col--wide` (200–360px) e `__col--compact`/`--numeric`/`--status`
existem no kit para outros casos.

Painel de resultados: a contagem do `DataTableSection` (`recordsCount`)
fica em `cf-table-section__meta` — pill discreto ao lado do título.
Header e toolbar nativa dividem a MESMA linha via `display:flex;
flex-wrap` na `.cf-table-section` (toolbar quebra para baixo em telas
estreitas) — composição CSS escopada sobre o DOM do kit, sem fork nem
segunda toolbar. A seção de tabela não soma margem extra dentro de
`cf-page-stack`. Densidade via `--delpi-ui-table-cell-pad-y` no escopo.

Consulta automática de filtros (Central de Fechamento): as páginas derivam
os filtros vigentes dos campos — seletores/toggles/datas aplicam na hora,
campos digitáveis passam por `useDebouncedValue` (400ms, `src/utils/`).
Mudança de filtro volta para a página 1 via ajuste de estado em render-time
(fingerprint), e o efeito de fetch usa `AbortController` + sequência de
requisição — resposta antiga nunca sobrescreve a mais recente. Páginas novas
de consulta devem seguir o mesmo padrão em vez de reintroduzir botão
"Consultar".

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


## Complemento aprovado de reuso — Fechamento mensal, cadastro DRE e detalhe interativo (26/10/2026)

**Referência funcional:** [Plano 113](./113-plano-canonico-fluxo-fechamento-controladoria-dre-vigencia-documental.md), §9. Todas as superfícies abaixo referem-se somente ao **Fechamento Mensal**. Entradas indicadas são **candidatas de kit**; Devin deve inspecionar export e props reais antes de implementar. Proibido copiar `plugin-ui` ou criar chrome paralelo.

| Superfície | Componentes/factories a avaliar no plugin-ui | Notas obrigatórias |
|---|---|---|
| Início | `createDashboardPageHero`, `createDashboardEventsSection`, `createDashboardCatalogSearchBar`, `createDashboardRecentAccessStrip`, `createDashboardSectionRouteCard` | Uma entrada principal para Fechamento mensal e atalhos para abas |
| Fechamento / Visão geral | `createDashboardPagePath`, `QuickPeriodSelector`, `KpiCard`, `MetricKpiCard`, `ProgressTracker`, `AlertQueue`, `Timeline`, `StateBanner`, `ActionButton` | Contexto por YYYY-MM; ação Abrir se inexistente; fonte dos KPIs |
| Documentos e interações | **Implementado (CF-PROC0072-DOCUMENTS-UX-006):** `createDashboardSectionCard`(+`hint`), `createDashboardStatusBadge`, `ActionButton`, `EmptyState`, `FiltersRow`/`FilterInputField`/`FilterSelectField`, QueryErrorBanner | Cartões por exigência/adicional; pesquisa+filtro na URL; resumo de solicitações = decisões REJECTED reais |
| Detalhe documento / interação | **Implementado (CF-PROC0072-DOCUMENTS-UX-006):** `createDashboardPagePath` (breadcrumb 3 níveis), `createDashboardSectionCard`, `FilePreviewView`+`useFilePreviewLoader` (prévia por blob autenticado), `FileDropzone`, `ActionButton`, `EmptyState`, `StatusBadge`, `FilterInputField` | Deep route `documents/{ref}`; PDF esq./interações dir./histórico abaixo; conversa livre `PLANNED` |
| Relatórios/divergências | `MetricKpiCard`, `DataTableSection`, `DataRecordCard`, `AlertQueue`, `DetailFieldGrid`, `Timeline` | Drilldown, PDF container e proveniência; sem calcular no frontend |
| Admin — lista de documentos DRE | `createDashboardPageHero`, `createDashboardPagePath`, `DataTableSection`, `DataRecordCard`, `ActionButton`, `EmptyGuidance` | Manage; entrada para rotas de cadastro/edição |
| Admin — cadastro (página) | `createDashboardPagePath`, `BackLink`, `ActionButton`, `FieldLabel`, `HelpTooltip`, `createDashboardNativeFormFields` | Não modal; vigência inicial/final/exceção |
| Admin — edição (página) | mesmos do cadastro + `Timeline`, `StateBanner` | Não modal; histórico e impacto; finalizados intactos |
| DRE — documentos recebidos | `createDashboardPageHero`, `createDashboardPagePath`, `DataTableSection`, `DataRecordCard`, `EmptyGuidance`, `ActionButton`, `Timeline` | **Última fase**; somente PDFs liberados; sem TOTVS/divergências |
| Ajuda contextual | `createDashboardUserManual`, `HelpTooltip`, `FieldLabel` | Atualizar no mesmo gate da funcionalidade |

**Verificação inicial de código-fonte do kit:** `plugins/plugin-ui/src/index.ts` e `plugins/plugin-ui/docs/component-catalog.md` foram consultados na branch `main` em 26/10/2026. O catálogo documenta `PagePath` via `createDashboardPagePath`, `KpiCard`, `QuickPeriodSelector`, `DataTableSection`, `DataRecordCard`, `Timeline`, `ActionButton`, `BackLink`, `FieldLabel`, `HelpTooltip` e `createDashboardNativeFormFields`. Para `PagePath`, `ResizableColumns`, attachments e preview, identificar o símbolo/factory exato no export reexportado; nunca confiar somente no nome mencionado em documentação.

A página de configuração substitui o **modal de criação/edição** mediante gate e validação de substituição. O detalhe PDF é **uma página contextual** comum a duas audiências, não novo módulo nem aba. Seguir contratos de interação/auditoria, sem importar domínio de outro plugin.


## Registro de execução — Visão geral V0.2 do Fechamento mensal (CF-PROC0072-OVERVIEW-UX-004, 26/10/2026)

Componentes efetivamente reutilizados via `@delpi/plugin-ui/index` (verificados em `plugins/plugin-ui/src/index.ts` antes do uso):

| Superfície | Componente/factory | Alias CF |
|---|---|---|
| Caminho da página | `createDashboardPagePath` | `CfPagePath` (novo) |
| Cabeçalho | `createDashboardPageHero` | `CfPageHero` via `ClosingHero` |
| Abas | `createDashboardSegmentToggle` | `CfSegmentToggle` |
| Indicadores clicáveis | `createDashboardInteractiveDataCard` | `CfInteractiveDataCard` |
| Atenção + Atividade recente | `createDashboardEventsSection` (AlertQueue) | `CfEventsSection` |
| Cartões de eixo e rodapé | `createDashboardSectionCard` | `CfSectionCard` |
| Estado do fechamento | `createDashboardStatusBadge` | `CfStatusBadge` |
| Ações contextuais | `ActionButton` | `CfActionButton` |
| Estados vazios | `EmptyState` | `CfEmptyState` |
| Ajuda | `createDashboardTitleWithHelp` + `hint` de SectionCard/EventsSection | `CfTitleWithHelp` |

`KpiCard`/`MetricKpiCard`, `Timeline`, `QuickPeriodSelector` e `ProgressTracker` foram avaliados e **não adotados** nesta fatia: os indicadores exigem ativação contextual (scroll/aba), `Timeline` exigiria um feed de eventos completo que não existe, a seleção de mês já está implementada e percentuais arbitrários foram proibidos pelo brief. Nenhum chrome paralelo criado; somente classes de layout locais (`.cf-monthly-status`, `.cf-monthly-axes`, `.cf-monthly-outcomes`, `.cf-axis-facts`).


## Registro de execução — Visão geral V0.3 (CF-PROC0072-OVERVIEW-UX-REWORK-005, 26/10/2026)

Refinamento de copy sobre a composição V0.2 — **nenhum componente adicionado, removido ou duplicado**. O conjunto de factories continua exatamente o do registro V0.2 acima (`PagePath`, `PageHero`/`ClosingHero`, `SegmentToggle`, `InteractiveDataCard`, `EventsSection`, `SectionCard`, `StatusBadge`, `ActionButton`, `EmptyState`, `TitleWithHelp`, `StateBanner`). A expansão da lista de atenção (`Mostrar todas as N situações`) usa `CfActionButton` + estado local — sem wrapper nem estilo global novo.


## Registro de execução — Rework documentos (CF-PROC0072-DOCUMENTS-REWORK-007, 26/10/2026)

| Superfície | Componente do kit | Bound local |
|---|---|---|
| Menu três pontos do cartão | `ContextMenu`, `ContextMenuItem`, `ContextMenuDivider` (portal, role `menu`/`menuitem`, Escape, hint) | trigger `<button>` com `aria-label` + estado de posição |
| Confirmação de remoção (U7) | `ConfirmModalPanel` dentro de `CfDialog` | `cfConfirmModalClassNames` |
| Prévia autenticada | `FilePreviewView` + `useFilePreviewLoader` | `source` estabilizado por `useCallback` (causa raiz V0.2) |
| Validação P2 no detalhe | `ItemValidationPanel` (componente do plugin, já existente) | embed direto, `onChanged` → refresh |

Nenhum componente de menu/contexto ou confirmação paralelo criado; nenhum chrome copiado.


## Registro de execução — Conversa documental (CF-PROC0072-DOCUMENT-INTERACTIONS-008, 27/10/2026)

| Superfície | Componente do kit | Bound local |
|---|---|---|
| Thread de mensagens | createDashboardMessageThread(prefix) | CfMessageThread em controllershipFinanceUi.ts — itens com autor/data/mine, bodyMode markdown, emptyLabel honesto |
| Composer multiline | createDashboardMentionComposer(prefix) | CfMentionComposer — showAttach=false, submitOnEnter=false, labels PT completas, submitting/disabled |
| Cartões do detalhe | createDashboardSectionCard | CfSectionCard («Validação do documento», «Conversa sobre o documento», «Histórico») |
| Erro de envio/carga | CfFeedbackMessage (adapter existente) | reuse direto |

Mesmo padrão de Minhas Solicitações (CommentsPanel) — somente factories
do kit + adapter do MFE; nenhum componente de chat copiado, nenhum
import de domain/API de outro contexto.


## Registro de execução — Refinamento do detalhe (CF-PROC0072-DOCUMENT-DETAIL-UX-009, 26/10/2026)

| Superfície | Componente do kit | Bound local |
|---|---|---|
| Linha do tempo do histórico | `createTimeline({ prefix })` — mesmo componente cronológico da CIPA (`CipaTimeline`) | `CfTimeline` em controllershipFinanceUi.ts — itens com título PT, tom por evento, `v{n}`, data e `meta` do responsável |
| Avatar do participante | `UnifiedAvatar` (`kind="person"`, `imageUrl`, `fallbackText`) | `CfUnifiedAvatar` — marcador da timeline; thread usa `authorSrc`/`authorUserId` nativos do `MessageThread` (`InitialsAvatar` interno) |
| Perfil de participantes | `useParticipantProfiles` + `participantsApi.ts` (padrão `useParticipantAvatarUrls` de Minhas Solicitações) | lookup em lote `/closing/participants/lookup` (diretório Core, bearer do caller) + blob `/closing/participants/{id}/avatar` (S2S person-profile); `createObjectURL` revogado por ciclo/unmount |
| Altura da conversa | thread `flex: 1` + `fill` (rolagem interna do kit) | `.cf-document-conversation` `min-height: 520px` desktop; `≤760px` sem altura aprisionada (`60vh`) |

`EventsSection` inventariado e **não usado** — é fila de alertas
(AlertQueue), não timeline cronológica. Nenhuma lista/avatar/timeline
paralela criada.

## Registro de execução — Rework de segurança de participantes (CF-PROC0072-DOCUMENT-DETAIL-UX-009-RW01, 26/10/2026)

Correção de autorização — **nenhum componente novo foi criado**: a
composição visual aprovada da UX-009 permanece idêntica
(`CfTimeline`, `CfUnifiedAvatar`, `MessageThread` com `authorSrc`,
composer no rodapé, altura 520px). O diff é só de contrato e estado:

| Superfície | Antes (UX-009) | Depois (RW01) |
|---|---|---|
| Lookup de participantes | `POST /closing/participants/lookup` — ids livres | `POST /closing/competences/{period}/documents/{document_id}/participants/lookup` — somente ids com vínculo canônico |
| Avatar | `GET /closing/participants/{user_id}/avatar` | `GET …/documents/{document_id}/participants/{user_id}/avatar` — participante sem vínculo = 404 |
| Prova de participação | nenhuma (frontend mandava ids) | repository: autor U9 + ator U8 + uploader, dentro de `_document_in_scope` |
| Isolamento do hook | chave = ids | chave = `period + documentId + ids`; perfil de outro contexto nunca é exibido |

Rotas antigas removidas — sem endpoint residual de consulta livre.
Nenhuma nova lista/avatar/timeline paralela criada.

## Registro de execução — Relatórios e divergências V0.2 (CF-PROC0072-REPORTS-UX-010, 27/10/2026)

Aba `?tab=reports` do Fechamento mensal composta inteiramente sobre exports/factories reais do kit — nenhum componente paralelo criado:

| Superfície | Export/factory `@delpi/plugin-ui` | Consumo |
|---|---|---|
| Indicadores clicáveis e cartões de família | `InteractiveDataCard` via `CfInteractiveDataCard` (`createDashboardInteractiveDataCard`) | 3 indicadores com `openHint` + `onActivate` (foco na seção); 2 cartões de família com `ariaLabel`, fields e seleção visual (classe `cf-report-card--selected`, sem novo componente) |
| Seções da aba | `SectionCard` via `CfSectionCard` (`createDashboardSectionCard`) | título + `subtitle` visível + `hint` de ajuda contextual |
| Situação de fonte/cobertura | `StatusBadge` via `CfStatusBadge` | badges de atenção (danger/warning/info por categoria), `source_state` P3 e cobertura R01–R15 (labels/variantes reexportadas de `ReportsMatrixPanel`) |
| Totais e agrupamentos | `MetricStrip` via `CfMetricStrip` (`createDashboardMetricStrip`, itens `PageHeroHighlight`) | total histórico de estoque, resumo por tipo e por armazém |
| Linhas sob demanda | `DataTableSection` (`createDashboardDataTableSection`) | registros do agrupamento de baixas e itens do snapshot — paginação server-side nativa, `hideSearch`, colunas `key/header/render` |
| Estados vazios e erros | `EmptyState` (`CfEmptyState` + `cfEmptyStateClassNames`), `FeedbackMessage`/`QueryErrorBanner` (`cfFeedbackUi`) | «Selecione um relatório…», «Nenhuma divergência…», fonte indisponível/erro de consulta com «Tentar novamente» |
| Ações | `ActionButton` via `CfActionButton` | «Atualizar dados», «Ver detalhes» (expansão com `aria-expanded`/`aria-controls`), «Ver itens do snapshot» |
| Ajuda | `helpTooltips.ts` (`CF_HELP.monthlyClosing.reports*`) + hint do `SectionCard` | textos de indicadores, atenção, catálogo, resultados e PDF |

`FilePreviewView`/`useFilePreviewLoader` **não usados** — não existe produtor/contrato binário de PDF de relatório no HEAD; o slot permanece com estado honesto até o contrato existir. Nenhuma tabela/matriz paralela nova: a cobertura R01–R15 reutiliza labels e variantes exportadas de `ReportsMatrixPanel`.


## Registro de execução — Relatórios e divergências V0.3 (CF-PROC0072-REPORTS-DETAIL-UX-011, 27/10/2026)

Páginas contextuais de relatório e hub compacto, ainda 100% sobre exports reais do kit:

| Superfície | Export/factory `@delpi/plugin-ui` | Consumo |
|---|---|---|
| Cartões compactos do hub | `InteractiveDataCard` via `CfInteractiveDataCard` — slot `children` | nome + descrição curta + badge de situação real + `openHint`/`onActivate` abrindo a rota contextual; sem fields duplicados nem labels caixa-alta |
| Tabela de agrupamentos de baixas | `DataTableSection` (`createDashboardDataTableSection`) | colunas Natureza/Tipo de movimento/Baixas/Valor/Moeda/Ação — separação exigida pelo §46; `hideSearch`, `columnPreferencesKey` |
| Tabelas de resumo de estoque | `DataTableSection` | Resumo por tipo de produto e por armazém na página contextual (reuso da página legada em modo `reportContext`) |
| Linhas/registros | `DataTableSection` legada | mesma tabela paginada server-side das páginas próprias — zero duplicação |
| Conciliação P3 | `SectionCard` + `StatusBadge` + tabela `cf-p3-table` | `ReportSharedSections.P3ReconciliationSection` — somente `divergence` do backend |
| PDF contextual | `SectionCard` (`CfSectionCard`) | `ReportSharedSections.ReportPdfSlot` — estado honesto; `FilePreviewView` segue não usado (sem produtor homologado) |
| Navegação contextual | `ActionButton` ghost + `CfPagePath` da página | «← Voltar para Relatórios e divergências» + breadcrumb `… > Relatórios e divergências > {Relatório}` |
| Disclosure técnico | `<details>` nativo + tabela `cf-p3-table` | matriz R01–R15 fora do fluxo visual principal, rastreabilidade preservada |

Nenhum componente paralelo de tabela/cartão criado; `selected` do cartão é classe CSS sobre o componente do kit.


## Registro de execução — persistência de filtros dos relatórios (CF-PROC0072-REPORTS-DETAIL-UX-011-RW01, 28/10/2026)

Rework de navegação — **nenhum componente visual novo**: o diff é de estado/URL, reutilizando o padrão canônico já existente na plataforma:

| Superfície | Owner/reuso | Consumo |
|---|---|---|
| Leitura da query | padrão canônico `window.location.search` + `popstate` (mesmo mecanismo de `plugins/api-delpi-console/src/lib/useConsoleSearchParams.ts` e da página de Documentos) | `reportQueryParams.readReportSearchParams` |
| Navegação | `navigatePluginPath` com `replace: true` (`app/pluginNavigation.ts`) — já emite `popstate` | serialização sem nova entrada de histórico |
| Serialização/validação | `features/closing/reportQueryParams.ts` (owner local — escopo do plugin, sem regra de negócio, consumido por 3 módulos) | `SETTLEMENT_PARAMS`, `STOCK_PARAMS`, `parse*`/`serialize*`, `pickFamilyParams`, `useReportQuerySync` |
| Filtros/tabelas | componentes de filtro e `DataTableSection` legados inalterados | mesma máquina de consulta; `applied`/debounce intactos |
| Retorno ao hub | `backToReports`/`openReport` da `MonthlyClosingPage` | agregam/repassam somente os params da família (`pickFamilyParams`) |

Sem helper paralelo por página: um único owner de params/parse/serialize e um único hook de sincronização; modo legado (`reportContext` ausente) não ativa o sync. `localStorage`/`sessionStorage` não usados — a URL é a fonte recuperável autorizada.

### UX-012 — Documentos do fechamento (28/10/2026)

| Necessidade | Componente/fábrica real | Consumo |
|---|---|---|
| Breadcrumb | `createDashboardPagePath` → `CfPagePath` | listagem e formulário (Início > Administração > Documentos) |
| Título + ajuda | `createDashboardTitleWithHelp` → `CfTitleWithHelp` + `CF_HELP.documentsAdmin.*` | página, listagem, formulário, vigência, histórico |
| Filtros | `createDashboardFiltersKit` → `FiltersRow`/`FilterInputField`/`FilterSelectField` | pesquisa, situação, destino — estado na URL |
| Tabela | `DataTableSection` (`cfDataTableUi`) | tipos de documento com colunas explícitas |
| Situação | `createDashboardStatusBadge` → `CfStatusBadge` | vigente/futuro/encerrado |
| Seções do formulário | `createDashboardSectionCard` → `CfSectionCard` | Identificação, Exigência, Vigência, Histórico |
| Ações | `ActionButton`/`CfActionButton` | adicionar, salvar, cancelar, editar, encerrar |
| Confirmação destrutiva | `ConfirmModalPanel` + `CfDialog` | «Encerrar exigência» |
| Estados | `EmptyState`/`CfEmptyState`, `CfQueryErrorBanner`, `CfFeedbackMessage` | vazio, 403/erro, rascunho aberto, validação |


### UX-013 — inventário obrigatório de reuse para refinamento do catálogo (PLANNED)

**Não assumir que o nome visual “Blueprint UI” autoriza novos imports:** verificar os exports e factories reais vigentes de `@delpi/plugin-ui` e as implementações dos demais Portais. Em UX-012 foram usados SectionCard, ActionButton, FiltersKit, DataTableSection, StatusBadge, ConfirmModalPanel e PagePath, mas o formulário ainda usa controles nativos/local CSS e a auditoria usa lista simples.

| Superfície | Reuso a investigar | Regra |
|---|---|---|
| Text input, textarea, select, month | Form/Input/Select/TextArea/Date ou equivalentes reais do kit | Só mapear componente comprovado; sem duplicar wrappers |
| Botões e ícones | ActionButton, IconButton, Icon/Tooltip/variants reais | CTA primário + ações secundárias/danger |
| Cards/layout | SectionCard e layout utilities/tokens | Card gap, padding, grid responsivo via tokens |
| Timeline/eventos | componente Media / MediaObject / Activity / Timeline, se exportado | Não inventar; registrar gap ou centralizar extensão no kit com gate |
| Tabela/filtros | DataTableSection, FiltersKit | Preservar URL/F5, ações e estados |
| Estados/badges/ajuda | EmptyState, StatusBadge, FeedbackMessage, TitleWithHelp | estados honestos e acessíveis |
| Navegação | PagePath e navegação do host | Sem nova árvore/chrome |

Revisão de implementação obrigatória: mapa final campo→export/import exato, CSS residual justificado, regressões visual e funcional, light/dark, teclado/mobile. Plano 113 §28.9; wireframe 112 §49.


### UX-015 — navegação em cascata do checklist admin (28/10/2026)

| Necessidade | Componente/fábrica real | Consumo |
|---|---|---|
| Breadcrumb contextual | `CfPagePath` (`createDashboardPagePath`) | todos os níveis: back→pai imediato, items→ancestrais |
| Metadados read-only | `cf-detail-list` (dl/dt/dd — padrão de `ClosingChecklistPage`) | «Dados da versão», «Identificação», «Exigência», «Contexto da versão» |
| Tabelas | `DataTableSection` (`cfDataTableUi`) | versões (nível 1), itens do snapshot (nível 2) |
| Cards | `CfSectionCard` | dados da versão, documentos, identificação, exigência, contexto, eventos |
| Timeline de auditoria | `CfTimeline` + `EVENT_LABELS`/`EVENT_TONES` | nível 4 — substitui o modal removido |
| Estados/badges | `CfStatusBadge`, `CfEmptyState`, `CfFeedbackMessage`, `CfQueryErrorBanner` | estado da versão, vazio legítimo, 403/404 honestos |
| Ações governadas | `ActionButton`/`CfActionButton`, `VersionStatusActions`, `useChecklistVersionActions`, `ChecklistItemFormDialog` (`checklistAdminShared.tsx` — owner local compartilhado das duas páginas admin) | ações por estado, diálogos publish/return/inactivate/discard, editor de item DRAFT |
| Navegação | `navigatePluginPath`/`navigatePluginView` + builders `checklistAdminVersionPath`/`checklistAdminVersionDocumentPath`/`checklistAdminEventsPath` (`pluginRoutes.ts`) | cascata sem nova aba; deep link/F5/back-forward nativos |

Zero componente novo de kit: a separação em páginas reutilizou o padrão read-only (`cf-detail-list`) e os wrappers de ritmo do UX-013-RW01 (`cf-lead-stack`/`cf-card-stack`). `checklistAdminShared.tsx` é o owner único do ciclo de ações de versão — elimina a duplicação que existiria entre lista e detalhe.


### UX-015-RW01 — mapa de reuso para wireframes (PLANNED)

| Elemento | Reuso preferencial (verificar export real HEAD) | Observação |
|---|---|---|
| Breadcrumb/header contextual | CfPagePath, CfTitleWithHelp, ActionButton | Preservar chrome |
| Resumo versão | CfSectionCard, CfStatusBadge, layout/grid do kit | Sem inventar KPI/componente novo |
| Tabela documentos | DataTableSection, filtros/badges existentes | Preservar dados reais, não expansão |
| Detalhe de propriedades | cf-detail-list ou read-only factory homologada, CSS grid escopado | Sem pares dt/dd empilhados à esquerda |
| Contexto resumido | CfSectionCard, badges, actions | Evitar card gigante repetitivo |
| Histórico | CfTimeline, sem modal | Identidade UX014 depende Core/BFF |
| Empty/error/loading | CfEmptyState, CfFeedbackMessage, CfQueryErrorBanner | Estados honestos |
| Iconografia/spacing | tokens e ícones homologados plugin-ui | Dark/light, foco/mobile |

Registrar no relatório final os imports reais e qualquer CSS residual; criar componentes paralelos somente após gate. Wireframe detalhado doc 112 §51.


### UX-015-RW01 — redesign visual da cascata (28/10/2026)

| Necessidade | Componente/padrão real | Consumo |
|---|---|---|
| Resumo compacto da versão | `CfMetricStrip` (`PageHeroHighlight` items) | 3 tiles reais do DTO — zero KPI inventado |
| Grid read-only | `cf-detail-list` (agora estilizada — era markup sem regra) | todos os metadados; reutiliza hierarquia de `cf-attention-facts__row` |
| Header com ações | `cf-lead-row` + `cf-lead-badges` + `cf-validation-panel__item-actions` | título+badges à esquerda, ações à direita, wrap no mobile |
| Contexto de versão | `cf-version-context` + `CfStatusBadge` | linha compacta, substitui card gigante |
| Banda de documentos | `DataTableSection` direta | removeu card aninhado com título duplicado |
| Timeline | `CfTimeline` + subtítulo de escopo | inalterado, só contexto textual |

Zero componente novo: o fix foi CSS scoped no padrão existente + recomposição JSX com exports já consumidos (`CfMetricStrip`, `CfStatusBadge`, `CfActionButton`, `CfPagePath`, `DataTableSection`).
