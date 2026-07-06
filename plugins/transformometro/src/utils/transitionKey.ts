import { normalizeTransformometroPath } from "./routeParser";

/** Chave estável para animar troca de rota no MFE. */
export function buildTransformometroTransitionKey(pathname: string): string {
  return normalizeTransformometroPath(pathname);
}
