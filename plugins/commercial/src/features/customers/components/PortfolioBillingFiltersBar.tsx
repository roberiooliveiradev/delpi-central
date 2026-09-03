import type { ReactNode } from "react";

import {
  CommercialClearFiltersButton,
  CommercialDateField,
  CommercialFilterBarShell,
  CommercialMultiSelectField,
  CommercialScopeChipBar,
  CommercialSectionHintLabel,
  CommercialStateBanner,
} from "../../../app/commercialUi";
import { CM_HELP } from "../../../content/helpTooltips";
import { CUSTOMER_BILLING_CONTENT } from "../../../content/customerBillingContent";
import { BILLING_SERIES_PRESET_OPTIONS } from "../utils/billingSeriesPeriod";
import type { PortfolioBillingWorkspaceFilters } from "../hooks/usePortfolioBillingWorkspaceFilters";

type ProductOption = { value: string; label: string };

type PortfolioBillingFiltersBarProps = {
  filters: PortfolioBillingWorkspaceFilters;
  productOptions: ProductOption[];
  productGroupOptions: ProductOption[];
  /** Escopo de carteira compartilhado (hero). */
  sellerFilter?: ReactNode;
  className?: string;
};

export function PortfolioBillingFiltersBar({
  filters,
  productOptions,
  productGroupOptions,
  sellerFilter = null,
  className,
}: PortfolioBillingFiltersBarProps) {
  const periodChips = BILLING_SERIES_PRESET_OPTIONS.map((option) => ({
    id: option.id,
    label: option.label,
    active: filters.preset === option.id,
    onSelect: () => filters.setPreset(option.id),
  }));

  const marketChips = [
    {
      id: "all",
      label: CUSTOMER_BILLING_CONTENT.filterMarketEmpty,
      active: filters.selectedMarkets.length === 0,
      onSelect: () => filters.setSelectedMarkets([]),
    },
    {
      id: "domestic",
      label: CUSTOMER_BILLING_CONTENT.marketDomestic,
      active:
        filters.selectedMarkets.length === 1 &&
        filters.selectedMarkets[0] === "domestic",
      onSelect: () => filters.setSelectedMarkets(["domestic"]),
    },
    {
      id: "export",
      label: CUSTOMER_BILLING_CONTENT.marketExport,
      active:
        filters.selectedMarkets.length === 1 &&
        filters.selectedMarkets[0] === "export",
      onSelect: () => filters.setSelectedMarkets(["export"]),
    },
  ];

  return (
    <div className={["cm-portfolio-billing-filters", className].filter(Boolean).join(" ")}>
      <div className="cm-customers-page__chip-row">
        <CommercialScopeChipBar
          label={
            <CommercialSectionHintLabel
              label="Período"
              hint={CM_HELP.customers.billingSeriesPeriod}
            />
          }
          aria-label={CM_HELP.customers.billingSeriesPeriod}
          chips={periodChips}
        />
        <CommercialScopeChipBar
          label={
            <CommercialSectionHintLabel
              label={CUSTOMER_BILLING_CONTENT.filterMarket}
              hint={CM_HELP.customers.billingFilterMarket}
            />
          }
          aria-label={CM_HELP.customers.billingFilterMarket}
          chips={marketChips}
        />
      </div>
      <CommercialFilterBarShell
        embedded
        ariaLabel={CUSTOMER_BILLING_CONTENT.portfolioFiltersAria}
        className="cm-customers-page__filter-bar"
      >
        {filters.preset === "custom" ? (
          <>
            <CommercialDateField
              label="Data inicial"
              hint={CM_HELP.customerDetail.billingSeriesDateStart}
              value={filters.customStart}
              onChange={filters.setCustomStart}
            />
            <CommercialDateField
              label="Data final"
              hint={CM_HELP.customerDetail.billingSeriesDateEnd}
              value={filters.customEnd}
              onChange={filters.setCustomEnd}
            />
          </>
        ) : null}
        {filters.periodError ? (
          <CommercialStateBanner>{filters.periodError}</CommercialStateBanner>
        ) : null}
        <CommercialMultiSelectField
          className="cm-customers-page__search-field"
          label={CUSTOMER_BILLING_CONTENT.filterCustomer}
          hint={CM_HELP.customers.billingFilterCustomer}
          options={filters.customerOptions.map((customer) => ({
            value: customer.key,
            label: `${customer.nome} (${customer.codigo}/${customer.loja})`,
          }))}
          selectedValues={filters.selectedCustomerKeys}
          onChange={filters.setSelectedCustomerKeys}
          emptyLabel={CUSTOMER_BILLING_CONTENT.filterCustomerEmpty}
          searchable
        />
        <CommercialMultiSelectField
          className="cm-customers-page__search-field"
          label={CUSTOMER_BILLING_CONTENT.filterProductGroup}
          hint={CM_HELP.customers.billingFilterProductGroup}
          options={productGroupOptions}
          selectedValues={filters.selectedProductGroups}
          onChange={filters.setSelectedProductGroups}
          emptyLabel={CUSTOMER_BILLING_CONTENT.filterProductGroupEmpty}
          searchable
        />
        <CommercialMultiSelectField
          className="cm-customers-page__search-field"
          label={CUSTOMER_BILLING_CONTENT.filterProduct}
          hint={CM_HELP.customers.billingFilterProduct}
          options={productOptions}
          selectedValues={filters.selectedProductCodes}
          onChange={filters.setSelectedProductCodes}
          emptyLabel={CUSTOMER_BILLING_CONTENT.filterProductEmpty}
          searchable
        />
        {sellerFilter}
        {filters.hasActiveRecorteFilters ? (
          <div className="cm-customers-page__filter-actions">
            <CommercialClearFiltersButton onClick={filters.clearRecorteFilters} />
          </div>
        ) : null}
      </CommercialFilterBarShell>
    </div>
  );
}
