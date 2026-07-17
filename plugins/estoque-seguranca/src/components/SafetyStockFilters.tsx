import type { SafetyStockFiltersData, SafetyStockQueryParams } from "../types/safetyStock";
import {
  SAFETY_STOCK_STATUS_LABELS,
  branchLabel,
} from "../utils/safetyStockStatus";
import { SORT_FIELD_OPTIONS } from "../types/safetyStock";
import {
  FilterBarShell,
  FilterCheckboxField,
  FilterInputField,
  FilterSelectField,
} from "./filtersUi";

type SafetyStockFiltersProps = {
  filters: SafetyStockQueryParams;
  options: SafetyStockFiltersData | null;
  loading?: boolean;
  onChange: (patch: Partial<SafetyStockQueryParams>) => void;
  onClear: () => void;
};

const STATUS_OPTIONS = Object.entries(SAFETY_STOCK_STATUS_LABELS).map(([value, label]) => ({
  value,
  label,
}));

export function SafetyStockFilters({
  filters,
  options,
  loading = false,
  onChange,
  onClear,
}: SafetyStockFiltersProps) {
  const branches = options?.authorized_branches ?? [];
  const branchOptions = branches.map((branch) => ({
    value: branch,
    label: branchLabel(branch),
  }));

  const groupOptions = (options?.product_groups ?? []).map((group) => ({
    value: group,
    label: group,
  }));

  const unitOptions = (options?.units ?? []).map((unit) => ({
    value: unit,
    label: unit,
  }));

  return (
    <FilterBarShell>
      <div className="ess-filters__primary">
        <FilterSelectField
          id="ess-filter-branch"
          label="Filial"
          value={filters.branch}
          options={branchOptions}
          placeholderOption="Selecione a filial"
          onChange={(value) => onChange({ branch: value })}
          disabled={loading || branchOptions.length === 0}
        />

        <FilterInputField
          id="ess-filter-search"
          label="Busca"
          type="search"
          value={filters.search}
          placeholder="Código ou descrição"
          onChange={(value) => onChange({ search: value })}
          disabled={loading || !filters.branch}
        />

        <FilterSelectField
          id="ess-filter-status"
          label="Situação"
          value={filters.status}
          options={STATUS_OPTIONS}
          placeholderOption="Todas"
          onChange={(value) => onChange({ status: value as SafetyStockQueryParams["status"] })}
          disabled={loading || !filters.branch}
        />
      </div>

      <div className="ess-filters__secondary">
        <FilterSelectField
          id="ess-filter-group"
          label="Grupo"
          value={filters.productGroup}
          options={groupOptions}
          placeholderOption="Todos"
          onChange={(value) => onChange({ productGroup: value })}
          disabled={loading || !filters.branch}
        />

        <FilterSelectField
          id="ess-filter-unit"
          label="Unidade"
          value={filters.unit}
          options={unitOptions}
          placeholderOption="Todas"
          onChange={(value) => onChange({ unit: value })}
          disabled={loading || !filters.branch}
        />

        <FilterSelectField
          id="ess-filter-sort-by"
          label="Ordenar por"
          value={filters.sortBy}
          options={SORT_FIELD_OPTIONS}
          onChange={(value) =>
            onChange({ sortBy: value as SafetyStockQueryParams["sortBy"] })
          }
          disabled={loading || !filters.branch}
        />

        <FilterSelectField
          id="ess-filter-sort-direction"
          label="Direção"
          value={filters.sortDirection}
          options={[
            { value: "asc", label: "Crescente" },
            { value: "desc", label: "Decrescente" },
          ]}
          onChange={(value) =>
            onChange({ sortDirection: value as SafetyStockQueryParams["sortDirection"] })
          }
          disabled={loading || !filters.branch}
        />
      </div>

      <div className="ess-filters__footer">
        <div className="ess-filters__options">
          <FilterCheckboxField
            id="ess-filter-include-blocked"
            label="Bloqueados"
            checked={filters.includeBlocked}
            checkboxLabel="Incluir produtos bloqueados"
            onChange={(checked) => onChange({ includeBlocked: checked })}
            disabled={loading || !filters.branch}
          />

          <FilterCheckboxField
            id="ess-filter-include-without"
            label="Sem ESTSEG"
            checked={filters.includeWithoutSafetyStock}
            checkboxLabel="Incluir sem estoque de segurança"
            onChange={(checked) => onChange({ includeWithoutSafetyStock: checked })}
            disabled={loading || !filters.branch}
          />
        </div>

        <button
          type="button"
          className="ess-btn ess-btn--secondary"
          onClick={onClear}
          disabled={loading}
        >
          Limpar filtros
        </button>
      </div>
    </FilterBarShell>
  );
}
