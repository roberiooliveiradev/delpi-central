import { ChevronDown, Palette } from "lucide-react";
import { useId, useMemo, useRef, useState } from "react";

import { AnchoredPanelPortal } from "../shape/AnchoredPanelPortal";
import { ColorPickerPopoverTrigger } from "../shape/ColorPickerPopover";

export type ChartSeriesColorItem = {
  dataKey: string;
  name: string;
  /** Effective fill shown in the swatch (default ∪ override). */
  fill: string;
};

export type ChartSeriesColorsPopoverProps = {
  series: readonly ChartSeriesColorItem[];
  /** Persisted overrides keyed by dataKey (may be empty). */
  values?: Record<string, string> | null;
  onChange: (dataKey: string, color: string) => void;
  onReset?: () => void;
  summaryLabel?: string;
  panelTitle?: string;
  triggerAriaLabel?: string;
  resetLabel?: string;
  disabled?: boolean;
  idPrefix?: string;
  portalScopeClassName?: string;
  className?: string;
};

/**
 * Thin host: lists chart series and reuses ColorPickerPopover per row.
 * Use inside ChartViewShell.seriesColors.
 */
export function ChartSeriesColorsPopover({
  series,
  values,
  onChange,
  onReset,
  summaryLabel = "Cores",
  panelTitle = "Cores das séries",
  triggerAriaLabel = "Cores das séries",
  resetLabel = "Restaurar padrão",
  disabled = false,
  idPrefix = "chart-series-colors",
  portalScopeClassName,
  className,
}: ChartSeriesColorsPopoverProps) {
  const [open, setOpen] = useState(false);
  const rootRef = useRef<HTMLDivElement>(null);
  const panelRef = useRef<HTMLDivElement>(null);
  const menuId = useId();

  const hasOverrides = useMemo(() => {
    if (!values) return false;
    return Object.keys(values).length > 0;
  }, [values]);

  const close = () => setOpen(false);

  if (series.length === 0) return null;

  const rootClass = [
    "delpi-ui-chart-series-colors",
    open ? "delpi-ui-chart-series-colors--open" : null,
    hasOverrides ? "delpi-ui-chart-series-colors--active" : null,
    className,
  ]
    .filter(Boolean)
    .join(" ");

  return (
    <div ref={rootRef} className={rootClass}>
      <button
        type="button"
        id={`${idPrefix}-trigger`}
        className="delpi-ui-chart-series-colors__trigger"
        aria-label={triggerAriaLabel}
        aria-haspopup="dialog"
        aria-expanded={open}
        aria-controls={open ? menuId : undefined}
        disabled={disabled}
        onClick={() => setOpen((current) => !current)}
      >
        <Palette
          size={16}
          strokeWidth={1.75}
          aria-hidden
          className="delpi-ui-chart-series-colors__icon"
        />
        <span className="delpi-ui-chart-series-colors__label">{summaryLabel}</span>
        <ChevronDown
          size={14}
          strokeWidth={2}
          aria-hidden
          className="delpi-ui-chart-series-colors__chevron"
        />
      </button>
      <AnchoredPanelPortal
        open={open}
        anchorRef={rootRef}
        panelRef={panelRef}
        variant="bare"
        role="dialog"
        aria-label={panelTitle}
        preferredPlacement="bottom"
        density="compact"
        portalScopeClassName={portalScopeClassName}
        className="delpi-ui-chart-series-colors__portal"
        onDismiss={close}
      >
        <div id={menuId} className="delpi-ui-chart-series-colors__panel">
          <p className="delpi-ui-chart-series-colors__panel-title">{panelTitle}</p>
          <ul className="delpi-ui-chart-series-colors__list">
            {series.map((entry) => {
              const override = values?.[entry.dataKey];
              const value =
                typeof override === "string" && override.trim()
                  ? override.trim()
                  : entry.fill;
              return (
                <li key={entry.dataKey} className="delpi-ui-chart-series-colors__row">
                  <span className="delpi-ui-chart-series-colors__row-name">{entry.name}</span>
                  <ColorPickerPopoverTrigger
                    variant="fill"
                    showNoFill={false}
                    value={value}
                    onChange={(color) => onChange(entry.dataKey, color)}
                    triggerLabel={entry.name}
                    triggerAriaLabel={`Cor da série ${entry.name}`}
                    triggerClassName="delpi-ui-chart-series-colors__picker"
                  />
                </li>
              );
            })}
          </ul>
          {onReset ? (
            <button
              type="button"
              className="delpi-ui-chart-series-colors__reset"
              disabled={!hasOverrides}
              onClick={() => {
                onReset();
              }}
            >
              {resetLabel}
            </button>
          ) : null}
        </div>
      </AnchoredPanelPortal>
    </div>
  );
}
