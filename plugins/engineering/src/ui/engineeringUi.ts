import {
  ActionButton,
  AnchoredPanelPortal,
  attachmentFileListBemClasses,
  createDashboardAttachmentFileList,
  createDashboardFileDropzone,
  fileDropzoneBemClasses,
  IconButton,
  catalogSearchBarBemClasses,
  ChartCard as DelpiChartCard,
  chartCardBemClasses,
  createDashboardSelectField,
  createDashboardCatalogSearchBar,
  createDashboardChartToolbarKit,
  createDashboardCommandPalette,
  createDashboardDetailCard,
  createDashboardDetailFieldGrid,
  createDashboardEmptyState,
  createDashboardEventsSection,
  createDashboardDataCardsGrid,
  createDashboardFiltersKit,
  createDashboardInteractiveDataCard,
  createDashboardKanbanBoard,
  createDashboardKpiCard,
  createDashboardLoadingActivityCard,
  createDashboardMetricStrip,
  createDashboardMultiSelectField,
  createDashboardDateField,
  createDashboardNativeFormFields,
  createDashboardProgressTracker,
  createDashboardSegmentToggle,
  createDashboardUnderlineNav,
  createHostContainedModalShell,
  createInitialsAvatar,
  createTimeline,
  FieldLabel,
  createDashboardQuickPeriodSelector,
  dataTableBemClasses,
  dataTableSectionBemClasses,
  dateFieldBemClasses,
  delpiUiClass,
  detailCardRichBemClasses,
  formActionsBemClasses,
  formFieldShellBemClasses,
  ghostBtnBemClasses,
  createDashboardPageHero,
  createDashboardPagePath,
  selectFieldPacClasses,
  createDashboardRecentAccessStrip,
  createDashboardSectionCard,
  createDashboardSectionRouteCard,
  createDashboardStateBanner,
  createDashboardStatusBadge,
  createDashboardTopBar,
  createDashboardTopBarFavoritesStrip,
  createDashboardTopBarSearchTrigger,
  createDashboardTopBarUserIdentity,
  createDashboardUserManual,
  createDashboardViewTransition,
  emptyStateCardBemClasses,
  sectionCardPacBemClasses,
  sectionRouteCardBemClasses,
  stateBannerBemClasses,
  stateBoxPlaceholderBemClasses,
  createDashboardFormActions,
  NativeCheckboxControl,
  usePersistedViewLayout,
  type ChartCardProps as DelpiChartCardProps,
} from "@delpi/plugin-ui/index";
import { createElement, type ComponentProps } from "react";

/** Prefixo BEM dual-class do MFE (pares com `.delpi-ui-*` no remote). */
export const ENG_UI_PREFIX = "engineering";
export const ENG_PORTAL_SCOPE = "portal-engineering";

export const EngineeringTopBar = createDashboardTopBar({
  prefix: ENG_UI_PREFIX,
});

export const EngineeringTopBarSearchTrigger =
  createDashboardTopBarSearchTrigger({ prefix: ENG_UI_PREFIX });

export const EngineeringTopBarFavoritesStrip =
  createDashboardTopBarFavoritesStrip({ prefix: ENG_UI_PREFIX });

export const EngineeringTopBarUserIdentity =
  createDashboardTopBarUserIdentity({ prefix: ENG_UI_PREFIX });

export const EngineeringCommandPalette = createDashboardCommandPalette({
  prefix: ENG_UI_PREFIX,
  portalScopeClassName: ENG_PORTAL_SCOPE,
});

export const EngineeringPageHeroBase = createDashboardPageHero({
  prefix: ENG_UI_PREFIX,
});
/** Default `density="compact"` — mesmo padrão do Portal Comercial:
 *  libera viewport nas páginas sem trocar tokens/tipografia. */
export function EngineeringPageHero(
  props: ComponentProps<typeof EngineeringPageHeroBase>,
) {
  return createElement(EngineeringPageHeroBase, {
    density: "compact",
    ...props,
  });
}

export const EngineeringMetricStrip = createDashboardMetricStrip({
  prefix: ENG_UI_PREFIX,
});

export const EngineeringKpiCard = createDashboardKpiCard({
  prefix: ENG_UI_PREFIX,
  labels: {
    goalPrefix: "Meta",
    iddScorePrefix: "Nota IDD",
    badgesStatus: "Escopo e desempenho em relação à meta",
  },
});

