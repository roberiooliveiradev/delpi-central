import {
  createDashboardLoadingActivityCard,
  createDashboardSectionCard,
  createDashboardStateBox,
  createHostContainedModalShell,
  sectionCardPacBemClasses,
} from "@delpi/plugin-ui/index";

export const UI_PREFIX = "po";

/** Classe do root do MFE — portal de modal host-contained. */
export const PO_ROOT_CLASS = "dashboard-planejamento-orcamentario";

const LOADING_LABELS = {
  progressRemaining: (remainingPercent: number) => `Faltam ${remainingPercent}%`,
  progressAriaDeterminate: (remainingPercent: number) =>
    `Carregamento: faltam ${remainingPercent} por cento`,
  progressAriaIndeterminate: "Carregamento em andamento",
};

export const SectionCard = createDashboardSectionCard({
  classNames: sectionCardPacBemClasses(UI_PREFIX),
  labels: {
    titleHelpAriaLabel: (title: string) => `Ajuda: ${title}`,
  },
});

export const LoadingActivityCard = createDashboardLoadingActivityCard({
  prefix: UI_PREFIX,
  labels: LOADING_LABELS,
});

export const StateBox = createDashboardStateBox({ prefix: UI_PREFIX });

/** Workbench do formulário — preenche a área do plugin sem cobrir a sidebar. */
export const HostContainedModal = createHostContainedModalShell({
  prefix: UI_PREFIX,
  portalScopeClassName: PO_ROOT_CLASS,
  containedLayout: "fill",
  closeAriaLabel: "Fechar",
});

/** Card centralizado (detalhe / aviso) — overlay só na área do plugin. */
export const HostContainedDialog = createHostContainedModalShell({
  prefix: UI_PREFIX,
  portalScopeClassName: PO_ROOT_CLASS,
  containedLayout: "dialog",
  closeAriaLabel: "Fechar",
});
