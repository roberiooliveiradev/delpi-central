import { useEffect, useState } from "react";
import { ExcelExportButton } from "@delpi/plugin-ui/index";

import { ErrorState } from "../../components/ErrorState";
import { EmptyState } from "../../components/EmptyState";
import { LoadingState } from "../../components/LoadingState";
import { Pagination } from "../../components/Pagination";
import type {
  ClientesSortBy,
  InadimplenciaClienteItem,
  InadimplenciaClientesData,
  PeriodFilter,
  SortDirection,
} from "../../types/inadimplencia";
import { CLIENTES_SORT_OPTIONS } from "../../types/inadimplencia";
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
  onSearchChange: (value: string) => void;
  onSortChange: (sortBy: ClientesSortBy, sortDir: SortDirection) => void;
  onOnlyWithDelaysChange: (value: boolean) => void;
  onPageChange: (page: number) => void;
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
  onSearchChange,
  onSortChange,
  onOnlyWithDelaysChange,
  onPageChange,
  onOpenTitles,
  onRetry,
}: ClientesTableProps) {
  const [draftSearch, setDraftSearch] = useState(search);
  const [prevSearch, setPrevSearch] = useState(search);
  const [exporting, setExporting] = useState(false);
  const [exportError, setExportError] = useState<string | null>(null);

  // Sincroniza rascunho quando a busca externa muda (padrão React: ajustar state na renderização).
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
  const canExport = (pagination?.total_items ?? items.length) > 0;
  const resolvedPeriodLabel = data?.periodo?.rotulo?.trim() || periodLabel?.trim() || null;
  const periodRangeLabel = formatPeriodRangeLabel(
    data?.periodo?.data_inicio ?? period.startDate,
    data?.periodo?.data_fim_exclusiva ?? period.endDate,
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
    <section className="fi-card fi-table-section" aria-label="Clientes com maior impacto">
      <header className="fi-table-section__header">
        <div>
          <h2 className="fi-table-section__title">Clientes com maior impacto</h2>
          {resolvedPeriodLabel || periodRangeLabel || pagination ? (
            <p className="fi-table-section__meta">
              {resolvedPeriodLabel || periodRangeLabel ? (
                <>
                  Período: {resolvedPeriodLabel || periodRangeLabel}
                  {resolvedPeriodLabel && periodRangeLabel ? ` (${periodRangeLabel})` : ""}
                  {pagination ? " · " : ""}
                </>
              ) : null}
              {pagination
                ? `${formatInteger(pagination.total_items)} cliente(s) · página ${pagination.page} de ${totalPages}`
                : null}
            </p>
          ) : null}
        </div>

        <div className="fi-table-toolbar">
          <label className="fi-field fi-field--inline">
            <span className="fi-sr-only">Buscar cliente</span>
            <input
              type="search"
              placeholder="Código, razão social ou nome reduzido"
              value={draftSearch}
              onChange={(event) => setDraftSearch(event.target.value)}
              aria-label="Buscar cliente"
            />
          </label>

          <label className="fi-field fi-field--inline">
            <span>Ordenar</span>
            <select
              value={sortBy}
              onChange={(event) =>
                onSortChange(event.target.value as ClientesSortBy, sortDir)
              }
              aria-label="Campo de ordenação"
            >
              {CLIENTES_SORT_OPTIONS.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
          </label>

          <label className="fi-field fi-field--inline">
            <span>Direção</span>
            <select
              value={sortDir}
              onChange={(event) =>
                onSortChange(sortBy, event.target.value as SortDirection)
              }
              aria-label="Direção da ordenação"
            >
              <option value="desc">Descendente</option>
              <option value="asc">Ascendente</option>
            </select>
          </label>

          <label className="fi-check">
            <input
              type="checkbox"
              checked={onlyWithDelays}
              onChange={(event) => onOnlyWithDelaysChange(event.target.checked)}
            />
            Somente com atraso
          </label>

          <ExcelExportButton
            disabled={!canExport || loading}
            exporting={exporting}
            onExport={handleExportExcel}
            className="fi-export-actions fi-no-print"
            buttonClassName="fi-btn fi-btn--secondary"
            label="Excel"
            exportingLabel="Exportando…"
          />
        </div>
      </header>

      {exportError ? (
        <p className="fi-filters__error" role="alert">
          {exportError}
        </p>
      ) : null}

      {error ? <ErrorState message={error} onRetry={onRetry} /> : null}

      {loading && items.length === 0 ? (
        <LoadingState message="Carregando ranking de clientes…" />
      ) : null}

      {!loading && !error && items.length === 0 ? (
        <EmptyState
          title="Nenhum cliente encontrado"
          message={
            onlyWithDelays
              ? "Nenhum cliente com atraso encontrado."
              : "Nenhum título encontrado para o período selecionado."
          }
        />
      ) : null}

      {items.length > 0 ? (
        <>
          <div className={`fi-table-wrap${loading ? " fi-table-wrap--loading" : ""}`}>
            <table className="fi-table">
              <thead>
                <tr>
                  <th scope="col">Cliente</th>
                  <th scope="col" className="fi-table__numeric">
                    Títulos
                  </th>
                  <th scope="col" className="fi-table__numeric">
                    Em dia
                  </th>
                  <th scope="col" className="fi-table__numeric">
                    Atrasados
                  </th>
                  <th scope="col" className="fi-table__numeric">
                    Pontualidade (qtd)
                  </th>
                  <th scope="col" className="fi-table__numeric">
                    Valor total
                  </th>
                  <th scope="col" className="fi-table__numeric">
                    Valor atrasado
                  </th>
                  <th scope="col">Ação</th>
                </tr>
              </thead>
              <tbody>
                {items.map((item) => (
                  <tr key={`${item.cliente_codigo}-${item.loja}`}>
                    <td data-label="Cliente">
                      <div className="fi-customer-cell">
                        <strong>{item.nome_cliente || item.nome_reduzido || "—"}</strong>
                        <span>
                          {item.cliente_codigo}/{item.loja}
                          {item.total_titulos <= 3
                            ? ` · base pequena (${formatInteger(item.total_titulos)} título(s))`
                            : ""}
                        </span>
                      </div>
                    </td>
                    <td data-label="Títulos" className="fi-table__numeric">
                      {formatInteger(item.total_titulos)}
                    </td>
                    <td data-label="Em dia" className="fi-table__numeric">
                      {formatInteger(item.titulos_em_dia)}
                    </td>
                    <td data-label="Atrasados" className="fi-table__numeric">
                      {formatInteger(item.titulos_atraso)}
                    </td>
                    <td data-label="Pontualidade (qtd)" className="fi-table__numeric">
                      {formatPercent(item.percentual_em_dia_qtd)}
                    </td>
                    <td data-label="Valor total" className="fi-table__numeric">
                      {formatCurrencyBrl(item.valor_total)}
                    </td>
                    <td data-label="Valor atrasado" className="fi-table__numeric">
                      {formatCurrencyBrl(item.valor_atraso)}
                    </td>
                    <td data-label="Ação">
                      <button
                        type="button"
                        className="fi-btn fi-btn--secondary"
                        onClick={() => onOpenTitles(item)}
                      >
                        Ver títulos
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {pagination ? (
            <Pagination
              page={pagination.page}
              pageSize={pagination.page_size}
              total={pagination.total_items}
              totalPages={totalPages}
              onPageChange={onPageChange}
              hideWhenSinglePage
            />
          ) : null}
        </>
      ) : null}
    </section>
  );
}
