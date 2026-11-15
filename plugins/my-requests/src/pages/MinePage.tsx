import { Plus } from "lucide-react";
import { useCallback, useEffect, useMemo, useState } from "react";
import {
  ActionButton,
  PRC_STATUS_LABELS,
  PRC_TYPE_LABELS,
  newDashboardFilterRuleId,
  type DashboardFilterFieldDescriptor,
  type DashboardFilterRule,
  type DashboardSortLevel,
  type DataTableColumn,
  type ScopeChip,
} from "@delpi/plugin-ui/index";

import { useMyRequestsListSync } from "../app/MyRequestsRealtimeProvider";
import { usePrcListSync } from "../app/PrcRealtimeProvider";
import { listMyRequests, listRequestTypes } from "../api/requestsApi";
import { listMyPrcRequests } from "../features/product-registration/prcApi";
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
  PRC_TYPE_CODE,
  defaultSortLevels,
  parseListSortLevels,
  serializeListSortLevels,
  sortCatalogForSource,
  sourceForTypeCode,
} from "../domain/requestListSort";
import {
  myRequestsPath,
  myRequestsPrcPath,
  navigateMyRequestsPath,
} from "../hooks/myRequestsNavigation";
import { useRequestListUrlState } from "../hooks/useRequestListUrlState";
import { canCreateAnyRequest } from "../security/requestsAccess";
import { useRequestsPermissions } from "../security/RequestsPermissionsContext";
import type { RequestTypeSummary } from "../types/requests";
import { MyRequestsRecordCard, MyRequestsStatusBadge } from "../ui/mrUi";

const INITIAL_FILTERS: RequestListFiltersState = {
  q: "",
  typeCode: "",
  status: "",
  branch: "",
  mineScope: "",
  sort: "",
  page: 1,
};

/* Janela de merge honesta: para compor a página N unificada por data,
 * basta a janela page*PAGE_SIZE de cada fonte (ambas paginadas e
 * ordenadas por criação na mesma direção). Limitada a 100 (contrato). */
const MERGE_WINDOW_MAX = 100;

const MINE_COLUMN_PREFS_KEY = "my-requests.mine.columns.v1";
const MINE_VIEW_LAYOUT_KEY = "my-requests.mine.view-layout.v1";

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

