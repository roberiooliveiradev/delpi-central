import { ChevronDown, Palette } from "lucide-react";
import { useEffect, useId, useMemo, useRef, useState } from "react";

import { FormSelectControl } from "../forms/FormSelectControl";
import { NativeCheckboxControl } from "../forms/NativeCheckboxControl";
import { AnchoredPanelPortal } from "../shape/AnchoredPanelPortal";
import { ColorPickerPopoverTrigger } from "../shape/ColorPickerPopover";
import type {
  SeriesTrendDash,
  SeriesTrendStyle,
} from "./seriesFillPreferences";
import { seriesViewHasOverrides } from "./seriesFillPreferences";

export type ChartSeriesColorItem = {
  dataKey: string;
  name: string;
  fill: string;
  visible?: boolean;
  trendCapable?: boolean;
  trendEnabled?: boolean;
  trendColor?: string | null;
  trendDash?: SeriesTrendDash;
  trendWidth?: number;
  trendApplyIncompleteBucket?: boolean;
};

export type ChartSeriesConfigLabels = {
  seriesLabel?: string;
  appearanceLabel?: string;
  colorLabel?: string;
  visibleLabel?: string;
  trendSectionLabel?: string;
  trendEnableLabel?: string;
  trendTypeLabel?: string;
  trendTypeLinearLabel?: string;
  trendColorLabel?: string;
  trendColorAutoLabel?: string;
  trendDashLabel?: string;
  trendDashSolidLabel?: string;
  trendDashDashedLabel?: string;
  trendWidthLabel?: string;
  trendWidthThinLabel?: string;
  trendWidthDefaultLabel?: string;
  trendWidthThickLabel?: string;
  trendWeightIncompleteLabel?: string;
};

export type ChartSeriesColorsPopoverProps = {
  series: readonly ChartSeriesColorItem[];
  /** Persisted fill overrides keyed by dataKey (may be empty). */
  values?: Record<string, string> | null;
  onChange: (dataKey: string, color: string) => void;
  onVisibleChange?: (dataKey: string, visible: boolean) => void;
  onTrendChange?: (dataKey: string, enabled: boolean) => void;
  onTrendStyleChange?: (dataKey: string, style: SeriesTrendStyle) => void;
  incompleteBucketWeighted?: boolean;
  onIncompleteBucketWeightChange?: (weighted: boolean) => void;
  incompleteBucketWeightHint?: string;
  incompleteBucketWeightHintAriaLabel?: string;
  onResetSeries?: (dataKey: string) => void;
  onReset?: () => void;
  hasOverrides?: boolean;
  summaryLabel?: string;
  panelTitle?: string;
  triggerAriaLabel?: string;
  resetLabel?: string;
  resetSeriesLabel?: string;
  labels?: ChartSeriesConfigLabels;
  disabled?: boolean;
  idPrefix?: string;
  portalScopeClassName?: string;
  className?: string;
};

const DEFAULT_LABELS = {
  seriesLabel: "Série",
  appearanceLabel: "Aparência",
  colorLabel: "Cor",
  visibleLabel: "Visível",
  trendSectionLabel: "Linha de tendência",
  trendEnableLabel: "Ativar",
  trendTypeLabel: "Tipo",
  trendTypeLinearLabel: "Linear",
  trendColorLabel: "Cor",
  trendColorAutoLabel: "Automática",
  trendDashLabel: "Estilo",
  trendDashSolidLabel: "Contínuo",
  trendDashDashedLabel: "Tracejado",
  trendWidthLabel: "Espessura",
  trendWidthThinLabel: "Fina",
  trendWidthDefaultLabel: "Padrão",
  trendWidthThickLabel: "Grossa",
  trendWeightIncompleteLabel: "Ponderar período parcial",
} as const;

/**
 * Inspector of one chart series (color, visibility, OLS trend and partial-period weight).
 * Use inside ChartViewShell.seriesColors. Color-only hosts omit optional callbacks.
 */
