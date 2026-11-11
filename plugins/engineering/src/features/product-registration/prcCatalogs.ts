/** Catálogos oficiais da ficha técnica — máquina de estados explícita
 * por campo: `idle → loading → success | empty | error` (+ retry).
 *
 * Regras do contrato de UI:
 * - array vazio é estado `empty` legítimo, nunca erro de integração;
 * - `error` expõe retry e preserva o valor já selecionado;
 * - request obsoleta (retry/unmount/troca de etapa) é abortada e seu
 *   resultado nunca sobrescreve uma carga mais nova (guard por epoch);
 * - códigos são strings — zeros à esquerda preservados.
 *
 * Módulo framework-agnostic para ser testável sem DOM; o componente
 * assina via `useSyncExternalStore`. */

import {
  fetchPrcCatalog,
} from "./api/productRegistrationApi";

/* PRC-REF-023-F03 — helpers puros de catálogo migraram para
 * `@delpi/plugin-ui` (`utils/prcProductRegistration`), fonte única
 * compartilhada com Minhas Solicitações; o store com fetch injetável
 * permanece local. */
import {
  catalogOptions,
  enumOptions,
  PRC_CATALOG_KINDS,
  PrcCatalogStore as KitPrcCatalogStore,
  withSelectedOption,
  type PrcCatalogOption,
  type PrcCatalogStatus,
  type PrcCatalogView,
} from "@delpi/plugin-ui/index";

export { catalogOptions, enumOptions, PRC_CATALOG_KINDS, withSelectedOption };
export type { PrcCatalogOption, PrcCatalogStatus, PrcCatalogView };

export const PRC_CATALOG_PAGE_LIMIT = 500;

type FetchCatalog = typeof fetchPrcCatalog;

/** Compat: implementação canônica em `@delpi/plugin-ui`
 * (`utils/prcCatalogStore`) — esta subclasse só injeta o fetcher do
 * Portal Engenharia como padrão. Compartilhada com Minhas
 * Solicitações na UX-PARITY-FIX-02. */
export class PrcCatalogStore extends KitPrcCatalogStore {
  constructor(
    fetchCatalog: FetchCatalog = fetchPrcCatalog,
    limit: number = PRC_CATALOG_PAGE_LIMIT,
  ) {
    super(fetchCatalog, limit);
  }
}
