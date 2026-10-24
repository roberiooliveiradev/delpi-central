import { useCallback } from "react";
import { Filter } from "lucide-react";

import { useCommittedTextFilter } from "../../app/useCommittedTextFilter";
import { formatSuppliesUnitName } from "../../app/suppliesUnits";
import {
  SuppliesClearFiltersButton,
  SuppliesFilterBarShell,
  SuppliesFilterCheckboxField,
  SuppliesSectionHintLabel,
  SuppliesSelectField,
  SuppliesTextField,
  spFiltersKit,
} from "../../app/suppliesUi";
import { SP_HELP } from "../../content/helpTooltips";
import { SAFETY_STOCK_CONTENT as C, SAFETY_STOCK_STATUS_LABELS } from "./content";
import { hasActiveSafetyStockFilters } from "./hasActiveFilters";
import type { SafetyStockQuery } from "./types";
import { SAFETY_STOCK_ALL_SCOPE, SAFETY_STOCK_STATUSES } from "./types";

type SafetyStockFiltersProps = {
  query: SafetyStockQuery;
  /** Catálogo operacional do BFF (branch_catalog); fallback = unidades da sessão. */
  branchOptions: readonly string[];
  productGroupOptions: readonly string[];
  unitOptions: readonly string[];
  onPatch: (patch: Partial<SafetyStockQuery>) => void;
  onClear: () => void;
};

export function SafetyStockFilters({
  query,
  branchOptions,
  productGroupOptions,
  unitOptions,
  onPatch,
  onClear,
}: SafetyStockFiltersProps) {
  const { FiltersRow } = spFiltersKit;
  const hasActiveFilters = hasActiveSafetyStockFilters(query);

  const commitSearch = useCallback(
    (value: string) => onPatch({ search: value, page: 1 }),
    [onPatch],
  );
  const search = useCommittedTextFilter(query.search, commitSearch);

  const branchSelectOptions = [
    { value: SAFETY_STOCK_ALL_SCOPE, label: C.branchAllOption },
    ...branchOptions.map((code) => ({
      value: code,
      label: formatSuppliesUnitName(code),
    })),
  ];

  const statusOptions = SAFETY_STOCK_STATUSES.map((status) => ({
    value: status,
    label: SAFETY_STOCK_STATUS_LABELS[status],
  }));

  const groupOptions = productGroupOptions.map((value) => ({
    value,
    label: value,
  }));
  const unitSelectOptions = unitOptions.map((value) => ({
    value,
    label: value,
  }));

  return (
    <form
      className="sp-list-filters sp-safety-stock__filters"
      onSubmit={(event) => event.preventDefault()}
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
                    hint={SP_HELP.safetyStockFilters}
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
          </div>
        }
      >
        {null}
      </SuppliesFilterBarShell>
      <FiltersRow variant="extended">
        <SuppliesSelectField
          label={C.branchLabel}
          hint={SP_HELP.safetyStockBranch}
          value={query.branch}
          options={branchSelectOptions}
          onChange={(value) =>
            onPatch({
              branch: (value || SAFETY_STOCK_ALL_SCOPE) as SafetyStockQuery["branch"],
              page: 1,
            })
          }
        />
        <SuppliesSelectField
          label={C.statusLabel}
          hint={SP_HELP.safetyStockStatus}
          value={query.status}
          options={statusOptions}
          allowEmpty
          emptyLabel={C.statusEmptyOption}
          onChange={(value) =>
            onPatch({ status: value as SafetyStockQuery["status"], page: 1 })
          }
        />
        <SuppliesSelectField
          label={C.productGroupLabel}
          hint={SP_HELP.safetyStockProductGroup}
          value={query.productGroup}
          options={groupOptions}
          allowEmpty
          emptyLabel={C.productGroupEmptyOption}
          onChange={(value) => onPatch({ productGroup: value, page: 1 })}
        />
        <SuppliesSelectField
          label={C.unitLabel}
          hint={SP_HELP.safetyStockUnit}
          value={query.unit}
          options={unitSelectOptions}
          allowEmpty
          emptyLabel={C.unitEmptyOption}
          onChange={(value) => onPatch({ unit: value, page: 1 })}
        />
        <SuppliesTextField
          label={C.searchLabel}
          value={search.draft}
          onChange={search.setDraft}
          hint={SP_HELP.safetyStockSearch}
          placeholder={C.searchPlaceholder}
        />
        <SuppliesFilterCheckboxField
          id="safety-stock-include-blocked"
          label={C.includeBlockedLabel}
          hint={SP_HELP.safetyStockIncludeBlocked}
          checked={query.includeBlocked}
          onChange={(checked) => onPatch({ includeBlocked: checked, page: 1 })}
        />
        <SuppliesFilterCheckboxField
          id="safety-stock-include-without"
          label={C.includeWithoutSafetyStockLabel}
          hint={SP_HELP.safetyStockIncludeWithoutSafetyStock}
          checked={query.includeWithoutSafetyStock}
          onChange={(checked) =>
            onPatch({ includeWithoutSafetyStock: checked, page: 1 })
          }
        />
      </FiltersRow>
    </form>
  );
}