export const EngineeringQuickPeriodSelector =
  createDashboardQuickPeriodSelector(ENG_UI_PREFIX);

export const EngineeringDateField = createDashboardDateField({
  classNames: dateFieldBemClasses(ENG_UI_PREFIX),
});

export const EngineeringMultiSelectField = createDashboardMultiSelectField({
  prefix: ENG_UI_PREFIX,
  portalScopeClassName: ENG_PORTAL_SCOPE,
  labels: {
    emptyLabel: "Todas",
    searchPlaceholder: "Buscar…",
    selectVisible: "Selecionar visíveis",
    clear: "Limpar",
    emptyOptions: "Nenhuma opção disponível.",
    multipleSelected: (count) => `${count} selecionadas`,
    searchAriaLabel: (label) => `Buscar em ${label}`,
    selectedCountLabel: (count) => `${count} unidades selecionadas`,
    removeTagAriaLabel: (value) => `Remover ${value}`,
  },
});

export const EngineeringEventsSection = createDashboardEventsSection({
  prefix: ENG_UI_PREFIX,
  labels: {
    titleHelpAriaLabel: (title) => `Ajuda: ${title}`,
  },
});

export const EngineeringCatalogSearchBar = createDashboardCatalogSearchBar({
  classNames: catalogSearchBarBemClasses(ENG_UI_PREFIX),
});

export const EngineeringRecentAccessStrip = createDashboardRecentAccessStrip({
  prefix: ENG_UI_PREFIX,
});

export const EngineeringSectionRouteCard = createDashboardSectionRouteCard({
  classNames: sectionRouteCardBemClasses(ENG_UI_PREFIX),
});

export const EngineeringUserManual = createDashboardUserManual({
  prefix: ENG_UI_PREFIX,
});

export const EngineeringPagePath = createDashboardPagePath({
  prefix: ENG_UI_PREFIX,
  portalScopeClassName: ENG_PORTAL_SCOPE,
});

export const EngineeringViewTransition = createDashboardViewTransition({
  prefix: ENG_UI_PREFIX,
});

export const EngineeringStatusBadge = createDashboardStatusBadge({
  prefix: ENG_UI_PREFIX,
});

export const EngineeringActionButton = ActionButton;

/** Botão só-ícone do kit (lupa, lixeira, desfazer) — hit target oficial
 * 36px, tons default/danger/primary; nome acessível obrigatório. */
export const EngineeringIconButton = IconButton;

export const EngineeringSectionCard = createDashboardSectionCard({
  classNames: sectionCardPacBemClasses(ENG_UI_PREFIX),
  labels: {
    titleHelpAriaLabel: (title) => `Ajuda: ${title}`,
  },
});

export const EngineeringStateBanner = createDashboardStateBanner({
  classNames: stateBannerBemClasses(ENG_UI_PREFIX),
});

export const EngineeringEmptyState = createDashboardEmptyState({
  classNames: emptyStateCardBemClasses(ENG_UI_PREFIX),
  defaultMessage: "Nenhum item no momento.",
});

/** Loading canônico dos portais (mesmo componente do TRANSFORMA+):
 *  `progressPercent` ausente → modo indeterminado oficial; nunca
 *  exibir percentual sem medição real vinda da Engineering API. */
export const EngineeringLoadingActivityCard =
  createDashboardLoadingActivityCard({
    prefix: ENG_UI_PREFIX,
    labels: {
      progressRemaining: (percent) => `Faltam ${percent}%`,
      progressAriaDeterminate: (percent) =>
        `Carregamento: faltam ${percent} por cento`,
      progressAriaIndeterminate: "Carregamento em andamento",
    },
    withCopyWrapper: true,
  });

// --- Blocos canônicos compartilhados pelas páginas internas do MFE ---
// Mesma fonte (`@delpi/plugin-ui`) e mesmo prefixo `engineering` usados
// por Home/Visão Geral — páginas internas não criam prefixo visual próprio.

export const ENGINEERING_GHOST_BTN = ghostBtnBemClasses(ENG_UI_PREFIX);

/** Placeholder de gráfico/lista vazio — dual `state-box--empty`. */
export const ENGINEERING_STATE_BOX_EMPTY =
  stateBoxPlaceholderBemClasses(ENG_UI_PREFIX);

