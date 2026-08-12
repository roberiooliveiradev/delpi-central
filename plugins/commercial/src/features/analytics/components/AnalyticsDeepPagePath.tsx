import { CommercialPagePath } from "../../../app/commercialUi";
import { navigatePluginView } from "../../../app/pluginNavigation";
import { ANALYTICS_CONTENT } from "../../../content/analyticsContent";

type AnalyticsDeepPagePathProps = {
  basePath: string;
  current: string;
  /** Origem: Visão geral (drills) ou Início (launcher). Default overview. */
  backTo?: "overview" | "home";
};

/** Breadcrumb das páginas profundas (OTD / Opp / Equipe) — fora da top nav. */
export function AnalyticsDeepPagePath({
  basePath,
  current,
  backTo = "overview",
}: AnalyticsDeepPagePathProps) {
  const backLabel =
    backTo === "home" ? "Portal Comercial" : ANALYTICS_CONTENT.overview.title;
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
      current={current}
    />
  );
}
