import type { FilterFormState, DespesasFiltrosData } from "../types/despesasCentroCusto";
import { formatCostCenterLabel, formatSupplierLabel } from "../utils/formatters";

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
  const update = (patch: Partial<FilterFormState>) => {
    onChange(patch);
  };

  return (
    <section className="fcc-card fcc-filters" aria-label="Filtros">
      <div className="fcc-filters__grid">
        <label className="fcc-field">
          <span>Período inicial</span>
          <input
            type="date"
            value={filters.startDate}
            onChange={(event) => update({ startDate: event.target.value })}
          />
        </label>

        <label className="fcc-field">
          <span>Período final</span>
          <input
            type="date"
            value={filters.endDate}
            onChange={(event) => update({ endDate: event.target.value })}
          />
        </label>

        <label className="fcc-field">
          <span>Filial</span>
          <select
            value={filters.branch}
            onChange={(event) => update({ branch: event.target.value })}
          >
            <option value="">Todas</option>
            {(options?.filiais ?? []).map((filial) => (
              <option key={filial.codigo} value={filial.codigo}>
                Filial {filial.codigo}
              </option>
            ))}
          </select>
        </label>

        <label className="fcc-field">
          <span>Centro de custo</span>
          <select
            value={filters.costCenter}
            onChange={(event) => update({ costCenter: event.target.value })}
          >
            <option value="">Todos</option>
            {(options?.centros_custo ?? []).map((centro) => (
              <option key={centro.codigo} value={centro.codigo}>
                {formatCostCenterLabel(centro.codigo, centro.descricao)}
              </option>
            ))}
          </select>
        </label>

        <label className="fcc-field">
          <span>Fornecedor</span>
          <select
            value={filters.supplierKey}
            onChange={(event) => update({ supplierKey: event.target.value })}
            disabled={loading && !options?.fornecedores?.length}
          >
            <option value="">Todos</option>
            {(options?.fornecedores ?? []).map((fornecedor) => {
              const key = `${fornecedor.codigo}|${fornecedor.loja}`;
              return (
                <option key={key} value={key}>
                  {formatSupplierLabel(
                    fornecedor.codigo,
                    fornecedor.loja,
                    fornecedor.razao_social,
                  )}
                </option>
              );
            })}
          </select>
        </label>
      </div>

      <div className="fcc-filters__actions">
        <button
          type="button"
          className="fcc-btn fcc-btn--secondary"
          onClick={onClear}
          disabled={loading}
        >
          Limpar filtros
        </button>
      </div>
    </section>
  );
}
