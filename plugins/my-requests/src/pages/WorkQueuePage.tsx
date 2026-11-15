import { useCallback, useEffect, useMemo, useState } from "react";
import {
  ActionButton,
  newDashboardFilterRuleId,
  type DashboardFilterFieldDescriptor,
  type DashboardFilterRule,
  type DashboardSortLevel,
  type DataTableColumn,
  type ScopeChip,
} from "@delpi/plugin-ui/index";

import { useMyRequestsListSync } from "../app/MyRequestsRealtimeProvider";
import { listRequestTypes, listWorkQueue } from "../api/requestsApi";
import { AppShell } from "../components/AppShell";
import { RequestListShell } from "../components/RequestListShell";
import { MY_REQUESTS_HELP_TOOLTIPS } from "../content/helpTooltips";
import {
  REQUEST_STATUS_FILTER_OPTIONS,
  requestTypeLabel,
  statusLabel,
} from "../content/presentationLabels";
import {
  REQUEST_LIST_PAGE_SIZE,
  WORK_QUEUE_MINE_SCOPE_OPTIONS,
  type RequestListFiltersState,
} from "../content/requestListFilters";
import {
  requestListRequesterName,
  requestListTitle,
} from "../domain/requestListPresentation";
import {
  REQUESTS_SORT_FIELDS,
  defaultSortLevels,
  parseListSortLevels,
  serializeListSortLevels,
} from "../domain/requestListSort";
import {
  myRequestsPath,
  navigateMyRequestsPath,
} from "../hooks/myRequestsNavigation";
import { useRequestListUrlState } from "../hooks/useRequestListUrlState";
import { useRequestsPermissions } from "../security/RequestsPermissionsContext";
import type { RequestSummary, RequestTypeSummary } from "../types/requests";
import { MyRequestsRecordCard, MyRequestsStatusBadge } from "../ui/mrUi";

const INITIAL_FILTERS: RequestListFiltersState = {
  q: "",
  typeCode: "",
  status: "",
  branch: "",
  mineScope: "",
  sort: "",
  page: 1,
  pageSize: REQUEST_LIST_PAGE_SIZE,
};

const QUEUE_COLUMN_PREFS_KEY = "my-requests.work-queue.columns.v1";
const QUEUE_VIEW_LAYOUT_KEY = "my-requests.work-queue.view-layout.v1";
const QUEUE_SORT_MAX_LEVELS = 3;

/** Coluna → campo ordenável do contrato requests-api (header-sort). */
const QUEUE_COLUMN_SORT_MAP: Record<string, string> = {
  number: "request_number",
  type: "type_code",
  status: "status",
  branch: "branch",
  date: "created_at",
};

function statusChips(
  current: string,
  onSelect: (value: string) => void,
): ScopeChip[] {
  return REQUEST_STATUS_FILTER_OPTIONS.filter((option) => option.value).map(
    (option) => ({
      id: `status-${option.value}`,
      label: option.label,
      active: current === option.value,
      onSelect: () => onSelect(option.value),
    }),
  );
}