/** Erro com shell card — dual `state-box--error`. */
export const ENGINEERING_STATE_BOX_ERROR = delpiUiClass(
  `${ENG_UI_PREFIX}-card ${ENG_UI_PREFIX}-state-box ${ENG_UI_PREFIX}-state-box--error`,
  "delpi-ui-card delpi-ui-state-box delpi-ui-state-box--error",
);

const ENGINEERING_CHART_CARD_CLASSES = chartCardBemClasses(ENG_UI_PREFIX);

export type EngineeringChartCardProps = Omit<
  DelpiChartCardProps,
  "classNames" | "titleLevel"
>;

export function EngineeringChartCard(props: EngineeringChartCardProps) {
  return createElement(DelpiChartCard, {
    classNames: ENGINEERING_CHART_CARD_CLASSES,
    titleLevel: 3,
    ...props,
  });
}

export const EngineeringChartToolbarKit = createDashboardChartToolbarKit({
  prefix: ENG_UI_PREFIX,
  labels: {
    groupAriaLabel: "Agrupamento do gráfico",
    exportSeries: "Exportar série",
    exportSeriesAriaLabel: "Exportar série do gráfico em CSV",
  },
});

export const EngineeringDetailCard = createDashboardDetailCard({
  classNames: detailCardRichBemClasses(ENG_UI_PREFIX),
  labels: {
    titleHelpAriaLabel: (title) => `Ajuda: ${title}`,
  },
});

export const EngineeringDetailFieldGrid = createDashboardDetailFieldGrid({
  prefix: ENG_UI_PREFIX,
  labels: {
    emptyMessage: "Sem dados.",
    fieldHelpAriaLabel: (label) => `Ajuda: ${label}`,
  },
  wrapLabels: true,
});

/** Timeline oficial do kit — histórico/auditoria das features. */
export const EngineeringTimeline = createTimeline({
  prefix: ENG_UI_PREFIX,
});

/** Avatar oficial por iniciais — foto é melhoria progressiva quando a
 * fonte de identidade oferece imagem governada; iniciais são o fallback
 * honesto para usuário sem foto publicada. */
export const EngineeringInitialsAvatar = createInitialsAvatar(ENG_UI_PREFIX);

/** Rótulo de formulário com ajuda no próprio texto (sem ícone `?`). */
export const EngineeringFieldLabel = FieldLabel;

/* Filters kit oficial do design system — mesma fábrica compartilhada
 * que outros MFEs (ex.: Helpdesk) consomem para construtores de
 * critérios; nenhum componente privado de outro plugin é importado. */
const engineeringFiltersKit = createDashboardFiltersKit({
  prefix: ENG_UI_PREFIX,
  labels: { filtersAriaLabel: "Filtros da listagem" },
  portalScopeClassName: ENG_PORTAL_SCOPE,
});

export const EngineeringFiltersRow = engineeringFiltersKit.FiltersRow;
export const EngineeringFilterInput = engineeringFiltersKit.FilterInputField;
export const EngineeringFilterSelect = engineeringFiltersKit.FilterSelectField;

/** Classes/labels canônicos da DataTable — o componente em si é genérico
 * (`DataTable<T>`) e é encapsulado pelos wrappers `.tsx` de cada feature. */
export const ENGINEERING_DATA_TABLE_CLASSES =
  dataTableBemClasses(ENG_UI_PREFIX);

export const ENGINEERING_DATA_TABLE_LABELS = {
  emptyMessage: "Nenhum registro encontrado.",
  loadingMessage: "Carregando…",
  sortByAriaLabel: (header: string) => `Ordenar por ${header}`,
  headerHelpAriaLabel: (header: string) => `Ajuda: ${header}`,
};

export const ENGINEERING_DATA_TABLE_SECTION_CLASSES =
  dataTableSectionBemClasses(ENG_UI_PREFIX);

/* --- Navegação por abas, stepper e formulários (PRC/intake) ---------- */

/** Abas acessíveis do kit (`mode="tabs"`: role=tablist, setas/Home/End,
 * `aria-selected`/`aria-controls`) — mesmo componente canônico usado
 * pelos demais MFEs para seções internas de uma página. */
export const EngineeringTabs = createDashboardUnderlineNav({
  prefix: ENG_UI_PREFIX,
});

