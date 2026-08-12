import type { ReactNode } from "react";

import type { RevisaoWorkspaceSectionId } from "./processWorkspaceNav";

type Props = {
  active: boolean;
  sectionId: RevisaoWorkspaceSectionId;
  children: ReactNode;
};

export function RevisionWorkspaceSectionPanel({ active, sectionId, children }: Props) {
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
