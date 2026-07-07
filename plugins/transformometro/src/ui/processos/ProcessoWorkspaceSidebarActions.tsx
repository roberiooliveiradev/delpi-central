import type { ReactNode } from "react";

import { useProcessoWorkspacePanelActionsRegistry } from "./processoWorkspacePanelActions";

type Props = {
  processActions?: ReactNode;
};

export function ProcessoWorkspaceSidebarActions({ processActions }: Props) {
  const registry = useProcessoWorkspacePanelActionsRegistry();
  const panelActions = registry?.panelActions;

  if (!panelActions && !processActions) return null;

  return (
    <div className="tm-processo-workspace-sidebar__footer">
      {panelActions ? (
        <div className="tm-processo-workspace-sidebar__actions tm-processo-workspace-sidebar__actions--panel">
          {panelActions}
        </div>
      ) : null}
      {processActions ? (
        <div className="tm-processo-workspace-sidebar__actions tm-processo-workspace-sidebar__actions--process">
          {processActions}
        </div>
      ) : null}
    </div>
  );
}
