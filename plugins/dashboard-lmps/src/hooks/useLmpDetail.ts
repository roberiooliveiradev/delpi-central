import { useCallback, useEffect, useState } from "react";

import { getLmpBySaleNumber } from "../api/lmpApi";
import type { LmpDetailData } from "../types/lmp";
import type { LmpsFilterUrlState } from "../utils/filterUrl";
import { resolveLmpsBranchFilter, toLmpApiDate } from "../utils/filterUrl";

type UseLmpDetailOptions = {
  branch?: string;
};

export function useLmpDetail(
  saleNumber: string,
  filters: LmpsFilterUrlState,
  options: UseLmpDetailOptions = {}
) {
  const [data, setData] = useState<LmpDetailData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const reload = useCallback(async () => {
    if (!saleNumber.trim()) {
      setData(null);
      setError("Número da proposta inválido.");
      setLoading(false);
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const result = await getLmpBySaleNumber(saleNumber, {
        date_start: toLmpApiDate(filters.dateStart),
        date_end: toLmpApiDate(filters.dateEnd),
        branch: options.branch || resolveLmpsBranchFilter(filters) || undefined,
      });
      setData(result);
    } catch (reason) {
      setData(null);
      setError(
        reason instanceof Error
          ? reason.message
          : "Não foi possível carregar o detalhe da OV."
      );
    } finally {
      setLoading(false);
    }
  }, [saleNumber, filters.dateStart, filters.dateEnd, filters.branches, options.branch]);

  useEffect(() => {
    void reload();
  }, [reload]);

  return {
    data,
    item: data,
    loading,
    error,
    reload,
  };
}
