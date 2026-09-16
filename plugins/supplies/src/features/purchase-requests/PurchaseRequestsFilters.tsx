import { useCallback, useState } from "react";
import { Filter } from "lucide-react";

import { buildSuppliesUnitOptions } from "../../app/suppliesUnits";
import { useCommittedTextFilter } from "../../app/useCommittedTextFilter";
import {
  SuppliesActionButton,
  SuppliesClearFiltersButton,
  SuppliesDateField,
  SuppliesFilterBarShell,
  SuppliesSectionHintLabel,
  SuppliesMultiSelectField,
  SuppliesSelectField,
  SuppliesTextField,
  spFiltersKit,
} from "../../app/suppliesUi";
import { SP_HELP } from "../../content/helpTooltips";
import { PURCHASE_REQUESTS_CONTENT as C } from "./content";
import { hasActivePurchaseRequestsFilters } from "./hasActiveFilters";
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
  const [showMore, setShowMore] = useState(false);
  const unitOptions = buildSuppliesUnitOptions(units);
  const hasActiveFilters = hasActivePurchaseRequestsFilters(query);
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
                  hint={SP_HELP.purchaseRequestsFilters}
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
            label={C.branchLabel}
            hint={SP_HELP.purchaseRequestsBranch}
            selectedValues={query.branches}
            onChange={(values) => onPatch({ branches: values, page: 1, request: "" })}
            options={unitOptions}
            emptyLabel="Todas"
            searchable={unitOptions.length > 4}
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
          {showMore ? (
            <>
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
            </>
          ) : null}
        </FiltersRow>
      </SuppliesFilterBarShell>
    </form>
  );
}
