import { HelpTooltip } from "@delpi/plugin-ui/index";

import {
  CommercialDateField,
  CommercialFilterBarShell,
  CommercialSectionCard,
  CommercialSectionHintLabel,
  CommercialSegmentToggle,
  CommercialSelectField,
  CommercialStateBanner,
  CommercialTextField,
} from "../../../../app/commercialUi";
import {
  BILLING_METRIC_CONTENT,
  type PortfolioBillingMetric,
} from "../../../../content/billingMetric";
import { CUSTOMER_BILLING_CONTENT } from "../../../../content/customerBillingContent";
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
  billingMetric: PortfolioBillingMetric;
  onBillingMetricChange: (value: PortfolioBillingMetric) => void;
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
  billingMetric,
  onBillingMetricChange,
  onPresetChange,
  onStartDateChange,
  onEndDateChange,
  onSituationChange,
  onSearchChange,
}: CustomerBillingFiltersProps) {
  return (
    <CommercialSectionCard
      title={CUSTOMER_BILLING_CONTENT.filtersSectionTitle}
      hint={CM_HELP.customerDetail.billingFilters}
      collapsible
      defaultOpen
      className="cm-customer-billing-filters"
    >
      <p
        className="cm-customer-billing-filters__hint"
        style={{ display: "flex", alignItems: "center", gap: 6 }}
      >
        {CUSTOMER_BILLING_CONTENT.filtersIntro}
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
          <CommercialSegmentToggle
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
          hint={CM_HELP.customerDetail.billingFilterDateStart}
          value={startDate}
          onChange={onStartDateChange}
          disabled={disabled}
        />
        <CommercialDateField
          label="Data final"
          hint={CM_HELP.customerDetail.billingFilterDateEnd}
          value={endDate}
          onChange={onEndDateChange}
          disabled={disabled}
        />
        <CommercialSelectField
          label="Situação"
          hint={CM_HELP.customerDetail.billingFilterSituation}
          options={[...SITUATION_OPTIONS]}
          value={situation}
          onChange={(value) => onSituationChange(value as CustomerBillingSituationFilter)}
          allowEmpty={false}
          disabled={disabled}
        />
        <CommercialTextField
          label="Busca"
          hint={CM_HELP.customerDetail.billingFilterSearch}
          type="search"
          value={search}
          onChange={onSearchChange}
          placeholder="Nota, série, pedido ou produto"
          disabled={disabled}
        />
        <div className="cm-field">
          <CommercialSectionHintLabel
            label="Métrica"
            hint={CM_HELP.customers.billingMetric}
          />
          <CommercialSegmentToggle
            ariaLabel={CM_HELP.customers.billingMetric}
            idPrefix="customer-billing-metric"
            value={billingMetric}
            widthMode="content"
            disabled={disabled}
            onChange={(value) => {
              if (value === "value" || value === "quantity") {
                onBillingMetricChange(value);
              }
            }}
            options={[
              {
                value: "value",
                label: BILLING_METRIC_CONTENT.value.shortLabel,
              },
              {
                value: "quantity",
                label: BILLING_METRIC_CONTENT.quantity.shortLabel,
              },
            ]}
          />
        </div>
      </CommercialFilterBarShell>

      {validationError ? (
        <CommercialStateBanner>
          {validationError}
        </CommercialStateBanner>
      ) : null}
    </CommercialSectionCard>
  );
}
