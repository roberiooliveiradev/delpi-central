import { ActionButton, HelpTooltip } from "@delpi/plugin-ui/index";

import { CM_HELP } from "../../../content/helpTooltips";
import { CommercialSelectField, CommercialTextField } from "../../../app/commercialUi";
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
      <div className="pva-customers-toolbar__search-row cm-form-grid">
        <CommercialTextField
          label="Buscar cliente"
          hint={CM_HELP.customers.filterSearch}
          type="search"
          value={search}
          onChange={onSearchChange}
          placeholder="Código, loja, nome ou pedido"
        />
        <CommercialSelectField
          label="Situação"
          hint={CM_HELP.customers.filterSituation}
          options={FILTER_OPTIONS}
          value={filter}
          onChange={(value) => onFilterChange(value as CustomerAttentionFilter)}
          allowEmpty={false}
        />
        {hasActiveFilters ? (
          <div className="cm-form-grid__actions">
            <ActionButton variant="ghost" onClick={onReset}>
              Limpar filtros
            </ActionButton>
            <HelpTooltip
              content={CM_HELP.customers.filterSituation}
              ariaLabel="Ajuda: filtros da carteira"
            />
          </div>
        ) : null}
      </div>
    </section>
  );
}
