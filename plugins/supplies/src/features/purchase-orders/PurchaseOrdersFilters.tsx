import { useCallback } from "react";
import { Filter } from "lucide-react";

import {
  buildSuppliesUnitOptions,
  canonicalizeUiBranches,
  SUPPLIES_UNIT_FILTER_LABEL,
} from "../../app/suppliesUnits";
import { useCommittedTextFilter } from "../../app/useCommittedTextFilter";
import {
  SuppliesClearFiltersButton,
  SuppliesDateField,
  SuppliesFilterBarShell,
  SuppliesMultiSelectField,
  SuppliesSectionHintLabel,
  SuppliesSegmentToggle,
  SuppliesTextField,
  spFiltersKit,
} from "../../app/suppliesUi";
import { SP_HELP } from "../../content/helpTooltips";
import { PURCHASE_ORDERS_CONTENT as C } from "./content";
import { hasActivePurchaseOrdersFilters } from "./hasActiveFilters";
import {
  matchPurchaseOrdersPeriod,
  PURCHASE_ORDERS_PERIOD_OPTIONS,
  resolvePurchaseOrdersPeriod,
  type PurchaseOrdersPeriodId,
} from "./purchaseOrdersPeriod";
import type { PurchaseOrdersQuery } from "./types";

type PurchaseOrdersFiltersProps = {
  query: PurchaseOrdersQuery;
  units: readonly string[];
  onPatch: (patch: Partial<PurchaseOrdersQuery>) => void;
  onClear: () => void;
};

export function PurchaseOrdersFilters({
  query,
  units,
  onPatch,
  onClear,
}: PurchaseOrdersFiltersProps) {
  const { FiltersRow } = spFiltersKit;
  const unitOptions = buildSuppliesUnitOptions(units);
  const hasActiveFilters = hasActivePurchaseOrdersFilters(query, units);
  const period = matchPurchaseOrdersPeriod(
    query.expected_delivery_from,
    query.expected_delivery_to,
  );

  const commitOrderNumber = useCallback(
    (value: string) => onPatch({ order_number: value, page: 1 }),
    [onPatch],
  );
  const commitProduct = useCallback(
    (value: string) => onPatch({ product_code: value, page: 1 }),
    [onPatch],
  );
  const commitSupplier = useCallback(
    (value: string) => onPatch({ supplier_code: value, page: 1 }),
    [onPatch],
  );

  const orderNumber = useCommittedTextFilter(query.order_number, commitOrderNumber);
  const product = useCommittedTextFilter(query.product_code, commitProduct);
  const supplier = useCommittedTextFilter(query.supplier_code, commitSupplier);

  const flushTextFilters = () => {
    orderNumber.flush();
    product.flush();
    supplier.flush();
  };

  const onPeriod = (value: PurchaseOrdersPeriodId) => {
    if (value === "custom") return;
    const resolved = resolvePurchaseOrdersPeriod(value);
    if (resolved === "unbounded") {
      onPatch({
        expected_delivery_from: "",
        expected_delivery_to: "",
        page: 1,
      });
      return;
    }
    if (!resolved) return;
    onPatch({
      expected_delivery_from: resolved.from,
      expected_delivery_to: resolved.to,
      page: 1,
    });
  };

  return (
    <form
      className="sp-list-filters sp-purchase-orders__filters"
      onSubmit={(event) => {
        event.preventDefault();
        flushTextFilters();
      }}
    >
      <SuppliesFilterBarShell
        embedded
        ariaLabel={C.filtersAriaLabel}
        leading={
          <div className="sp-filter-bar__period-block">
            <div className="sp-filter-bar__header">
              <div className="sp-filter-bar__title">
                <Filter size={18} aria-hidden="true" />
                <h2>
                  <SuppliesSectionHintLabel
                    label={C.filtersTitle}
                    hint={SP_HELP.purchaseOrdersFilters}
                  />
                </h2>
              </div>
              {hasActiveFilters ? (
                <div className="sp-filter-bar__header-actions">
                  <SuppliesClearFiltersButton
                    density="compact"
                    label={C.clearFilters}
                    onClick={onClear}
                  />
                </div>
              ) : null}
            </div>
            <div className="sp-purchase-orders__period-presets">
              <SuppliesSectionHintLabel
                label={C.periodLabel}
                hint={SP_HELP.purchaseOrdersDelivery}
              />
              <SuppliesSegmentToggle
                ariaLabel={C.periodLabel}
                idPrefix="purchase-orders-period-preset"
                size="sm"
                value={period}
                onChange={(value) => onPeriod(value as PurchaseOrdersPeriodId)}
                options={PURCHASE_ORDERS_PERIOD_OPTIONS}
              />
            </div>
          </div>
        }
      >
        {null}
      </SuppliesFilterBarShell>
      <FiltersRow variant="extended">
        <SuppliesDateField
          label={C.deliveryFromLabel}
          value={query.expected_delivery_from}
          onChange={(value) => onPatch({ expected_delivery_from: value, page: 1 })}
          hint={SP_HELP.purchaseOrdersDelivery}
        />
        <SuppliesDateField
          label={C.deliveryToLabel}
          value={query.expected_delivery_to}
          onChange={(value) => onPatch({ expected_delivery_to: value, page: 1 })}
          hint={SP_HELP.purchaseOrdersDelivery}
        />
        <SuppliesMultiSelectField
          className="sp-purchase-orders__unit-filter"
          label={SUPPLIES_UNIT_FILTER_LABEL}
          hint={SP_HELP.purchaseOrdersBranch}
          selectedValues={query.branches}
          onChange={(values) =>
            onPatch({
              branches: canonicalizeUiBranches(values, units),
              page: 1,
            })
          }
          options={unitOptions}
          emptyLabel="Todas"
          searchable
        />
        <SuppliesTextField
          label={C.orderNumberLabel}
          value={orderNumber.draft}
          onChange={orderNumber.setDraft}
          hint={SP_HELP.purchaseOrdersNumber}
        />
        <SuppliesTextField
          label={C.productLabel}
          value={product.draft}
          onChange={product.setDraft}
          hint={SP_HELP.purchaseOrdersProduct}
        />
        <SuppliesTextField
          label={C.supplierLabel}
          value={supplier.draft}
          onChange={supplier.setDraft}
          hint={SP_HELP.purchaseOrdersSupplier}
        />
      </FiltersRow>
    </form>
  );
}
