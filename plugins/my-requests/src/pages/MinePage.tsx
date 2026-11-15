import { useCallback, useEffect, useMemo, useState } from "react";
import {
  ActionButton,
  DataTable,
  PRC_STATUS_LABELS,
  PRC_TYPE_LABELS,
  type DataTableColumn,
} from "@delpi/plugin-ui/index";

import { useMyRequestsListSync } from "../app/MyRequestsRealtimeProvider";
import { usePrcListSync } from "../app/PrcRealtimeProvider";
import { listMyRequests, listRequestTypes } from "../api/requestsApi";
import { listMyPrcRequests } from "../features/product-registration/prcApi";
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
  mergeUnifiedRows,
  prcToUnifiedRow,
  requestListTitle,
  toUnifiedRow,
  type UnifiedRequestRow,
} from "../domain/requestListPresentation";
import {
  prcListErrorMessage,
  shouldIncludePrcInList,
} from "../domain/prcIntegrationGate";
import {
  myRequestsPath,
  myRequestsPrcPath,
  navigateMyRequestsPath,
} from "../hooks/myRequestsNavigation";
import { useRequestsPermissions } from "../security/RequestsPermissionsContext";
import type { RequestTypeSummary } from "../types/requests";
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

/* Janela de merge honesta: para compor a página N unificada por data,
 * basta a janela page*PAGE_SIZE de cada fonte (ambas paginadas e
 * ordenadas por criação desc). Limitada a 100 por chamada (contrato). */
const MERGE_WINDOW_MAX = 100;

