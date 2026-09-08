import { SP_HELP } from "../content/helpTooltips";
import { navigatePluginView } from "../app/pluginNavigation";
import { SuppliesPagePath } from "../app/suppliesUi";
import { buildPluginPath } from "../app/pluginRoutes";

type HelpPageProps = {
  basePath: string;
};

export function HelpPage({ basePath }: HelpPageProps) {
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
        current="Ajuda"
      />
      <article className="sp-help">
        <h1>Ajuda do Portal Suprimentos</h1>
        <section>
          <h2>Portal vs apps antigos</h2>
          <p>{SP_HELP.coexistence}</p>
        </section>
        <section>
          <h2>Início vs Visão geral</h2>
          <p>{SP_HELP.homeVsOverview}</p>
        </section>
        <section>
          <h2>Sem permissão (403)</h2>
          <p>{SP_HELP.forbiddenUnit}</p>
        </section>
      </article>
    </div>
  );
}
