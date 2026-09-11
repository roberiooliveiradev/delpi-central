import {
  SuppliesActionButton,
  SuppliesDateField,
  SuppliesFilterBarShell,
  SuppliesSelectField,
  SuppliesTextField,
  spFiltersKit,
} from "../../app/suppliesUi";
import { SP_HELP } from "../../content/helpTooltips";
import { PURCHASE_REQUESTS_CONTENT as C } from "./content";
import { labelOverallStage } from "./query";
import type { OverallStage, PurchaseRequestsQuery } from "./types";
import { OVERALL_STAGE_VALUES } from "./types";

type PurchaseRequestsFiltersProps = {
  query: PurchaseRequestsQuery;
  units: readonly string[];
  onPatch: (patch: Partial<PurchaseRequestsQuery>) => void;
  onApply: () => void;
  onClear: () => void;
};

export function PurchaseRequestsFilters({
  query,
  units,
  onPatch,
  onApply,
  onClear,
}: PurchaseRequestsFiltersProps) {
  const { FiltersRow } = spFiltersKit;
  const unitOptions = units.map((unit) => ({ value: unit, label: unit }));
  const stageOptions = OVERALL_STAGE_VALUES.map((stage) => ({
    value: stage,
    label: labelOverallStage(stage),
  }));

  return (
    <form
      className="sp-purchase-requests__filters"
      onSubmit={(event) => {
        event.preventDefault();
        onApply();
      }}
    >
      <SuppliesFilterBarShell embedded ariaLabel={C.filtersAriaLabel}>
        <FiltersRow variant="extended">
          <SuppliesSelectField
            label={C.branchLabel}
            hint={SP_HELP.purchaseRequestsBranch}
            value={query.branch}
            onChange={(value) => onPatch({ branch: value, page: 1, request: "" })}
            options={unitOptions}
            allowEmpty={false}
            searchable={unitOptions.length > 4}
          />
          <SuppliesDateField
            label={C.dateFromLabel}
            value={query.date_from}
            onChange={(value) => onPatch({ date_from: value, page: 1 })}
            hint={SP_HELP.purchaseRequestsPeriod}
          />
          <SuppliesDateField
            label={C.dateToLabel}
            value={query.date_to}
            onChange={(value) => onPatch({ date_to: value, page: 1 })}
            hint={SP_HELP.purchaseRequestsPeriod}
          />
          <SuppliesTextField
            label={C.requestNumberLabel}
            value={query.request_number}
            onChange={(value) => onPatch({ request_number: value, page: 1 })}
            hint={SP_HELP.purchaseRequestsNumber}
          />
          <SuppliesTextField
            label={C.productLabel}
            value={query.product_code}
            onChange={(value) => onPatch({ product_code: value, page: 1 })}
            hint={SP_HELP.purchaseRequestsProduct}
          />
          <SuppliesSelectField
            label={C.stageLabel}
            hint={SP_HELP.purchaseRequestsStage}
            value={query.overall_stages[0] ?? ""}
            onChange={(value) => {
              const stage = value as OverallStage | "";
              onPatch({
                overall_stages: stage ? [stage] : [],
                page: 1,
              });
            }}
            options={stageOptions}
            allowEmpty
            emptyLabel={C.stageAll}
            searchable={false}
          />
        </FiltersRow>
      </SuppliesFilterBarShell>
      <div className="sp-purchase-requests__filter-actions">
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
