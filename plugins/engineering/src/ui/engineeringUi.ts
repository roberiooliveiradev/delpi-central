import {
  ActionButton,
  catalogSearchBarBemClasses,
  ChartCard as DelpiChartCard,
  chartCardBemClasses,
  createDashboardCatalogSearchBar,
  createDashboardChartToolbarKit,
  createDashboardCommandPalette,
  createDashboardDetailCard,
  createDashboardDetailFieldGrid,
  createDashboardEmptyState,
  createDashboardEventsSection,
  createDashboardKpiCard,
  createDashboardLoadingActivityCard,
  createDashboardMetricStrip,
  createDashboardMultiSelectField,
  createDashboardDateField,
  createInitialsAvatar,
  createTimeline,
  FieldLabel,
  createDashboardQuickPeriodSelector,
  dataTableBemClasses,
  dataTableSectionBemClasses,
  dateFieldBemClasses,
  delpiUiClass,
  detailCardRichBemClasses,
  ghostBtnBemClasses,
  createDashboardPageHero,
  createDashboardPagePath,
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