export function ChartSeriesColorsPopover({
  series,
  values,
  onChange,
  onVisibleChange,
  onTrendChange,
  onTrendStyleChange,
  incompleteBucketWeighted = false,
  onIncompleteBucketWeightChange,
  incompleteBucketWeightHint,
  incompleteBucketWeightHintAriaLabel = "Ajuda: tendência em período parcial",
  onResetSeries,
  onReset,
  hasOverrides,
  summaryLabel = "Séries",
  panelTitle = "Configurar séries",
  triggerAriaLabel = "Configurar séries",
  resetLabel = "Restaurar todas",
  resetSeriesLabel = "Restaurar padrão",
  labels,
  disabled = false,
  idPrefix = "chart-series-colors",
  portalScopeClassName,
  className,
}: ChartSeriesColorsPopoverProps) {
  const [open, setOpen] = useState(false);
  const [selectedKey, setSelectedKey] = useState(series[0]?.dataKey ?? "");
  const rootRef = useRef<HTMLDivElement>(null);
  const panelRef = useRef<HTMLDivElement>(null);
  const menuId = useId();
  const copy = { ...DEFAULT_LABELS, ...labels };

  useEffect(() => {
    if (series.some((entry) => entry.dataKey === selectedKey)) return;
    setSelectedKey(series[0]?.dataKey ?? "");
  }, [selectedKey, series]);

  const dirty = useMemo(() => {
    if (typeof hasOverrides === "boolean") return hasOverrides;
    if (values && Object.keys(values).length > 0) return true;
    return seriesViewHasOverrides({
      seriesFills: values ?? undefined,
    });
  }, [hasOverrides, values]);

  const selected = series.find((entry) => entry.dataKey === selectedKey) ?? series[0];
  const visibleCount = series.filter((entry) => entry.visible !== false).length;
  const close = () => setOpen(false);

  if (series.length === 0) return null;

  const rootClass = [
    "delpi-ui-chart-series-colors",
    open ? "delpi-ui-chart-series-colors--open" : null,
    dirty ? "delpi-ui-chart-series-colors--active" : null,
    className,
  ]
    .filter(Boolean)
    .join(" ");

  const fillValue = (() => {
    if (!selected) return "#089bdb";
    const override = values?.[selected.dataKey];
    if (typeof override === "string" && override.trim()) return override.trim();
    return selected.fill;
  })();

  const trendColorValue = selected?.trendColor?.trim() || selected?.fill || fillValue;
  const trendAutomatic = !selected?.trendColor?.trim();
  const selectClassName = "delpi-ui-select--compact";

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
          {selected ? (
            <>
              <label className="delpi-ui-chart-series-colors__field">
                <span className="delpi-ui-chart-series-colors__field-label">
                  {copy.seriesLabel}
                </span>
                <FormSelectControl
                  id={`${idPrefix}-series`}
                  ariaLabel={copy.seriesLabel}
                  value={selected.dataKey}
                  onChange={setSelectedKey}
                  allowEmpty={false}
                  searchable={false}
                  portalScopeClassName={portalScopeClassName}
                  className={selectClassName}
                  options={series.map((entry) => ({
                    value: entry.dataKey,
                    label: entry.name,
                  }))}
                />
              </label>
              <p className="delpi-ui-chart-series-colors__section">{copy.appearanceLabel}</p>
              <div className="delpi-ui-chart-series-colors__row">
                <span className="delpi-ui-chart-series-colors__row-name">{copy.colorLabel}</span>
                <ColorPickerPopoverTrigger
                  variant="fill"
                  showNoFill={false}
                  value={fillValue}
                  onChange={(color) => onChange(selected.dataKey, color)}
                  triggerLabel={copy.colorLabel}
                  triggerAriaLabel={`Cor da série ${selected.name}`}
                  triggerClassName="delpi-ui-chart-series-colors__picker"
                />
              </div>
              {onVisibleChange ? (
                <NativeCheckboxControl
                  id={`${idPrefix}-visible`}
                  checked={selected.visible !== false}
                  disabled={selected.visible !== false && visibleCount <= 1}
                  onChange={(checked) => onVisibleChange(selected.dataKey, checked)}
                  label={copy.visibleLabel}
                />
              ) : null}
              {selected.trendCapable !== false && onTrendChange ? (
                <>
                  <p className="delpi-ui-chart-series-colors__section">
                    {copy.trendSectionLabel}
                  </p>
                  <NativeCheckboxControl
                    id={`${idPrefix}-trend`}
                    checked={Boolean(selected.trendEnabled)}
                    onChange={(checked) => onTrendChange(selected.dataKey, checked)}
                    label={copy.trendEnableLabel}
                  />
                  {selected.trendEnabled ? (
                    <>
                      <div className="delpi-ui-chart-series-colors__row">
                        <span className="delpi-ui-chart-series-colors__row-name">
                          {copy.trendTypeLabel}
                        </span>
                        <span className="delpi-ui-chart-series-colors__readonly">
                          {copy.trendTypeLinearLabel}
                        </span>
                      </div>
                      <div className="delpi-ui-chart-series-colors__row">
                        <span className="delpi-ui-chart-series-colors__row-name">
                          {copy.trendColorLabel}
                        </span>
                        <ColorPickerPopoverTrigger
                          variant="text"
                          showNoFill={false}
                          showAutomatic
                          automaticLabel={copy.trendColorAutoLabel}
                          value={trendColorValue}
                          onChange={(color) =>
                            onTrendStyleChange?.(selected.dataKey, { color })
                          }
                          onAutomatic={() =>
                            onTrendStyleChange?.(selected.dataKey, { color: "" })
                          }
                          triggerLabel={
                            trendAutomatic
                              ? copy.trendColorAutoLabel
                              : copy.trendColorLabel
                          }
                          triggerAriaLabel={`Cor da tendência ${selected.name}`}
                          triggerClassName="delpi-ui-chart-series-colors__picker"
                        />
                      </div>
                      {onTrendStyleChange ? (
                        <>
                          <label className="delpi-ui-chart-series-colors__field">
                            <span className="delpi-ui-chart-series-colors__field-label">
                              {copy.trendDashLabel}
                            </span>
                            <FormSelectControl
                              id={`${idPrefix}-trend-dash`}
                              ariaLabel={copy.trendDashLabel}
                              value={selected.trendDash ?? "dashed"}
                              onChange={(value) =>
                                onTrendStyleChange(selected.dataKey, {
                                  dash: value as SeriesTrendDash,
                                })
                              }
                              allowEmpty={false}
                              searchable={false}
                              portalScopeClassName={portalScopeClassName}
                              className={selectClassName}
                              options={[
                                { value: "dashed", label: copy.trendDashDashedLabel },
                                { value: "solid", label: copy.trendDashSolidLabel },
                              ]}
                            />
                          </label>
                          <label className="delpi-ui-chart-series-colors__field">
                            <span className="delpi-ui-chart-series-colors__field-label">
                              {copy.trendWidthLabel}
                            </span>
                            <FormSelectControl
                              id={`${idPrefix}-trend-width`}
                              ariaLabel={copy.trendWidthLabel}
                              value={String(selected.trendWidth ?? 3)}
                              onChange={(value) =>
                                onTrendStyleChange(selected.dataKey, {
                                  width: Number(value),
                                })
                              }
                              allowEmpty={false}
                              searchable={false}
                              portalScopeClassName={portalScopeClassName}
                              className={selectClassName}
                              options={[
                                { value: "2", label: copy.trendWidthThinLabel },
                                { value: "3", label: copy.trendWidthDefaultLabel },
                                { value: "4", label: copy.trendWidthThickLabel },
                              ]}
                            />
                          </label>
                        </>
                      ) : null}
                      {onIncompleteBucketWeightChange ? (
                        <NativeCheckboxControl
                          id={`${idPrefix}-trend-weight`}
                          checked={incompleteBucketWeighted}
                          disabled={selected.trendApplyIncompleteBucket === false}
                          onChange={onIncompleteBucketWeightChange}
                          label={copy.trendWeightIncompleteLabel}
                          hint={incompleteBucketWeightHint}
                          hintPlacement={
                            incompleteBucketWeightHint ? "tooltip" : "inline"
                          }
                          hintAriaLabel={incompleteBucketWeightHintAriaLabel}
                        />
                      ) : null}
                    </>
                  ) : null}
                </>
              ) : null}
            </>
          ) : null}
          <div className="delpi-ui-chart-series-colors__actions">
            {onResetSeries && selected ? (
              <button
                type="button"
                className="delpi-ui-chart-series-colors__reset"
                onClick={() => onResetSeries(selected.dataKey)}
              >
                {resetSeriesLabel}
              </button>
            ) : null}
            {onReset ? (
              <button
                type="button"
                className="delpi-ui-chart-series-colors__reset"
                disabled={!dirty}
                onClick={() => onReset()}
              >
                {resetLabel}
              </button>
            ) : null}
          </div>
        </div>
      </AnchoredPanelPortal>
    </div>
  );
}
