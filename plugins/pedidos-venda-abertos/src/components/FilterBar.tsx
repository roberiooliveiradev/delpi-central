import { Filter, RotateCcw } from "lucide-react";

import type { ClientOption, PedidosVendaAbertosFilters } from "../utils/filterItems";
import type { StockFilter } from "../utils/statusBadges";
import { ClientMultiSelect } from "./ClientMultiSelect";

type FilterBarProps = {
  filters: PedidosVendaAbertosFilters;
  filiais: string[];
  clients: ClientOption[];
  hasActiveFilters: boolean;
  onChange: (patch: Partial<PedidosVendaAbertosFilters>) => void;
  onReset: () => void;
};

const STOCK_OPTIONS: Array<{ value: StockFilter; label: string }> = [
  { value: "", label: "Todos os status" },
  { value: "com_estoque", label: "Pode faturar / com estoque" },
  { value: "parcial", label: "Estoque parcial" },
  { value: "sem_estoque", label: "Sem estoque / atrasado" },
];

export function FilterBar({
  filters,
  filiais,
  clients,
  hasActiveFilters,
  onChange,
  onReset,
}: FilterBarProps) {
  return (
    <section className="pva-card pva-filter-bar" aria-label="Filtros">
      <div className="pva-filter-bar__header">
        <div className="pva-filter-bar__title">
          <Filter size={18} aria-hidden="true" />
          <h2>Filtros</h2>
        </div>
        {hasActiveFilters ? (
          <button type="button" className="pva-btn pva-btn--ghost pva-btn--sm" onClick={onReset}>
            <RotateCcw size={14} aria-hidden="true" />
            Limpar filtros
          </button>
        ) : null}
      </div>

      <div className="pva-filter-grid">
        <label className="pva-field pva-field--wide">
          <span>Busca livre</span>
          <input
            type="search"
            value={filters.search}
            placeholder="Cliente, pedido, produto, código…"
            onChange={(event) => onChange({ search: event.target.value })}
          />
        </label>

        <label className="pva-field">
          <span>Filial</span>
          <select
            value={filters.filial}
            onChange={(event) => onChange({ filial: event.target.value })}
          >
            <option value="">Todas</option>
            {filiais.map((filial) => (
              <option key={filial} value={filial}>
                {filial}
              </option>
            ))}
          </select>
        </label>

        <ClientMultiSelect
          clients={clients}
          selectedKeys={filters.clientCodes}
          onChange={(clientCodes) => onChange({ clientCodes })}
        />

        <label className="pva-field">
          <span>Status da linha</span>
          <select
            value={filters.stockStatus}
            onChange={(event) =>
              onChange({ stockStatus: event.target.value as StockFilter })
            }
          >
            {STOCK_OPTIONS.map((option) => (
              <option key={option.label} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
        </label>

        <label className="pva-field">
          <span>Entrega de</span>
          <input
            type="date"
            value={filters.dateStart}
            onChange={(event) => onChange({ dateStart: event.target.value })}
          />
        </label>

        <label className="pva-field">
          <span>Entrega até</span>
          <input
            type="date"
            value={filters.dateEnd}
            onChange={(event) => onChange({ dateEnd: event.target.value })}
          />
        </label>
      </div>
    </section>
  );
}
