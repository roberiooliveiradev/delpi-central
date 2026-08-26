import {
  ActionButton,
  createDashboardFilterCheckboxField,
  createDashboardInteractiveDataCard,
  createDashboardLoadingActivityCard,
  createDashboardPageHero,
  createDashboardScreenLoading,
  createDashboardSegmentToggle,
  createDashboardStatusBadge,
  createDashboardTabularExportButtons,
  createDashboardTableFontSizeControls,
  createDashboardTitleWithHelp,
  createDashboardTopBar,
  createDashboardCompareSparkline,
  createDashboardSeriesSparkline,
  createSimpleKpiCard,
  FieldLabel,
  NativeCheckboxControl,
  filterCheckboxFieldBemClasses,
  SectionHintLabel,
  titleWithHelpBemClasses,
  type DashboardSimpleKpiCardProps,
} from "@delpi/plugin-ui/index";
import { createElement, type ComponentProps } from "react";

import {
  MAINTENANCE_LOADING_LABELS,
  MAINTENANCE_LOADING_TITLES,
} from "../content/loadingLabels";

export const UI_PREFIX = "dm";
export const DM_PORTAL_SCOPE = "dashboard-maintenance";

export const MaintenanceActionButton = ActionButton;
export const MaintenanceFieldLabel = FieldLabel;
export const MaintenanceSectionHintLabel = SectionHintLabel;
export const MaintenanceTitleWithHelp = createDashboardTitleWithHelp({
  classNames: titleWithHelpBemClasses(UI_PREFIX),
  labels: {
    titleHelpAriaLabel: (title: string) => `Ajuda: ${title}`,
  },
});
export const MaintenanceStatusBadge = createDashboardStatusBadge({ prefix: UI_PREFIX });

export const MaintenanceLoadingCard = createDashboardLoadingActivityCard({
  prefix: UI_PREFIX,
  labels: MAINTENANCE_LOADING_LABELS,
});

export const MaintenanceScreenLoading = createDashboardScreenLoading({
  defaultLabel: MAINTENANCE_LOADING_TITLES.default,
  variant: "embedded",
  tone: "brand",
});

export const MaintenancePageHeroBase = createDashboardPageHero({ prefix: UI_PREFIX });

/** Default `density="compact"` — padrão Portal Comercial. */
export function MaintenancePageHero(
  props: ComponentProps<typeof MaintenancePageHeroBase>,
) {
  return createElement(MaintenancePageHeroBase, { density: "compact", ...props });
}

export const MaintenanceTopBar = createDashboardTopBar({ prefix: UI_PREFIX });

export const MaintenanceFilterCheckboxField = createDashboardFilterCheckboxField({
  classNames: filterCheckboxFieldBemClasses(UI_PREFIX),
  labels: { defaultCheckboxLabel: "Ativar" },
});

export const MaintenanceNativeCheckboxControl = NativeCheckboxControl;

export const MaintenanceInteractiveDataCard = createDashboardInteractiveDataCard({
  prefix: UI_PREFIX,
});

export const MaintenanceTabularExportButtons = createDashboardTabularExportButtons({
  prefix: UI_PREFIX,
  groupAriaLabel: "Exportar dados",
});

export const MaintenanceSimpleKpiCard = createSimpleKpiCard(UI_PREFIX, {
  withBody: true,
  withSubtitle: true,
});

export type MaintenanceSimpleKpiCardProps = DashboardSimpleKpiCardProps;

export const MaintenanceCompareSparkline = createDashboardCompareSparkline({ prefix: UI_PREFIX });

export const MaintenanceSeriesSparkline = createDashboardSeriesSparkline({ prefix: UI_PREFIX });

export const MaintenanceTableFontSizeControls = createDashboardTableFontSizeControls({
  prefix: UI_PREFIX,
});

export const MaintenanceSegmentToggle = createDashboardSegmentToggle(UI_PREFIX);
