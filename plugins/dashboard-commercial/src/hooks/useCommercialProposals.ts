import { useCallback, useEffect, useState } from "react";

import { getCommercialProposals } from "../api/commercialApi";
import { formatCommercialApiError } from "../utils/formatCommercialApiError";
import type {
  CommercialFilterParams,
  CommercialProposal,
  CommercialProposalStatusFilter,
} from "../types/commercial";

type UseCommercialProposalsResult = {
  items: CommercialProposal[];
  total: number;
  loading: boolean;
  refreshing: boolean;
  error: string | null;
  reload: () => void;
};

export function useCommercialProposals(
  filters: CommercialFilterParams,
  statusFilter: CommercialProposalStatusFilter = "all"
): UseCommercialProposalsResult {
  const [items, setItems] = useState<CommercialProposal[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [reloadKey, setReloadKey] = useState(0);

  useEffect(() => {
    const controller = new AbortController();

    async function run() {
      try {
        setError(null);

        const hasPreviousData = items.length > 0;
        if (hasPreviousData) {
          setRefreshing(true);
        } else {
          setLoading(true);
        }

        const page = await getCommercialProposals(
          {
            ...filters,
            status: statusFilter === "all" ? undefined : statusFilter,
            page: 1,
            page_size: 200,
          },
          controller.signal
        );

        if (!controller.signal.aborted) {
          setItems(page.items);
          setTotal(page.total);
        }
      } catch (cause) {
        if (!controller.signal.aborted) {
          setItems([]);
          setTotal(0);
          setError(
            formatCommercialApiError(cause) ||
              "Não foi possível carregar as propostas."
          );
        }
      } finally {
        if (!controller.signal.aborted) {
          setLoading(false);
          setRefreshing(false);
        }
      }
    }

    void run();

    return () => controller.abort();
  }, [
    filters.branch,
    filters.customer_segment,
    filters.end_date,
    filters.start_date,
    statusFilter,
    reloadKey,
  ]);

  const reload = useCallback(() => {
    setReloadKey((prev) => prev + 1);
  }, []);

  return { items, total, loading, refreshing, error, reload };
}