export function WorkQueuePage() {
  const access = useRequestsPermissions();
  const [items, setItems] = useState<RequestSummary[]>([]);
  const [total, setTotal] = useState(0);
  const [types, setTypes] = useState<RequestTypeSummary[]>([]);
  const [filters, patchFilters] = useRequestListUrlState(INITIAL_FILTERS);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [listEpoch, setListEpoch] = useState(0);

  const bumpList = useCallback(() => {
    setListEpoch((value) => value + 1);
  }, []);
  useMyRequestsListSync(bumpList);

  const appliedLevels = useMemo(() => {
    const parsed = parseListSortLevels(filters.sort, REQUESTS_SORT_FIELDS);
    return parsed.length ? parsed : defaultSortLevels("requests");
  }, [filters.sort]);

  const [sortLevels, setSortLevels] =
    useState<DashboardSortLevel[]>(appliedLevels);
  useEffect(() => setSortLevels(appliedLevels), [appliedLevels]);

  /* Aplicação atômica: o nível a gravar vem por extenso — header e
   * popover convergem para o mesmo commit, sem closure sobre draft. */
  const applySort = useCallback(
    (levels: DashboardSortLevel[]) => {
      setSortLevels(levels);
      patchFilters({ sort: serializeListSortLevels(levels), page: 1 });
    },
    [patchFilters],
  );

  const sortSummary = useMemo(() => {
    const first = appliedLevels[0];
    const option = REQUESTS_SORT_FIELDS.find(
      (field) => field.value === first?.field,
    );
    if (!option) return "Ordenar";
    const suffix =
      appliedLevels.length > 1 ? ` (+${appliedLevels.length - 1})` : "";
    return `${option.label} ${first?.direction === "asc" ? "↑" : "↓"}${suffix}`;
  }, [appliedLevels]);

  /* ----- builder de critérios: Tipo / Status / Filial / Escopo ----- */

  const typeOptions = useMemo(
    () => types.map((item) => ({ value: item.code, label: item.name })),
    [types],
  );

  const statusOptions = useMemo(
    () =>
      REQUEST_STATUS_FILTER_OPTIONS.filter((option) => option.value).map(
        (option) => ({ value: option.value, label: option.label }),
      ),
    [],
  );

  const branchOptions = useMemo(
    () => access.branches.map((branch) => ({ value: branch, label: branch })),
    [access.branches],
  );

  const filterFields: DashboardFilterFieldDescriptor[] = useMemo(
    () => [
      {
        key: "typeCode",
        label: "Tipo",
        operator: "eq",
        input: "select",
        options: typeOptions,
        placeholderOption: "Todos",
        searchable: true,
      },
      {
        key: "status",
        label: "Status",
        operator: "eq",
        input: "select",
        options: statusOptions,
        placeholderOption: "Todos",
      },
      {
        key: "branch",
        label: "Filial",
        operator: "eq",
        input: "select",
        options: branchOptions,
        placeholderOption: "Todas",
      },
      {
        key: "mineScope",
        label: "Escopo",
        operator: "eq",
        input: "select",
        options: WORK_QUEUE_MINE_SCOPE_OPTIONS.filter(
          (option) => option.value,
        ).map((option) => ({ value: option.value, label: option.label })),
        placeholderOption: "Todas",
      },
    ],
    [typeOptions, statusOptions, branchOptions],
  );

  const filtersToRules = useCallback((): DashboardFilterRule[] => {
    const rules: DashboardFilterRule[] = [];
    const pairs: Array<[string, string]> = [
      ["typeCode", filters.typeCode],
      ["status", filters.status],
      ["branch", filters.branch],
      ["mineScope", filters.mineScope],
    ];
    for (const [field, value] of pairs) {
      if (!value) continue;
      rules.push({
        id: newDashboardFilterRuleId(),
        field,
        operator: "eq",
        value,
      });
    }
    return rules;
  }, [
    filters.typeCode,
    filters.status,
    filters.branch,
    filters.mineScope,
  ]);

  const [filterRules, setFilterRules] =
    useState<DashboardFilterRule[]>(filtersToRules);
  useEffect(() => setFilterRules(filtersToRules()), [filtersToRules]);

  const applyFilterRules = useCallback(() => {
    const next: RequestListFiltersState = {
      ...filters,
      typeCode: "",
      status: "",
      branch: "",
      mineScope: "",
      page: 1,
    };
    for (const rule of filterRules) {
      if (rule.field === "typeCode") next.typeCode = rule.value;
      if (rule.field === "status") next.status = rule.value;
      if (rule.field === "branch") next.branch = rule.value;
      if (rule.field === "mineScope") {
        next.mineScope =
          rule.value === "completed_by_me" || rule.value === "assigned_to_me"
            ? rule.value
            : "";
      }
    }
    patchFilters(next);
  }, [filterRules, filters, patchFilters]);

  /* -------------------------------------------------------- */

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
      pageSize: filters.pageSize,
      typeCode: filters.typeCode || undefined,
      status: filters.status || undefined,
      branch: filters.branch || undefined,
      q: filters.q || undefined,
      mineScope: filters.mineScope || undefined,
      sort: serializeListSortLevels(appliedLevels),
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
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [filters, listEpoch]);

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
        key: "requester",
        header: "Solicitante",
        render: (row) => requestListRequesterName(row),
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
      {
        key: "branch",
        header: "Filial",
        render: (row) => row.branch_code || "—",
      },
      {
        key: "completed_by",
        header: "Concluída por",
        render: (row) => row.completed_by_name?.trim() || "—",
      },
      {
        key: "date",
        header: "Data",
        render: (row) =>
          row.created_at
            ? new Date(row.created_at).toLocaleDateString("pt-BR")
            : "—",
      },
    ],
    [typeNameByCode],
  );

  const activeSortColumn = useMemo(() => {
    const field = appliedLevels[0]?.field;
    for (const [column, candidate] of Object.entries(QUEUE_COLUMN_SORT_MAP)) {
      if (candidate === field) return column;
    }
    return null;
  }, [appliedLevels]);

  const renderCard = useCallback(
    (row: RequestSummary) => (
      <MyRequestsRecordCard
        title={requestListTitle(row) || "—"}
        subtitle={`${row.request_number} · ${requestTypeLabel(
          row.type_code,
          typeNameByCode.get(row.type_code),
        )}`}
        status={
          <MyRequestsStatusBadge
            label={statusLabel(row.status, row.status_alias)}
            variant="info"
          />
        }
        fields={[
          {
            id: "requester",
            label: "Solicitante",
            value: requestListRequesterName(row),
          },
          {
            id: "branch",
            label: "Filial",
            value: row.branch_code || "—",
          },
          {
            id: "completed_by",
            label: "Concluída por",
            value: row.completed_by_name?.trim() || "—",
            present: Boolean(row.completed_by_name?.trim()),
          },
          {
            id: "date",
            label: "Data",
            value: row.created_at
              ? new Date(row.created_at).toLocaleDateString("pt-BR")
              : "—",
          },
        ]}
        href={myRequestsPath({ requestId: row.id })}
        ariaLabel={`Abrir ${row.request_number}`}
        onNavigate={(event: { preventDefault(): void }) => {
          event.preventDefault();
          navigateMyRequestsPath(myRequestsPath({ requestId: row.id }));
        }}
      />
    ),
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
    <AppShell>
      <RequestListShell
        title="Fila de trabalho"
        description="Solicitações abertas aos processadores — filtre por escopo, tipo, status e filial."
        count={`${total} ${total === 1 ? "pendência" : "pendências"}`}
        onRefresh={bumpList}
        refreshing={loading}
        rows={items}
        columns={columns}
        rowKey={(row) => row.id}
        loading={loading}
        error={error}
        emptyMessage={emptyMessage}
        sectionHint={MY_REQUESTS_HELP_TOOLTIPS.workQueue.section}
        searchHint="Busca no número, assunto e solicitante da fila."
        page={filters.page}
        pageSize={filters.pageSize}
        total={total}
        onPageChange={(page) => patchFilters({ page })}
        onPageSizeChange={(pageSize) => patchFilters({ pageSize, page: 1 })}
        search={filters.q}
        onSearchCommit={(value) => patchFilters({ q: value.trim(), page: 1 })}
        chips={statusChips(filters.status, (value) =>
          patchFilters({
            status: value === filters.status ? "" : value,
            page: 1,
          }),
        )}
        chipsLabel="Status"
        onClearChips={() => patchFilters({ status: "", page: 1 })}
        sort={{
          fields: REQUESTS_SORT_FIELDS,
          levels: sortLevels,
          maxLevels: QUEUE_SORT_MAX_LEVELS,
          onChange: setSortLevels,
          onApply: applySort,
          summaryLabel: sortSummary,
        }}
        filter={{
          fields: filterFields,
          rules: filterRules,
          onChange: setFilterRules,
          onApply: applyFilterRules,
          onClear: () => setFilterRules([]),
        }}
        columnSortMap={QUEUE_COLUMN_SORT_MAP}
        sortKey={activeSortColumn}
        sortDirection={appliedLevels[0]?.direction ?? "desc"}
        columnPrefsKey={QUEUE_COLUMN_PREFS_KEY}
        viewLayoutKey={QUEUE_VIEW_LAYOUT_KEY}
        renderCard={renderCard}
      />
    </AppShell>
  );
}
