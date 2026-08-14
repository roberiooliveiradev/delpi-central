/**
 * Controles compartilhados de período + comparação YoY / N anos (até 3).
 * Presets e custom alinhados a Minha Carteira / Overview; sem CSS de kit no MFE.
 */
import { ChevronDown, GitCompareArrows } from "lucide-react";
import { useId, useRef, useState, type ReactNode } from "react";
import {
  AnchoredPanelPortal,
  NativeCheckboxControl,
  SegmentToggle,
} from "@delpi/plugin-ui/index";

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

function compareYearsSummaryLabel(compareYears: CompareYearsCount): string {
  const copy = ANALYTICS_CONTENT.overview;
  if (compareYears >= 3) return copy.compareYearsDepth3;
  if (compareYears >= 2) return copy.compareYearsDepth2;
  if (compareYears >= 1) return copy.compareYearsDepth1;
  return copy.compareYearsNone;
}

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
  const [open, setOpen] = useState(false);
  const rootRef = useRef<HTMLDivElement>(null);
  const panelRef = useRef<HTMLDivElement>(null);
  const menuId = useId();
  const copy = ANALYTICS_CONTENT.overview;
  const summary = compareYearsSummaryLabel(compareYears);
  const close = () => setOpen(false);

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
        {trailing ? (
          <div className="cm-period-compare-controls__trailing">{trailing}</div>
        ) : null}
        <div
          ref={rootRef}
          className={[
            "cm-period-compare-controls__popover",
            open ? "cm-period-compare-controls__popover--open" : null,
            compareYears > 0 ? "cm-period-compare-controls__popover--active" : null,
          ]
            .filter(Boolean)
            .join(" ")}
        >
          <button
            type="button"
            id={`${idPrefix}-compare-trigger`}
            className="cm-period-compare-controls__trigger"
            aria-label={copy.compareYearsTrigger}
            aria-haspopup="menu"
            aria-expanded={open}
            aria-controls={open ? menuId : undefined}
            disabled={disabled}
            onClick={() => setOpen((current) => !current)}
          >
            <GitCompareArrows
              size={16}
              strokeWidth={1.75}
              aria-hidden
              className="cm-period-compare-controls__trigger-icon"
            />
            <span className="cm-period-compare-controls__trigger-label">{summary}</span>
            <ChevronDown
              size={14}
              strokeWidth={2}
              aria-hidden
              className="cm-period-compare-controls__trigger-chevron"
            />
          </button>
          <AnchoredPanelPortal
            open={open}
            anchorRef={rootRef}
            panelRef={panelRef}
            variant="bare"
            role="menu"
            aria-label={copy.compareYearsPanelTitle}
            preferredPlacement="bottom"
            density="compact"
            portalScopeClassName="dashboard-commercial"
            className="cm-period-compare-controls__portal"
            onDismiss={close}
          >
            <div id={menuId} className="cm-period-compare-controls__panel">
              <p className="cm-period-compare-controls__panel-title">
                {copy.compareYearsPanelTitle}
              </p>
              <div className="cm-period-compare-controls__options">
                <NativeCheckboxControl
                  id={`${idPrefix}-yoy`}
                  checked={yoyActive}
                  onChange={(checked) =>
                    onCompareYearsChange(
                      checked ? clampCompareYears(Math.max(compareYears, 1)) : 0,
                    )
                  }
                  label={copy.comparePriorYear}
                  hint={typeof yoyHint === "string" ? yoyHint : undefined}
                  hintPlacement="tooltip"
                  hintAriaLabel="Ajuda: comparar ano anterior"
                  disabled={disabled}
                />
                <NativeCheckboxControl
                  id={`${idPrefix}-yoy-2`}
                  checked={compare2}
                  onChange={(checked) =>
                    onCompareYearsChange(
                      checked
                        ? clampCompareYears(Math.max(compareYears, 2))
                        : yoyActive
                          ? 1
                          : 0,
                    )
                  }
                  label={copy.compareYearsPlus2}
                  hint="Sobrepõe também o período deslocado −2 anos."
                  hintPlacement="tooltip"
                  hintAriaLabel="Ajuda: +2 anos"
                  disabled={disabled || !yoyActive}
                />
                <NativeCheckboxControl
                  id={`${idPrefix}-yoy-3`}
                  checked={compare3}
                  onChange={(checked) =>
                    onCompareYearsChange(
                      checked ? 3 : compare2 ? 2 : yoyActive ? 1 : 0,
                    )
                  }
                  label={copy.compareYearsPlus3}
                  hint="Sobrepõe também o período deslocado −3 anos."
                  hintPlacement="tooltip"
                  hintAriaLabel="Ajuda: +3 anos"
                  disabled={disabled || compareYears < 2}
                />
              </div>
            </div>
          </AnchoredPanelPortal>
        </div>
      </div>
    </div>
  );
}
