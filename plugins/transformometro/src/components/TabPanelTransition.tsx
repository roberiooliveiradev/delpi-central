import type { ReactNode } from "react";

type TabPanelTransitionProps = {
  tabKey: string;
  children: ReactNode;
  className?: string;
};

/** Troca suave entre painéis de abas internas (cadastro, diagrama, WBS). */
export function TabPanelTransition({ tabKey, children, className }: TabPanelTransitionProps) {
  const classes = ["tm-tab-panel-transition", className].filter(Boolean).join(" ");
  return (
    <div key={tabKey} className={classes}>
      {children}
    </div>
  );
}
