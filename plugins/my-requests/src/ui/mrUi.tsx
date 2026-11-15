import { createElement, type ComponentProps } from "react";

import {
  attachmentPreviewStripBemClasses,
  createCompactPagination,
  createDashboardAttachmentPreviewStrip,
  createDashboardDataCardsGrid,
  createDashboardDataRecordCard,
  createDashboardDetailFieldGrid,
  createDashboardEmptyState,
  createDashboardFileDropzone,
  createDashboardFilterRulesBuilder,
  createDashboardFiltersKit,
  createDashboardFormActions,
  createDashboardJourneyProgressBar,
  createDashboardLoadingState,
  createDashboardMentionComposer,
  createDashboardMessageThread,
  createDashboardNavigationCard,
  createDashboardPageHeader,
  createDashboardPageHero,
  createDashboardProgressTracker,
  createDashboardRoomConversationShell,
  createDashboardScopeChipBar,
  createDashboardSectionCard,
  createDashboardSegmentToggle,
  createDashboardSelectField,
  createDashboardSortLevelsBuilder,
  createDashboardStateBanner,
  createDashboardStatusBadge,
  createDashboardTextField,
  createDashboardToolbarPopover,
  createDashboardTopBar,
  createDashboardUnderlineNav,
  createHostContainedModalShell,
  createInitialsAvatar,
  createTimeline,
  emptyStateCardBemClasses,
  EntityDirectoryPicker,
  fileDropzoneBemClasses,
  formActionsBemClasses,
  HintAction,
  loadingStateCardBemClasses,
  navigationCardBemClasses,
  pageHeaderTitleRowBemClasses,
  sectionCardPacBemClasses,
  selectFieldPacClasses,
  stateBannerBemClasses,
  textFieldPacClasses,
} from "@delpi/plugin-ui/index";

export type {
  EntityDirectoryOption,
  EntityDirectoryPickerProps,
  MessageThreadAction,
  MessageThreadItem,
} from "@delpi/plugin-ui/index";

export { HintAction };

/** Prefixo BEM dual-class do MFE (pares com `.delpi-ui-*` no remote). */
export const MR_UI_PREFIX = "my-requests";
export const MR_PORTAL_SCOPE = "dashboard-my-requests";

export const MyRequestsPageHeader = createDashboardPageHeader({
  layout: "titleRow",
  classNames: pageHeaderTitleRowBemClasses(MR_UI_PREFIX),
  labels: {
    refresh: "Atualizar",
    refreshing: "Atualizando…",
  },
});

export const MyRequestsSectionCard = createDashboardSectionCard({
  classNames: sectionCardPacBemClasses(MR_UI_PREFIX),
  labels: {
    titleHelpAriaLabel: (title) => `Ajuda: ${title}`,
  },
});

export const MyRequestsNavigationCard = createDashboardNavigationCard({
  classNames: navigationCardBemClasses(MR_UI_PREFIX),
});

/** Hero compacto — mesmo padrão do Helpdesk nas listas. */
const MyRequestsPageHeroBase = createDashboardPageHero({ prefix: MR_UI_PREFIX });

export function MyRequestsPageHero(
  props: Omit<ComponentProps<typeof MyRequestsPageHeroBase>, "density">,
) {
  return createElement(MyRequestsPageHeroBase, { density: "compact", ...props });
}

export const MyRequestsScopeChipBar = createDashboardScopeChipBar({
  prefix: MR_UI_PREFIX,
});

export const MyRequestsRecordCard = createDashboardDataRecordCard({
  prefix: MR_UI_PREFIX,
});

export const MyRequestsDataCardsGrid = createDashboardDataCardsGrid({
  prefix: MR_UI_PREFIX,
});

/** Popover ancorado de toolbar — mecânica do kit (portal + flip/clamp). */
export const MyRequestsListToolbarPopover = createDashboardToolbarPopover({
  prefix: MR_UI_PREFIX,
  portalScopeClassName: MR_PORTAL_SCOPE,
});

/** Ordenação multinível — catálogo de campos vem do contrato da página. */
export const MyRequestsSortLevelsBuilder = createDashboardSortLevelsBuilder({
  prefix: MR_UI_PREFIX,
  portalScopeClassName: MR_PORTAL_SCOPE,
  labels: {
    ariaLabel: "Ordenação da lista",
    fieldHint: "Campo deste nível de ordenação.",
    directionLabel: "Direção",
    directionHint: "Ascendente (A→Z) ou descendente.",
    levelHint: "Até três níveis. O primeiro é o que a grade destaca.",
    levelAriaLabel: (level) => `Nível ${level}`,
    removeLevelHint: "Remove este nível (precisa restar pelo menos um).",
    removeLevelAriaLabel: (level) => `Remover nível ${level}`,
    addLevelHint: "Inclui outro nível (máximo três).",
    addLevelLabel: "Outro nível",
    addLevelAriaLabel: "Adicionar nível de ordenação",
    applyHint: "Grava a ordenação na URL e recarrega a lista.",
    applyLabel: "Aplicar",
    applyAriaLabel: "Aplicar ordenação",
    directionAscLabel: "Ascendente",
    directionDescLabel: "Descendente",
  },
});

