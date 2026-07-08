import { normalizeTransformometroPath, parseTransformometroPath } from "./routeParser";
import { TRANSFORMOMETRO_ROUTES } from "../constants/routes";

/** Chave estável para animar troca de rota no MFE. */
export function buildTransformometroTransitionKey(pathname: string): string {
  const route = parseTransformometroPath(pathname);
  if (
    route.processoId &&
    (route.view === "processo" || route.view === "instancia" || route.view === "revisao")
  ) {
    return normalizeTransformometroPath(`${TRANSFORMOMETRO_ROUTES.processos}/${route.processoId}`);
  }
  if (
    route.view === "configuracoes" ||
    route.view === "filial" ||
    route.view === "setor" ||
    route.view === "recurso"
  ) {
    return normalizeTransformometroPath(TRANSFORMOMETRO_ROUTES.configuracoes);
  }
  return normalizeTransformometroPath(pathname);
}
