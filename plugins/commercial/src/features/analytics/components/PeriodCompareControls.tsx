/**
 * Controles de período (presets + custom). Overlays YoY/tendência ficam no
 * popover de opções do ChartViewShell (plugin-ui).
 */
import { SegmentToggle } from "@delpi/plugin-ui/index";

import {
  CommercialDateField,
  CommercialFilterBarShell,
  UI_PREFIX,
} from "../../../app/commercialUi";
import { CM_HELP } from "../../../content/helpTooltips";
import {
  BILLING_SERIES_PRESET_OPTIONS,
  type BillingSeriesPeriodPreset,
} from "../../customers/utils/billingSeriesPeriod";

export type { CompareYearsCount } from "../utils/compareYears";
export {
  clampCompareYears,
  compareYearOffsets,
  MAX_COMPARE_YEARS,
} from "../utils/compareYears";

type PeriodCompareControlsProps = {
  idPrefix: string;
  preset: BillingSeriesPeriodPreset;
  onPresetChange: (preset: BillingSeriesPeriodPreset) => void;
  customStart: string;
  customEnd: string;
  onCustomStartChange: (value: string) => void;
  onCustomEndChange: (value: string) => void;
  periodHint?: string;
  dateStartHint?: string;
  dateEndHint?: string;
  disabled?: boolean;
};

export function PeriodCompareControls({
  idPrefix,
  preset,
  onPresetChange,
  customStart,
  customEnd,
  onCustomStartChange,
  onCustomEndChange,
  periodHint = CM_HELP.customers.billingSeriesPeriod,
  dateStartHint = CM_HELP.customerDetail.billingSeriesDateStart,
  dateEndHint = CM_HELP.customerDetail.billingSeriesDateEnd,
  disabled = false,
}: PeriodCompareControlsProps) {
  return (
    <div className="cm-period-compare-controls">
      <CommercialFilterBarShell
        embedded
        layout={preset === "custom" ? "grid" : "inline"}
        ariaLabel={periodHint}
        leading={
          <SegmentToggle
            prefix={UI_PREFIX}
            ariaLabel={periodHint}
            idPrefix={`${idPrefix}-period`}
            value={preset}
            onChange={(value) => onPresetChange(value as BillingSeriesPeriodPreset)}
            options={BILLING_SERIES_PRESET_OPTIONS.map((item) => ({
              value: item.id,
              label: item.label,
            }))}
            disabled={disabled}
          />
        }
      >
        {preset === "custom" ? (
          <>
            <CommercialDateField
              label="Data inicial"
              hint={dateStartHint}
              value={customStart}
              onChange={onCustomStartChange}
              disabled={disabled}
            />
            <CommercialDateField
              label="Data final"
              hint={dateEndHint}
              value={customEnd}
              onChange={onCustomEndChange}
              disabled={disabled}
            />
          </>
        ) : null}
      </CommercialFilterBarShell>
    </div>
  );
}
