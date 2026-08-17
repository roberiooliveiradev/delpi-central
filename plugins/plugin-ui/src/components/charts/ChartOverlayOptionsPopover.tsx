import { ChevronDown, SlidersHorizontal } from "lucide-react";
import { useId, useMemo, useRef, useState } from "react";

import { NativeCheckboxControl } from "../forms/NativeCheckboxControl";
import { AnchoredPanelPortal } from "../shape/AnchoredPanelPortal";

export type ChartOverlayOption = {
  id: string;
  label: string;
  checked: boolean;
  onChange: (checked: boolean) => void;
  /** Shorter text for the trigger summary (defaults to `label`). */
  summaryLabel?: string;
  hint?: string;
  hintAriaLabel?: string;
  disabled?: boolean;
};

export type ChartOverlayOptionsPopoverProps = {
  options: readonly ChartOverlayOption[];
  /** Override trigger text (defaults to joined checked summaries). */
  summaryLabel?: string;
  emptySummaryLabel?: string;
  panelTitle?: string;
  triggerAriaLabel?: string;
  disabled?: boolean;
  idPrefix?: string;
  portalScopeClassName?: string;
  className?: string;
};

export function summarizeChartOverlayOptions(
  options: readonly ChartOverlayOption[],
  emptySummaryLabel = "Opções",
): string {
  const active = options.filter((option) => option.checked && !option.disabled);
  if (active.length === 0) return emptySummaryLabel;
  return active.map((option) => option.summaryLabel ?? option.label).join(" · ");
}

/**
 * Popover of chart overlay checkboxes (YoY / multi-year / trend).
 * Same density as ChartTypeSegmentToggle — use inside ChartViewShell.overlays.
 */
export function ChartOverlayOptionsPopover({
  options,
  summaryLabel,
  emptySummaryLabel = "Opções",
  panelTitle = "Opções do gráfico",
  triggerAriaLabel = "Opções do gráfico",
  disabled = false,
  idPrefix = "chart-overlays",
  portalScopeClassName,
  className,
}: ChartOverlayOptionsPopoverProps) {
  const [open, setOpen] = useState(false);
  const rootRef = useRef<HTMLDivElement>(null);
  const panelRef = useRef<HTMLDivElement>(null);
  const menuId = useId();

  const resolvedSummary = useMemo(
    () => summaryLabel ?? summarizeChartOverlayOptions(options, emptySummaryLabel),
    [emptySummaryLabel, options, summaryLabel],
  );

  const hasActive = options.some((option) => option.checked);
  const close = () => setOpen(false);

  if (options.length === 0) return null;

  const rootClass = [
    "delpi-ui-chart-overlay-popover",
    open ? "delpi-ui-chart-overlay-popover--open" : null,
    hasActive ? "delpi-ui-chart-overlay-popover--active" : null,
    className,
  ]
    .filter(Boolean)
    .join(" ");

  return (
    <div ref={rootRef} className={rootClass}>
      <button
        type="button"
        id={`${idPrefix}-trigger`}
        className="delpi-ui-chart-overlay-popover__trigger"
        aria-label={triggerAriaLabel}
        aria-haspopup="menu"
        aria-expanded={open}
        aria-controls={open ? menuId : undefined}
        disabled={disabled}
        onClick={() => setOpen((current) => !current)}
      >
        <SlidersHorizontal
          size={16}
          strokeWidth={1.75}
          aria-hidden
          className="delpi-ui-chart-overlay-popover__icon"
        />
        <span className="delpi-ui-chart-overlay-popover__label">{resolvedSummary}</span>
        <ChevronDown
          size={14}
          strokeWidth={2}
          aria-hidden
          className="delpi-ui-chart-overlay-popover__chevron"
        />
      </button>
      <AnchoredPanelPortal
        open={open}
        anchorRef={rootRef}
        panelRef={panelRef}
        variant="bare"
        role="menu"
        aria-label={panelTitle}
        preferredPlacement="bottom"
        density="compact"
        portalScopeClassName={portalScopeClassName}
        className="delpi-ui-chart-overlay-popover__portal"
        onDismiss={close}
      >
        <div id={menuId} className="delpi-ui-chart-overlay-popover__panel">
          <p className="delpi-ui-chart-overlay-popover__panel-title">{panelTitle}</p>
          <div className="delpi-ui-chart-overlay-popover__options">
            {options.map((option) => (
              <NativeCheckboxControl
                key={option.id}
                id={`${idPrefix}-${option.id}`}
                checked={option.checked}
                onChange={option.onChange}
                label={option.label}
                hint={option.hint}
                hintPlacement={option.hint ? "tooltip" : "inline"}
                hintAriaLabel={option.hintAriaLabel}
                disabled={disabled || option.disabled}
              />
            ))}
          </div>
        </div>
      </AnchoredPanelPortal>
    </div>
  );
}
