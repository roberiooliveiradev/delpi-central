import { useEffect } from "react";

import { CommercialLoadingCard } from "../../app/commercialUi";
import { navigatePluginView } from "../../app/pluginNavigation";

type AnalyticsTeamRedirectProps = {
  basePath: string;
};

/** Equipe depreciada: redirect canônico para Administração. */
export function AnalyticsTeamRedirect({ basePath }: AnalyticsTeamRedirectProps) {
  useEffect(() => {
    navigatePluginView("administration", { basePath, replace: true });
  }, [basePath]);

  return <CommercialLoadingCard title="Redirecionando para Administração…" variant="panel" />;
}
