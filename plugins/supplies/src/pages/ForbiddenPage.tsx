import { SP_HELP } from "../content/helpTooltips";
import { navigatePluginView } from "../app/pluginNavigation";
import { SuppliesEmptyState } from "../app/suppliesUi";

type ForbiddenPageProps = {
  basePath: string;
};

export function ForbiddenPage({ basePath }: ForbiddenPageProps) {
  return (
    <SuppliesEmptyState title="Sem permissão" message={SP_HELP.forbiddenUnit} role="alert">
      <button type="button" onClick={() => navigatePluginView("help", { basePath })}>
        Abrir Ajuda
      </button>
    </SuppliesEmptyState>
  );
}
