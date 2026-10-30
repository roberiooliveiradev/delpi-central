import { navigateEngineeringView } from "../../app/engineeringRoutes";
import {
  EngineeringActionButton,
  EngineeringEmptyState,
} from "../../ui/engineeringUi";
import { resolveProductsPath } from "./productRoutes";
import { ProductsListPage } from "./pages/ProductsListPage";
import { ProductDetailPage } from "./pages/ProductDetailPage";

type ProductsFeatureProps = {
  /** Caminho relativo sob `/apps/engineering` (ex.: `products/{code}`). */
  relativePath: string;
};

/** Raiz da feature Produtos — bounded context próprio do Portal
 * Engenharia (doc 61/63): caminho standalone
 * `/apps/engineering/products`, dados oficiais delegados pela
 * Engineering API ao owner API DELPI/TOTVS. */
export function ProductsFeature({ relativePath }: ProductsFeatureProps) {
  const route = resolveProductsPath(relativePath);

  if (route.kind === "detail") {
    return <ProductDetailPage code={route.code} />;
  }
  if (route.kind === "list") return <ProductsListPage />;

  return (
    <main className="engineering-products">
      <EngineeringEmptyState message="Este endereço não corresponde a uma página de produtos.">
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
