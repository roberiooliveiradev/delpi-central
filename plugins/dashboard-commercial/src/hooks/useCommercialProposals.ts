import { useCallback, useEffect, useRef, useState } from "react";

import { getCommercialProposals, resolveProposalSortApiKey } from "../api/commercialApi";
import { formatCommercialApiError } from "../utils/formatCommercialApiError";
import type {
  CommercialFilterParams,
  CommercialProposal,
  CommercialProposalStatusFilter,
} from "../types/commercial";
import type { ServerTableQuery } from "./useServerTable";

type UseCommercialProposalsOptions = {
  filters: CommercialFilterParams;
  statusFilter?: CommercialProposalStatusFilter;
  tableQuery: Pick<
    ServerTableQuery,
    "page" | "pageSize" | "sortKey" | "sortDirection"
  >;
};

type UseCommercialProposalsResult = {
  items: CommercialProposal[];
  total: number;
  page: number;
  pageSize: number;
  loading: boolean;
  refreshing: boolean;
  error: string | null;
  reload: () => void;
};

export function useCommercialProposals({
  filters,
  statusFilter = "all",
  tableQuery,
}: UseCommercialProposalsOptions): UseCommercialProposalsResult {
  const [items, setItems] = useState<CommercialProposal[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(tableQuery.pageSize);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [reloadKey, setReloadKey] = useState(0);
  const hasLoadedRef = useRef(false);

  useEffect(() => {
    const controller = new AbortController();

    async function run() {
      try {
        setError(null);

        if (hasLoadedRef.current) {
          setRefreshing(true);
        } else {
          setLoading(true);
        }

        const result = await getCommercialProposals(
          {
            ...filters,
            status: statusFilter === "all" ? undefined : statusFilter,
            page: tableQuery.page,
            page_size: tableQuery.pageSize,
            sort_by: resolveProposalSortApiKey(tableQuery.sortKey),
            sort_dir: tableQuery.sortDirection,
          },
          controller.signal
        );

        if (!controller.signal.aborted) {
          setItems(result.items);
          setTotal(result.total);
          setPage(result.page);
          setPageSize(result.page_size);
          hasLoadedRef.current = true;
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
    tableQuery.page,
    tableQuery.pageSize,
    tableQuery.sortKey,
    tableQuery.sortDirection,
    reloadKey,
  ]);

  const reload = useCallback(() => {
    setReloadKey((prev) => prev + 1);
  }, []);

  return {
    items,
    total,
    page,
    pageSize,
    loading,
    refreshing,
    error,
    reload,
  };
}
