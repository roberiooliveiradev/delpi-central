import { useEffect, useMemo, useState } from "react";

import { enrichPortfolioCustomers } from "../api/customerEnrichmentApi";

export type CustomerAvatarPresenceMap = Map<string, boolean>;

export type CustomerCodeStorePair = {
  customer_code: string;
  customer_store: string;
};

export function customerAvatarKey(code: string, store: string): string {
  return `${code.trim()}|${store.trim()}`;
}

/**
 * Resolve `has_avatar` para pares código+loja via enrichment da carteira.
 */
export function useCustomerAvatarPresence(
  pairs: CustomerCodeStorePair[],
): CustomerAvatarPresenceMap {
  const [map, setMap] = useState<CustomerAvatarPresenceMap>(() => new Map());

  const keys = useMemo(() => {
    const seen = new Set<string>();
    const unique: CustomerCodeStorePair[] = [];
    for (const pair of pairs) {
      const code = pair.customer_code?.trim();
      const store = pair.customer_store?.trim();
      if (!code || !store) continue;
      const key = customerAvatarKey(code, store);
      if (seen.has(key)) continue;
      seen.add(key);
      unique.push({ customer_code: code, customer_store: store });
    }
    return unique;
  }, [pairs]);

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
