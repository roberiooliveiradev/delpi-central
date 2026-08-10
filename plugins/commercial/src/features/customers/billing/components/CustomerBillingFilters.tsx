import { ActionButton, HelpTooltip } from "@delpi/plugin-ui/index";

import {
  CommercialSelectField,
  CommercialStateBanner,
  CommercialTextField,
} from "../../../../app/commercialUi";
import { CM_HELP } from "../../../../content/helpTooltips";
import type {
  CustomerBillingPeriodPreset,
  CustomerBillingSituationFilter,
} from "../types/customerBilling";

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

const SITUATION_OPTIONS = [
  { value: "all", label: "Todas" },
  { value: "emitted", label: "Emitidas" },
  { value: "return", label: "Devoluções" },
] as const;

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
    <section className="cm-customer-billing-filters" aria-label="Filtros de faturamento">
      <p
        className="cm-customer-billing-filters__hint"
        style={{ display: "flex", alignItems: "center", gap: 6 }}
      >
        Período e situação das notas de saída deste cliente.
        <HelpTooltip
          content={CM_HELP.customerDetail.billingFilters}
          ariaLabel="Ajuda: Filtros de faturamento"
        />
      </p>

      <div className="cm-nav-row" role="group" aria-label="Período">
        {PRESETS.map((item) => (
          <ActionButton
            key={item.id}
            variant={preset === item.id ? "primary" : "ghost"}
            aria-pressed={preset === item.id}
            disabled={disabled}
            onClick={() => onPresetChange(item.id)}
          >
            {item.label}
          </ActionButton>
        ))}
      </div>

      <div className="cm-form-grid cm-customer-billing-filters__dates">
        <CommercialTextField
          label="Data inicial"
          type="date"
          value={startDate}
          onChange={onStartDateChange}
          disabled={disabled}
        />
        <CommercialTextField
          label="Data final"
          type="date"
          value={endDate}
          onChange={onEndDateChange}
          disabled={disabled}
        />
        <CommercialSelectField
          label="Situação"
          options={[...SITUATION_OPTIONS]}
          value={situation}
          onChange={(value) => onSituationChange(value as CustomerBillingSituationFilter)}
          allowEmpty={false}
          disabled={disabled}
        />
        <CommercialTextField
          label="Busca"
          type="search"
          value={search}
          onChange={onSearchChange}
          placeholder="Nota, série, pedido ou produto"
          disabled={disabled}
        />
      </div>

      {validationError ? (
        <CommercialStateBanner>
          {validationError}
        </CommercialStateBanner>
      ) : null}

      <p className="cm-customer-billing-filters__hint">
        Notas canceladas no Protheus (exclusão lógica) não aparecem nesta lista.
      </p>
    </section>
  );
}
