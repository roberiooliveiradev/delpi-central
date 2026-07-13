import type { CSSProperties, ReactNode } from "react";

import {
  configurableTableOptionsCssVars,
  configurableTableOptionsModifierClasses,
  type ConfigurableTableOptions,
} from "../configurableTableOptions";
import { resolveTableFrameStyle, type TablePartsMap } from "../configurableTableParts";
import { useConfigurableTableClasses } from "../configurableTableClasses";

export type TableContainerProps = {
  options: ConfigurableTableOptions;
  className?: string;
  empty?: boolean;
  emptyMessage?: string;
  children?: ReactNode;
  /** Moldura Office (`tableParts.frame`) — fill/stroke/radius. */
  tableParts?: TablePartsMap | null;
};

export function TableContainer({
  options,
  className,
  empty,
  emptyMessage = "Sem linhas",
  children,
  tableParts,
}: TableContainerProps) {
  const cn = useConfigurableTableClasses();
  const frame = resolveTableFrameStyle(tableParts);
  const classes = [
    cn.root,
    ...configurableTableOptionsModifierClasses(options, cn),
    empty ? cn.rootEmpty : "",
    className,
  ]
    .filter(Boolean)
    .join(" ");

  const style = {
    ...configurableTableOptionsCssVars(options, cn.cssVarPrefix),
    [`--${cn.cssVarPrefix}-bg`]: frame.fill,
    [`--${cn.cssVarPrefix}-frame-border-color`]: frame.stroke,
    [`--${cn.cssVarPrefix}-frame-border-width`]: `${Math.max(0, frame.strokeWidth)}px`,
    [`--${cn.cssVarPrefix}-frame-radius`]: `${Math.max(0, frame.borderRadius)}px`,
    [`--${cn.cssVarPrefix}-frame-shadow`]: frame.boxShadow,
  } as CSSProperties;

  if (empty) {
    return (
      <div className={classes} style={style}>
        <div className={cn.emptyState}>{emptyMessage}</div>
      </div>
    );
  }

  return (
    <div className={classes} style={style}>
      {children}
    </div>
  );
}
