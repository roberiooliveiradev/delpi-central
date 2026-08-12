import { useEffect, useMemo, useState } from "react";

import { lookupCustomerSharedCoverage } from "../../../api/commercialPortfolioApi";
import type { CustomerSharedCoverageItem } from "../../../types/portfolio";
import { customerKey } from "../../../shared/format";
import { sharedCoverageByCustomerKey } from "../../../utils/portfolioCoverage";

const BATCH_SIZE = 200;

export type CustomerSharedCoverageKey = {
  codigo: string;
  loja: string;
};

export type UseCustomerSharedCoverageResult = {
  byKey: Map<string, CustomerSharedCoverageItem>;
  loading: boolean;
  error: string | null;
};

function stableCustomerFingerprint(
  customers: readonly CustomerSharedCoverageKey[],
): string {
  return customers
    .map((item) => customerKey(item.codigo, item.loja))
    .filter((key) => key !== "|")
    .sort()
    .join(",");
}

/**
 * Batch lookup de clientes em 2+ carteiras do escopo (E6.4).
 */
export function useCustomerSharedCoverage(
  customers: readonly CustomerSharedCoverageKey[],
  portfolioIds: readonly string[],
): UseCustomerSharedCoverageResult {
  const [byKey, setByKey] = useState<Map<string, CustomerSharedCoverageItem>>(
    () => new Map(),
  );
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const customersFingerprint = useMemo(
    () => stableCustomerFingerprint(customers),
    [customers],
  );
  const portfolioFingerprint = useMemo(
    () =>
      [...new Set(portfolioIds.map((id) => id.trim()).filter(Boolean))]
        .sort()
        .join(","),
    [portfolioIds],
  );

  useEffect(() => {
    const keys = customersFingerprint
      ? customersFingerprint.split(",").filter(Boolean)
      : [];
    if (keys.length === 0) {
      setByKey(new Map());
      setLoading(false);
      setError(null);
      return;
    }

    const controller = new AbortController();
    const payloadCustomers = keys.map((key) => {
      const [customer_code = "", customer_store = ""] = key.split("|");
      return { customer_code, customer_store };
    });
    const scopeIds = portfolioFingerprint
      ? portfolioFingerprint.split(",").filter(Boolean)
      : [];

    async function run() {
      setLoading(true);
      setError(null);
      try {
        const items: CustomerSharedCoverageItem[] = [];
        for (let index = 0; index < payloadCustomers.length; index += BATCH_SIZE) {
          const chunk = payloadCustomers.slice(index, index + BATCH_SIZE);
          const result = await lookupCustomerSharedCoverage(
            {
              customers: chunk,
              portfolio_ids: scopeIds,
            },
            controller.signal,
          );
          items.push(...(result.items ?? []));
        }
        if (controller.signal.aborted) return;
        setByKey(sharedCoverageByCustomerKey(items));
      } catch (err: unknown) {
        if (controller.signal.aborted) return;
        setByKey(new Map());
        setError(
          err instanceof Error
            ? err.message
            : "Erro ao carregar cobertura compartilhada.",
        );
      } finally {
        if (!controller.signal.aborted) setLoading(false);
      }
    }

    void run();
    return () => controller.abort();
  }, [customersFingerprint, portfolioFingerprint]);

  return { byKey, loading, error };
}
