import {
  SuppliesDateField,
  SuppliesFilterBarShell,
  SuppliesSectionHintLabel,
  SuppliesSegmentToggle,
  SuppliesSelectField,
  spFiltersKit,
} from "../../app/suppliesUi";
import { SP_HELP } from "../../content/helpTooltips";
import { OVERVIEW_CONTENT } from "./overviewContent";
import {
  PERIOD_PRESET_OPTIONS,
  type PeriodPresetId,
} from "./periodPreset";

type OverviewFiltersProps = {
  period: PeriodPresetId;
  from: string;
  to: string;
  branch: string;
  unitOptions: readonly string[];
  onPeriod: (value: PeriodPresetId) => void;
  onFrom: (value: string) => void;
  onTo: (value: string) => void;
  onBranch: (value: string) => void;
};

export function OverviewFilters({
  period,
  from,
  to,
  branch,
  unitOptions,
  onPeriod,
  onFrom,
  onTo,
  onBranch,
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
        <SuppliesSelectField
          label={OVERVIEW_CONTENT.branchLabel}
          value={branch}
          onChange={onBranch}
          options={unitOptions.map((unit) => ({ value: unit, label: unit }))}
          allowEmpty
          emptyLabel={OVERVIEW_CONTENT.branchAll}
          hint={SP_HELP.overviewFiltersBranch}
        />
      </FiltersRow>
    </>
  );
}
