import { useEffect, useMemo, useState } from "react";

import { getCommercialCustomerCenters } from "../../../api/analyticsApi";

export type AnalyticsCustomerCenterOption = {
  value: string;
  label: string;
};

function sellerScopeKey(sellerIds: string[]): string {
  return sellerIds
    .map((id) => id.trim())
    .filter(Boolean)
    .join(",");
}

/** Catálogo de centros distintos da SA7 no recorte de carteira (BFF). */
export function useAnalyticsCustomerCenterOptions(
  sellerIds: string[] | string | null | undefined,
): AnalyticsCustomerCenterOption[] {
  const [options, setOptions] = useState<AnalyticsCustomerCenterOption[]>([]);
  const scopeKey = sellerScopeKey(
    Array.isArray(sellerIds) ? sellerIds : sellerIds ? [sellerIds] : [],
  );

  useEffect(() => {
    const controller = new AbortController();
    void getCommercialCustomerCenters(
      { seller_id: scopeKey || undefined },
      controller.signal,
    )
      .then((data) => {
        if (controller.signal.aborted) return;
        const byCenter = new Map<string, AnalyticsCustomerCenterOption>();
        for (const item of data.items ?? []) {
          const center = (item.center || "").trim();
          if (!center || byCenter.has(center)) continue;
          const label = (item.label || "").trim() || center;
          byCenter.set(center, { value: center, label });
        }
        setOptions(
          [...byCenter.values()].sort((a, b) =>
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
