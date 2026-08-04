import type { CustomerBillingPeriodPreset, CustomerBillingSituationFilter } from "../types/customerBilling";

type CustomerBillingFiltersProps = {
  preset: CustomerBillingPeriodPreset;
  startDate: string;
  endDate: string;
  situation: CustomerBillingSituationFilter;
  search: string;
  validationError: string | null;
  disabled?: boolean;
  onPresetChange: (value: CustomerBillingPeriodPreset) => void;
  onStartDateChange: (value: string) => void;
  onEndDateChange: (value: string) => void;
  onSituationChange: (value: CustomerBillingSituationFilter) => void;
  onSearchChange: (value: string) => void;
};

const PRESETS: { id: CustomerBillingPeriodPreset; label: string }[] = [
  { id: "30", label: "Últimos 30 dias" },
  { id: "90", label: "Últimos 90 dias" },
  { id: "180", label: "Últimos 180 dias" },
  { id: "365", label: "Últimos 12 meses" },
  { id: "custom", label: "Personalizado" },
];

export function CustomerBillingFilters({
  preset,
  startDate,
  endDate,
  situation,
  search,
  validationError,
  disabled,
  onPresetChange,
  onStartDateChange,
  onEndDateChange,
  onSituationChange,
  onSearchChange,
}: CustomerBillingFiltersProps) {
  return (
    <section className="pva-billing-filters" aria-label="Filtros de faturamento">
      <div className="pva-billing-filters__presets" role="group" aria-label="Período">
        {PRESETS.map((item) => (
          <button
            key={item.id}
            type="button"
            className={
              preset === item.id
                ? "pva-customers-filters__chip pva-customers-filters__chip--active"
                : "pva-customers-filters__chip"
            }
            aria-pressed={preset === item.id}
            disabled={disabled}
            onClick={() => onPresetChange(item.id)}
          >
            {item.label}
          </button>
        ))}
      </div>

      <div className="pva-billing-filters__dates">
        <label className="pva-customers-filters__label" htmlFor="pva-billing-start">
          Data inicial
          <input
            id="pva-billing-start"
            type="date"
            className="pva-input"
            value={startDate}
            disabled={disabled}
            onChange={(event) => onStartDateChange(event.target.value)}
          />
        </label>
        <label className="pva-customers-filters__label" htmlFor="pva-billing-end">
          Data final
          <input
            id="pva-billing-end"
            type="date"
            className="pva-input"
            value={endDate}
            disabled={disabled}
            onChange={(event) => onEndDateChange(event.target.value)}
          />
        </label>
        <label className="pva-customers-filters__label" htmlFor="pva-billing-situation">
          Situação
          <select
            id="pva-billing-situation"
            className="pva-input"
            value={situation}
            disabled={disabled}
            onChange={(event) =>
              onSituationChange(event.target.value as CustomerBillingSituationFilter)
            }
          >
            <option value="all">Todas</option>
            <option value="emitted">Emitidas</option>
            <option value="return">Devoluções</option>
          </select>
        </label>
        <label className="pva-customers-filters__label" htmlFor="pva-billing-search">
          Busca
          <input
            id="pva-billing-search"
            type="search"
            className="pva-input"
            placeholder="Nota, série, pedido ou produto"
            value={search}
            disabled={disabled}
            onChange={(event) => onSearchChange(event.target.value)}
          />
        </label>
      </div>

      {validationError ? (
        <p className="pva-alert pva-alert--warning" role="alert">
          {validationError}
        </p>
      ) : null}

      <p className="pva-billing-filters__hint">
        Notas canceladas no Protheus (exclusão lógica) não aparecem nesta lista.
      </p>
    </section>
  );
}