export function MinePage() {
  const access = useRequestsPermissions();
  const [rows, setRows] = useState<UnifiedRequestRow[]>([]);
  const [total, setTotal] = useState(0);
  const [types, setTypes] = useState<RequestTypeSummary[]>([]);
  const [filters, patchFilters] = useRequestListUrlState(INITIAL_FILTERS);
  const [error, setError] = useState<string | null>(null);
  const [prcError, setPrcError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [listEpoch, setListEpoch] = useState(0);

  const bumpList = useCallback(() => {
    setListEpoch((value) => value + 1);
  }, []);
  useMyRequestsListSync(bumpList);
  /* ENG-REALTIME-01 — casos PRC vivem na Engineering API; evento dela
   * também reindexa a lista unificada (mesmo epoch/refetch oficial). */
  usePrcListSync(bumpList);

  /* Fonte efetiva: tipo requests-api "raw-material-creation" ainda
   * combina casos PRC da Engineering API — catálogo mesclado só
   * expõe o campo comparável nas duas fontes (Data). */
  const source = sourceForTypeCode(filters.typeCode);
  const sortCatalog = sortCatalogForSource(
    source === "prc" ? "merged" : source,
  );

  const appliedLevels = useMemo(() => {
    const parsed = parseListSortLevels(filters.sort, sortCatalog.fields);
    return parsed.length ? parsed : defaultSortLevels(source);
  }, [filters.sort, sortCatalog.fields, source]);

  const [sortLevels, setSortLevels] = useState<DashboardSortLevel[]>(
    appliedLevels,
  );
  useEffect(() => setSortLevels(appliedLevels), [appliedLevels]);

  /* Troca de fonte invalida o sort aplicado (campos incompatíveis). */
  useEffect(() => {
    if (
      filters.sort &&
      !parseListSortLevels(filters.sort, sortCatalog.fields).length
    ) {
      patchFilters({ sort: "", page: 1 });
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [sortCatalog]);

  const applySort = useCallback(() => {
    patchFilters({
      sort: serializeListSortLevels(sortLevels),
      page: 1,
    });
  }, [sortLevels, patchFilters]);

  const sortSummary = useMemo(() => {
    const first = appliedLevels[0];
    const option = sortCatalog.fields.find(
      (field) => field.value === first?.field,
    );
    if (!option) return "Ordenar";
    const suffix = appliedLevels.length > 1 ? ` (+${appliedLevels.length - 1})` : "";
    return `${option.label} ${first?.direction === "asc" ? "↑" : "↓"}${suffix}`;
  }, [appliedLevels, sortCatalog.fields]);

  /* ----- builder de critérios: Tipo / Status / Filial ----- */

  const typeOptions = useMemo(
    () =>
      types.map((item) => ({ value: item.code, label: item.name })),
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
    () =>
      access.branches.map((branch) => ({ value: branch, label: branch })),
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
    ],
    [typeOptions, statusOptions, branchOptions],
  );

  const filtersToRules = useCallback((): DashboardFilterRule[] => {
    const rules: DashboardFilterRule[] = [];
    const pairs: Array<[string, string]> = [
      ["typeCode", filters.typeCode],
      ["status", filters.status],
      ["branch", filters.branch],
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
  }, [filters.typeCode, filters.status, filters.branch]);

  const [filterRules, setFilterRules] = useState<DashboardFilterRule[]>(
    filtersToRules,
  );
  useEffect(() => setFilterRules(filtersToRules()), [filtersToRules]);

  const applyFilterRules = useCallback(() => {
    const next: RequestListFiltersState = {
      ...filters,
      typeCode: "",
      status: "",
      branch: "",
      page: 1,
    };
    for (const rule of filterRules) {
      if (rule.field === "typeCode") next.typeCode = rule.value;
      if (rule.field === "status") next.status = rule.value;
      if (rule.field === "branch") next.branch = rule.value;
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
    setPrcError(null);

    const windowSize = Math.min(
      filters.page * REQUEST_LIST_PAGE_SIZE,
      MERGE_WINDOW_MAX,
    );
    /* typeCode: `raw-material-creation` é o tipo requests-api equivalente
     * ao caso PRC; qualquer outro tipo exclui PRC honestamente. Filial:
     * o PRC não possui filial no contrato — excluído quando filtrada. */
    const includePrc =
      (!filters.typeCode || filters.typeCode === PRC_TYPE_CODE) &&
      !filters.branch;

    const requestsSort = serializeListSortLevels(appliedLevels);
    const primary = appliedLevels[0] ?? {
      field: "created_at",
      direction: "desc" as const,
    };

    const reqPromise = listMyRequests({
      signal: ac.signal,
      page: 1,
      pageSize: windowSize,
      typeCode: filters.typeCode || undefined,
      status: filters.status || undefined,
      branch: filters.branch || undefined,
      q: filters.q || undefined,
      sort: requestsSort,
    });

    const prcPromise = includePrc
      ? listMyPrcRequests(ac.signal, {
          page: 1,
          pageSize: windowSize,
          status: filters.status || undefined,
          search: filters.q || undefined,
          sortBy: "createdAt",
          sortDir: primary.direction,
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
          setError(
            (reqRes.reason as Error)?.message ||
              "Falha ao carregar suas solicitações.",
          );
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
          setPrcError(
            (prcRes.reason as Error)?.message ||
              "Falha ao carregar os casos de cadastro de produto.",
          );
        }

        const merged = mergeUnifiedRows(reqRows, prcRows, primary.direction);
        const start = (filters.page - 1) * REQUEST_LIST_PAGE_SIZE;
        setRows(merged.slice(start, start + REQUEST_LIST_PAGE_SIZE));
        setTotal(reqTotal + prcTotal);
      })
      .finally(() => {
        if (!ac.signal.aborted) setLoading(false);
      });
    return () => ac.abort();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [filters, listEpoch, types]);

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

  /* Coluna → campo do contrato efetivo (header-sort). */
  const columnSortMap = useMemo(() => {
    const map: Record<string, string> = { date: "created_at" };
    if (source === "requests") {
      map.number = "request_number";
      map.type = "type_code";
      map.status = "status";
      map.branch = "branch";
    }
    return map;
  }, [source]);

  const activeSortColumn = useMemo(() => {
    const field = appliedLevels[0]?.field;
    for (const [column, candidate] of Object.entries(columnSortMap)) {
      if (candidate === field) return column;
    }
    return null;
  }, [appliedLevels, columnSortMap]);

  const renderCard = useCallback(
    (row: UnifiedRequestRow) => (
      <MyRequestsRecordCard
        title={row.subject}
        subtitle={`${row.displayNumber} · ${row.typeLabel}`}
        status={
          <MyRequestsStatusBadge
            label={row.statusLabel}
            variant={row.statusVariant}
          />
        }
        fields={[
          { id: "branch", label: "Filial", value: row.branch || "—" },
          {
            id: "date",
            label: "Data",
            value: row.createdAt
              ? new Date(row.createdAt).toLocaleDateString("pt-BR")
              : "—",
          },
        ]}
        href={
          row.source === "engineering-prc"
            ? row.destination
            : myRequestsPath({ requestId: row.id })
        }
        ariaLabel={`Abrir ${row.displayNumber}`}
        onNavigate={(event: { preventDefault(): void }) => {
          event.preventDefault();
          navigateMyRequestsPath(
            row.source === "engineering-prc"
              ? row.destination
              : myRequestsPath({ requestId: row.id }),
          );
        }}
      />
    ),
    [],
  );

  const listError = [error, prcError].filter(Boolean).join(" · ") || null;
  const emptyMessage =
    filters.q || filters.typeCode || filters.status || filters.branch
      ? "Nenhuma solicitação para os filtros selecionados."
      : "Você ainda não criou solicitações.";

  return (
    <AppShell>
      <RequestListShell
        eyebrow="Início / Minhas solicitações"
        title="Minhas solicitações"
        description="Acompanhe as solicitações que você abriu — serviços gerais e casos de cadastro de produto (PRC) no mesmo lugar."
        count={`${total} ${total === 1 ? "solicitação" : "solicitações"}`}
        heroAction={
          canCreateAnyRequest(access) ? (
            <ActionButton
              type="button"
              variant="primary"
              onClick={() => navigateMyRequestsPath("new")}
            >
              <Plus size={16} aria-hidden />
              Nova solicitação
            </ActionButton>
          ) : undefined
        }
        onRefresh={bumpList}
        refreshing={loading}
        rows={rows}
        columns={columns}
        rowKey={(row) => `${row.source}-${row.id}`}
        loading={loading}
        error={listError}
        emptyMessage={emptyMessage}
        sectionHint={MY_REQUESTS_HELP_TOOLTIPS.mine.section}
        searchHint="Busca no número, tipo e assunto das suas solicitações."
        page={filters.page}
        pageSize={REQUEST_LIST_PAGE_SIZE}
        total={total}
        onPageChange={(page) => patchFilters({ page })}
        search={filters.q}
        onSearchCommit={(value) => patchFilters({ q: value.trim(), page: 1 })}
        chips={statusChips(filters.status, (value) =>
          patchFilters({ status: value === filters.status ? "" : value, page: 1 }),
        )}
        chipsLabel="Status"
        onClearChips={() => patchFilters({ status: "", page: 1 })}
        sort={{
          fields: sortCatalog.fields,
          levels: sortLevels,
          maxLevels: sortCatalog.maxLevels,
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
        columnSortMap={columnSortMap}
        sortKey={activeSortColumn}
        sortDirection={appliedLevels[0]?.direction ?? "desc"}
        columnPrefsKey={MINE_COLUMN_PREFS_KEY}
        viewLayoutKey={MINE_VIEW_LAYOUT_KEY}
        renderCard={renderCard}
      />
    </AppShell>
  );
}
