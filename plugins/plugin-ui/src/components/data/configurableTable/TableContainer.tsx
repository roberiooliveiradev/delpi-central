import type { CSSProperties, ReactNode } from "react";

import {
  configurableTableOptionsCssVars,
  configurableTableOptionsModifierClasses,
  type ConfigurableTableOptions,
} from "../configurableTableOptions";
import { useConfigurableTableClasses } from "../configurableTableClasses";

export type TableContainerProps = {
  options: ConfigurableTableOptions;
  className?: string;
  empty?: boolean;
  emptyMessage?: string;
  children?: ReactNode;
};

export function TableContainer({
  options,
  className,
  empty,
  emptyMessage = "Sem linhas",
  children,
}: TableContainerProps) {
  const cn = useConfigurableTableClasses();
  const classes = [
    cn.root,
    ...configurableTableOptionsModifierClasses(options, cn),
    empty ? cn.rootEmpty : "",
    className,
  ]
    .filter(Boolean)
    .join(" ");

  const style = configurableTableOptionsCssVars(options, cn.cssVarPrefix) as CSSProperties;

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
