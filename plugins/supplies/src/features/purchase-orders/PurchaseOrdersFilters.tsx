import { useCallback } from "react";

import { buildSuppliesUnitOptions } from "../../app/suppliesUnits";
import { useCommittedTextFilter } from "../../app/useCommittedTextFilter";
import {
  SuppliesActionButton,
  SuppliesDateField,
  SuppliesFilterBarShell,
  SuppliesSelectField,
  SuppliesTextField,
  spFiltersKit,
} from "../../app/suppliesUi";
import { SP_HELP } from "../../content/helpTooltips";
import { PURCHASE_ORDERS_CONTENT as C } from "./content";
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
      <SuppliesFilterBarShell embedded ariaLabel={C.filtersAriaLabel}>
        <FiltersRow variant="extended">
          <SuppliesSelectField
            label={C.branchLabel}
            hint={SP_HELP.purchaseOrdersBranch}
            value={query.branch}
            onChange={(value) => onPatch({ branch: value, page: 1, order: "" })}
            options={unitOptions}
            allowEmpty={false}
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
        </FiltersRow>
      </SuppliesFilterBarShell>
      <div className="sp-list-filters__actions sp-purchase-orders__filter-actions">
        <p className="sp-list-filters__hint">{SP_HELP.purchaseOrdersFiltersAuto}</p>
        <SuppliesActionButton type="button" variant="ghost" onClick={onClear}>
          {C.clearFilters}
        </SuppliesActionButton>
      </div>
    </form>
  );
}
