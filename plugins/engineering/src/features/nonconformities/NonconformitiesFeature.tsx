import { navigateEngineeringView } from "../../app/engineeringRoutes";
import {
  EngineeringActionButton,
  EngineeringEmptyState,
} from "../../ui/engineeringUi";
import { resolveNcPath } from "./nonconformityRoutes";
import { NonconformitiesListPage } from "./pages/NonconformitiesListPage";
import { NonconformityDetailPage } from "./pages/NonconformityDetailPage";
import { NonconformityFormPage } from "./pages/NonconformityFormPage";

type NonconformitiesFeatureProps = {
  /** Caminho relativo sob `/apps/engineering` (ex.: `nonconformities/{id}`). */
  relativePath: string;
};

/** Raiz da feature Não Conformidades — bounded context próprio do
 * Portal Engenharia (doc 45): caminho standalone
 * `/apps/engineering/nonconformities`, nunca sob `/lmps`. */
export function NonconformitiesFeature({
  relativePath,
}: NonconformitiesFeatureProps) {
  const route = resolveNcPath(relativePath);

  if (route.kind === "new") return <NonconformityFormPage mode="create" />;
  if (route.kind === "detail") {
    return <NonconformityDetailPage recordId={route.recordId} />;
  }
  if (route.kind === "edit") {
    return <NonconformityFormPage mode="edit" recordId={route.recordId} />;
  }
  if (route.kind === "list") return <NonconformitiesListPage />;

  return (
    <main className="engineering-nonconformities">
      <EngineeringEmptyState message="Este endereço não corresponde a uma página de não conformidades.">
        <EngineeringActionButton
          variant="primary"
          onClick={() => navigateEngineeringView("home")}
        >
          Voltar ao Início
        </EngineeringActionButton>
      </EngineeringEmptyState>
    </main>
  );
}
