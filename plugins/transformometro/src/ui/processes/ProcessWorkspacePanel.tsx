import type { ReactNode } from "react";

type Props = {
  active: boolean;
  panelId: string;
  children: ReactNode;
};

export function ProcessWorkspacePanel({ active, panelId, children }: Props) {
  return (
    <div
      className={`tm-processo-workspace-section${active ? " tm-processo-workspace-section--active" : ""}`}
      data-panel={panelId}
      aria-hidden={!active}
    >
      {children}
    </div>
  );
}
