import { RefreshCw } from "lucide-react";

import {
  PAC_BRANCH_OPTIONS,
  PAC_NONCONFORMITY_SCOPES,
  PLAN_SEVERITIES,
  PLAN_STATUSES,
} from "../../constants/actionPlans";
import type { PlansFilterState } from "../../utils/planFilters";
import { FilterBar } from "../ui/FilterBar";
import { MultiSelectField } from "../ui/MultiSelectField";
import { TextField } from "../ui/TextField";

type Props = {
  filters: PlansFilterState;
  onChange: (filters: PlansFilterState) => void;
  onRefresh: () => void;
  loading?: boolean;
};

export function PlansFilters({ filters, onChange, onRefresh, loading = false }: Props) {
  function patch(partial: Partial<PlansFilterState>) {
    onChange({ ...filters, ...partial });
  }

  return (
    <FilterBar
      actions={
        <>
          <span className="pac-filter-box__spacer" aria-hidden />
          <button type="button" className="pac-primary-btn" disabled={loading} onClick={onRefresh}>
            <RefreshCw size={16} aria-hidden="true" />
            {loading ? "Atualizando…" : "Atualizar"}
          </button>
        </>
      }
    >
      <MultiSelectField
        id="pac-filter-scope"
        label="Escopo NC"
        options={PAC_NONCONFORMITY_SCOPES.map((item) => ({ value: item.value, label: item.label }))}
        selectedValues={filters.scopes}
        onChange={(scopes) => patch({ scopes })}
        emptyLabel="Todos"
        searchable={false}
      />
      <MultiSelectField
        id="pac-filter-status"
        label="Status"
        options={PLAN_STATUSES.map((item) => ({ value: item.value, label: item.label }))}
        selectedValues={filters.statuses}
        onChange={(statuses) => patch({ statuses })}
        emptyLabel="Todos"
      />
      <MultiSelectField
        id="pac-filter-severity"
        label="Severidade"
        options={PLAN_SEVERITIES.map((item) => ({ value: item.value, label: item.label }))}
        selectedValues={filters.severities}
        onChange={(severities) => patch({ severities })}
        emptyLabel="Todas"
      />
      <MultiSelectField
        id="pac-filter-branch"
        label="Filial"
        options={PAC_BRANCH_OPTIONS.map((item) => ({ value: item.value, label: item.label }))}
        selectedValues={filters.branches}
        onChange={(branches) => patch({ branches })}
        emptyLabel="Todas"
        searchable={false}
      />
      <TextField
        id="pac-filter-customer"
        label="Cliente"
        value={filters.customerName}
        onChange={(customerName) => patch({ customerName })}
        placeholder="Filtrar por cliente"
        type="search"
      />
      <TextField
        id="pac-filter-product"
        label="Produto"
        value={filters.productCode}
        onChange={(productCode) => patch({ productCode })}
        placeholder="Código do produto"
        type="search"
      />
    </FilterBar>
  );
}
