import { CommercialUnderlineNav } from "../../app/commercialUi";
import { navigatePluginView } from "../../app/pluginNavigation";
import type { PluginNavigationTarget } from "../../app/pluginRoutes";
import { ADMINISTRATION_CONTENT } from "../../content/administration";

export type AdministrationTabId = "panel" | "portfolios" | "team" | "groups";

const TAB_TO_VIEW: Record<AdministrationTabId, PluginNavigationTarget> = {
  panel: "administration",
  portfolios: "administration_portfolios",
  team: "administration_team",
  groups: "administration_groups",
};

type AdministrationSubNavProps = {
  basePath: string;
  active: AdministrationTabId;
};

export function AdministrationSubNav({ basePath, active }: AdministrationSubNavProps) {
  const items: Array<{ id: AdministrationTabId; label: string }> = [
    { id: "panel", label: ADMINISTRATION_CONTENT.panel.navLabel },
    { id: "portfolios", label: ADMINISTRATION_CONTENT.portfolios.navLabel },
    { id: "team", label: ADMINISTRATION_CONTENT.team.navLabel },
    { id: "groups", label: ADMINISTRATION_CONTENT.groups.navLabel },
  ];

  return (
    <CommercialUnderlineNav
      mode="tabs"
      activeId={active}
      aria-label={ADMINISTRATION_CONTENT.subnavAriaLabel}
      items={items.map((item) => ({
        id: item.id,
        label: item.label,
        onSelect: () => {
          if (item.id === active) return;
          navigatePluginView(TAB_TO_VIEW[item.id], { basePath });
        },
      }))}
    />
  );
}
