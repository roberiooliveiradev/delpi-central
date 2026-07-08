import type { ReactNode } from "react";

import type { RevisaoWorkspaceSectionId } from "./processoWorkspaceNav";

type Props = {
  active: boolean;
  sectionId: RevisaoWorkspaceSectionId;
  children: ReactNode;
};

export function RevisaoWorkspaceSectionPanel({ active, sectionId, children }: Props) {
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
