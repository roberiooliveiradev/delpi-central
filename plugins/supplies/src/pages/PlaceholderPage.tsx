import { SP_HELP } from "../content/helpTooltips";
import { navigatePluginView } from "../app/pluginNavigation";
import {
  SuppliesEmptyState,
  SuppliesPageHero,
  SuppliesPagePath,
  SuppliesTitleWithHelp,
} from "../app/suppliesUi";
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
      <SuppliesPageHero
        title={<SuppliesTitleWithHelp title={title} hint={SP_HELP.homeVsOverview} />}
        description={description}
      />
      <SuppliesEmptyState message="Conteúdo desta área será entregue na próxima etapa do portal." />
    </div>
  );
}
