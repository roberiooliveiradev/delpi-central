import { useEffect, useState } from "react";
import {
  NativeTextControl,
  dataTableBemClasses,
  dataTableSectionBemClasses,
  ghostBtnBemClasses,
} from "@delpi/plugin-ui/index";
import type {
  DespesasLancamentoItem,
  DespesasLancamentosData,
  LancamentosSortBy,
  SortDirection,
} from "../types/despesasCentroCusto";
import {
  formatCostCenterLabel,
  formatCurrencyBrl,
  formatDatePtBr,
  formatSupplierLabel,
} from "../utils/formatters";
import { EmptyState } from "./EmptyState";
import { ErrorState } from "./ErrorState";
import { LoadingState } from "./LoadingState";
import { Pagination } from "./Pagination";

const FCC_TABLE = dataTableBemClasses("fcc");
const FCC_SECTION = dataTableSectionBemClasses("fcc");
const FCC_GHOST_BTN = ghostBtnBemClasses("fcc");

type ColumnDef = {
  label: string;
  sortKey?: LancamentosSortBy;
  align?: "left" | "right";
};

const columns: ColumnDef[] = [
  { label: "Data", sortKey: "data_emissao" },
  { label: "Centro de custo", sortKey: "centro_custo_descricao" },
  { label: "Fornecedor", sortKey: "razao_social" },
  { label: "Documento", sortKey: "documento" },
  { label: "Pedido" },
  { label: "Produto", sortKey: "produto_descricao" },
  { label: "Observações" },
  { label: "Valor", sortKey: "valor_total", align: "right" },
];

type LancamentosTableProps = {
  data: DespesasLancamentosData | null;
  loading?: boolean;
  error?: string | null;
  search: string;
  sortBy: LancamentosSortBy;
  sortDir: SortDirection;
  onSearchChange: (value: string) => void;
  onSearchSubmit: () => void;
  onSortChange: (sortBy: LancamentosSortBy, sortDir: SortDirection) => void;
  onPageChange: (page: number) => void;
  onRetry?: () => void;
};

function renderRow(item: DespesasLancamentoItem) {
  return (
    <tr key={`${item.recno_sd1}-${item.documento}-${item.valor_total}`}>
      <td>{formatDatePtBr(item.data_emissao_formatada || item.data_emissao)}</td>
      <td>{formatCostCenterLabel(item.centro_custo_codigo, item.centro_custo_descricao)}</td>
      <td>
        {formatSupplierLabel(item.fornecedor_cliente_codigo, item.loja, item.razao_social)}
      </td>
      <td>{item.documento || "—"}</td>
      <td>{item.pedido || "—"}</td>
      <td>{item.produto_descricao || item.produto_codigo || "—"}</td>
      <td>{item.observacoes || "—"}</td>
      <td className={FCC_TABLE.colNumeric}>{formatCurrencyBrl(item.valor_total)}</td>
    </tr>
  );
}

export function LancamentosTable({
  data,
  loading = false,
  error = null,
  search,
  sortBy,
  sortDir,
  onSearchChange,
  onSearchSubmit,
  onSortChange,
  onPageChange,
  onRetry,
}: LancamentosTableProps) {
  const [draftSearch, setDraftSearch] = useState(search);

  useEffect(() => {
    setDraftSearch(search);
  }, [search]);

  const pagination = data?.pagination;
  const items = data?.items ?? [];
  const totalPages = pagination?.total_pages ?? 1;
  const currentPage = pagination?.page ?? 1;

  const toggleSort = (key: LancamentosSortBy) => {
    if (sortBy === key) {
      onSortChange(key, sortDir === "asc" ? "desc" : "asc");
      return;
    }
    onSortChange(key, "desc");
  };

  return (
    <section className={FCC_SECTION.section} aria-label="Lançamentos">
      <header className={FCC_SECTION.header}>
        <div>
          <h2 className={FCC_SECTION.title}>Lançamentos</h2>
          {pagination ? (
            <p className={FCC_SECTION.meta}>
              {pagination.total_items} registro(s) · página {pagination.page} de {totalPages}
            </p>
          ) : null}
        </div>

        <form
          className={FCC_SECTION.actions}
          onSubmit={(event) => {
            event.preventDefault();
            onSearchChange(draftSearch);
            onSearchSubmit();
          }}
        >
          <NativeTextControl
            type="search"
            value={draftSearch}
            placeholder="Buscar documento, fornecedor, produto…"
            onChange={setDraftSearch}
            aria-label="Buscar lançamentos"
          />
          <button type="submit" className={FCC_GHOST_BTN}>
            Buscar
          </button>
        </form>
      </header>

      {error ? <ErrorState message={error} onRetry={onRetry} /> : null}

      {loading && !data ? <LoadingState message="Carregando lançamentos…" /> : null}

      {!loading && !error && items.length === 0 ? (
        <EmptyState message="Nenhum lançamento encontrado para os filtros atuais." />
      ) : null}

      {items.length > 0 ? (
        <div className={FCC_TABLE.wrap}>
          <table className={FCC_TABLE.sortableTable ?? FCC_TABLE.table}>
            <thead>
              <tr>
                {columns.map((column) => {
                  const sortKey = column.sortKey;
                  const isActive = Boolean(sortKey && sortBy === sortKey);
                  return (
                    <th
                      key={column.label}
                      className={
                        column.align === "right" ? FCC_TABLE.colNumeric : undefined
                      }
                    >
                      {sortKey ? (
                        <button
                          type="button"
                          className={
                            isActive ? FCC_TABLE.sortButtonActive : FCC_TABLE.sortButton
                          }
                          onClick={() => toggleSort(sortKey)}
                        >
                          <span className={FCC_TABLE.headerLabel}>
                            <span className={FCC_TABLE.headerText}>{column.label}</span>
                          </span>
                          {isActive ? (sortDir === "asc" ? " ↑" : " ↓") : null}
                        </button>
                      ) : (
                        column.label
                      )}
                    </th>
                  );
                })}
              </tr>
            </thead>
            <tbody>{items.map(renderRow)}</tbody>
          </table>
        </div>
      ) : null}

      {pagination ? (
        <Pagination
          page={currentPage}
          pageSize={pagination.page_size}
          total={pagination.total_items}
          totalPages={totalPages}
          onPageChange={onPageChange}
          hideWhenSinglePage
        />
      ) : null}
    </section>
  );
}
