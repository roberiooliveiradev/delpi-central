import { useCallback, useEffect, useMemo, useState } from "react";
import {
  ActionButton,
  HelpTooltip,
  type StatusBadgeVariant,
} from "@delpi/plugin-ui/index";
import { Plus } from "lucide-react";

import { fetchLmpNonconformities } from "../api/lmpNonconformityApi";
import { DataTableSection } from "../components/DataTableSection";
import {
  FilterInputField,
  FilterSelectField,
  FiltersRow,
} from "../components/dashboardFiltersUi";
import { LmpsNav } from "../components/LmpsNav";
import type { DataTableColumn } from "../components/dataTableUi";
import { StatusBadge } from "../components/ncUi";
import { LMPS_HELP_TOOLTIPS } from "../content/helpTooltips";
import {
  buildNcDetailPath,
  LMPS_ROUTES,
} from "../constants/routes";
import type { LmpNonconformity } from "../types/lmpNonconformity";
import {
  LMP_NC_STATUS_OPTIONS,
  lmpNcStatusLabel,
} from "../types/lmpNonconformity";
import { readLmpsFilters } from "../utils/filterUrl";
import {
  formatDisplayDate,
  formatDisplayDateOnly,
  problemTagsSummary,
  productsSummary,
} from "../utils/ncFormModel";
import { navigateLmps } from "../utils/navigation";

const NC_HELP = LMPS_HELP_TOOLTIPS.nonconformities;

const COLUMN_PREFERENCES_KEY =
  "dashboard-lmps:NonconformitiesPage:listagem:v2";

/** Descrição disponível no menu Colunas, oculta por padrão. */
const DEFAULT_COLUMN_VISIBILITY: Record<string, boolean> = {
  defect_description: false,
};

type Props = {
  pathname: string;
  canWrite?: boolean;
};

function statusVariant(status: string): StatusBadgeVariant {
  if (status === "done") return "success";
  if (status === "in_progress") return "info";
  return "warning";
}

