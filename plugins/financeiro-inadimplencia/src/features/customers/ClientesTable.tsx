import { useEffect, useMemo, useState } from "react";
import {
  ActionButton,
  ExcelExportButton,
  NativeCheckboxControl,
  ToolbarSelectField,
} from "@delpi/plugin-ui/index";

import { ErrorState } from "../../components/ErrorState";
import {
  DataTableSection,
  type DataTableColumn,
} from "../../components/dataTableUi";
import type {
  ClientesSortBy,
  InadimplenciaClienteItem,
  InadimplenciaClientesData,
  PeriodFilter,
  SortDirection,
} from "../../types/inadimplencia";
import { CLIENTES_SORT_OPTIONS, paginationTotal } from "../../types/inadimplencia";
import {
  formatCurrencyBrl,
  formatInteger,
  formatPercent,
  formatPeriodRangeLabel,
} from "../../utils/formatters";
import { exportClientesExcel } from "../../utils/exportClientesExcel";

type ClientesTableProps = {
  period: PeriodFilter;
  periodLabel?: string;
  data: InadimplenciaClientesData | null;
  loading?: boolean;
  error?: string | null;
  search: string;
  sortBy: ClientesSortBy;
  sortDir: SortDirection;
  onlyWithDelays: boolean;
  pageSize: number;
  onSearchChange: (value: string) => void;
  onSortChange: (sortBy: ClientesSortBy, sortDir: SortDirection) => void;
  onOnlyWithDelaysChange: (value: boolean) => void;
  onPageChange: (page: number) => void;
  onPageSizeChange: (pageSize: number) => void;
  onOpenTitles: (customer: InadimplenciaClienteItem) => void;
  onRetry?: () => void;
};

