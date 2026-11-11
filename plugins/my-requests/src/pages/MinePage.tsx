import { useCallback, useEffect, useMemo, useState } from "react";
import {
  ActionButton,
  DataTable,
  PRC_STATUS_LABELS,
  PRC_TYPE_LABELS,
  type DataTableColumn,
} from "@delpi/plugin-ui/index";

import { useMyRequestsListSync } from "../app/MyRequestsRealtimeProvider";
import { listMyRequests, listRequestTypes } from "../api/requestsApi";
import {
  listMyPrcRequests,
  type PrcRequestSummary,
} from "../features/product-registration/prcApi";
import { myRequestsPrcPath } from "../hooks/myRequestsNavigation";
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
import { requestListTitle } from "../domain/requestListPresentation";
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

export function MinePage() {
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
        key: "title",
        header: "Assunto",
        render: (row) => requestListTitle(row) || "—",
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
    ],
    [typeNameByCode],
  );

  /* PRC-REF-023-F04 — casos oficiais de cadastro de produto na
   * Engineering API (mesmo requestId; sem registro duplicado). */
  const [prcItems, setPrcItems] = useState<PrcRequestSummary[]>([]);
  useEffect(() => {
    const ac = new AbortController();
    listMyPrcRequests(ac.signal)
      .then((res) => setPrcItems(res.items))
      .catch(() => setPrcItems([]));
    return () => ac.abort();
  }, []);

  const emptyMessage =
    filters.q || filters.typeCode || filters.status || filters.branch
      ? "Nenhuma solicitação para os filtros selecionados."
      : "Você ainda não criou solicitações.";

  return (
    <AppShell title="Minhas solicitações">
      <MyRequestsSectionCard title="Minhas solicitações">
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
      {prcItems.length ? (
        <MyRequestsSectionCard
          title="Cadastro de produtos e matérias-primas"
          hint="Acompanhamento oficial junto à Engenharia."
        >
          {prcItems.map((row) => (
            <p key={row.id}>
              <a href={myRequestsPrcPath(row.id)}>
                {PRC_TYPE_LABELS[row.requestType] || row.requestType} —{" "}
                {row.id.slice(0, 8)}
              </a>{" "}
              <MyRequestsStatusBadge
                label={PRC_STATUS_LABELS[row.status] || row.status}
                variant={
                  row.status === "completed"
                    ? "success"
                    : row.status === "rejected"
                      ? "danger"
                      : row.status === "needs_correction"
                        ? "warning"
                        : "info"
                }
              />{" "}
              {new Date(row.createdAt).toLocaleDateString("pt-BR")}
              {row.officialCode ? ` · ${row.officialCode}` : ""}
            </p>
          ))}
        </MyRequestsSectionCard>
      ) : null}
    </AppShell>
  );
}
