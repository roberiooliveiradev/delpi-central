import { useMemo } from "react";

import type { OpenOrdersTotvsItem } from "../types/openOrdersTotvs";
import {
  customerAvatarKey,
  useCustomerAvatarPresence,
  type CustomerAvatarPresenceMap,
} from "./useCustomerAvatarPresence";

export type OpenOrdersCustomerAvatarMap = CustomerAvatarPresenceMap;
export { customerAvatarKey };

/**
 * Cruza código+loja das linhas com enrichment da carteira (has_avatar),
 * no mesmo fluxo da lista de clientes.
 */
export function useOpenOrdersCustomerAvatars(
  rows: OpenOrdersTotvsItem[],
): OpenOrdersCustomerAvatarMap {
  const pairs = useMemo(() => {
    const seen = new Set<string>();
    const out: Array<{ customer_code: string; customer_store: string }> = [];
    for (const row of rows) {
      const code = row.codigo_cadastro?.trim();
      const store = row.loja_cadastro?.trim();
      if (!code || !store) continue;
      const key = customerAvatarKey(code, store);
      if (seen.has(key)) continue;
      seen.add(key);
      out.push({ customer_code: code, customer_store: store });
    }
    return out;
  }, [rows]);

  return useCustomerAvatarPresence(pairs);
}
