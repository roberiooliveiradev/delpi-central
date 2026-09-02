import type { ComponentProps, ReactNode } from "react";
import {
  ActionButton,
  BackLink,
  ChartCard,
  chartCardBemClasses,
  createCompactPagination,
  createHostContainedModalShell,
  catalogSearchBarBemClasses,
  createDashboardCatalogSearchBar,
  createDashboardFormActions,
  createDashboardFormGrid,
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
export const PpBackLink = BackLink;
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

const CHART_CARD_CLASSES = chartCardBemClasses(PREFIX, { headerLayout: "titleRow" });

type PpChartCardProps = {
  title: string;
  hint?: string;
  titleHint?: string;
  children: ReactNode;
  headerActions?: ReactNode;
};

export function PpChartCard({ title, hint, titleHint, children, headerActions }: PpChartCardProps) {
  return (
    <ChartCard
      title={title}
      hint={hint}
      titleHint={titleHint}
      headerActions={headerActions}
      classNames={CHART_CARD_CLASSES}
    >
      {children}
    </ChartCard>
  );
}

export const ppShellIcon = <Activity size={28} strokeWidth={1.75} />;
