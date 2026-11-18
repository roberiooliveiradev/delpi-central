import type { CSSProperties, DragEvent, ReactNode } from "react";
import { ChartSegmentButton } from "./ChartSegmentButton";

type Segment = { id: string; label: string; value: number; color?: string };
type Column = {
  id: string;
  label: string;
  value: number;
  partial?: boolean;
  segments: readonly Segment[];
  footer?: ReactNode;
};

export type StackedColumnChartProps = {
  columns: readonly Column[];
  scale: number;
  reference: number | null;
  referenceLabel: string;
  referenceExceededLabel: string;
  formatValue: (value: number) => string;
  formatAxis: (value: number) => string;
  segmentActionLabel?: string;
  onSelectSegment?: (id: string) => void;
  onDragSegment?: (event: DragEvent<HTMLButtonElement>, id: string) => void;
  onDragEnd?: () => void;
  footer?: ReactNode;
  unassignLabel?: string;
};

const chart = "delpi-ui-stacked-column-chart";

export function StackedColumnChart({
  columns, scale, reference, referenceLabel, referenceExceededLabel, formatValue, formatAxis,
  segmentActionLabel, onSelectSegment, onDragSegment, onDragEnd, footer, unassignLabel,
}: StackedColumnChartProps) {
  const ticks = Array.from({ length: 5 }, (_, index) => scale * index / 4);
  const height = (value: number) => `${value / scale * 100}%`;
  return (
    <div className={chart}>
      <div className={`${chart}__scroll`}>
        <div className={`${chart}__grid`} style={{ "--column-count": columns.length } as CSSProperties}>
          <div className={`${chart}__plot`} aria-hidden="true">
            {ticks.map(value => (
              <div className={`${chart}__gridline`} key={value} style={{ bottom: height(value) }}><span>{formatAxis(value)}</span></div>
            ))}
            {reference !== null && (
              <div className={`${chart}__reference`} style={{ bottom: height(reference) }}><span>{referenceLabel} {formatValue(reference)}</span></div>
            )}
          </div>
          {columns.map(column => {
            const over = reference !== null && column.value > reference;
            return (
              <div className={`${chart}__column`} key={column.id} data-drop={column.id}>
                <div className={`${chart}__track`} aria-label={`${column.label}, ${formatValue(column.value)}`}>
                  <div className={`${chart}__stack`} style={{ height: height(column.value) }}>
                    {column.segments.map(segment => (
                      <ChartSegmentButton key={segment.id} draggable={Boolean(onDragSegment)}
                        style={{ flexGrow: segment.value, "--delpi-ui-chart-segment-fill": segment.color } as CSSProperties}
                        title={`${segment.label} · ${formatValue(segment.value)}`}
                        aria-label={[segment.label, formatValue(segment.value), segmentActionLabel].filter(Boolean).join(", ")}
                        onClick={onSelectSegment && (() => onSelectSegment(segment.id))}
                        onDragStart={onDragSegment && (event => onDragSegment(event, segment.id))}
                        onDragEnd={onDragEnd}>{segment.label}</ChartSegmentButton>
                    ))}
                  </div>
                  <span className={`${chart}__value${over ? " is-over" : ""}`} style={{ bottom: height(column.value) }}>
                    {formatValue(column.value)}{column.partial ? "*" : ""}
                    {over && <span title={referenceExceededLabel} aria-label={referenceExceededLabel}> ↑</span>}
                  </span>
                </div>
                {column.footer && <div className={`${chart}__column-footer`}>{column.footer}</div>}
              </div>
            );
          })}
        </div>
      </div>
      {(footer || unassignLabel) && (
        <div className={`${chart}__footer`}>
          {footer}
          {unassignLabel && <span className={`${chart}__unassign`} data-drop="">{unassignLabel}</span>}
        </div>
      )}
    </div>
  );
}