export function NonconformitiesPage({ pathname, canWrite = true }: Props) {
  const filterState = readLmpsFilters();
  const [items, setItems] = useState<LmpNonconformity[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [status, setStatus] = useState("");
  const [saleNumber, setSaleNumber] = useState("");
  const [customerName, setCustomerName] = useState("");
  const [productCode, setProductCode] = useState("");
  const [dateStart, setDateStart] = useState("");
  const [dateEnd, setDateEnd] = useState("");
  const [sortKey, setSortKey] = useState<string | null>("registered_at");
  const [sortDirection, setSortDirection] = useState<"asc" | "desc">("desc");

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await fetchLmpNonconformities({
        status: status || undefined,
        sale_number: saleNumber || undefined,
        customer_name: customerName || undefined,
        product_code: productCode || undefined,
        start_date: dateStart || undefined,
        end_date: dateEnd || undefined,
        sort_by: sortKey || undefined,
        sort_dir: sortDirection,
        page,
        page_size: 50,
      });
      setItems(data.items);
      setTotal(data.total);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao carregar NCs.");
    } finally {
      setLoading(false);
    }
  }, [
    status,
    saleNumber,
    customerName,
    productCode,
    dateStart,
    dateEnd,
    sortKey,
    sortDirection,
    page,
  ]);

  useEffect(() => {
    void load();
  }, [load]);

  const openDetail = (record: LmpNonconformity) => {
    navigateLmps(buildNcDetailPath(record.id));
  };

  const handleSortChange = useCallback((columnKey: string) => {
    setPage(1);
    setSortKey((currentKey) => {
      if (currentKey === columnKey) {
        setSortDirection((currentDirection) =>
          currentDirection === "asc" ? "desc" : "asc",
        );
        return currentKey;
      }
      setSortDirection("asc");
      return columnKey;
    });
  }, []);

  const columns = useMemo<DataTableColumn<LmpNonconformity>[]>(
    () => [
      {
        key: "registered_at",
        header: "Registro",
        headerHint: NC_HELP.table.registeredAt,
        sortable: true,
        sortValue: (row) => row.registered_at ?? "",
        render: (row) => formatDisplayDate(row.registered_at),
      },
      {
        key: "sale_number",
        header: "OV / LMP",
        headerHint: NC_HELP.table.saleNumber,
        sortable: true,
        sortValue: (row) => row.sale_number ?? "",
        render: (row) => row.sale_number || "—",
      },
      {
        key: "customer_name",
        header: "Cliente",
        headerHint: NC_HELP.table.customer,
        sortable: true,
        sortValue: (row) => row.customer_name ?? "",
        render: (row) => row.customer_name || "—",
      },
      {
        key: "launch_date",
        header: "Lançamento",
        headerHint: NC_HELP.table.launchDate,
        sortable: true,
        sortValue: (row) => row.launch_date ?? "",
        render: (row) => formatDisplayDateOnly(row.launch_date),
      },
      {
        key: "last_revision_date",
        header: "Últ. revisão",
        headerHint: NC_HELP.table.lastRevisionDate,
        sortable: true,
        sortValue: (row) => row.last_revision_date ?? "",
        render: (row) => formatDisplayDateOnly(row.last_revision_date),
      },
      {
        key: "executed_by",
        header: "Executou",
        headerHint: NC_HELP.table.executedBy,
        sortable: true,
        sortValue: (row) => row.executed_by ?? "",
        render: (row) => row.executed_by || "—",
      },
      {
        key: "released_by",
        header: "Liberou",
        headerHint: NC_HELP.table.releasedBy,
        sortable: true,
        sortValue: (row) => row.released_by ?? "",
        render: (row) => row.released_by || "—",
      },
      {
        key: "products",
        header: "Produtos",
        headerHint: NC_HELP.table.products,
        sortable: true,
        sortValue: (row) => productsSummary(row),
        render: (row) => productsSummary(row),
      },
      {
        key: "problem_tags",
        header: "Problema identificado",
        headerHint: NC_HELP.table.problemTags,
        sortable: true,
        sortValue: (row) => problemTagsSummary(row),
        render: (row) => problemTagsSummary(row),
      },
      {
        key: "defect_description",
        header: "Descrição",
        headerHint: NC_HELP.table.problem,
        sortable: true,
        sortValue: (row) => row.defect_description ?? "",
        render: (row) => {
          const text = (row.defect_description || "").trim();
          if (!text) return "—";
          return text.length > 56 ? `${text.slice(0, 56)}…` : text;
        },
      },
      {
        key: "status",
        header: "Status",
        headerHint: NC_HELP.table.status,
        sortable: true,
        sortValue: (row) => String(row.status ?? ""),
        render: (row) => (
          <StatusBadge
            label={lmpNcStatusLabel(String(row.status))}
            variant={statusVariant(String(row.status))}
          />
        ),
      },
    ],
    [],
  );

  return (
    <div className="dashboard-page dashboard-lmps">
      <header className="lmps-page-header">
        <div>
          <p className="lmps-eyebrow">DELPI • Analytics</p>
          <div className="lmps-page-header__title-row">
            <h1>Acompanhamento de LMPs</h1>
          </div>
          <span className="lmps-page-subtitle lmps-page-subtitle--with-help">
            Registro de não conformidades de engenharia
            <HelpTooltip
              content={NC_HELP.pageSubtitle}
              ariaLabel="Ajuda: escopo do registro de NCs"
              className="lmps-page-subtitle__help"
            />
          </span>
          <LmpsNav currentPath={pathname} filterState={filterState} />
        </div>
        <div className="lmps-header-actions">
          {canWrite ? (
            <div className="lmps-header-action">
              <ActionButton
                type="button"
                variant="primary"
                onClick={() => navigateLmps(LMPS_ROUTES.nonconformityNew)}
              >
                <Plus size={16} />
                Nova não conformidade
              </ActionButton>
              <HelpTooltip
                content={NC_HELP.newButton}
                ariaLabel="Ajuda: nova não conformidade"
                className="lmps-header-action__help"
              />
            </div>
          ) : null}
        </div>
      </header>

      <FiltersRow>
        <FilterSelectField
          id="lmps-nc-status"
          label="Status"
          hint={NC_HELP.filters.status}
          value={status}
          onChange={(v) => {
            setPage(1);
            setStatus(v);
          }}
          placeholderOption="Todos"
          options={LMP_NC_STATUS_OPTIONS.map((o) => ({
            value: o.value,
            label: o.label,
          }))}
        />
        <FilterInputField
          label="OV / LMP"
          hint={NC_HELP.filters.saleNumber}
          type="text"
          value={saleNumber}
          onChange={(v) => {
            setPage(1);
            setSaleNumber(v);
          }}
        />
        <FilterInputField
          label="Cliente"
          hint={NC_HELP.filters.customer}
          type="text"
          value={customerName}
          onChange={(v) => {
            setPage(1);
            setCustomerName(v);
          }}
        />
        <FilterInputField
          label="Produto"
          hint={NC_HELP.filters.product}
          type="text"
          value={productCode}
          onChange={(v) => {
            setPage(1);
            setProductCode(v);
          }}
        />
        <FilterInputField
          label="Data início"
          hint={NC_HELP.filters.dateStart}
          type="date"
          value={dateStart}
          onChange={(v) => {
            setPage(1);
            setDateStart(v);
          }}
        />
        <FilterInputField
          label="Data fim"
          hint={NC_HELP.filters.dateEnd}
          type="date"
          value={dateEnd}
          onChange={(v) => {
            setPage(1);
            setDateEnd(v);
          }}
        />
      </FiltersRow>

      {error ? (
        <div className="lmps-refreshing-banner" role="alert">
          {error}
        </div>
      ) : null}

      <DataTableSection
        title="Não conformidades"
        titleHint={NC_HELP.table.section}
        hint="Clique na linha para abrir o detalhe. Exclusão somente na página da NC."
        searchHint={NC_HELP.table.search}
        columns={columns}
        rows={items}
        rowKey={(row) => row.id}
        loading={loading}
        emptyMessage="Nenhuma não conformidade encontrada."
        onRowClick={openDetail}
        getRowClassName={() => "lmps-table__row--clickable"}
        columnPreferencesKey={COLUMN_PREFERENCES_KEY}
        defaultColumnVisibility={DEFAULT_COLUMN_VISIBILITY}
        serverSort={{
          sortKey,
          sortDirection,
          onSortChange: handleSortChange,
        }}
        serverPagination={{
          page,
          pageSize: 50,
          total,
          onPageChange: setPage,
        }}
      />
    </div>
  );
}
