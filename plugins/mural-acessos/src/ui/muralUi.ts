import {
  createDashboardEmptyState,
  createDashboardPageHeader,
  createHostContainedModalShell,
  emptyStatePanelBemClasses,
  pageHeaderTitleRowBemClasses,
} from "@delpi/plugin-ui/index";

export const MURAL_ROOT_CLASS = "dashboard-mural-acessos";
export const MURAL_PREFIX = "ma";

export const MuralPageHeader = createDashboardPageHeader({
  layout: "titleRow",
  classNames: pageHeaderTitleRowBemClasses(MURAL_PREFIX),
  labels: {
    refresh: "Atualizar",
    refreshing: "Atualizando…",
  },
});

export const MuralEmptyState = createDashboardEmptyState({
  classNames: emptyStatePanelBemClasses(MURAL_PREFIX),
  defaultTitle: "Nenhum acesso cadastrado",
  defaultMessage: "Cadastre o primeiro link para montar o menu do mural.",
});

export const MuralDialog = createHostContainedModalShell({
  prefix: MURAL_PREFIX,
  portalScopeClassName: MURAL_ROOT_CLASS,
  containedLayout: "dialog",
});
