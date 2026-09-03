import { useEffect, useMemo, useState } from "react";

import { getCustomersInScope } from "../../../api/customersInScopeApi";

export type AnalyticsCustomerOption = {
  value: string;
  label: string;
};

function sellerScopeKey(sellerIds: string[]): string {
  return sellerIds.join(",");
}

/** Opções do filtro Cliente: códigos TOTVS únicos no recorte de carteira (BFF). */
export function useAnalyticsCustomerOptions(
  sellerIds: string[],
): AnalyticsCustomerOption[] {
  const [options, setOptions] = useState<AnalyticsCustomerOption[]>([]);
  const scopeKey = sellerScopeKey(sellerIds);

  useEffect(() => {
    const controller = new AbortController();
    void getCustomersInScope(controller.signal, {
      sellerId: scopeKey || null,
    })
      .then((data) => {
        if (controller.signal.aborted) return;
        const byCode = new Map<string, AnalyticsCustomerOption>();
        for (const item of data.items) {
          const code = item.customer_code.trim();
          if (!code || byCode.has(code)) continue;
          const name = item.customer_name?.trim() ?? "";
          byCode.set(code, {
            value: code,
            label: name ? `${name} (${code})` : code,
          });
        }
        setOptions(
          [...byCode.values()].sort((a, b) =>
            a.label.localeCompare(b.label, "pt-BR"),
          ),
        );
      })
      .catch(() => {
        if (!controller.signal.aborted) setOptions([]);
      });
    return () => controller.abort();
  }, [scopeKey]);

  return useMemo(() => options, [options]);
}