/** Stepper/progresso linear do kit — wizard de intake e andamento do
 * workflow PRC (estados de domínio, não percentual inventado). */
export const EngineeringProgressTracker = createDashboardProgressTracker({
  prefix: ENG_UI_PREFIX,
});

/** Toggle segmentado (ex.: escolha Criação × Alteração no intake). */
export const EngineeringSegmentToggle =
  createDashboardSegmentToggle(ENG_UI_PREFIX);

/** Campos de formulário nativos do kit — label+hint+shell canônicos. */
const engineeringNativeFormFields = createDashboardNativeFormFields({
  classNames: formFieldShellBemClasses(ENG_UI_PREFIX),
});

export const EngineeringFormFieldShell = engineeringNativeFormFields.FormFieldShell;
export const EngineeringTextField = engineeringNativeFormFields.TextField;
export const EngineeringSelectField = engineeringNativeFormFields.SelectField;
export const EngineeringTextAreaField = engineeringNativeFormFields.TextAreaField;

/** Select rico do kit (trigger + painel ancorado, busca por label,
 * listbox a11y) — componente canônico para campos com opções reais
 * (catálogos TOTVS, enums de domínio). O `<select>` nativo acima só
 * deve ser usado para opções triviais sem busca. */
const engineeringSelectClasses = selectFieldPacClasses(ENG_UI_PREFIX);
export const EngineeringSearchableSelect = createDashboardSelectField({
  field: engineeringSelectClasses.field,
  control: engineeringSelectClasses.control,
  labels: {
    placeholder: "Selecionar…",
    emptyLabel: "Nenhuma opção",
    control: {
      searchPlaceholder: "Buscar por código ou descrição…",
      emptyOptions: "Nenhum item encontrado.",
      searchAriaLabel: (label) =>
        label ? `Buscar em ${label}` : "Buscar opções",
    },
  },
});

/** Checkbox nativo do kit (seleção explícita de paths em UPDATE). */
export const EngineeringCheckboxControl = NativeCheckboxControl;

/** Barra de ações de formulário (alinha botões do wizard/editor). */
export const EngineeringFormActions = createDashboardFormActions({
  classNames: formActionsBemClasses(ENG_UI_PREFIX),
});

/** Visões alternativas da fila (REF-006) — mesmas factories do kit
 * usadas pelo Portal Comercial. */
export const EngineeringDataCardsGrid = createDashboardDataCardsGrid({
  prefix: ENG_UI_PREFIX,
});
export const EngineeringInteractiveDataCard =
  createDashboardInteractiveDataCard({ prefix: ENG_UI_PREFIX });
export const EngineeringKanbanBoard = createDashboardKanbanBoard({
  prefix: ENG_UI_PREFIX,
});

export { usePersistedViewLayout };

/** Modal contido no host `.portal-engineering` — nunca cobre a sidebar
 * do portal (regra mfe-modal-host-contained). Base dos diálogos de
 * confirmação PRC. */
export const EngineeringHostDialog = createHostContainedModalShell({
  prefix: ENG_UI_PREFIX,
  portalScopeClassName: ENG_PORTAL_SCOPE,
  containedLayout: "dialog",
});

/** Painel ancorado em portal (body) do kit — dropdowns dentro de
 * containers com overflow/clip (tabelas editáveis) ficam visíveis,
 * com flip/clamp de viewport e dismiss por Escape/clique fora. */
export const EngineeringAnchoredPanel = AnchoredPanelPortal;
export { ENG_PORTAL_SCOPE as ENGINEERING_PORTAL_SCOPE };



/** PRC-REF-023-F01-FIX-01 — wrappers oficiais do kit para upload de
 * documentos. Labels de limite vêm do consumidor (contrato PRC), nunca
 * de constante divergente. */
export const EngineeringFileDropzone = createDashboardFileDropzone({
  classNames: fileDropzoneBemClasses(ENG_UI_PREFIX, "file-dropzone"),
  labels: {
    title: "Arraste arquivos ou clique para escolher",
    hint: "PDF ou imagens",
  },
});

export const EngineeringAttachmentFileList = createDashboardAttachmentFileList({
  classNames: attachmentFileListBemClasses(ENG_UI_PREFIX),
  labels: {
    open: "Abrir",
    download: "Baixar",
    remove: "Remover",
    empty: "Nenhum arquivo selecionado.",
  },
});
