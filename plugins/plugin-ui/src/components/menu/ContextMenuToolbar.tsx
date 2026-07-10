import type { ReactNode } from "react";

export type ContextMenuToolbarProps = {
  children: ReactNode;
  "aria-label"?: string;
};

export function ContextMenuToolbar({ children, "aria-label": ariaLabel }: ContextMenuToolbarProps) {
  return (
    <div className="delpi-ui-context-menu__toolbar" role="toolbar" aria-label={ariaLabel}>
      {children}
    </div>
  );
}
