import { useMemo, type KeyboardEvent } from "react";

import { delpiUiClass, withBemModifier } from "../../utils/delpiUiClass";
import { buildPieSlicePath } from "./seriesChart/ChartSeriesPie";

export type DistributionDonutTone =
  | "chart-1"
  | "chart-2"
  | "chart-3"
  | "chart-4"
  | "chart-5"
  | "chart-6"
  | "chart-7"
  | "chart-8"
  | "success"
  | "warning"
  | "danger"
  | "info"
  | "neutral";

export type DistributionDonutItem = {
  id: string;
  label: string;
  value: number;
  /** Default: `chart-n` following the item order. */
  tone?: DistributionDonutTone;
  /** Tooltip and accessible description. */
  description?: string;
};

export type DistributionDonutLabels = {
  /** Name of the grouped remainder when `maxItems` is exceeded. */
  others: string;
  /** Center caption when nothing is selected. */
  total: string;
  /** Button that clears the current selection (shown only with a selection). */
  clearSelection: string;
};

export type DistributionDonutClassNames = {
  root: string;
  chart: string;
  svg: string;
  slice: string;
  center: string;
  centerValue: string;
  centerLabel: string;
  legend: string;
  legendList: string;
  legendItem: string;
  legendButton: string;
  legendDot: string;
  legendLabel: string;
  legendValue: string;
  legendPercent: string;
  clearSelection: string;
  empty: string;
};

export type DistributionDonutProps = {
  items: DistributionDonutItem[];
  selectedId?: string | null;
  /** With it, slices and list items become toggle buttons. Selecting the selected item sends `null`. */
  onSelect?: (item: DistributionDonutItem | null) => void;
  /** Default: formatted total (or the selected item's value). */
  centerValue?: string;
  /** Default: total caption (or the selected item's label). */
  centerLabel?: string;
  /** Diameter in px. Default 200. */
  size?: number;
  /** Ring thickness as a fraction of the radius (0.1–0.5). Default 0.28. */
  thickness?: number;
  /** Default `"side"`; becomes `"below"` under 480px of container width. */
  legendPlacement?: "side" | "below" | "none";
  /** Default true. */
  showPercent?: boolean;
  valueFormatter?: (value: number) => string;
  /** Above this count the remaining items are grouped into a non-selectable "others" entry. */
  maxItems?: number;
  emptyMessage?: string;
  ariaLabel: string;
  labels?: Partial<DistributionDonutLabels>;
  /** BEM dual-class prefix. Default `ds`. */
  prefix?: string;
  className?: string;
  classNames?: Partial<DistributionDonutClassNames>;
};

export const DEFAULT_DISTRIBUTION_DONUT_LABELS: DistributionDonutLabels = {
  others: "Outros",
  total: "Total",
  clearSelection: "Limpar seleção",
};

export const DISTRIBUTION_DONUT_CHART_TONES: readonly DistributionDonutTone[] = [
  "chart-1",
  "chart-2",
  "chart-3",
  "chart-4",
  "chart-5",
  "chart-6",
  "chart-7",
  "chart-8",
];

const DEFAULT_SIZE = 200;
const DEFAULT_THICKNESS = 0.28;
const MIN_THICKNESS = 0.1;
const MAX_THICKNESS = 0.5;
const VIEW = 100;
const CENTER = VIEW / 2;
const OUTER_RADIUS = 48;
const OTHERS_ID = "__others__";

export function distributionDonutBemClasses(prefix: string): DistributionDonutClassNames {
  const ui = "delpi-ui-distribution-donut";
  const base = `${prefix}-distribution-donut`;
  const pair = (local: string, canonical: string) => delpiUiClass(local, canonical);
  return {
    root: pair(base, ui),
    chart: pair(`${base}__chart`, `${ui}__chart`),
    svg: pair(`${base}__svg`, `${ui}__svg`),
    slice: pair(`${base}__slice`, `${ui}__slice`),
    center: pair(`${base}__center`, `${ui}__center`),
    centerValue: pair(`${base}__center-value`, `${ui}__center-value`),
    centerLabel: pair(`${base}__center-label`, `${ui}__center-label`),
    legend: pair(`${base}__legend`, `${ui}__legend`),
    legendList: pair(`${base}__legend-list`, `${ui}__legend-list`),
    legendItem: pair(`${base}__legend-item`, `${ui}__legend-item`),
    legendButton: pair(`${base}__legend-button`, `${ui}__legend-button`),
    legendDot: pair(`${base}__legend-dot`, `${ui}__legend-dot`),
    legendLabel: pair(`${base}__legend-label`, `${ui}__legend-label`),
    legendValue: pair(`${base}__legend-value`, `${ui}__legend-value`),
    legendPercent: pair(`${base}__legend-percent`, `${ui}__legend-percent`),
    clearSelection: pair(`${base}__clear-selection`, `${ui}__clear-selection`),
    empty: pair(`${base}__empty`, `${ui}__empty`),
  };
}

