import type { ReactNode } from "react";

import type { ProcessoWorkspaceSectionId } from "./processoWorkspaceNav";

type Props = {
  active: boolean;
  sectionId: ProcessoWorkspaceSectionId;
  children: ReactNode;
};

export function ProcessoWorkspaceSectionPanel({ active, sectionId, children }: Props) {
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
