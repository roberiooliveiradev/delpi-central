import { CommercialPagePath } from "../../../app/commercialUi";
import { navigatePluginView } from "../../../app/pluginNavigation";
import type { PluginNavigationTarget } from "../../../app/pluginRoutes";
import { ANALYTICS_CONTENT } from "../../../content/analyticsContent";
import { HUB_CONTENT, hubRouteLabelByView } from "../../../content/pluginRouteCatalog";

type AnalyticsDeepPagePathProps = {
  basePath: string;
  current: string;
  /** Origem: Visão geral (drills) ou Início (hub). Default overview. */
  backTo?: "overview" | "home";
  /** Quando informado, prioriza o label canônico do catálogo do hub. */
  viewId?: PluginNavigationTarget;
};

/** Breadcrumb das páginas profundas (OTD / Opp / Propostas) — fora da top nav. */
export function AnalyticsDeepPagePath({
  basePath,
  current,
  backTo = "overview",
  viewId,
}: AnalyticsDeepPagePathProps) {
  const catalogLabel = viewId ? hubRouteLabelByView(viewId) : undefined;
  const backLabel =
    backTo === "home" ? HUB_CONTENT.productName : ANALYTICS_CONTENT.overview.title;
  const backView = backTo === "home" ? "home" : "overview";

  return (
    <CommercialPagePath
      back={{
        label: backLabel,
        href: backTo === "home" ? basePath : `${basePath}/overview`,
        onNavigate: (event) => {
          event.preventDefault();
          navigatePluginView(backView, { basePath });
        },
      }}
      items={[]}
      current={catalogLabel ?? current}
    />
  );
}
