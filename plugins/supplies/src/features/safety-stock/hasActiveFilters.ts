import { createDefaultQuery } from "./query";
import type { SafetyStockQuery } from "./types";

/** Limpar volta ao padrão: filial «all», sem status/grupo/UM/busca e toggles padrão. */
export function hasActiveSafetyStockFilters(query: SafetyStockQuery): boolean {
  const defaults = createDefaultQuery();
  return Boolean(
    query.branch !== defaults.branch ||
      query.status !== defaults.status ||
      query.productGroup.trim() !== defaults.productGroup ||
      query.unit.trim() !== defaults.unit ||
      query.search.trim() !== defaults.search ||
      query.includeBlocked !== defaults.includeBlocked ||
      query.includeWithoutSafetyStock !== defaults.includeWithoutSafetyStock,
  );
}
