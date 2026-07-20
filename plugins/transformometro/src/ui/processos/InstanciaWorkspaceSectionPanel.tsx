import type { ReactNode } from "react";

import type { InstanciaWorkspaceSectionId } from "./processoWorkspaceNav";

type Props = {
  active: boolean;
  sectionId: InstanciaWorkspaceSectionId;
  children: ReactNode;
};

export function InstanciaWorkspaceSectionPanel({ active, sectionId, children }: Props) {
  return (
    <div
      className={`tm-processo-workspace-section${active ? " tm-processo-workspace-section--active" : ""}`}
      data-section={sectionId}
      aria-hidden={!active}
    >
      {children}
    </div>
  );
}