export function ClientesTable({
  period,
  periodLabel,
  data,
  loading = false,
  error = null,
  search,
  sortBy,
  sortDir,
  onlyWithDelays,
  pageSize,
  onSearchChange,
  onSortChange,
  onOnlyWithDelaysChange,
  onPageChange,
  onPageSizeChange,
  onOpenTitles,
  onRetry,
}: ClientesTableProps) {
  const [draftSearch, setDraftSearch] = useState(search);
  const [prevSearch, setPrevSearch] = useState(search);
  const [exporting, setExporting] = useState(false);
  const [exportError, setExportError] = useState<string | null>(null);

  if (search !== prevSearch) {
    setPrevSearch(search);
    setDraftSearch(search);
  }

  useEffect(() => {
    const timer = window.setTimeout(() => {
      if (draftSearch !== search) {
        onSearchChange(draftSearch);
      }
    }, 350);
    return () => window.clearTimeout(timer);
  }, [draftSearch, search, onSearchChange]);

  const pagination = data?.pagination;
  const items = data?.items ?? [];
  const totalPages = pagination?.total_pages ?? 1;
  const totalCount = paginationTotal(pagination, items.length);
  const canExport = totalCount > 0;
  const resolvedPeriodLabel = data?.periodo?.rotulo?.trim() || periodLabel?.trim() || null;
  const periodRangeLabel = formatPeriodRangeLabel(
    data?.periodo?.data_inicio ?? period.startDate,
    data?.periodo?.data_fim_exclusiva ?? period.endDate,
  );

  const hintParts = [
    resolvedPeriodLabel || periodRangeLabel
      ? `Período: ${resolvedPeriodLabel || periodRangeLabel}${
          resolvedPeriodLabel && periodRangeLabel ? ` (${periodRangeLabel})` : ""
        }`
      : null,
    pagination
      ? `${formatInteger(totalCount)} cliente(s) · página ${pagination.page} de ${totalPages}`
      : null,
  ].filter(Boolean);

  const columns = useMemo<DataTableColumn<InadimplenciaClienteItem>[]>(
    () => [
      {
        key: "customer",
        header: "Cliente",
        render: (item) => (
          <div className="fi-customer-cell">
            <strong>{item.nome_cliente || item.nome_reduzido || "—"}</strong>
            <span>
              {item.cliente_codigo}/{item.loja}
              {item.total_titulos <= 3
                ? ` · base pequena (${formatInteger(item.total_titulos)} título(s))`
                : ""}
            </span>
          </div>
        ),
      },
      {
        key: "total_titulos",
        header: "Títulos",
        align: "right",
        render: (item) => formatInteger(item.total_titulos),
      },
      {
        key: "titulos_em_dia",
        header: "Em dia",
        align: "right",
        render: (item) => formatInteger(item.titulos_em_dia),
      },
      {
        key: "titulos_atraso",
        header: "Atrasados",
        align: "right",
        render: (item) => formatInteger(item.titulos_atraso),
      },
      {
        key: "percentual_em_dia_qtd",
        header: "Pontualidade (qtd)",
        align: "right",
        render: (item) => formatPercent(item.percentual_em_dia_qtd),
      },
      {
        key: "valor_total",
        header: "Valor total",
        align: "right",
        render: (item) => formatCurrencyBrl(item.valor_total),
      },
      {
        key: "valor_atraso",
        header: "Valor atrasado",
        align: "right",
        render: (item) => formatCurrencyBrl(item.valor_atraso),
      },
      {
        key: "action",
        header: "Ação",
        interactive: true,
        render: (item) => (
          <ActionButton variant="ghost" onClick={() => onOpenTitles(item)}>
            Ver títulos
          </ActionButton>
        ),
      },
    ],
    [onOpenTitles],
  );

  const handleExportExcel = async () => {
    if (exporting || !canExport) return;
    setExporting(true);
    setExportError(null);
    try {
      await exportClientesExcel({
        ...period,
        search,
        sortBy,
        sortDir,
        onlyWithDelays,
      });
    } catch (err) {
      setExportError(
        err instanceof Error ? err.message : "Não foi possível exportar o Excel.",
      );
    } finally {
      setExporting(false);
    }
  };

  return (
    <>
      {error ? <ErrorState message={error} onRetry={onRetry} /> : null}
      {exportError ? (
        <p className="fi-filters__error" role="alert">
          {exportError}
        </p>
      ) : null}

      <DataTableSection
        columnPreferencesKey="financeiro-inadimplencia:clientes:v1"
        title="Clientes com maior impacto"
        hint={hintParts.length > 0 ? hintParts.join(" · ") : undefined}
        columns={columns}
        rows={items}
        rowKey={(row) => `${row.cliente_codigo}-${row.loja}`}
        loading={loading && items.length === 0}
        refreshing={loading && items.length > 0}
        emptyMessage={
          onlyWithDelays
            ? "Nenhum cliente com atraso encontrado."
            : "Nenhum título encontrado para o período selecionado."
        }
        searchPlaceholder="Código, razão social ou nome reduzido"
        serverSearch={{
          value: draftSearch,
          onChange: setDraftSearch,
        }}
        serverPagination={{
          page: pagination?.page ?? 1,
          pageSize: pagination?.page_size ?? pageSize,
          total: totalCount,
          onPageChange,
          onPageSizeChange,
        }}
        toolbarExtra={
          <>
            <ToolbarSelectField
              label="Ordenar"
              value={sortBy}
              allowEmptyOption={false}
              options={CLIENTES_SORT_OPTIONS.map((option) => ({
                value: option.value,
                label: option.label,
              }))}
              onChange={(value) => onSortChange(value as ClientesSortBy, sortDir)}
            />

            <ToolbarSelectField
              label="Direção"
              value={sortDir}
              allowEmptyOption={false}
              options={[
                { value: "desc", label: "Descendente" },
                { value: "asc", label: "Ascendente" },
              ]}
              onChange={(value) => onSortChange(sortBy, value as SortDirection)}
            />

            <NativeCheckboxControl
              checked={onlyWithDelays}
              label="Somente com atraso"
              onChange={onOnlyWithDelaysChange}
            />
          </>
        }
        headerActions={
          <ExcelExportButton
            disabled={!canExport || loading}
            exporting={exporting}
            onExport={handleExportExcel}
            className="fi-no-print"
            label="Excel"
            exportingLabel="Exportando…"
          />
        }
      />
    </>
  );
}
