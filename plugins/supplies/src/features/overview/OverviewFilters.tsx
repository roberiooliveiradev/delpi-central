import {
  SuppliesDateField,
  SuppliesFilterBarShell,
  SuppliesMultiSelectField,
  SuppliesSectionHintLabel,
  SuppliesSegmentToggle,
  spFiltersKit,
} from "../../app/suppliesUi";
import { SP_HELP } from "../../content/helpTooltips";
import { OVERVIEW_CONTENT } from "./overviewContent";
import { PERIOD_PRESET_OPTIONS, type PeriodPresetId } from "./periodPreset";
import { SUPPLIES_UNIT_FIELD_LABEL } from "./suppliesBranchFilters";

type OverviewFiltersProps = {
  period: PeriodPresetId;
  from: string;
  to: string;
  branches: string[];
  unitOptions: ReadonlyArray<{ value: string; label: string }>;
  onPeriod: (value: PeriodPresetId) => void;
  onFrom: (value: string) => void;
  onTo: (value: string) => void;
  onBranches: (value: string[]) => void;
};

export function OverviewFilters({
  period,
  from,
  to,
  branches,
  unitOptions,
  onPeriod,
  onFrom,
  onTo,
  onBranches,
}: OverviewFiltersProps) {
  const { FiltersRow } = spFiltersKit;

  return (
    <>
      <SuppliesFilterBarShell
        embedded
        ariaLabel={OVERVIEW_CONTENT.periodPresetLabel}
        leading={
          <div>
            <SuppliesSectionHintLabel
              label={OVERVIEW_CONTENT.periodPresetLabel}
              hint={SP_HELP.overviewFiltersPeriod}
            />
            <SuppliesSegmentToggle
              ariaLabel={OVERVIEW_CONTENT.periodPresetLabel}
              idPrefix="overview-period-preset"
              size="sm"
              value={period}
              onChange={(value) => onPeriod(value as PeriodPresetId)}
              options={PERIOD_PRESET_OPTIONS}
            />
          </div>
        }
      >
        {null}
      </SuppliesFilterBarShell>
      <FiltersRow variant="extended">
        <SuppliesDateField
          label={OVERVIEW_CONTENT.periodFromLabel}
          value={from}
          onChange={onFrom}
          hint={SP_HELP.overviewFiltersFrom}
        />
        <SuppliesDateField
          label={OVERVIEW_CONTENT.periodToLabel}
          value={to}
          onChange={onTo}
          hint={SP_HELP.overviewFiltersTo}
        />
        <SuppliesMultiSelectField
          className="sp-overview-unit-filter"
          label={SUPPLIES_UNIT_FIELD_LABEL}
          selectedValues={branches}
          onChange={onBranches}
          options={[...unitOptions]}
          emptyLabel={OVERVIEW_CONTENT.branchAll}
          searchable
          hint={SP_HELP.overviewFiltersBranch}
        />
      </FiltersRow>
    </>
  );
}
