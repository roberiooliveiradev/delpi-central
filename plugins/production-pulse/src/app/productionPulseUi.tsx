import type { ComponentProps, ReactNode } from "react";
import {
  ActionButton,
  createCompactPagination,
  createHostContainedModalShell,
  catalogSearchBarBemClasses,
  createDashboardCatalogSearchBar,
  createDashboardDataRecordCard,
  createDashboardFormActions,
  createDashboardFormGrid,
  createDashboardPagePath,
  createDashboardSectionCard,
  createDashboardSegmentToggle,
  createDashboardUnderlineNav,
  createSimpleKpiCard,
  createStateBoxPanel,
  FieldLabel,
  PageHero,
  pageHeroBemClasses,
  sectionCardPacBemClasses,
  formActionsBemClasses,
  formGridBemClasses,
  type StateBoxVariant,
} from "@delpi/plugin-ui/index";
import { Activity, AlertTriangle, FileQuestion, Loader2 } from "lucide-react";

const PREFIX = "pp";
const PP_PORTAL_SCOPE = "dashboard-production-pulse";

export const PpHostContainedDialog = createHostContainedModalShell({
  prefix: PREFIX,
  portalScopeClassName: PP_PORTAL_SCOPE,
  containedLayout: "dialog",
});

export function PpPageHero(props: ComponentProps<typeof PageHero>) {
  return <PageHero {...props} classNames={pageHeroBemClasses(PREFIX)} density="compact" />;
}

export const PpStateBox = createStateBoxPanel({
  prefix: PREFIX,
  renderIcon: (variant: StateBoxVariant) => {
    if (variant === "error") return <AlertTriangle size={22} />;
    if (variant === "empty") return <FileQuestion size={22} />;
    return <Loader2 size={22} />;
  },
});

export const PpActionButton = ActionButton;
export const PpPagePath = createDashboardPagePath({
  prefix: PREFIX,
  portalScopeClassName: PP_PORTAL_SCOPE,
});
export const PpFieldLabel = FieldLabel;
export const PpSimpleKpiCard = createSimpleKpiCard(PREFIX, { withBody: true, withSubtitle: true });
export const PpSegmentToggle = createDashboardSegmentToggle(PREFIX);
export const PpCatalogSearchBar = createDashboardCatalogSearchBar({
  classNames: catalogSearchBarBemClasses(PREFIX),
});
export const PpSectionCard = createDashboardSectionCard({
  classNames: sectionCardPacBemClasses(PREFIX),
  labels: { titleHelpAriaLabel: (title: string) => `Ajuda: ${title}` },
});
export const PpFormGrid = createDashboardFormGrid({ classNames: formGridBemClasses(PREFIX) });
export const PpFormActions = createDashboardFormActions({ classNames: formActionsBemClasses(PREFIX) });
export const PpUnderlineNav = createDashboardUnderlineNav({ prefix: PREFIX });
export const PpPagination = createCompactPagination({
  prefix: PREFIX,
  layout: "flat",
  labels: {
    info: ({ page, totalPages, total }) =>
      `Página ${page} de ${totalPages} · ${total.toLocaleString("pt-BR")} registro(s)`,
    previous: "Anterior",
    next: "Próxima",
    navigationAriaLabel: "Paginação",
  },
});

export const PpDataRecordCard = createDashboardDataRecordCard({ prefix: PREFIX });

export const ppShellIcon = <Activity size={28} strokeWidth={1.75} />;

export {
  PpChartCard,
  PpReadingsAreaChart,
  buildPpReadingsChartSeries,
  formatPpReadingsChartValue,
  readingsToComparativeData,
  readingsToSeriesPoints,
  type PpReadingsChartVariant,
} from "../components/data/ppCharts";
export { PpDataTable, type DataTableColumn } from "../components/data/dataTableUi";
export {
  PpFilterInputField,
  PpFilterSelectField,
  PpFiltersRow,
  PpFilterToolbarRowClasses,
} from "../components/data/filtersUi";
export {
  PpFormFieldShell,
  PpNativeInlineTextField,
  PpNativeSelectField,
  PpNativeSwitchField,
  PpNativeTextAreaField,
  PpNativeTextField,
  ppFieldError,
  ppFieldHint,
} from "../components/data/ppFormFields";
