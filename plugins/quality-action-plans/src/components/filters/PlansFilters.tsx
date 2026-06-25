import { RefreshCw } from "lucide-react";

import {
  PAC_BRANCH_OPTIONS,
  PAC_NONCONFORMITY_SCOPES,
  PLAN_SEVERITIES,
  PLAN_STATUSES,
} from "../../constants/actionPlans";
import { EMPTY_PLANS_FILTERS, type PlansFilterState } from "../../utils/planFilters";
import { FilterBar } from "../ui/FilterBar";
import { MultiSelectField } from "../ui/MultiSelectField";
import { TextField } from "../ui/TextField";

type Props = {
  filters: PlansFilterState;
  onChange: (filters: PlansFilterState) => void;
  onRefresh: () => void;
  loading?: boolean;
};

function hasActiveFilters(filters: PlansFilterState): boolean {
  return (
    filters.statuses.length > 0
    || filters.severities.length > 0
    || filters.branches.length > 0
    || filters.scopes.length > 0
    || Boolean(filters.customerName.trim())
    || Boolean(filters.productCode.trim())
    || Boolean(filters.ownerUserId.trim())
    || Boolean(filters.department.trim())
    || Boolean(filters.rootCauseCategory.trim())
    || filters.overdueOnly
  );
}

export function PlansFilters({ filters, onChange, onRefresh, loading = false }: Props) {
  function patch(partial: Partial<PlansFilterState>) {
    onChange({ ...filters, ...partial });
  }

  return (
    <FilterBar
      actions={
        <>
          {hasActiveFilters(filters) ? (
            <button
              type="button"
              className="pac-ghost-btn"
              disabled={loading}
              onClick={() => onChange(EMPTY_PLANS_FILTERS)}
            >
              Limpar filtros
            </button>
          ) : (
            <span className="pac-filter-box__spacer" aria-hidden />
          )}
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
      <TextField
        id="pac-filter-owner"
        label="Responsável"
        value={filters.ownerUserId}
        onChange={(ownerUserId) => patch({ ownerUserId })}
        placeholder="ID ou usuário responsável"
        type="search"
      />
      <TextField
        id="pac-filter-department"
        label="Departamento"
        value={filters.department}
        onChange={(department) => patch({ department })}
        placeholder="Ex.: Pintura, Montagem"
        type="search"
      />
      <TextField
        id="pac-filter-root-cause"
        label="Causa raiz"
        value={filters.rootCauseCategory}
        onChange={(rootCauseCategory) => patch({ rootCauseCategory })}
        placeholder="Categoria ou texto da causa"
        type="search"
      />
      <div className="pac-filter-box pac-filter-box--checkbox">
        <label className="pac-checkbox pac-filter-checkbox" htmlFor="pac-filter-overdue">
          <input
            id="pac-filter-overdue"
            type="checkbox"
            checked={filters.overdueOnly}
            onChange={(event) => patch({ overdueOnly: event.target.checked })}
          />
          <span>Somente com ações atrasadas</span>
        </label>
      </div>
    </FilterBar>
  );
}
