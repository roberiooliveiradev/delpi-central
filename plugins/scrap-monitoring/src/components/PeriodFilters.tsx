import type { FilterFormState, ScrapFiltrosData } from "../types/scrap";
import { validatePeriodRange } from "../utils/dateRange";
import { FilterBarShell, FilterInputField, FilterSelectField } from "./filtersUi";

export type QuickRangePreset = "12m" | "6m" | "thisMonth";

type PeriodFiltersProps = {
  filters: FilterFormState;
  options: ScrapFiltrosData;
  optionsLoading?: boolean;
  validationError: string | null;
  loading?: boolean;
  onChange: (patch: Partial<FilterFormState>) => void;
  onApply: () => void;
  onQuickRange: (preset: QuickRangePreset) => void;
  onClearOptional?: () => void;
};

function optionLabel(codigo: string, descricao?: string): string {
  const desc = descricao?.trim();
  return desc ? `${codigo} — ${desc}` : codigo;
}

export function PeriodFilters({
  filters,
  options,
  optionsLoading = false,
  validationError,
  loading = false,
  onChange,
  onApply,
  onQuickRange,
  onClearOptional,
}: PeriodFiltersProps) {
  const localError = validatePeriodRange(filters.dataInicio, filters.dataFim);
  const busy = loading || optionsLoading;

  const mpOptions = options.materiasPrimas.map((item) => ({
    value: item.codigo,
    label: optionLabel(item.codigo, item.descricao),
  }));
  const paOptions = options.produtosAcabados.map((item) => ({
    value: item.codigo,
    label: optionLabel(item.codigo, item.descricao),
  }));
  const opOptions = options.ordensProducao.map((item) => ({
    value: item.codigo,
    label: item.codigo,
  }));
  const motivoOptions = options.motivos.map((item) => ({
    value: item.codigo,
    label: optionLabel(item.codigo, item.descricao),
  }));

  return (
    <FilterBarShell>
      <div className="sm-filter-bar__grid">
        <FilterInputField
          id="sm-filter-start"
          label="Data inicial"
          type="date"
          value={filters.dataInicio}
          onChange={(value) => onChange({ dataInicio: value })}
        />
        <FilterInputField
          id="sm-filter-end"
          label="Data final"
          type="date"
          value={filters.dataFim}
          onChange={(value) => onChange({ dataFim: value })}
        />
        <FilterSelectField
          id="sm-filter-mp"
          label="Matéria-prima"
          value={filters.mp}
          onChange={(value) => onChange({ mp: value })}
          options={mpOptions}
          placeholderOption="Todas"
          searchable
          disabled={busy}
        />
        <FilterSelectField
          id="sm-filter-pa"
          label="Produto acabado"
          value={filters.pa}
          onChange={(value) => onChange({ pa: value })}
          options={paOptions}
          placeholderOption="Todos"
          searchable
          disabled={busy}
        />
        <FilterSelectField
          id="sm-filter-op"
          label="Ordem de produção"
          value={filters.op}
          onChange={(value) => onChange({ op: value })}
          options={opOptions}
          placeholderOption="Todas"
          searchable
          disabled={busy}
        />
        <FilterSelectField
          id="sm-filter-motivo"
          label="Motivo"
          value={filters.motivo}
          onChange={(value) => onChange({ motivo: value })}
          options={motivoOptions}
          placeholderOption="Todos"
          disabled={busy}
        />
        <FilterInputField
          id="sm-filter-centro"
          label="Centro de trabalho"
          type="text"
          placeholder="Ex.: CT-23"
          value={filters.centroTrabalho}
          onChange={(value) => onChange({ centroTrabalho: value })}
        />
      </div>
      {validationError || localError ? (
        <p className="sm-filters__error" role="alert">
          {validationError ?? localError}
        </p>
      ) : null}
      <div className="sm-filter-bar__actions">
        <button
          type="button"
          className="sm-btn sm-btn--primary"
          onClick={onApply}
          disabled={loading || Boolean(localError)}
        >
          Aplicar filtros
        </button>
        {onClearOptional ? (
          <button
            type="button"
            className="sm-btn sm-btn--secondary"
            onClick={onClearOptional}
            disabled={loading}
          >
            Limpar filtros
          </button>
        ) : null}
        <button
          type="button"
          className="sm-btn sm-btn--secondary"
          onClick={() => onQuickRange("thisMonth")}
          disabled={loading}
        >
          Este mês
        </button>
        <button
          type="button"
          className="sm-btn sm-btn--secondary"
          onClick={() => onQuickRange("6m")}
          disabled={loading}
        >
          Últimos 6 meses
        </button>
        <button
          type="button"
          className="sm-btn sm-btn--secondary"
          onClick={() => onQuickRange("12m")}
          disabled={loading}
        >
          Últimos 12 meses
        </button>
      </div>
    </FilterBarShell>
  );
}
