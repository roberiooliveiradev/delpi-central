import { ChevronDown } from "lucide-react";
import { useId, useMemo, useRef, useState } from "react";

import type { PersistedChartType } from "../../hooks/usePersistedChartPreferences";
import { AnchoredPanelPortal } from "../shape/AnchoredPanelPortal";
import { ChartTypeCatalogPanel } from "./ChartTypeCatalogPanel";
import { DELPI_CHART_TYPE_CATALOG } from "./chartCatalogTypes";
import { resolveChartCatalogIcon } from "./chartCatalogIcons";
import {
  CHART_TYPE_LABELS_PT,
  chartTypesForFamily,
  type ChartDataFamily,
} from "./chartDataFamilies";
import {
  delpiChartTypeToPersisted,
  persistedChartTypeToDelpi,
  persistedChartTypesToDelpi,
} from "./chartTypeBridge";
import type { DelpiChartType } from "./chartCatalogTypes";

export type ChartTypeSegmentToggleProps = {
  family: ChartDataFamily;
  value: PersistedChartType;
  onChange: (value: PersistedChartType) => void;
  idPrefix?: string;
  prefix?: string;
  disabled?: boolean;
  categoryCount?: number;
  ariaLabel?: string;
  className?: string;
  /** Catalog panel title. */
  panelTitle?: string;
  portalScopeClassName?: string;
};

/**
 * Chart-type switcher: trigger with icon + label opens the same catalog
 * popover used by TV Dashboard (filtered by data family).
 */
export function ChartTypeSegmentToggle({
  family,
  value,
  onChange,
  idPrefix = "chart-type",
  prefix = "ds",
  disabled = false,
  categoryCount,
  ariaLabel = "Tipo de gráfico",
  className,
  panelTitle = "Tipo de gráfico",
  portalScopeClassName,
}: ChartTypeSegmentToggleProps) {
  const types = chartTypesForFamily(family, { categoryCount });
  const [open, setOpen] = useState(false);
  const rootRef = useRef<HTMLDivElement>(null);
  const panelRef = useRef<HTMLDivElement>(null);
  const menuId = useId();

  const allowedDelpi = useMemo(() => persistedChartTypesToDelpi(types), [types]);
  const selectedDelpi = persistedChartTypeToDelpi(value);

  const catalogEntry = useMemo(
    () => DELPI_CHART_TYPE_CATALOG.find((entry) => entry.type === selectedDelpi),
    [selectedDelpi],
  );
  const Icon = resolveChartCatalogIcon(catalogEntry?.icon);
  const label = CHART_TYPE_LABELS_PT[value] ?? catalogEntry?.label ?? value;

  if (types.length <= 1) return null;

  const close = () => setOpen(false);

  const handleSelect = (chartType: DelpiChartType) => {
    const next = delpiChartTypeToPersisted(chartType, types);
    if (next) onChange(next);
    close();
  };

  const rootClass = [
    "delpi-ui-chart-type-popover",
    `${prefix}-chart-type-popover`,
    open ? "delpi-ui-chart-type-popover--open" : null,
    className,
  ]
    .filter(Boolean)
    .join(" ");

  return (
    <div ref={rootRef} className={rootClass}>
      <button
        type="button"
        id={`${idPrefix}-trigger`}
        className="delpi-ui-chart-type-popover__trigger"
        aria-label={ariaLabel}
        aria-haspopup="menu"
        aria-expanded={open}
        aria-controls={open ? menuId : undefined}
        disabled={disabled}
        onClick={() => setOpen((current) => !current)}
      >
        <Icon size={16} strokeWidth={1.75} aria-hidden className="delpi-ui-chart-type-popover__icon" />
        <span className="delpi-ui-chart-type-popover__label">{label}</span>
        <ChevronDown
          size={14}
          strokeWidth={2}
          aria-hidden
          className="delpi-ui-chart-type-popover__chevron"
        />
      </button>
      <AnchoredPanelPortal
        open={open}
        anchorRef={rootRef}
        panelRef={panelRef}
        variant="bare"
        role="menu"
        aria-label={ariaLabel}
        preferredPlacement="bottom"
        portalScopeClassName={portalScopeClassName}
        density="compact"
        className="delpi-ui-chart-type-popover__portal"
        onDismiss={close}
      >
        <div id={menuId} className="delpi-ui-chart-type-popover__panel">
          <ChartTypeCatalogPanel
            title={panelTitle}
            selectedType={selectedDelpi}
            allowedTypes={allowedDelpi}
            onSelect={handleSelect}
          />
        </div>
      </AnchoredPanelPortal>
    </div>
  );
}
