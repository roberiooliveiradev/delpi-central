import type { ReactNode } from "react";

import {
  CommercialFilterBarShell,
  CommercialMultiSelectField,
  CommercialStateBanner,
  cmFiltersKit,
} from "../../../app/commercialUi";
import { CM_HELP } from "../../../content/helpTooltips";
import { CUSTOMER_BILLING_CONTENT } from "../../../content/customerBillingContent";
import {
  PeriodCompareControls,
} from "../../analytics/components/PeriodCompareControls";
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
  const { FiltersRow } = cmFiltersKit;

  return (
    <div className={["cm-portfolio-billing-filters", className].filter(Boolean).join(" ")}>
      <CommercialFilterBarShell
        embedded
        ariaLabel={CUSTOMER_BILLING_CONTENT.portfolioFiltersAria}
        className="cm-customers-page__filter-bar"
      >
        <PeriodCompareControls
          idPrefix="portfolio-billing"
          variant="bare"
          size="sm"
          preset={filters.preset}
          onPresetChange={filters.setPreset}
          customStart={filters.customStart}
          customEnd={filters.customEnd}
          onCustomStartChange={filters.setCustomStart}
          onCustomEndChange={filters.setCustomEnd}
        />
        {filters.periodError ? (
          <CommercialStateBanner>{filters.periodError}</CommercialStateBanner>
        ) : null}
        <FiltersRow variant="extended">
          <CommercialMultiSelectField
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
            label={CUSTOMER_BILLING_CONTENT.filterProductGroup}
            hint={CM_HELP.customers.billingFilterProductGroup}
            options={productGroupOptions}
            selectedValues={filters.selectedProductGroups}
            onChange={filters.setSelectedProductGroups}
            emptyLabel={CUSTOMER_BILLING_CONTENT.filterProductGroupEmpty}
            searchable
          />
          <CommercialMultiSelectField
            label={CUSTOMER_BILLING_CONTENT.filterProduct}
            hint={CM_HELP.customers.billingFilterProduct}
            options={productOptions}
            selectedValues={filters.selectedProductCodes}
            onChange={filters.setSelectedProductCodes}
            emptyLabel={CUSTOMER_BILLING_CONTENT.filterProductEmpty}
            searchable
          />
          <CommercialMultiSelectField
            label={CUSTOMER_BILLING_CONTENT.filterMarket}
            hint={CM_HELP.customers.billingFilterMarket}
            options={[
              { value: "domestic", label: CUSTOMER_BILLING_CONTENT.marketDomestic },
              { value: "export", label: CUSTOMER_BILLING_CONTENT.marketExport },
            ]}
            selectedValues={filters.selectedMarkets}
            onChange={(values) =>
              filters.setSelectedMarkets(
                values.filter((value): value is "domestic" | "export" =>
                  value === "domestic" || value === "export",
                ),
              )
            }
            emptyLabel={CUSTOMER_BILLING_CONTENT.filterMarketEmpty}
          />
          {sellerFilter}
        </FiltersRow>
      </CommercialFilterBarShell>
    </div>
  );
}
