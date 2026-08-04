import { Search, X } from "lucide-react";

import type { CustomerAttentionFilter } from "../types/customerSummary";

type CustomersFiltersProps = {
  search: string;
  filter: CustomerAttentionFilter;
  onSearchChange: (value: string) => void;
  onFilterChange: (value: CustomerAttentionFilter) => void;
  onReset: () => void;
  hasActiveFilters: boolean;
};

const FILTER_OPTIONS: { value: CustomerAttentionFilter; label: string }[] = [
  { value: "all", label: "Todos os clientes" },
  { value: "overdue", label: "Com atraso" },
  { value: "partial", label: "Parcialmente atendidos" },
];

export function CustomersFilters({
  search,
  filter,
  onSearchChange,
  onFilterChange,
  onReset,
  hasActiveFilters,
}: CustomersFiltersProps) {
  return (
    <section className="pva-customers-toolbar" aria-label="Busca e filtros de clientes">
      <div className="pva-customers-toolbar__search-row">
        <div className="pva-search">
          <Search size={18} className="pva-search__icon" aria-hidden="true" />
          <label className="visually-hidden" htmlFor="pva-customers-search">
            Buscar cliente
          </label>
          <input
            id="pva-customers-search"
            className="pva-search__input"
            type="search"
            value={search}
            onChange={(event) => onSearchChange(event.target.value)}
            placeholder="Buscar por código, loja, nome ou pedido"
            autoComplete="off"
          />
          {search.trim() ? (
            <button
              type="button"
              className="pva-search__clear"
              onClick={() => onSearchChange("")}
              aria-label="Limpar busca"
            >
              <X size={16} aria-hidden="true" />
            </button>
          ) : null}
        </div>
        <label className="pva-customers-toolbar__select-wrap">
          <span className="visually-hidden">Situação</span>
          <select
            className="pva-customers-toolbar__select"
            value={filter}
            onChange={(event) =>
              onFilterChange(event.target.value as CustomerAttentionFilter)
            }
          >
            {FILTER_OPTIONS.map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
        </label>
        {hasActiveFilters ? (
          <button type="button" className="pva-btn pva-btn--secondary" onClick={onReset}>
            Limpar filtros
          </button>
        ) : null}
      </div>
    </section>
  );
}
