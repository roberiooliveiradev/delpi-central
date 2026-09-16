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
import { PURCHASE_REQUESTS_CONTENT as C } from "./content";
import { labelOverallStage } from "./query";
import type { OverallStage, PurchaseRequestsQuery } from "./types";
import { OVERALL_STAGE_VALUES } from "./types";

type PurchaseRequestsFiltersProps = {
  query: PurchaseRequestsQuery;
  units: readonly string[];
  onPatch: (patch: Partial<PurchaseRequestsQuery>) => void;
  onClear: () => void;
};

export function PurchaseRequestsFilters({
  query,
  units,
  onPatch,
  onClear,
}: PurchaseRequestsFiltersProps) {
  const { FiltersRow } = spFiltersKit;
  const unitOptions = buildSuppliesUnitOptions(units);
  const stageOptions = OVERALL_STAGE_VALUES.map((stage) => ({
    value: stage,
    label: labelOverallStage(stage),
  }));

  const commitRequestNumber = useCallback(
    (value: string) => onPatch({ request_number: value, page: 1 }),
    [onPatch],
  );
  const commitProduct = useCallback(
    (value: string) => onPatch({ product_code: value, page: 1 }),
    [onPatch],
  );

  const requestNumber = useCommittedTextFilter(query.request_number, commitRequestNumber);
  const product = useCommittedTextFilter(query.product_code, commitProduct);

  const flushTextFilters = () => {
    requestNumber.flush();
    product.flush();
  };

  return (
    <form
      className="sp-list-filters sp-purchase-requests__filters"
      onSubmit={(event) => {
        event.preventDefault();
        flushTextFilters();
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
            value={requestNumber.draft}
            onChange={requestNumber.setDraft}
            hint={SP_HELP.purchaseRequestsNumber}
          />
          <SuppliesTextField
            label={C.productLabel}
            value={product.draft}
            onChange={product.setDraft}
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
      <div className="sp-list-filters__actions sp-purchase-requests__filter-actions">
        <p className="sp-list-filters__hint">{SP_HELP.purchaseRequestsFiltersAuto}</p>
        <SuppliesActionButton type="button" variant="ghost" onClick={onClear}>
          {C.clearFilters}
        </SuppliesActionButton>
      </div>
    </form>
  );
}
