import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import {
  ActionButton,
  HelpTooltip,
  type StatusBadgeVariant,
} from "@delpi/plugin-ui/index";
import { Download, Plus, Upload } from "lucide-react";

import {
  exportLmpNonconformities,
  fetchLmpNonconformities,
  importLmpNonconformities,
} from "../api/lmpNonconformityApi";
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
import { triggerBlobDownload } from "../export/primitives";
import type {
  LmpNonconformity,
  LmpNonconformityExportFile,
} from "../types/lmpNonconformity";
import {
  LMP_NC_STATUS_OPTIONS,
  lmpNcStatusLabel,
} from "../types/lmpNonconformity";
import { readLmpsFilters } from "../utils/filterUrl";
import {
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
  // Listagem de NCs: período só vale se o usuário preencher os filtros da própria
  // página. Não herdar o mês default do dashboard na URL da aba de NCs.
  const ncNavFilters = {
    ...filterState,
    dateStart: "",
    dateEnd: "",
    competence: "",
  };
  const [items, setItems] = useState<LmpNonconformity[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [status, setStatus] = useState("");
  const [saleNumber, setSaleNumber] = useState("");
  const [lmpNumber, setLmpNumber] = useState("");
  const [customerName, setCustomerName] = useState("");
  const [productCode, setProductCode] = useState("");
  const [dateStart, setDateStart] = useState("");
  const [dateEnd, setDateEnd] = useState("");
  const [sortKey, setSortKey] = useState<string | null>("occurrence_date");
  const [sortDirection, setSortDirection] = useState<"asc" | "desc">("desc");
  const [exporting, setExporting] = useState(false);
  const [importing, setImporting] = useState(false);
  const [ioMessage, setIoMessage] = useState<string | null>(null);
  const importInputRef = useRef<HTMLInputElement | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await fetchLmpNonconformities({
        status: status || undefined,
        sale_number: saleNumber || undefined,
        lmp_number: lmpNumber || undefined,
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
    lmpNumber,
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

  const handleExport = useCallback(async () => {
    setExporting(true);
    setError(null);
    setIoMessage(null);
    try {
      const data = await exportLmpNonconformities();
      const blob = new Blob([JSON.stringify(data, null, 2)], {
        type: "application/json",
      });
      const stamp = new Date().toISOString().slice(0, 10);
      triggerBlobDownload(blob, `lmp-nonconformities-${stamp}.json`);
      setIoMessage(`Exportação concluída: ${data.count} NC(s) no arquivo.`);
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Erro ao exportar não conformidades.",
      );
    } finally {
      setExporting(false);
    }
  }, []);

  const handleImportFile = useCallback(
    async (file: File) => {
      setImporting(true);
      setError(null);
      setIoMessage(null);
      try {
        const text = await file.text();
        const parsed = JSON.parse(text) as
          | LmpNonconformityExportFile
          | Array<Record<string, unknown>>;
        const items = Array.isArray(parsed) ? parsed : parsed.items;
        if (!Array.isArray(items) || items.length === 0) {
          throw new Error('Arquivo JSON sem NCs (campo "items" vazio).');
        }
        const result = await importLmpNonconformities(
          items as Array<Record<string, unknown>>,
        );
        setIoMessage(
          `Importação concluída (substituição total): ${result.deleted ?? 0} removida(s), ${result.created} criada(s), ${result.skipped} ignorada(s), ${result.errors} erro(s).`,
        );
        await load();
      } catch (err) {
        setError(
          err instanceof Error
            ? err.message
            : "Erro ao importar não conformidades do arquivo JSON.",
        );
      } finally {
        setImporting(false);
      }
    },
    [load],
  );

  const handleImportChange = useCallback(
    (event: React.ChangeEvent<HTMLInputElement>) => {
      const file = event.target.files?.[0];
      event.target.value = "";
      if (file) void handleImportFile(file);
    },
    [handleImportFile],
  );

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
        key: "occurrence_date",
        header: "Ocorrência",
        headerHint: NC_HELP.table.occurrenceDate,
        sortable: true,
        sortValue: (row) => row.occurrence_date ?? row.registered_at ?? "",
        render: (row) =>
          formatDisplayDateOnly(row.occurrence_date ?? row.registered_at),
      },
      {
        key: "sale_number",
        header: "OV",
        headerHint: NC_HELP.table.saleNumber,
        sortable: true,
        sortValue: (row) => row.sale_number ?? "",
        render: (row) => row.sale_number || "—",
      },
      {
        key: "lmp_number",
        header: "Número da LMP",
        headerHint: NC_HELP.table.lmpNumber,
        sortable: true,
        sortValue: (row) => row.lmp_number ?? "",
        render: (row) => row.lmp_number || "—",
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
          <LmpsNav currentPath={pathname} filterState={ncNavFilters} />
        </div>
        <div className="lmps-header-actions">
          <div className="lmps-header-action">
            <ActionButton
              type="button"
              variant="ghost"
              disabled={exporting || importing}
              onClick={() => void handleExport()}
            >
              <Download size={16} />
              {exporting ? "Exportando…" : "Exportar JSON"}
            </ActionButton>
            <HelpTooltip
              content={NC_HELP.exportJson}
              ariaLabel="Ajuda: exportar NCs em JSON"
              className="lmps-header-action__help"
            />
          </div>
          {canWrite ? (
            <div className="lmps-header-action">
              <input
                ref={importInputRef}
                type="file"
                accept="application/json,.json"
                className="lmps-sr-only"
                aria-hidden="true"
                tabIndex={-1}
                onChange={handleImportChange}
              />
              <ActionButton
                type="button"
                variant="ghost"
                disabled={exporting || importing}
                onClick={() => importInputRef.current?.click()}
              >
                <Upload size={16} />
                {importing ? "Importando…" : "Importar JSON"}
              </ActionButton>
              <HelpTooltip
                content={NC_HELP.importJson}
                ariaLabel="Ajuda: importar NCs de JSON"
                className="lmps-header-action__help"
              />
            </div>
          ) : null}
          {canWrite ? (
            <div className="lmps-header-action">
              <ActionButton
                type="button"
                variant="primary"
                disabled={exporting || importing}
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

      {ioMessage ? (
        <div className="lmps-refreshing-banner" role="status">
          {ioMessage}
        </div>
      ) : null}
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
          label="OV"
          hint={NC_HELP.filters.saleNumber}
          type="text"
          value={saleNumber}
          onChange={(v) => {
            setPage(1);
            setSaleNumber(v);
          }}
        />
        <FilterInputField
          label="Número da LMP"
          hint={NC_HELP.filters.lmpNumber}
          type="text"
          value={lmpNumber}
          onChange={(v) => {
            setPage(1);
            setLmpNumber(v);
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
          label="Ocorrência início"
          hint={NC_HELP.filters.dateStart}
          type="date"
          value={dateStart}
          onChange={(v) => {
            setPage(1);
            setDateStart(v);
          }}
        />
        <FilterInputField
          label="Ocorrência fim"
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