export function MinePage() {
  const access = useRequestsPermissions();
  const [rows, setRows] = useState<UnifiedRequestRow[]>([]);
  const [total, setTotal] = useState(0);
  const [types, setTypes] = useState<RequestTypeSummary[]>([]);
  const [filters, setFilters] = useState<RequestListFiltersState>(INITIAL_FILTERS);
  const [error, setError] = useState<string | null>(null);
  const [prcError, setPrcError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [listEpoch, setListEpoch] = useState(0);

  const patchFilters = useCallback((patch: Partial<RequestListFiltersState>) => {
    setFilters((prev) => ({ ...prev, ...patch }));
  }, []);

  const bumpList = useCallback(() => {
    setListEpoch((value) => value + 1);
  }, []);
  useMyRequestsListSync(bumpList);
  /* ENG-REALTIME-01 — casos PRC vivem na Engineering API; evento dela
   * também reindexa a lista unificada (mesmo epoch/refetch oficial). */
  usePrcListSync(bumpList);

  useEffect(() => {
    const ac = new AbortController();
    listRequestTypes({ signal: ac.signal })
      .then(setTypes)
      .catch((err: Error) => {
        if (err.name !== "AbortError")
          setError("Falha ao carregar suas solicitações.");
      });
    return () => ac.abort();
  }, []);

  useEffect(() => {
    const ac = new AbortController();
    setLoading(true);
    setError(null);
    setPrcError(null);

    const windowSize = Math.min(
      filters.page * REQUEST_LIST_PAGE_SIZE,
      MERGE_WINDOW_MAX,
    );
    /* ISOLATION-01 — gate canônico: somente o recorte que pode conter
     * casos do tipo `raw-material-creation` aciona a Engineering API. */
    const includePrc = shouldIncludePrcInList(filters);

    const reqPromise = listMyRequests({
      signal: ac.signal,
      page: 1,
      pageSize: windowSize,
      typeCode: filters.typeCode || undefined,
      status: filters.status || undefined,
      branch: filters.branch || undefined,
      q: filters.q || undefined,
    });

    const prcPromise = includePrc
      ? listMyPrcRequests(ac.signal, {
          page: 1,
          pageSize: windowSize,
          status: filters.status || undefined,
          search: filters.q || undefined,
        })
      : Promise.resolve(null);

    Promise.allSettled([reqPromise, prcPromise])
      .then(([reqRes, prcRes]) => {
        if (ac.signal.aborted) return;
        const typeNameByCode = new Map(
          types.map((item) => [item.code, item.name]),
        );
        const reqRows: UnifiedRequestRow[] = [];
        let reqTotal = 0;
        if (reqRes.status === "fulfilled") {
          reqTotal = Number(reqRes.value.total) || 0;
          for (const row of reqRes.value.items || []) {
            reqRows.push(
              toUnifiedRow(
                row,
                requestTypeLabel(
                  row.type_code,
                  typeNameByCode.get(row.type_code),
                ),
                statusLabel(row.status, row.status_alias),
                requestListTitle(row) || "—",
              ),
            );
          }
        } else {
          setError("Falha ao carregar suas solicitações.");
        }

        const prcRows: UnifiedRequestRow[] = [];
        let prcTotal = 0;
        if (prcRes.status === "fulfilled" && prcRes.value) {
          prcTotal = Number(prcRes.value.total) || prcRes.value.items.length;
          for (const row of prcRes.value.items) {
            prcRows.push(
              prcToUnifiedRow(
                row,
                PRC_TYPE_LABELS,
                PRC_STATUS_LABELS,
                myRequestsPrcPath(row.id),
              ),
            );
          }
        } else if (prcRes.status === "rejected") {
          /* ISOLATION-01 — falha da integração PRC é contextual e não
           * vaza internals do backend (ex.: erro de conexão SQL). */
          setPrcError(prcListErrorMessage());
        }

        const merged = mergeUnifiedRows(reqRows, prcRows);
        const start = (filters.page - 1) * REQUEST_LIST_PAGE_SIZE;
        setRows(
          merged.slice(start, start + REQUEST_LIST_PAGE_SIZE),
        );
        setTotal(reqTotal + prcTotal);
      })
      .finally(() => {
        if (!ac.signal.aborted) setLoading(false);
      });
    return () => ac.abort();
  }, [filters, listEpoch, types]);

  const totalPages = Math.max(1, Math.ceil(total / REQUEST_LIST_PAGE_SIZE) || 1);

  const columns = useMemo<DataTableColumn<UnifiedRequestRow>[]>(
    () => [
      {
        key: "number",
        header: "Número",
        render: (row) => (
          <ActionButton
            type="button"
            title={
              row.source === "engineering-prc"
                ? `Abrir caso PRC ${row.fullIdentifier}`
                : `Abrir ${row.displayNumber}`
            }
            variant="link"
            onClick={() =>
              navigateMyRequestsPath(
                row.source === "engineering-prc"
                  ? row.destination
                  : myRequestsPath({ requestId: row.id }),
              )
            }
          >
            {row.displayNumber}
          </ActionButton>
        ),
      },
      {
        key: "type",
        header: "Tipo",
        render: (row) => row.typeLabel,
      },
      {
        key: "title",
        header: "Assunto",
        render: (row) => row.subject,
      },
      {
        key: "status",
        header: "Status",
        render: (row) => (
          <MyRequestsStatusBadge
            label={row.statusLabel}
            variant={row.statusVariant}
          />
        ),
      },
      {
        key: "branch",
        header: "Filial",
        render: (row) => row.branch,
      },
      {
        key: "date",
        header: "Data",
        render: (row) =>
          row.createdAt
            ? new Date(row.createdAt).toLocaleDateString("pt-BR")
            : "—",
      },
    ],
    [],
  );

  const hasRows = rows.length > 0;
  const hasError = Boolean(error) && Boolean(prcError);
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
          {prcError ? (
            <MyRequestsStateBanner variant="error">
              {prcError}
            </MyRequestsStateBanner>
          ) : null}
          {loading ? <MyRequestsLoadingState /> : null}
          {!loading && !hasRows && !error && !prcError ? (
            <MyRequestsEmptyState message={emptyMessage} />
          ) : null}
          {!loading && hasRows ? (
            <>
              <DataTable
                columns={columns}
                rows={rows}
                rowKey={(row) => `${row.source}-${row.id}`}
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
          {!loading && hasError ? null : null}
        </div>
      </MyRequestsSectionCard>
    </AppShell>
  );
}
