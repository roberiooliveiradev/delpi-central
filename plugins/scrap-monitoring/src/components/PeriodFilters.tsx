import type { FilterFormState, ScrapFiltrosData } from "../types/scrap";
import { validatePeriodRange } from "../utils/dateRange";

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

  return (
    <section className="sm-filter-bar sm-card" aria-label="Filtros de refugos">
      <div className="sm-filter-bar__grid">
        <label className="sm-field" htmlFor="sm-filter-start">
          <span className="sm-field__label">Data inicial</span>
          <input
            id="sm-filter-start"
            className="sm-field__input"
            type="date"
            value={filters.dataInicio}
            onChange={(event) => onChange({ dataInicio: event.target.value })}
          />
        </label>
        <label className="sm-field" htmlFor="sm-filter-end">
          <span className="sm-field__label">Data final</span>
          <input
            id="sm-filter-end"
            className="sm-field__input"
            type="date"
            value={filters.dataFim}
            onChange={(event) => onChange({ dataFim: event.target.value })}
          />
        </label>
        <label className="sm-field" htmlFor="sm-filter-mp">
          <span className="sm-field__label">Matéria-prima</span>
          <select
            id="sm-filter-mp"
            className="sm-field__input"
            value={filters.mp}
            onChange={(event) => onChange({ mp: event.target.value })}
            disabled={busy}
          >
            <option value="">Todas</option>
            {options.materiasPrimas.map((item) => (
              <option key={item.codigo} value={item.codigo}>
                {optionLabel(item.codigo, item.descricao)}
              </option>
            ))}
          </select>
        </label>
        <label className="sm-field" htmlFor="sm-filter-pa">
          <span className="sm-field__label">Produto acabado</span>
          <select
            id="sm-filter-pa"
            className="sm-field__input"
            value={filters.pa}
            onChange={(event) => onChange({ pa: event.target.value })}
            disabled={busy}
          >
            <option value="">Todos</option>
            {options.produtosAcabados.map((item) => (
              <option key={item.codigo} value={item.codigo}>
                {optionLabel(item.codigo, item.descricao)}
              </option>
            ))}
          </select>
        </label>
        <label className="sm-field" htmlFor="sm-filter-op">
          <span className="sm-field__label">Ordem de produção</span>
          <select
            id="sm-filter-op"
            className="sm-field__input"
            value={filters.op}
            onChange={(event) => onChange({ op: event.target.value })}
            disabled={busy}
          >
            <option value="">Todas</option>
            {options.ordensProducao.map((item) => (
              <option key={item.codigo} value={item.codigo}>
                {item.codigo}
              </option>
            ))}
          </select>
        </label>
        <label className="sm-field" htmlFor="sm-filter-motivo">
          <span className="sm-field__label">Motivo</span>
          <select
            id="sm-filter-motivo"
            className="sm-field__input"
            value={filters.motivo}
            onChange={(event) => onChange({ motivo: event.target.value })}
            disabled={busy}
          >
            <option value="">Todos</option>
            {options.motivos.map((item) => (
              <option key={item.codigo} value={item.codigo}>
                {optionLabel(item.codigo, item.descricao)}
              </option>
            ))}
          </select>
        </label>
        <label className="sm-field" htmlFor="sm-filter-centro">
          <span className="sm-field__label">Centro de trabalho</span>
          <input
            id="sm-filter-centro"
            className="sm-field__input"
            type="text"
            placeholder="Ex.: CT-23"
            value={filters.centroTrabalho}
            onChange={(event) => onChange({ centroTrabalho: event.target.value })}
          />
        </label>
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
    </section>
  );
}
