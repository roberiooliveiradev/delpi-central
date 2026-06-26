import { useCallback, useEffect, useState } from "react";

import {
  getCommercialProposalByNumber,
  getCommercialProposalHistoryEvents,
} from "../api/commercialApi";
import type { CommercialProposalDetailData } from "../types/commercial";
import type { CommercialDetailRequestScope } from "./useCommercialDetailRequestScope";

function isAbortError(reason: unknown): boolean {
  return reason instanceof DOMException && reason.name === "AbortError";
}

export function useCommercialProposalDetail(
  proposalNumber: string,
  requestScope: CommercialDetailRequestScope
) {
  const [data, setData] = useState<CommercialProposalDetailData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [reloadKey, setReloadKey] = useState(0);

  const reload = useCallback(() => {
    setReloadKey((prev) => prev + 1);
  }, []);

  useEffect(() => {
    const controller = new AbortController();

    async function run() {
      if (!proposalNumber.trim()) {
        setData(null);
        setError("Número da proposta inválido.");
        setLoading(false);
        return;
      }

      if (!requestScope.branch) {
        setData(null);
        setError("Unidade da proposta não informada na URL.");
        setLoading(false);
        return;
      }

      setLoading(true);
      setError(null);

      try {
        const detailParams = {
          branch: requestScope.branch,
          revision: requestScope.revision,
        };
        const historyParams = {
          ...detailParams,
          start_date: requestScope.dateStart,
          end_date: requestScope.dateEnd,
        };

        const [detailResult, historyResult] = await Promise.allSettled([
          getCommercialProposalByNumber(
            proposalNumber,
            detailParams,
            controller.signal
          ),
          getCommercialProposalHistoryEvents(
            proposalNumber,
            historyParams,
            controller.signal
          ),
        ]);

        if (controller.signal.aborted) return;

        if (detailResult.status === "rejected") {
          if (isAbortError(detailResult.reason)) return;
          throw detailResult.reason;
        }

        const historyItems =
          historyResult.status === "fulfilled"
            ? historyResult.value.items ?? []
            : [];

        setData({
          ...detailResult.value,
          list_history: historyItems,
        });
      } catch (reason) {
        if (controller.signal.aborted || isAbortError(reason)) return;

        setData(null);
        setError(
          reason instanceof Error
            ? reason.message
            : "Não foi possível carregar o detalhe da proposta."
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
    proposalNumber,
    requestScope.branch,
    requestScope.revision,
    requestScope.dateStart,
    requestScope.dateEnd,
    reloadKey,
  ]);

  return { data, loading, error, reload };
}
