/**
 * Adapter fino: fábricas do `@delpi/plugin-ui` com o prefixo `itp` do portal.
 * Nenhum componente visual é reimplementado — somente binding de classes/labels.
 */
import {
  ActionButton,
  ConfirmModalPanel,
  confirmModalBemClasses,
  createDashboardCommandPalette,
  createDashboardDateField,
  createDashboardEmptyState,
  createDashboardLoadingActivityCard,
  createDashboardPageHero,
  createDashboardPagePath,
  createDashboardSectionCard,
  createDashboardSelectField,
  createDashboardStateBanner,
  createDashboardStatusBadge,
  createDashboardTextAreaField,
  createDashboardTextField,
  createDashboardTopBar,
  createDashboardTopBarSearchTrigger,
  createDashboardTopBarUserIdentity,
  createDashboardTopBarUtilityCluster,
  createDashboardUserManual,
  createFloatingNoticeStack,
  createHostContainedModalShell,
  createMetricKpiCard,
  dateFieldBemClasses,
  emptyStatePanelBemClasses,
  sectionCardPacBemClasses,
  selectFieldPacClasses,
  stateBannerBemClasses,
  textAreaFieldBemClasses,
  textFieldBemClasses,
} from "@delpi/plugin-ui/index";
import { createElement, type ComponentProps } from "react";

import { NOTICE_CONTENT } from "../content/labels";

export const UI_PREFIX = "itp";
export const ITP_PORTAL_SCOPE = "dashboard-it-portal";

const sectionLabels = {
  titleHelpAriaLabel: (title: string) => `Ajuda: ${title}`,
  expandAriaLabel: (title: string) => `Expandir ${title}`,
  collapseAriaLabel: (title: string) => `Recolher ${title}`,
};

export const ItpActionButton = ActionButton;

const ItpPageHeroBase = createDashboardPageHero({ prefix: UI_PREFIX });
export function ItpPageHero(props: ComponentProps<typeof ItpPageHeroBase>) {
  return createElement(ItpPageHeroBase, { density: "compact", ...props });
}

export const ItpTopBar = createDashboardTopBar({ prefix: UI_PREFIX });
export const ItpTopBarUtilityCluster = createDashboardTopBarUtilityCluster({ prefix: UI_PREFIX });
export const ItpTopBarSearchTrigger = createDashboardTopBarSearchTrigger({ prefix: UI_PREFIX });
export const ItpTopBarUserIdentity = createDashboardTopBarUserIdentity({ prefix: UI_PREFIX });
export const ItpCommandPalette = createDashboardCommandPalette({
  prefix: UI_PREFIX,
  portalScopeClassName: ITP_PORTAL_SCOPE,
});
export const ItpPagePath = createDashboardPagePath({
  prefix: UI_PREFIX,
  portalScopeClassName: ITP_PORTAL_SCOPE,
});
export const ItpSectionCard = createDashboardSectionCard({
  classNames: sectionCardPacBemClasses(UI_PREFIX),
  labels: sectionLabels,
});
export const ItpKpiCard = createMetricKpiCard(UI_PREFIX);
export const ItpStatusBadge = createDashboardStatusBadge({ prefix: UI_PREFIX });
export const ItpStateBanner = createDashboardStateBanner({
  classNames: stateBannerBemClasses(UI_PREFIX),
});
export const ItpEmptyState = createDashboardEmptyState({
  classNames: emptyStatePanelBemClasses(UI_PREFIX),
  defaultMessage: "Nenhum registro encontrado.",
});
export const ItpLoadingCard = createDashboardLoadingActivityCard({
  prefix: UI_PREFIX,
  labels: {
    progressRemaining: (remainingPercent: number) => `Faltam ${remainingPercent}%`,
    progressAriaDeterminate: (remainingPercent: number) =>
      `Carregamento: faltam ${remainingPercent} por cento`,
    progressAriaIndeterminate: "Carregamento em andamento",
  },
});

export const ItpTextField = createDashboardTextField({ classNames: textFieldBemClasses(UI_PREFIX) });
export const ItpTextAreaField = createDashboardTextAreaField({
  classNames: textAreaFieldBemClasses(UI_PREFIX),
});
export const ItpDateField = createDashboardDateField({ classNames: dateFieldBemClasses(UI_PREFIX) });
const { field: selectField, control: selectControl } = selectFieldPacClasses(UI_PREFIX);
export const ItpSelectField = createDashboardSelectField({
  field: selectField,
  control: selectControl,
  labels: {
    placeholder: "Selecione…",
    emptyLabel: "Todos",
    control: {
      searchPlaceholder: "Buscar…",
      emptyOptions: "Nenhuma opção encontrada.",
      searchAriaLabel: (label?: string) => (label ? `Buscar em ${label}` : "Buscar opções"),
    },
  },
});

export const ItpDialog = createHostContainedModalShell({
  prefix: UI_PREFIX,
  portalScopeClassName: ITP_PORTAL_SCOPE,
  containedLayout: "dialog",
  closeAriaLabel: "Fechar",
});
export const ItpWideDialog = createHostContainedModalShell({
  prefix: UI_PREFIX,
  portalScopeClassName: ITP_PORTAL_SCOPE,
  containedLayout: "dialog",
  variant: "wide",
  closeAriaLabel: "Fechar",
});
export const ItpConfirmPanel = ConfirmModalPanel;
export const itpConfirmClassNames = confirmModalBemClasses(UI_PREFIX);

export const ItpNoticeStack = createFloatingNoticeStack({
  prefix: UI_PREFIX,
  portalScopeClassName: ITP_PORTAL_SCOPE,
  labels: {
    stackAriaLabel: NOTICE_CONTENT.stackAriaLabel,
    dismissAriaLabel: NOTICE_CONTENT.dismissAriaLabel,
  },
});

export const ItpUserManual = createDashboardUserManual({ prefix: UI_PREFIX });
