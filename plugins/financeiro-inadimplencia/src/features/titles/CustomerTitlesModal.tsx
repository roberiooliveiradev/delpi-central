import { useEffect, useMemo, useState } from "react";
import { ExcelExportButton } from "@delpi/plugin-ui/index";

import { ErrorState } from "../../components/ErrorState";
import { FiModal } from "../../components/FiModal";
import {
  DataTableSection,
  type DataTableColumn,
} from "../../components/dataTableUi";
import {
  defaultTitulosTableState,
  useInadimplenciaTitulos,
  type TitulosTableState,
} from "../../hooks/useInadimplenciaTitulos";
import type {
  InadimplenciaTituloItem,
  PeriodFilter,
  SelectedCustomer,
  TituloStatus,
} from "../../types/inadimplencia";
import { DELAY_RANGE_OPTIONS, paginationTotal } from "../../types/inadimplencia";
import {
  formatCurrencyBrl,
  formatDatePtBr,
  formatInteger,
  formatTituloLabel,
} from "../../utils/formatters";
import { exportTitulosExcel } from "../../utils/exportTitulosExcel";

type CustomerTitlesModalProps = {
  open: boolean;
  customer: SelectedCustomer | null;
  period: PeriodFilter;
  onClose: () => void;
};

type TitlesModalBodyProps = {
  customer: SelectedCustomer;
  period: PeriodFilter;
};

/**
 * Corpo com estado local; remonta via `key` ao trocar cliente
 * para limpar filtros/busca sem effect de reset.
 */
function TitlesModalBody({ customer, period }: TitlesModalBodyProps) {
  const [tableState, setTableState] = useState<TitulosTableState>(defaultTitulosTableState);
  const [draftSearch, setDraftSearch] = useState("");
  const [exporting, setExporting] = useState(false);
  const [exportError, setExportError] = useState<string | null>(null);

  useEffect(() => {
    const timer = window.setTimeout(() => {
      setTableState((current) =>
        current.search === draftSearch
          ? current
          : { ...current, search: draftSearch, page: 1 },
      );
    }, 350);
    return () => window.clearTimeout(timer);
  }, [draftSearch]);

  const titulos = useInadimplenciaTitulos(
    period,
    customer.cliente_codigo,
    customer.loja,
    tableState,
    true,
  );

  const items = titulos.data?.items ?? [];
  const pagination = titulos.data?.pagination;
  const totalCount = paginationTotal(pagination, items.length);
  const canExport = totalCount > 0;

  const columns = useMemo<DataTableColumn<InadimplenciaTituloItem>[]>(
    () => [
      {
        key: "titulo",
        header: "Título",
        render: (item) => formatTituloLabel(item.prefixo, item.numero, item.parcela),
      },
      {
        key: "tipo",
        header: "Tipo",
        render: (item) => item.tipo || "—",
      },
      {
        key: "emissao",
        header: "Emissão",
        render: (item) => formatDatePtBr(item.data_emissao),
      },
      {
        key: "vencimento",
        header: "Vencimento real",
        render: (item) => formatDatePtBr(item.data_vencimento_real),
      },
      {
        key: "baixa",
        header: "Baixa",
        render: (item) => formatDatePtBr(item.data_baixa),
      },
      {
        key: "valor",
        header: "Valor",
        align: "right",
        render: (item) => formatCurrencyBrl(item.valor_titulo),
      },
      {
        key: "dias_atraso",
        header: "Dias de atraso",
        align: "right",
        render: (item) => formatInteger(item.dias_atraso),
      },
      {
        key: "faixa",
        header: "Faixa",
        render: (item) => item.faixa_atraso?.rotulo || item.faixa_atraso?.codigo || "—",
      },
    ],
    [],
  );

  const handleExportExcel = async () => {
    if (exporting || !canExport) return;
    setExporting(true);
    setExportError(null);
    try {
      await exportTitulosExcel({
        ...period,
        customerCode: customer.cliente_codigo,
        storeCode: customer.loja,
        search: tableState.search,
        sortBy: tableState.sortBy,
        sortDir: tableState.sortDir,
        status: tableState.status,
        delayRange: tableState.delayRange,
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
      {titulos.error ? (
        <ErrorState message={titulos.error} onRetry={titulos.reload} />
      ) : null}
      {exportError ? (
        <p className="fi-filters__error" role="alert">
          {exportError}
        </p>
      ) : null}

      <DataTableSection
        embedded
        columnPreferencesKey="financeiro-inadimplencia:titulos-cliente:v1"
        title="Títulos"
        columns={columns}
        rows={items}
        rowKey={(item) =>
          `${item.prefixo}-${item.numero}-${item.parcela}-${item.data_baixa}-${item.valor_titulo}`
        }
        loading={titulos.isLoading && items.length === 0}
        refreshing={titulos.isLoading && items.length > 0}
        emptyMessage="Nenhum título encontrado para os filtros aplicados."
        searchPlaceholder="Número, prefixo ou nome"
        serverSearch={{
          value: draftSearch,
          onChange: setDraftSearch,
        }}
        serverPagination={{
          page: pagination?.page ?? tableState.page,
          pageSize: pagination?.page_size ?? tableState.pageSize,
          total: totalCount,
          onPageChange: (page) => setTableState((current) => ({ ...current, page })),
          onPageSizeChange: (nextPageSize) =>
            setTableState((current) => ({
              ...current,
              pageSize: nextPageSize,
              page: 1,
            })),
        }}
        toolbarExtra={
          <>
            <label className="fi-field fi-field--inline">
              <span>Status</span>
              <select
                value={tableState.status}
                onChange={(event) =>
                  setTableState((current) => ({
                    ...current,
                    status: event.target.value as TituloStatus,
                    page: 1,
                  }))
                }
              >
                <option value="late">Somente atrasados</option>
                <option value="on_time">Em dia</option>
                <option value="all">Todos</option>
              </select>
            </label>

            <label className="fi-field fi-field--inline">
              <span>Faixa</span>
              <select
                value={tableState.delayRange}
                onChange={(event) =>
                  setTableState((current) => ({
                    ...current,
                    delayRange: event.target.value,
                    page: 1,
                  }))
                }
              >
                {DELAY_RANGE_OPTIONS.map((option) => (
                  <option key={option.value || "all"} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </select>
            </label>
          </>
        }
        headerActions={
          <ExcelExportButton
            disabled={!canExport || titulos.isLoading}
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

export function CustomerTitlesModal({
  open,
  customer,
  period,
  onClose,
}: CustomerTitlesModalProps) {
  return (
    <FiModal
      open={open}
      title="Títulos do cliente"
      subtitle={
        customer
          ? `${customer.nome_cliente} · ${customer.cliente_codigo}/${customer.loja} · ${formatInteger(customer.titulos_atraso)} atrasado(s) · ${formatCurrencyBrl(customer.valor_atraso)}`
          : undefined
      }
      onClose={onClose}
    >
      {open && customer ? (
        <TitlesModalBody
          key={`${customer.cliente_codigo}-${customer.loja}`}
          customer={customer}
          period={period}
        />
      ) : null}
    </FiModal>
  );
}
