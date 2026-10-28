import {
  navigateEngineeringView,
  navigateGovernedHref,
} from "./engineeringRoutes";
import type { CatalogRoute } from "../content/engineeringRouteCatalog";

/** Abre uma rota do catálogo — interna via pushState do host, externa
 * via href oficial `/apps/...`; destino futuro não é executável. */
export function openCatalogRoute(route: CatalogRoute, basePath: string): void {
  if (route.comingSoon) return;
  if (route.target.kind === "internal") {
    navigateEngineeringView(route.target.view, { basePath });
    return;
  }
  navigateGovernedHref(route.target.href);
}
