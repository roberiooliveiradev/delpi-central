import {
  buildCustomerKey,
  normalizeCadastroPart,
} from "./customerIdentity.ts";
import { normalizeBasePath } from "../../../app/pluginRoutes.ts";

/**
 * Constrói `/base/customers/:codigo/:loja` (rotas EN do Portal Comercial).
 */
export function buildCustomerDetailPath(
  basePath: string | undefined,
  codigo: string | null | undefined,
  loja: string | null | undefined,
): string | null {
  const key = buildCustomerKey(codigo, loja);
  if (!key) return null;
  const normalizedCodigo = normalizeCadastroPart(codigo);
  const normalizedLoja = normalizeCadastroPart(loja);
  const base = normalizeBasePath(basePath);
  return `${base}/customers/${encodeURIComponent(normalizedCodigo)}/${encodeURIComponent(normalizedLoja)}`;
}
