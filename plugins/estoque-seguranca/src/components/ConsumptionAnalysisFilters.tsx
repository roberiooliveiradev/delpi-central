import type { SafetyStockFiltersData } from "../types/safetyStock";
import type { ConsumptionAnalysisQueryParams } from "../types/consumptionAnalysis";
import { ANALYSIS_SORT_FIELD_OPTIONS } from "../types/consumptionAnalysis";
import {
  ANALYSIS_STATUS_LABELS,
  branchLabel,
} from "../utils/safetyStockStatus";
import {
  FilterBarShell,
  FilterCheckboxField,
  FilterInputField,
  FilterSelectField,
} from "./filtersUi";

type ConsumptionAnalysisFiltersProps = {
  filters: ConsumptionAnalysisQueryParams;
  options: SafetyStockFiltersData | null;
  loading?: boolean;
  onChange: (patch: Partial<ConsumptionAnalysisQueryParams>) => void;
  onClear: () => void;
};

const STATUS_OPTIONS = Object.entries(ANALYSIS_STATUS_LABELS).map(([value, label]) => ({
  value,
  label,
}));

export function ConsumptionAnalysisFilters({
  filters,
  options,
  loading = false,
  onChange,
  onClear,
}: ConsumptionAnalysisFiltersProps) {
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
          id="ess-analysis-branch"
          label="Filial"
          value={filters.branch}
          options={branchOptions}
          placeholderOption="Selecione a filial"
          onChange={(value) => onChange({ branch: value })}
          disabled={loading || branchOptions.length === 0}
        />
        <FilterInputField
          id="ess-analysis-search"
          label="Busca"
          type="search"
          value={filters.search}
          placeholder="Código ou descrição"
          onChange={(value) => onChange({ search: value })}
          disabled={loading || !filters.branch}
        />
        <FilterSelectField
          id="ess-analysis-status"
          label="Situação vs sugerido"
          value={filters.analysisStatus}
          options={STATUS_OPTIONS}
          placeholderOption="Todas"
          onChange={(value) =>
            onChange({
              analysisStatus: value as ConsumptionAnalysisQueryParams["analysisStatus"],
            })
          }
          disabled={loading || !filters.branch}
        />
      </div>

      <div className="ess-filters__secondary">
        <FilterSelectField
          id="ess-analysis-group"
          label="Grupo"
          value={filters.productGroup}
          options={groupOptions}
          placeholderOption="Todos"
          onChange={(value) => onChange({ productGroup: value })}
          disabled={loading || !filters.branch}
        />
        <FilterSelectField
          id="ess-analysis-unit"
          label="Unidade"
          value={filters.unit}
          options={unitOptions}
          placeholderOption="Todas"
          onChange={(value) => onChange({ unit: value })}
          disabled={loading || !filters.branch}
        />
        <FilterSelectField
          id="ess-analysis-sort"
          label="Ordenar por"
          value={filters.sortBy}
          options={ANALYSIS_SORT_FIELD_OPTIONS}
          onChange={(value) =>
            onChange({ sortBy: value as ConsumptionAnalysisQueryParams["sortBy"] })
          }
          disabled={loading || !filters.branch}
        />
        <FilterSelectField
          id="ess-analysis-sort-dir"
          label="Direção"
          value={filters.sortDirection}
          options={[
            { value: "asc", label: "Crescente" },
            { value: "desc", label: "Decrescente" },
          ]}
          onChange={(value) =>
            onChange({
              sortDirection: value as ConsumptionAnalysisQueryParams["sortDirection"],
            })
          }
          disabled={loading || !filters.branch}
        />
        <FilterCheckboxField
          id="ess-analysis-blocked"
          label="Incluir bloqueados"
          checked={filters.includeBlocked}
          onChange={(checked) => onChange({ includeBlocked: checked })}
          disabled={loading || !filters.branch}
        />
        <button
          type="button"
          className="ess-btn ess-btn--ghost"
          onClick={onClear}
          disabled={loading}
        >
          Limpar filtros
        </button>
      </div>
    </FilterBarShell>
  );
}
