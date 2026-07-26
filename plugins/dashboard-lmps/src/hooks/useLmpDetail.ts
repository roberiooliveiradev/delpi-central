import { useCallback, useEffect, useState } from "react";

import {
  getLmpBySaleNumber,
  getLmpHistoryEvents,
  getLmpHistoryFlow,
} from "../api/lmpApi";
import type { LmpDetailData } from "../types/lmp";
import type { LmpDetailRequestScope } from "./useLmpDetailRequestScope";
import { mergeHistoryFlowIntoEvents } from "../utils/historyFormatting";
import { toLmpApiDate } from "../utils/filterUrl";

function isAbortError(reason: unknown): boolean {
  return (
    reason instanceof DOMException && reason.name === "AbortError"
  );
}

export function useLmpDetail(
  saleNumber: string,
  requestScope: LmpDetailRequestScope,
) {
  const [data, setData] = useState<LmpDetailData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [reloadKey, setReloadKey] = useState(0);

  const reload = useCallback(() => {
    setReloadKey((prev) => prev + 1);
  }, []);

  useEffect(() => {
    const controller = new AbortController();

    async function run() {
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
          start_date: toLmpApiDate(requestScope.dateStart),
          end_date: toLmpApiDate(requestScope.dateEnd),
          branch: requestScope.branch,
        };

        const [detailResult, historyResult, flowResult] = await Promise.allSettled([
          getLmpBySaleNumber(saleNumber, requestParams, controller.signal),
          getLmpHistoryEvents(saleNumber, requestParams, controller.signal),
          getLmpHistoryFlow(saleNumber, requestParams, controller.signal),
        ]);

        if (controller.signal.aborted) return;

        if (detailResult.status === "rejected") {
          if (isAbortError(detailResult.reason)) return;
          throw detailResult.reason;
        }

        const detail = detailResult.value;
        const historyItems =
          historyResult.status === "fulfilled" ? historyResult.value.items ?? [] : [];
        const flowItems =
          flowResult.status === "fulfilled" ? flowResult.value.items ?? [] : [];
        const referenceRevision =
          historyResult.status === "fulfilled"
            ? historyResult.value.reference_revision
            : detail.reference_revision;

        setData({
          ...detail,
          reference_revision: detail.reference_revision ?? referenceRevision,
          list_history: mergeHistoryFlowIntoEvents(historyItems, flowItems),
        });
      } catch (reason) {
        if (controller.signal.aborted || isAbortError(reason)) return;

        setData(null);
        setError(
          reason instanceof Error
            ? reason.message
            : "Não foi possível carregar o detalhe da OV."
        );
      } finally {
        if (!controller.signal.aborted) {
          setLoading(false);
        }
      }
    }

    void run();

    return () => controller.abort();
  }, [
    saleNumber,
    requestScope.dateStart,
    requestScope.dateEnd,
    requestScope.branch,
    reloadKey,
  ]);

  return {
    data,
    item: data,
    loading,
    error,
    reload,
  };
}
