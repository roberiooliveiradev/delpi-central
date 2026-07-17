import type { HTMLAttributes } from "react";

import {
  resolveDataCellSemantics,
  type ResolveDataCellOptions,
} from "./dataCellSemantics";

export type DataCellValueProps = {
  value: unknown;
  present?: boolean;
  labels?: Omit<ResolveDataCellOptions, "present">;
} & Omit<HTMLAttributes<HTMLSpanElement>, "children">;

export function DataCellValue({
  value,
  present = true,
  labels,
  className,
  title,
  ...props
}: DataCellValueProps) {
  const cell = resolveDataCellSemantics(value, { ...labels, present });
  const classes = [
    "delpi-ui-data-cell",
    `delpi-ui-data-cell--${cell.kind}`,
    className,
  ]
    .filter(Boolean)
    .join(" ");

  return (
    <span
      {...props}
      className={classes}
      data-cell-kind={cell.kind}
      aria-label={cell.ariaLabel}
      title={title ?? cell.title}
    >
      {cell.displayText}
    </span>
  );
}
