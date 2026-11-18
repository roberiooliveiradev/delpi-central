import type { ButtonHTMLAttributes } from "react";

export type ChartSegmentButtonProps = Pick<
  ButtonHTMLAttributes<HTMLButtonElement>,
  "children" | "style" | "title" | "aria-label" | "draggable" | "onClick" | "onDragStart" | "onDragEnd"
>;

/** An individually focusable segment inside a stacked chart. */
export function ChartSegmentButton(props: ChartSegmentButtonProps) {
  return <button {...props} type="button" className="delpi-ui-chart-segment-button" />;
}
