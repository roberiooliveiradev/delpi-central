import { useCallback, useState } from "react";
import { Filter } from "lucide-react";

import { buildSuppliesUnitOptions } from "../../app/suppliesUnits";
import { useCommittedTextFilter } from "../../app/useCommittedTextFilter";
import {
  SuppliesActionButton,
  SuppliesClearFiltersButton,
  SuppliesDateField,
  SuppliesFilterBarShell,
  SuppliesMultiSelectField,
  SuppliesSectionHintLabel,
  SuppliesTextField,
  spFiltersKit,
} from "../../app/suppliesUi";
import { SP_HELP } from "../../content/helpTooltips";
import { PURCHASE_ORDERS_CONTENT as C } from "./content";
import { hasActivePurchaseOrdersFilters } from "./hasActiveFilters";
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
  const [showMore, setShowMore] = useState(false);
  const unitOptions = buildSuppliesUnitOptions(units);
  const hasActiveFilters = hasActivePurchaseOrdersFilters(query, units);

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
            <div className="sp-filter-bar__header-actions">
              <SuppliesActionButton
                type="button"
                variant="ghost"
                onClick={() => setShowMore((value) => !value)}
              >
                {showMore ? C.lessFilters : C.moreFilters}
              </SuppliesActionButton>
              {hasActiveFilters ? (
                <SuppliesClearFiltersButton
                  density="compact"
                  label={C.clearFilters}
                  onClick={onClear}
                />
              ) : null}
            </div>
          </div>
        }
      >
        <FiltersRow variant="extended">
          <SuppliesMultiSelectField
            className="sp-purchase-orders__unit-filter"
            label={C.branchLabel}
            hint={SP_HELP.purchaseOrdersBranch}
            selectedValues={query.branches}
            onChange={(values) => onPatch({ branches: values, page: 1, order: "" })}
            options={unitOptions}
            emptyLabel="Todas"
            searchable={unitOptions.length > 4}
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
          {showMore ? (
            <>
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
            </>
          ) : null}
        </FiltersRow>
      </SuppliesFilterBarShell>
    </form>
  );
}