function defaultFormatValue(value: number): string {
  return value.toLocaleString("pt-BR", { maximumFractionDigits: 1 });
}

function formatPercent(ratio: number): string {
  return `${(ratio * 100).toLocaleString("pt-BR", { maximumFractionDigits: 1 })}%`;
}

function clamp(value: number, min: number, max: number): number {
  return Math.min(max, Math.max(min, value));
}

type ResolvedEntry = {
  item: DistributionDonutItem;
  tone: DistributionDonutTone;
  value: number;
  ratio: number;
  selectable: boolean;
};

/**
 * Distribution donut with a side list; slices and list items can filter.
 * Arc geometry is shared with the series charts (`buildPieSlicePath`); the
 * kit owns presentation only — the consumer decides what a selection means.
 */
export function DistributionDonut({
  items,
  selectedId,
  onSelect,
  centerValue,
  centerLabel,
  size = DEFAULT_SIZE,
  thickness = DEFAULT_THICKNESS,
  legendPlacement = "side",
  showPercent = true,
  valueFormatter = defaultFormatValue,
  maxItems,
  emptyMessage = "Sem dados.",
  ariaLabel,
  labels: labelsOverride,
  prefix = "ds",
  className,
  classNames: classNamesOverride,
}: DistributionDonutProps) {
  const base = useMemo(() => distributionDonutBemClasses(prefix), [prefix]);
  const classNames = { ...base, ...classNamesOverride };
  const labels = { ...DEFAULT_DISTRIBUTION_DONUT_LABELS, ...labelsOverride };
  const interactive = typeof onSelect === "function";

  const entries = useMemo<ResolvedEntry[]>(() => {
    const clean = items.map((item) => ({
      ...item,
      value: Number.isFinite(item.value) && item.value > 0 ? item.value : 0,
    }));
    const groupRest = maxItems != null && maxItems >= 0 && clean.length > maxItems;
    const kept = groupRest ? clean.slice(0, maxItems) : clean;
    const resolved: Array<{ item: DistributionDonutItem; tone: DistributionDonutTone; selectable: boolean }> =
      kept.map((item, index) => ({
        item,
        tone: item.tone ?? DISTRIBUTION_DONUT_CHART_TONES[index % DISTRIBUTION_DONUT_CHART_TONES.length]!,
        selectable: true,
      }));
    if (groupRest) {
      resolved.push({
        item: {
          id: OTHERS_ID,
          label: labels.others,
          value: clean.slice(maxItems).reduce((sum, item) => sum + item.value, 0),
        },
        tone: "neutral",
        selectable: false,
      });
    }
    const sum = resolved.reduce((acc, entry) => acc + entry.item.value, 0);
    return resolved.map((entry) => ({
      ...entry,
      value: entry.item.value,
      ratio: sum > 0 ? entry.item.value / sum : 0,
    }));
  }, [items, maxItems, labels.others]);

  const total = entries.reduce((sum, entry) => sum + entry.value, 0);
  const rootClass = [withBemModifier(classNames.root, `legend-${legendPlacement}`), className]
    .filter(Boolean)
    .join(" ");

  if (entries.length === 0 || total <= 0) {
    return (
      <div className={[classNames.root, className].filter(Boolean).join(" ")}>
        <p className={classNames.empty}>{emptyMessage}</p>
      </div>
    );
  }

  const selectedEntry =
    selectedId != null ? entries.find((entry) => entry.selectable && entry.item.id === selectedId) : undefined;
  const hasSelection = selectedEntry !== undefined;

  const ringThickness = clamp(thickness, MIN_THICKNESS, MAX_THICKNESS);
  const innerRadius = OUTER_RADIUS * (1 - ringThickness);

  const toggle = (entry: ResolvedEntry) => {
    if (!onSelect || !entry.selectable) return;
    onSelect(entry.item.id === selectedId ? null : entry.item);
  };

  const describeEntry = (entry: ResolvedEntry): string => {
    const parts = [`${entry.item.label}: ${valueFormatter(entry.value)}`];
    if (showPercent) parts.push(formatPercent(entry.ratio));
    const text = parts.join(", ");
    return entry.item.description ? `${text}. ${entry.item.description}` : text;
  };

  const summary = `${ariaLabel}: ${entries
    .filter((entry) => entry.value > 0)
    .map((entry) => `${entry.item.label} ${showPercent ? formatPercent(entry.ratio) : valueFormatter(entry.value)}`)
    .join(", ")}`;

  const stateClass = (entry: ResolvedEntry, baseClass: string): string => {
    if (!hasSelection) return baseClass;
    return withBemModifier(baseClass, entry.item.id === selectedId ? "selected" : "dimmed");
  };

  let angle = -Math.PI / 2;
  const slices = entries
    .filter((entry) => entry.value > 0)
    .map((entry) => {
      const start = angle;
      const end = angle + entry.ratio * Math.PI * 2;
      angle = end;
      const sliceClass = withBemModifier(stateClass(entry, classNames.slice), `tone-${entry.tone}`);
      const path = buildPieSlicePath(CENTER, CENTER, OUTER_RADIUS, innerRadius, start, end);
      if (!interactive || !entry.selectable) {
        return (
          <path key={entry.item.id} d={path} className={sliceClass} data-slice-id={entry.item.id}>
            <title>{describeEntry(entry)}</title>
          </path>
        );
      }
      return (
        <path
          key={entry.item.id}
          d={path}
          className={sliceClass}
          data-slice-id={entry.item.id}
          role="button"
          tabIndex={0}
          aria-pressed={entry.item.id === selectedId}
          aria-label={describeEntry(entry)}
          onClick={() => toggle(entry)}
          onKeyDown={(event: KeyboardEvent<SVGPathElement>) => {
            if (event.key === "Enter" || event.key === " ") {
              event.preventDefault();
              toggle(entry);
            }
          }}
        >
          <title>{describeEntry(entry)}</title>
        </path>
      );
    });

  const centerValueText =
    centerValue ?? valueFormatter(selectedEntry ? selectedEntry.value : total);
  const centerLabelText = centerLabel ?? (selectedEntry ? selectedEntry.item.label : labels.total);

  return (
    <div className={rootClass} data-legend-placement={legendPlacement}>
      <div className={classNames.chart} style={{ width: size, height: size, maxWidth: "100%" }}>
        <svg
          className={classNames.svg}
          viewBox={`0 0 ${VIEW} ${VIEW}`}
          width="100%"
          height="100%"
          {...(interactive
            ? { role: "group", "aria-label": summary }
            : { role: "img", "aria-label": summary })}
        >
          {slices}
        </svg>
        <div className={classNames.center} aria-hidden="true">
          <strong className={classNames.centerValue}>{centerValueText}</strong>
          <span className={classNames.centerLabel}>{centerLabelText}</span>
        </div>
      </div>
      {legendPlacement !== "none" ? (
        <div className={classNames.legend}>
          <ul className={classNames.legendList} role="list">
            {entries.map((entry) => {
              const content = (
                <>
                  <span
                    className={withBemModifier(classNames.legendDot, `tone-${entry.tone}`)}
                    aria-hidden="true"
                  />
                  <span className={classNames.legendLabel}>{entry.item.label}</span>
                  <span className={classNames.legendValue}>{valueFormatter(entry.value)}</span>
                  {showPercent ? (
                    <span className={classNames.legendPercent}>{formatPercent(entry.ratio)}</span>
                  ) : null}
                </>
              );
              const itemClass = stateClass(entry, classNames.legendItem);
              if (!interactive || !entry.selectable) {
                return (
                  <li
                    key={entry.item.id}
                    className={itemClass}
                    title={entry.item.description}
                  >
                    {content}
                  </li>
                );
              }
              return (
                <li key={entry.item.id} className={itemClass}>
                  <button
                    type="button"
                    className={classNames.legendButton}
                    aria-pressed={entry.item.id === selectedId}
                    aria-label={entry.item.description ? describeEntry(entry) : undefined}
                    title={entry.item.description}
                    onClick={() => toggle(entry)}
                  >
                    {content}
                  </button>
                </li>
              );
            })}
          </ul>
          {interactive && hasSelection ? (
            <button
              type="button"
              className={classNames.clearSelection}
              onClick={() => onSelect?.(null)}
            >
              {labels.clearSelection}
            </button>
          ) : null}
        </div>
      ) : null}
    </div>
  );
}

export function createDashboardDistributionDonut(config: { prefix: string }) {
  return function DashboardDistributionDonut(
    props: Omit<DistributionDonutProps, "prefix">,
  ) {
    return <DistributionDonut prefix={config.prefix} {...props} />;
  };
}

export type DashboardDistributionDonutProps = Omit<DistributionDonutProps, "prefix">;
