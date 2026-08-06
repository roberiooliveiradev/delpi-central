import { Filter, RotateCcw } from "lucide-react";

import type { ClientOption, PedidosVendaAbertosFilters } from "../utils/filterItems";
import type { StockFilter } from "../utils/statusBadges";
import { MultiSelectField } from "./MultiSelectField";
import { FilterBarShell, FilterInputField, FilterSelectField } from "./filtersUi";

type FilterBarProps = {
  filters: PedidosVendaAbertosFilters;
  filiais: string[];
  clients: ClientOption[];
  hasActiveFilters: boolean;
  onChange: (patch: Partial<PedidosVendaAbertosFilters>) => void;
  onReset: () => void;
};

const STOCK_OPTIONS: Array<{ value: StockFilter; label: string }> = [
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
  const filialOptions = filiais.map((filial) => ({ value: filial, label: filial }));
  const clientOptions = clients.map((client) => ({
    value: client.key,
    label: client.name,
  }));

  return (
    <FilterBarShell
      leading={
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
      }
    >
      <FilterInputField
        id="pva-filter-search"
        label="Busca livre"
        type="search"
        wide
        value={filters.search}
        placeholder="Cliente, pedido, produto, código…"
        onChange={(value) => onChange({ search: value })}
      />
      <FilterSelectField
        id="pva-filter-filial"
        label="Filial"
        value={filters.filial}
        onChange={(value) => onChange({ filial: value })}
        options={filialOptions}
        placeholderOption="Todas"
      />
      <MultiSelectField
        label="Cliente"
        searchable
        options={clientOptions}
        selectedValues={filters.clientCodes}
        onChange={(clientCodes) => onChange({ clientCodes })}
      />
      <FilterSelectField
        id="pva-filter-stock"
        label="Status da linha"
        value={filters.stockStatus}
        onChange={(value) => onChange({ stockStatus: value as StockFilter })}
        options={STOCK_OPTIONS}
        placeholderOption="Todos os status"
      />
      <FilterInputField
        id="pva-filter-date-start"
        label="Entrega de"
        type="date"
        value={filters.dateStart}
        onChange={(value) => onChange({ dateStart: value })}
      />
      <FilterInputField
        id="pva-filter-date-end"
        label="Entrega até"
        type="date"
        value={filters.dateEnd}
        onChange={(value) => onChange({ dateEnd: value })}
      />
    </FilterBarShell>
  );
}
