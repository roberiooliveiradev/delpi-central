import type { ReactNode } from "react";

import type { RecursoWorkspaceSectionId } from "./configuracoesWorkspaceNav";

type Props = {
  active: boolean;
  sectionId: RecursoWorkspaceSectionId;
  children: ReactNode;
};

export function RecursoWorkspaceSectionPanel({ active, sectionId, children }: Props) {
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
