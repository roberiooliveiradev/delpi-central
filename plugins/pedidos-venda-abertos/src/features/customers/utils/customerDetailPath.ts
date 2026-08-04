import {
  buildCustomerKey,
  normalizeCadastroPart,
} from "./customerIdentity.ts";
import { normalizeBasePath } from "../../../app/pluginRoutes.ts";

/**
 * Constrói `/base/clientes/:codigo/:loja` com encode seguro por segmento.
 * Retorna null se código ou loja forem inválidos (impede rota incompleta).
 * Preserva zeros à esquerda (sem conversão numérica).
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
  return `${base}/clientes/${encodeURIComponent(normalizedCodigo)}/${encodeURIComponent(normalizedLoja)}`;
}
