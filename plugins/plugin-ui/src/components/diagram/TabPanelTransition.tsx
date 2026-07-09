import type { ReactNode } from "react";

type TabPanelTransitionProps = {
  tabKey: string;
  children: ReactNode;
  className?: string;
};

export function TabPanelTransition({ tabKey, children, className }: TabPanelTransitionProps) {
  const classes = ["delpi-ui-tab-panel-transition", className].filter(Boolean).join(" ");
  return (
    <div key={tabKey} className={classes}>
      {children}
    </div>
  );
}
