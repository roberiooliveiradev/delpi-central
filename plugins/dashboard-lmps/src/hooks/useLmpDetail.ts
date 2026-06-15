import { useCallback, useEffect, useState } from "react";

import {
  getLmpBySaleNumber,
  getLmpHistoryEvents,
  getLmpHistoryFlow,
} from "../api/lmpApi";
import type { LmpDetailData } from "../types/lmp";
import type { LmpsFilterUrlState } from "../utils/filterUrl";
import { mergeHistoryFlowIntoEvents } from "../utils/historyFormatting";
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
      const requestParams = {
        date_start: toLmpApiDate(filters.dateStart),
        date_end: toLmpApiDate(filters.dateEnd),
        branch: options.branch || resolveLmpsBranchFilter(filters) || undefined,
      };

      const [detail, historyResponse, flowResponse] = await Promise.all([
        getLmpBySaleNumber(saleNumber, requestParams),
        getLmpHistoryEvents(saleNumber, requestParams),
        getLmpHistoryFlow(saleNumber, requestParams),
      ]);

      setData({
        ...detail,
        reference_revision:
          detail.reference_revision ?? historyResponse.reference_revision,
        list_history: mergeHistoryFlowIntoEvents(
          historyResponse.items ?? [],
          flowResponse.items ?? [],
        ),
      });
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
