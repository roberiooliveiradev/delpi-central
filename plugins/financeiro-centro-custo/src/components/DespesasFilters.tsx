import type { FilterFormState, DespesasFiltrosData } from "../types/despesasCentroCusto";
import { formatCostCenterLabel, formatSupplierLabel } from "../utils/formatters";
import { FilterBarShell, FilterInputField, FilterSelectField } from "./filtersUi";

type DespesasFiltersProps = {
  filters: FilterFormState;
  options: DespesasFiltrosData | null;
  loading?: boolean;
  onChange: (patch: Partial<FilterFormState>) => void;
  onClear: () => void;
};

export function DespesasFilters({
  filters,
  options,
  loading = false,
  onChange,
  onClear,
}: DespesasFiltersProps) {
  const filialOptions = (options?.filiais ?? []).map((filial) => ({
    value: filial.codigo,
    label: `Filial ${filial.codigo}`,
  }));

  const centroOptions = (options?.centros_custo ?? []).map((centro) => ({
    value: centro.codigo,
    label: formatCostCenterLabel(centro.codigo, centro.descricao),
  }));

  const fornecedorOptions = (options?.fornecedores ?? []).map((fornecedor) => {
    const key = `${fornecedor.codigo}|${fornecedor.loja}`;
    return {
      value: key,
      label: formatSupplierLabel(
        fornecedor.codigo,
        fornecedor.loja,
        fornecedor.razao_social,
      ),
    };
  });

  return (
    <FilterBarShell>
      <div className="fcc-filter-bar__grid fcc-filters__grid">
        <FilterInputField
          id="fcc-filter-start"
          label="Período inicial"
          type="date"
          value={filters.startDate}
          onChange={(value) => onChange({ startDate: value })}
        />
        <FilterInputField
          id="fcc-filter-end"
          label="Período final"
          type="date"
          value={filters.endDate}
          onChange={(value) => onChange({ endDate: value })}
        />
        <FilterSelectField
          id="fcc-filter-branch"
          label="Filial"
          value={filters.branch}
          onChange={(value) => onChange({ branch: value })}
          options={filialOptions}
          placeholderOption="Todas"
        />
        <FilterSelectField
          id="fcc-filter-cost-center"
          label="Centro de custo"
          value={filters.costCenter}
          onChange={(value) => onChange({ costCenter: value })}
          options={centroOptions}
          placeholderOption="Todos"
        />
        <FilterSelectField
          id="fcc-filter-supplier"
          label="Fornecedor"
          value={filters.supplierKey}
          onChange={(value) => onChange({ supplierKey: value })}
          options={fornecedorOptions}
          placeholderOption="Todos"
          disabled={loading && !options?.fornecedores?.length}
        />
      </div>

      <div className="fcc-filter-bar__actions fcc-filters__actions">
        <button
          type="button"
          className="fcc-btn fcc-btn--secondary"
          onClick={onClear}
          disabled={loading}
        >
          Limpar filtros
        </button>
      </div>
    </FilterBarShell>
  );
}
