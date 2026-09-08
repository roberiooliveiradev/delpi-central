import { navigatePluginView } from "../app/pluginNavigation";
import { SuppliesEmptyState } from "../app/suppliesUi";

type NotFoundPageProps = {
  basePath: string;
};

export function NotFoundPage({ basePath }: NotFoundPageProps) {
  return (
    <SuppliesEmptyState
      title="Página não encontrada"
      message="Este caminho não existe no Portal Suprimentos."
      role="alert"
    >
      <button type="button" onClick={() => navigatePluginView("home", { basePath })}>
        Voltar ao Início
      </button>
    </SuppliesEmptyState>
  );
}
