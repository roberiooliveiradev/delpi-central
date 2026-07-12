import { useEffect, useState } from "react";
import { NativeTextControl } from "@delpi/plugin-ui/index";

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
      <td className="fcc-table__numeric">{formatCurrencyBrl(item.valor_total)}</td>
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
    <section className="fcc-card fcc-table-section" aria-label="Lançamentos">
      <header className="fcc-table-section__header">
        <div>
          <h2 className="fcc-table-section__title">Lançamentos</h2>
          {pagination ? (
            <p className="fcc-table-section__meta">
              {pagination.total_items} registro(s) · página {pagination.page} de {totalPages}
            </p>
          ) : null}
        </div>

        <form
          className="fcc-table-search"
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
          <button type="submit" className="fcc-btn fcc-btn--secondary">
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
        <div className="fcc-table-wrap">
          <table className="fcc-table">
            <thead>
              <tr>
                {columns.map((column) => {
                  const sortKey = column.sortKey;
                  const isActive = Boolean(sortKey && sortBy === sortKey);
                  return (
                    <th
                      key={column.label}
                      className={column.align === "right" ? "fcc-table__numeric" : undefined}
                    >
                      {sortKey ? (
                        <button
                          type="button"
                          className={`fcc-table-sort${isActive ? " fcc-table-sort--active" : ""}`}
                          onClick={() => toggleSort(sortKey)}
                        >
                          {column.label}
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
