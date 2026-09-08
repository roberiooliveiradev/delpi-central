import { HelpTooltip } from "@delpi/plugin-ui/index";

import { SP_HELP } from "../content/helpTooltips";
import { navigatePluginView } from "../app/pluginNavigation";
import { SuppliesEmptyState, SuppliesPagePath } from "../app/suppliesUi";
import { buildPluginPath } from "../app/pluginRoutes";

type PlaceholderPageProps = {
  basePath: string;
  title: string;
  description: string;
};

export function PlaceholderPage({ basePath, title, description }: PlaceholderPageProps) {
  const homeHref = buildPluginPath("home", basePath);
  return (
    <div className="sp-page-stack">
      <SuppliesPagePath
        back={{
          label: "Início",
          href: homeHref,
          onNavigate: (event) => {
            event.preventDefault();
            navigatePluginView("home", { basePath });
          },
        }}
        items={[]}
        current={title}
      />
      <SuppliesEmptyState title={title} message={description}>
        <HelpTooltip content={SP_HELP.homeVsOverview} ariaLabel="Ajuda: Início vs Visão geral" />
      </SuppliesEmptyState>
    </div>
  );
}
