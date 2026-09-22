import { Filter } from "lucide-react";

import {
  buildSuppliesUnitOptions,
  canonicalizeUiBranches,
  SUPPLIES_UNIT_FILTER_LABEL,
} from "../../app/suppliesUnits";
import {
  SuppliesClearFiltersButton,
  SuppliesFilterBarShell,
  SuppliesMultiSelectField,
  SuppliesSelectField,
  spFiltersKit,
} from "../../app/suppliesUi";
import { INVENTORY_CONTENT as C } from "./content";
import { hasActiveInventoryFilters } from "./hasActiveFilters";
import type { InventoryQuery } from "./types";

type InventoryFiltersProps = {
  query: InventoryQuery;
  units: readonly string[];
  warehouseOptions: readonly { value: string; label: string }[];
  onPatch: (patch: Partial<InventoryQuery>) => void;
  onClear: () => void;
};

export function InventoryFilters({
  query,
  units,
  warehouseOptions,
  onPatch,
  onClear,
}: InventoryFiltersProps) {
  const { FiltersRow } = spFiltersKit;
  const unitOptions = buildSuppliesUnitOptions(units);
  const hasActiveFilters = hasActiveInventoryFilters(query, units);
  const warehouseSelectOptions = [...warehouseOptions];

  return (
    <form
      className="sp-list-filters sp-inventory__filters"
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
                <h2>{C.filtersTitle}</h2>
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
        <SuppliesMultiSelectField
          className="sp-inventory__unit-filter"
          label={SUPPLIES_UNIT_FILTER_LABEL}
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
        <SuppliesSelectField
          label={C.warehouseLabel}
          value={query.warehouse}
          options={warehouseSelectOptions}
          allowEmpty
          emptyLabel={C.warehouseEmptyOption}
          onChange={(value) =>
            onPatch({
              warehouse: value,
              page: 1,
            })
          }
        />
      </FiltersRow>
    </form>
  );
}
