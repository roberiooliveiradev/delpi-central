import { Filter } from "lucide-react";

import {
  matchPeriodPreset,
  PERIOD_PRESET_OPTIONS,
  resolvePeriodPreset,
  type PeriodPresetId,
} from "../../app/periodPreset";
import {
  buildSuppliesUnitOptions,
  canonicalizeUiBranches,
  SUPPLIES_UNIT_FILTER_LABEL,
} from "../../app/suppliesUnits";
import {
  SuppliesClearFiltersButton,
  SuppliesDateField,
  SuppliesFilterBarShell,
  SuppliesMultiSelectField,
  SuppliesSectionHintLabel,
  SuppliesSegmentToggle,
  SuppliesSelectField,
  spFiltersKit,
} from "../../app/suppliesUi";
import { SP_HELP } from "../../content/helpTooltips";
import { DELIVERIES_CONTENT as C } from "./content";
import { hasActiveDeliveriesFilters } from "./hasActiveFilters";
import type { DeliveriesQuery, DeliveryPunctualityStatus } from "./types";
import { DELIVERY_STATUS_OPTIONS } from "./types";

type DeliveriesFiltersProps = {
  query: DeliveriesQuery;
  units: readonly string[];
  onPatch: (patch: Partial<DeliveriesQuery>) => void;
  onClear: () => void;
};

export function DeliveriesFilters({
  query,
  units,
  onPatch,
  onClear,
}: DeliveriesFiltersProps) {
  const { FiltersRow } = spFiltersKit;
  const unitOptions = buildSuppliesUnitOptions(units);
  const hasActiveFilters = hasActiveDeliveriesFilters(query, units);
  const period = matchPeriodPreset(query.start_date, query.end_date);

  const onPeriod = (value: PeriodPresetId) => {
    if (value === "custom") return;
    const resolved = resolvePeriodPreset(value);
    if (!resolved) return;
    onPatch({
      start_date: resolved.from,
      end_date: resolved.to,
      page: 1,
    });
  };

  return (
    <form
      className="sp-list-filters sp-deliveries__filters"
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
                    hint={SP_HELP.deliveriesFilters}
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
            <div className="sp-deliveries__period-presets">
              <SuppliesSectionHintLabel
                label={C.periodLabel}
                hint={SP_HELP.deliveriesPeriod}
              />
              <SuppliesSegmentToggle
                ariaLabel={C.periodLabel}
                idPrefix="deliveries-period-preset"
                size="sm"
                value={period}
                onChange={(value) => onPeriod(value as PeriodPresetId)}
                options={PERIOD_PRESET_OPTIONS}
              />
            </div>
          </div>
        }
      >
        {null}
      </SuppliesFilterBarShell>
      <FiltersRow variant="extended">
        <SuppliesDateField
          label={C.entryFromLabel}
          value={query.start_date}
          onChange={(value) => onPatch({ start_date: value, page: 1 })}
        />
        <SuppliesDateField
          label={C.entryToLabel}
          value={query.end_date}
          onChange={(value) => onPatch({ end_date: value, page: 1 })}
        />
        <SuppliesMultiSelectField
          className="sp-deliveries__unit-filter"
          label={SUPPLIES_UNIT_FILTER_LABEL}
          hint={SP_HELP.deliveriesBranch}
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
          label={C.statusLabel}
          hint={SP_HELP.deliveriesStatus}
          value={query.status}
          options={DELIVERY_STATUS_OPTIONS}
          onChange={(value) =>
            onPatch({
              status: (value === "on_time" ? "on_time" : "late") as DeliveryPunctualityStatus,
              page: 1,
            })
          }
        />
      </FiltersRow>
    </form>
  );
}
