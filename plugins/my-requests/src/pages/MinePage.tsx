import { useCallback, useEffect, useMemo, useState } from "react";
import { ActionButton, DataTable, type DataTableColumn } from "@delpi/plugin-ui/index";

import { listMyRequests, listRequestTypes } from "../api/requestsApi";
import { AppShell } from "../components/AppShell";
import { RequestListFilters } from "../components/RequestListFilters";
import { MY_REQUESTS_HELP_TOOLTIPS } from "../content/helpTooltips";
import {
  REQUEST_LIST_PAGE_SIZE,
  type RequestListFiltersState,
} from "../content/requestListFilters";
import { useRequestsPermissions } from "../security/RequestsPermissionsContext";
import { canCreateAnyRequest } from "../security/requestsAccess";
import type { RequestSummary, RequestTypeSummary } from "../types/requests";
import {
  MyRequestsCompactPagination,
  MyRequestsEmptyState,
  MyRequestsLoadingState,
  MyRequestsSectionCard,
  MyRequestsStateBanner,
  MyRequestsStatusBadge,
} from "../ui/mrUi";
import { mrDataTableClassNames, mrDataTableLabels } from "../ui/mrUiContracts";

const INITIAL_FILTERS: RequestListFiltersState = {
  q: "",
  typeCode: "",
  status: "",
  branch: "",
  page: 1,
};

export function MinePage() {
  const access = useRequestsPermissions();
  const [items, setItems] = useState<RequestSummary[]>([]);
  const [total, setTotal] = useState(0);
  const [types, setTypes] = useState<RequestTypeSummary[]>([]);
  const [filters, setFilters] = useState<RequestListFiltersState>(INITIAL_FILTERS);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  const patchFilters = useCallback((patch: Partial<RequestListFiltersState>) => {
    setFilters((prev) => ({ ...prev, ...patch }));
  }, []);

  useEffect(() => {
    const ac = new AbortController();
    listRequestTypes({ signal: ac.signal })
      .then(setTypes)
      .catch((err: Error) => {
        if (err.name !== "AbortError") setError(err.message);
      });
    return () => ac.abort();
  }, []);

  useEffect(() => {
    const ac = new AbortController();
    setLoading(true);
    setError(null);
    listMyRequests({
      signal: ac.signal,
      page: filters.page,
      pageSize: REQUEST_LIST_PAGE_SIZE,
      typeCode: filters.typeCode || undefined,
      status: filters.status || undefined,
      branch: filters.branch || undefined,
      q: filters.q || undefined,
    })
      .then((data) => {
        setItems(data.items || []);
        setTotal(Number(data.total) || 0);
      })
      .catch((err: Error) => {
        if (err.name !== "AbortError") setError(err.message);
      })
      .finally(() => setLoading(false));
    return () => ac.abort();
  }, [filters]);

  const totalPages = Math.max(1, Math.ceil(total / REQUEST_LIST_PAGE_SIZE) || 1);

  const columns = useMemo<DataTableColumn<RequestSummary>[]>(
    () => [
      {
        key: "number",
        header: "Número",
        render: (row) => (
          <ActionButton
            href={`/apps/my-requests/requests/${row.id}`}
            title={`Abrir ${row.request_number}`}
            variant="link"
          >
            {row.request_number}
          </ActionButton>
        ),
      },
      { key: "type", header: "Tipo", render: (row) => row.type_code },
      {
        key: "status",
        header: "Status",
        render: (row) => (
          <MyRequestsStatusBadge label={row.status_alias || row.status} variant="info" />
        ),
      },
      { key: "branch", header: "Filial", render: (row) => row.branch_code || "—" },
    ],
    [],
  );

  const emptyMessage =
    filters.q || filters.typeCode || filters.status || filters.branch
      ? "Nenhuma solicitação para os filtros selecionados."
      : "Você ainda não criou solicitações.";

  return (
    <AppShell title="Minhas solicitações" canCreate={canCreateAnyRequest(access)}>
      <MyRequestsSectionCard title="Lista">
        <div data-help="mine" title={MY_REQUESTS_HELP_TOOLTIPS.mine.section}>
          <RequestListFilters
            filters={filters}
            types={types}
            branches={access.branches}
            disabled={loading}
            onChange={patchFilters}
            onClear={() => setFilters(INITIAL_FILTERS)}
          />
          {error ? (
            <MyRequestsStateBanner variant="error">{error}</MyRequestsStateBanner>
          ) : null}
          {loading ? <MyRequestsLoadingState /> : null}
          {!loading && !error && items.length === 0 ? (
            <MyRequestsEmptyState message={emptyMessage} />
          ) : null}
          {!loading && items.length > 0 ? (
            <>
              <DataTable
                columns={columns}
                rows={items}
                rowKey={(row) => row.id}
                layout="embedded"
                classNames={mrDataTableClassNames}
                labels={mrDataTableLabels}
              />
              <MyRequestsCompactPagination
                page={filters.page}
                pageSize={REQUEST_LIST_PAGE_SIZE}
                total={total}
                totalPages={totalPages}
                onPageChange={(page) => patchFilters({ page })}
                disabled={loading}
              />
            </>
          ) : null}
        </div>
      </MyRequestsSectionCard>
    </AppShell>
  );
}
