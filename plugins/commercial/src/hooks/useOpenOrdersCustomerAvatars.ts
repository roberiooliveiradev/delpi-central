import { useEffect, useMemo, useState } from "react";

import { enrichPortfolioCustomers } from "../api/customerEnrichmentApi";
import type { OpenOrdersTotvsItem } from "../types/openOrdersTotvs";

export type OpenOrdersCustomerAvatarMap = Map<string, boolean>;

export function customerAvatarKey(code: string, store: string): string {
  return `${code.trim()}|${store.trim()}`;
}

/**
 * Cruza código+loja das linhas com enrichment da carteira (has_avatar),
 * no mesmo fluxo da lista de clientes.
 */
export function useOpenOrdersCustomerAvatars(
  rows: OpenOrdersTotvsItem[],
): OpenOrdersCustomerAvatarMap {
  const [map, setMap] = useState<OpenOrdersCustomerAvatarMap>(() => new Map());

  const keys = useMemo(() => {
    const seen = new Set<string>();
    const pairs: Array<{ customer_code: string; customer_store: string }> = [];
    for (const row of rows) {
      const code = row.codigo_cadastro?.trim();
      const store = row.loja_cadastro?.trim();
      if (!code || !store) continue;
      const key = customerAvatarKey(code, store);
      if (seen.has(key)) continue;
      seen.add(key);
      pairs.push({ customer_code: code, customer_store: store });
    }
    return pairs;
  }, [rows]);

  const keysSig = keys.map((p) => `${p.customer_code}|${p.customer_store}`).join(",");

  useEffect(() => {
    if (keys.length === 0) {
      setMap(new Map());
      return;
    }
    const controller = new AbortController();
    void enrichPortfolioCustomers(keys, controller.signal)
      .then((items) => {
        if (controller.signal.aborted) return;
        const next = new Map<string, boolean>();
        for (const item of items) {
          const code = item.customer_code?.trim();
          const store = item.customer_store?.trim();
          if (!code || !store) continue;
          next.set(customerAvatarKey(code, store), Boolean(item.has_avatar));
        }
        setMap(next);
      })
      .catch(() => {
        if (!controller.signal.aborted) setMap(new Map());
      });
    return () => controller.abort();
  }, [keysSig]);

  return map;
}
