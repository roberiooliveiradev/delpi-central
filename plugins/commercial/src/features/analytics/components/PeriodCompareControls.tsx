/**
 * Controles compartilhados de período + comparação YoY / N anos (até 3).
 * Presets e custom alinhados a Minha Carteira / Overview; sem CSS de kit no MFE.
 */
import type { ReactNode } from "react";
import { NativeCheckboxControl, SegmentToggle } from "@delpi/plugin-ui/index";

import {
  CommercialDateField,
  CommercialFilterBarShell,
  UI_PREFIX,
} from "../../../app/commercialUi";
import { ANALYTICS_CONTENT } from "../../../content/analyticsContent";
import { CM_HELP } from "../../../content/helpTooltips";
import {
  BILLING_SERIES_PRESET_OPTIONS,
  type BillingSeriesPeriodPreset,
} from "../../customers/utils/billingSeriesPeriod";
import {
  clampCompareYears,
  type CompareYearsCount,
} from "../utils/compareYears";

export type { CompareYearsCount } from "../utils/compareYears";
export { clampCompareYears, compareYearOffsets, MAX_COMPARE_YEARS } from "../utils/compareYears";

type PeriodCompareControlsProps = {
  idPrefix: string;
  preset: BillingSeriesPeriodPreset;
  onPresetChange: (preset: BillingSeriesPeriodPreset) => void;
  customStart: string;
  customEnd: string;
  onCustomStartChange: (value: string) => void;
  onCustomEndChange: (value: string) => void;
  /** Quantidade de anos anteriores a sobrepor (0–3). */
  compareYears: CompareYearsCount;
  onCompareYearsChange: (value: CompareYearsCount) => void;
  periodHint?: string;
  yoyHint?: string;
  dateStartHint?: string;
  dateEndHint?: string;
  /** Conteúdo extra na mesma linha (ex.: ChartToolbar de granularidade). */
  trailing?: ReactNode;
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
  compareYears,
  onCompareYearsChange,
  periodHint = CM_HELP.customers.billingSeriesPeriod,
  yoyHint = CM_HELP.customers.billingSeriesYoy,
  dateStartHint = CM_HELP.customerDetail.billingSeriesDateStart,
  dateEndHint = CM_HELP.customerDetail.billingSeriesDateEnd,
  trailing,
  disabled = false,
}: PeriodCompareControlsProps) {
  const yoyActive = compareYears >= 1;
  const compare2 = compareYears >= 2;
  const compare3 = compareYears >= 3;

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
      <div className="cm-period-compare-controls__compare-row">
        {trailing}
        <NativeCheckboxControl
          id={`${idPrefix}-yoy`}
          checked={yoyActive}
          onChange={(checked) =>
            onCompareYearsChange(checked ? Math.max(compareYears, 1) as CompareYearsCount : 0)
          }
          label={ANALYTICS_CONTENT.overview.comparePriorYear}
          hint={yoyHint}
          disabled={disabled}
        />
        <NativeCheckboxControl
          id={`${idPrefix}-yoy-2`}
          checked={compare2}
          onChange={(checked) =>
            onCompareYearsChange(
              checked ? (Math.max(compareYears, 2) as CompareYearsCount) : (yoyActive ? 1 : 0),
            )
          }
          label="+2 anos"
          hint="Sobrepõe também o período deslocado −2 anos."
          disabled={disabled || !yoyActive}
        />
        <NativeCheckboxControl
          id={`${idPrefix}-yoy-3`}
          checked={compare3}
          onChange={(checked) =>
            onCompareYearsChange(
              checked ? 3 : (compare2 ? 2 : yoyActive ? 1 : 0),
            )
          }
          label="+3 anos"
          hint="Sobrepõe também o período deslocado −3 anos."
          disabled={disabled || compareYears < 2}
        />
      </div>
    </div>
  );
}
