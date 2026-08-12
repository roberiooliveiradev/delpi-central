import { CommercialUnderlineNav } from "../../../app/commercialUi";
import { usePortfolioScope } from "../../../app/PortfolioScopeContext";
import { navigatePluginView } from "../../../app/pluginNavigation";
import type { PluginView } from "../../../app/pluginRoutes";
import { ANALYTICS_CONTENT } from "../../../content/analyticsContent";

type AnalyticsSubNavProps = {
  view: PluginView;
  basePath: string;
};

const BASE_ITEMS = [
  { id: "analytics" as const, label: ANALYTICS_CONTENT.nav.overview },
  { id: "analytics_otd" as const, label: ANALYTICS_CONTENT.nav.otd },
  { id: "analytics_opportunities" as const, label: ANALYTICS_CONTENT.nav.oportunidades },
];

function resolveActiveId(
  view: PluginView,
): "analytics" | "analytics_otd" | "analytics_team" | "analytics_opportunities" {
  if (view === "analytics_otd" || view === "analytics_otd_line") return "analytics_otd";
  if (view === "analytics_team") return "analytics_team";
  if (view === "analytics_opportunities" || view === "analytics_opportunity_detail") {
    return "analytics_opportunities";
  }
  return "analytics";
}

export function AnalyticsSubNav({ view, basePath }: AnalyticsSubNavProps) {
  const { canUseTeamScope } = usePortfolioScope();
  const activeId = resolveActiveId(view);
  const search =
    typeof window !== "undefined" ? window.location.search || undefined : undefined;

  const items = [
    ...BASE_ITEMS.slice(0, 2),
    ...(canUseTeamScope
      ? [{ id: "analytics_team" as const, label: ANALYTICS_CONTENT.nav.equipe }]
      : []),
    ...BASE_ITEMS.slice(2),
  ];

  return (
    <CommercialUnderlineNav
      aria-label="Áreas de gestão"
      activeId={activeId}
      items={items.map((item) => ({
        id: item.id,
        label: item.label,
        onSelect: () =>
          navigatePluginView(item.id, {
            basePath,
            search,
          }),
      }))}
    />
  );
}
