import { Filter, RotateCcw } from "lucide-react";
import { HelpTooltip } from "@delpi/plugin-ui/index";

import { CM_HELP } from "../content/helpTooltips";
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
            <HelpTooltip content={CM_HELP.openOrders.filters} ariaLabel="Ajuda: Filtros" />
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
        hint={CM_HELP.openOrders.filterSearch}
        type="search"
        wide
        value={filters.search}
        placeholder="Cliente, pedido, produto, código…"
        onChange={(value) => onChange({ search: value })}
      />
      <FilterSelectField
        id="pva-filter-filial"
        label="Filial"
        hint={CM_HELP.openOrders.filterBranch}
        value={filters.filial}
        onChange={(value) => onChange({ filial: value })}
        options={filialOptions}
        placeholderOption="Todas"
      />
      <MultiSelectField
        label="Cliente"
        hint={CM_HELP.openOrders.filterClient}
        searchable
        options={clientOptions}
        selectedValues={filters.clientCodes}
        onChange={(clientCodes) => onChange({ clientCodes })}
      />
      <FilterSelectField
        id="pva-filter-stock"
        label="Status da linha"
        hint={CM_HELP.openOrders.filterStock}
        value={filters.stockStatus}
        onChange={(value) => onChange({ stockStatus: value as StockFilter })}
        options={STOCK_OPTIONS}
        placeholderOption="Todos os status"
      />
      <FilterSelectField
        id="pva-filter-late"
        label="Entrega"
        hint="Filtrar só linhas com entrega em atraso."
        value={filters.lateOnly ? "late" : ""}
        onChange={(value) => onChange({ lateOnly: value === "late" })}
        options={[{ value: "late", label: "Em atraso" }]}
        placeholderOption="Todas"
      />
      <FilterInputField
        id="pva-filter-date-start"
        label="Entrega de"
        hint={CM_HELP.openOrders.filterDateStart}
        type="date"
        value={filters.dateStart}
        onChange={(value) => onChange({ dateStart: value })}
      />
      <FilterInputField
        id="pva-filter-date-end"
        label="Entrega até"
        hint={CM_HELP.openOrders.filterDateEnd}
        type="date"
        value={filters.dateEnd}
        onChange={(value) => onChange({ dateEnd: value })}
      />
    </FilterBarShell>
  );
}
