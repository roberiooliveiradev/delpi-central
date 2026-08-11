import { HelpTooltip, SegmentToggle } from "@delpi/plugin-ui/index";

import {
  CommercialDateField,
  CommercialFilterBarShell,
  CommercialSelectField,
  CommercialStateBanner,
  CommercialTextField,
  UI_PREFIX,
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

      <CommercialFilterBarShell
        embedded
        layout="grid"
        ariaLabel="Período"
        leading={
          <SegmentToggle
            prefix={UI_PREFIX}
            ariaLabel="Período"
            idPrefix="customer-billing-period"
            value={preset}
            disabled={disabled}
            onChange={onPresetChange}
            options={PRESETS.map((item) => ({
              value: item.id,
              label: item.label,
            }))}
          />
        }
      >
        <CommercialDateField
          label="Data inicial"
          value={startDate}
          onChange={onStartDateChange}
          disabled={disabled}
        />
        <CommercialDateField
          label="Data final"
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
      </CommercialFilterBarShell>

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
