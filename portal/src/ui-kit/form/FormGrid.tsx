// portal/src/ui-kit/form/FormGrid.tsx

import type { HTMLAttributes, ReactNode } from "react";
import "./FormGrid.css";

export type FormGridProps = HTMLAttributes<HTMLDivElement> & {
  columns?: 1 | 2 | 3;
  children?: ReactNode;
};

export function FormGrid({
  columns = 2,
  className,
  children,
  ...rest
}: FormGridProps) {
  const classes = [
    "portal-ui-form-grid",
    `portal-ui-form-grid--${columns}`,
    className ?? "",
  ]
    .filter(Boolean)
    .join(" ");

  return (
    <div className={classes} {...rest}>
      {children}
    </div>
  );
}