/** Builder de critérios AND — campos/operadores vêm do contrato da página. */
export const MyRequestsFilterRulesBuilder = createDashboardFilterRulesBuilder({
  prefix: MR_UI_PREFIX,
  portalScopeClassName: MR_PORTAL_SCOPE,
  labels: {
    ariaLabel: "Construtor de filtros",
    fieldLabel: "Campo",
    fieldHint: "Campo do filtro. Critérios alinhados à grade.",
    operatorHint: "Operação do critério — conforme o campo.",
    valueLabel: "Valor",
    valueHint: "Valor da regra. Vazio não entra ao aplicar.",
    removeRuleHint: "Remove esta regra. A lista só muda depois de Aplicar.",
    removeRuleAriaLabel: "Remover critério",
    addRuleHint: "Inclui outro critério.",
    addRuleLabel: "Adicionar critério",
    addRuleAriaLabel: "Adicionar critério",
    clearHint: "Apaga as regras do painel sem mudar a URL até aplicar.",
    clearLabel: "Limpar",
    clearAriaLabel: "Limpar critérios",
    applyHint: "Aplica os critérios e atualiza a lista.",
    applyLabel: "Aplicar filtros",
    applyAriaLabel: "Aplicar filtros",
  },
});

export const MyRequestsTopBar = createDashboardTopBar({
  prefix: MR_UI_PREFIX,
});

export const MyRequestsFormActions = createDashboardFormActions({
  classNames: formActionsBemClasses(MR_UI_PREFIX),
});

export const MyRequestsStateBanner = createDashboardStateBanner({
  classNames: stateBannerBemClasses(MR_UI_PREFIX),
});

export const MyRequestsEmptyState = createDashboardEmptyState({
  classNames: emptyStateCardBemClasses(MR_UI_PREFIX),
  defaultMessage: "Nenhum item encontrado.",
});

export const MyRequestsLoadingState = createDashboardLoadingState({
  classNames: loadingStateCardBemClasses(MR_UI_PREFIX),
  defaultMessage: "Carregando…",
});

export const MyRequestsTimeline = createTimeline({ prefix: MR_UI_PREFIX });

export const MyRequestsStatusBadge = createDashboardStatusBadge({
  prefix: MR_UI_PREFIX,
});

export const TextField = createDashboardTextField({
  classNames: textFieldPacClasses(MR_UI_PREFIX),
});

const selectClasses = selectFieldPacClasses(MR_UI_PREFIX);

export const SelectField = createDashboardSelectField({
  ...selectClasses,
  labels: {
    placeholder: "Selecione…",
    emptyLabel: "—",
    control: {
      searchPlaceholder: "Buscar…",
      emptyOptions: "Nenhuma opção encontrada.",
      searchAriaLabel: (label?: string) =>
        label ? `Buscar em ${label}` : "Buscar opções",
    },
  },
});

export const SegmentToggle = createDashboardSegmentToggle(MR_UI_PREFIX);

export const DetailFields = createDashboardDetailFieldGrid({
  prefix: MR_UI_PREFIX,
  labels: {
    fieldHelpAriaLabel: (label: string) => `Ajuda: ${label}`,
  },
  valueFallback: "—",
  wrapLabels: true,
});

const filtersKit = createDashboardFiltersKit({
  prefix: MR_UI_PREFIX,
  labels: { filtersAriaLabel: "Filtros de solicitações" },
  portalScopeClassName: MR_PORTAL_SCOPE,
});

export const MyRequestsFiltersRow = filtersKit.FiltersRow;
export const MyRequestsFilterSelectField = filtersKit.FilterSelectField;
export const MyRequestsFilterInputField = filtersKit.FilterInputField;

export const MyRequestsCompactPagination = createCompactPagination({
  prefix: MR_UI_PREFIX,
  layout: "flat",
  labels: {
    info: ({ page, totalPages, total }) =>
      `Página ${page} / ${totalPages} · ${total} solicitações`,
    previous: "Anterior",
    next: "Próxima",
    navigationAriaLabel: "Paginação das solicitações",
  },
});

export const MyRequestsModal = createHostContainedModalShell({
  prefix: MR_UI_PREFIX,
  portalScopeClassName: MR_PORTAL_SCOPE,
  containedLayout: "dialog",
});

export const MyRequestsFileDropzone = createDashboardFileDropzone({
  classNames: fileDropzoneBemClasses(MR_UI_PREFIX, "file-dropzone"),
  labels: {
    title: "Arraste um arquivo ou clique para selecionar",
    hint: "PDF ou imagem · máx. 25 MB",
  },
});

export const MyRequestsAttachmentPreviewStrip = createDashboardAttachmentPreviewStrip({
  classNames: attachmentPreviewStripBemClasses(MR_UI_PREFIX),
  labels: {
    empty: "Nenhum arquivo.",
    openAriaLabel: (fileName) => `Abrir ${fileName}`,
    removeAriaLabel: (fileName) => `Remover ${fileName}`,
  },
});

export const MyRequestsProgressTracker = createDashboardProgressTracker({
  prefix: MR_UI_PREFIX,
});

export const MyRequestsJourneyProgressBar = createDashboardJourneyProgressBar({
  prefix: MR_UI_PREFIX,
  defaultLabel: "Progresso da solicitação",
});

/** UI-FIX-07 — mesma navegação por abas sublinhada usada pelo
 * Portal Engenharia (`createDashboardUnderlineNav` do kit). */
export const MyRequestsUnderlineNav = createDashboardUnderlineNav({
  prefix: MR_UI_PREFIX,
});

export const MyRequestsAvatar = createInitialsAvatar(MR_UI_PREFIX);

export const MyRequestsMessageThread = createDashboardMessageThread(MR_UI_PREFIX);

export const MyRequestsMentionComposer = createDashboardMentionComposer(MR_UI_PREFIX);

const roomConversationKit = createDashboardRoomConversationShell(MR_UI_PREFIX);
export const MyRequestsRoomConversationChatColumn = roomConversationKit.ChatColumn;
export const MyRequestsRoomPanel = roomConversationKit.Panel;
export const myRequestsRoomConversationClassNames = roomConversationKit.classNames;

/** Typeahead genérico do kit (avatar/chips via slots no consumidor). */
export const MyRequestsEntityDirectoryPicker = EntityDirectoryPicker;
