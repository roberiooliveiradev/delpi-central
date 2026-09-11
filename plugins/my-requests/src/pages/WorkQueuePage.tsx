import { useCallback, useEffect, useMemo, useState } from "react";
import { ActionButton, DataTable, type DataTableColumn } from "@delpi/plugin-ui/index";

import { useMyRequestsListSync } from "../app/MyRequestsRealtimeProvider";
import { listRequestTypes, listWorkQueue } from "../api/requestsApi";
import { AppShell } from "../components/AppShell";
import { RequestListFilters } from "../components/RequestListFilters";
import { MY_REQUESTS_HELP_TOOLTIPS } from "../content/helpTooltips";
import {
  requestTypeLabel,
  statusLabel,
} from "../content/presentationLabels";
import {
  REQUEST_LIST_PAGE_SIZE,
  type RequestListFiltersState,
} from "../content/requestListFilters";
import {
  myRequestsPath,
  navigateMyRequestsPath,
} from "../hooks/myRequestsNavigation";
import { useRequestsPermissions } from "../security/RequestsPermissionsContext";
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
  mineScope: "",
  page: 1,
};

export function WorkQueuePage() {
  const access = useRequestsPermissions();
  const [items, setItems] = useState<RequestSummary[]>([]);
  const [total, setTotal] = useState(0);
  const [types, setTypes] = useState<RequestTypeSummary[]>([]);
  const [filters, setFilters] = useState<RequestListFiltersState>(INITIAL_FILTERS);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [listEpoch, setListEpoch] = useState(0);

  const patchFilters = useCallback((patch: Partial<RequestListFiltersState>) => {
    setFilters((prev) => ({ ...prev, ...patch }));
  }, []);

  const bumpList = useCallback(() => {
    setListEpoch((value) => value + 1);
  }, []);
  useMyRequestsListSync(bumpList);

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
    listWorkQueue({
      signal: ac.signal,
      page: filters.page,
      pageSize: REQUEST_LIST_PAGE_SIZE,
      typeCode: filters.typeCode || undefined,
      status: filters.status || undefined,
      branch: filters.branch || undefined,
      q: filters.q || undefined,
      mineScope: filters.mineScope || undefined,
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
  }, [filters, listEpoch]);

  const totalPages = Math.max(1, Math.ceil(total / REQUEST_LIST_PAGE_SIZE) || 1);

  const typeNameByCode = useMemo(() => {
    const map = new Map<string, string>();
    for (const item of types) map.set(item.code, item.name);
    return map;
  }, [types]);

  const columns = useMemo<DataTableColumn<RequestSummary>[]>(
    () => [
      {
        key: "number",
        header: "Número",
        render: (row) => (
          <ActionButton
            type="button"
            title={`Abrir ${row.request_number}`}
            variant="link"
            onClick={() =>
              navigateMyRequestsPath(myRequestsPath({ requestId: row.id }))
            }
          >
            {row.request_number}
          </ActionButton>
        ),
      },
      {
        key: "type",
        header: "Tipo",
        render: (row) =>
          requestTypeLabel(row.type_code, typeNameByCode.get(row.type_code)),
      },
      {
        key: "status",
        header: "Status",
        render: (row) => (
          <MyRequestsStatusBadge
            label={statusLabel(row.status, row.status_alias)}
            variant="info"
          />
        ),
      },
      { key: "branch", header: "Filial", render: (row) => row.branch_code || "—" },
      {
        key: "completed_by",
        header: "Concluída por",
        render: (row) => row.completed_by_name?.trim() || "—",
      },
    ],
    [typeNameByCode],
  );

  const emptyMessage =
    filters.q ||
    filters.typeCode ||
    filters.status ||
    filters.branch ||
    filters.mineScope
      ? "Nenhuma solicitação para os filtros selecionados."
      : "Fila vazia no momento.";

  return (
    <AppShell title="Fila de trabalho">
      <MyRequestsSectionCard title="Pendências">
        <div data-help="work-queue" title={MY_REQUESTS_HELP_TOOLTIPS.workQueue.section}>
          <RequestListFilters
            filters={filters}
            types={types}
            branches={access.branches}
            disabled={loading}
            showMineScope
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
