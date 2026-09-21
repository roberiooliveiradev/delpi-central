import { SectionHintLabel } from "../help/SectionHintLabel";
import { SegmentToggle } from "../forms/SegmentToggle";
import { PERIOD_PRESET_OPTIONS, type PeriodPresetId } from "../../utils/periodPreset";
import { FilterBarShell, filterBarShellBemClasses } from "./FilterBarShell";

export type QuickPeriodSelectorProps = {
  value: PeriodPresetId;
  onChange: (value: PeriodPresetId) => void;
  /** Plugin BEM prefix (default `ds`). */
  prefix?: string;
  label?: string;
  hint?: string;
  ariaLabel?: string;
  idPrefix?: string;
};

const DEFAULT_LABEL = "Período rápido";

/**
 * Shared chrome for portal quick-period pills.
 * Compose FilterBarShell + SegmentToggle. No API, dashboard, or domain objects.
 */
export function QuickPeriodSelector({
  value,
  onChange,
  prefix = "ds",
  label = DEFAULT_LABEL,
  hint,
  ariaLabel,
  idPrefix = "quick-period",
}: QuickPeriodSelectorProps) {
  const accessibleName = ariaLabel ?? label;

  return (
    <FilterBarShell
      embedded
      ariaLabel={accessibleName}
      classNames={filterBarShellBemClasses(prefix)}
      leading={
        <div>
          {hint ? (
            <SectionHintLabel label={label} hint={hint} />
          ) : (
            <span className="delpi-ui-section-hint-label">{label}</span>
          )}
          <SegmentToggle
            prefix={prefix}
            ariaLabel={accessibleName}
            idPrefix={idPrefix}
            size="sm"
            value={value}
            onChange={onChange}
            options={PERIOD_PRESET_OPTIONS}
          />
        </div>
      }
    >
      {null}
    </FilterBarShell>
  );
}

export function createDashboardQuickPeriodSelector(prefix: string) {
  return function DashboardQuickPeriodSelector(
    props: Omit<QuickPeriodSelectorProps, "prefix">,
  ) {
    return <QuickPeriodSelector {...props} prefix={prefix} />;
  };
}
