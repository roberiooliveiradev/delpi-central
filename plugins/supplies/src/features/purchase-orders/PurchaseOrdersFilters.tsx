import {
  SuppliesActionButton,
  SuppliesDateField,
  SuppliesFilterBarShell,
  SuppliesSelectField,
  SuppliesSegmentToggle,
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
  onApply: () => void;
  onClear: () => void;
};

export function PurchaseOrdersFilters({
  query,
  units,
  onPatch,
  onApply,
  onClear,
}: PurchaseOrdersFiltersProps) {
  const { FiltersRow } = spFiltersKit;
  const unitOptions = units.map((unit) => ({ value: unit, label: unit }));

  return (
    <form
      className="sp-purchase-orders__filters"
      onSubmit={(event) => {
        event.preventDefault();
        onApply();
      }}
    >
      <SuppliesFilterBarShell
        embedded
        ariaLabel={C.filtersAriaLabel}
        leading={
          <div>
            <SuppliesSegmentToggle
              ariaLabel={C.lateOnlyLabel}
              idPrefix="po-late-only"
              size="sm"
              value={query.late_only ? "late" : "all"}
              onChange={(value) =>
                onPatch({ late_only: value === "late", page: 1 })
              }
              options={[
                { value: "all", label: C.lateOnlyNo },
                { value: "late", label: C.lateOnlyYes },
              ]}
            />
          </div>
        }
      >
        {null}
      </SuppliesFilterBarShell>
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
          value={query.order_number}
          onChange={(value) => onPatch({ order_number: value, page: 1 })}
          hint={SP_HELP.purchaseOrdersNumber}
        />
        <SuppliesTextField
          label={C.productLabel}
          value={query.product_code}
          onChange={(value) => onPatch({ product_code: value, page: 1 })}
          hint={SP_HELP.purchaseOrdersProduct}
        />
        <SuppliesTextField
          label={C.supplierLabel}
          value={query.supplier_code}
          onChange={(value) => onPatch({ supplier_code: value, page: 1 })}
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
      <div className="sp-purchase-orders__filter-actions">
        <SuppliesActionButton type="submit" variant="primary">
          {C.applyFilters}
        </SuppliesActionButton>
        <SuppliesActionButton type="button" variant="ghost" onClick={onClear}>
          {C.clearFilters}
        </SuppliesActionButton>
      </div>
    </form>
  );
}
