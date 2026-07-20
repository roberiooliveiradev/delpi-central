import type { ReactNode } from "react";

import { useProcessoWorkspacePanelActionsRegistry } from "./processoWorkspacePanelActions";

type Props = {
  processActions?: ReactNode;
};

/**
 * Footer da sidebar: ações do escopo ativo apenas.
 * Painel (melhoria/revisão) tem prioridade sobre ações do processo-mestre —
 * nunca empilha os dois para evitar exclusão no escopo errado.
 */
export function ProcessoWorkspaceSidebarActions({ processActions }: Props) {
  const registry = useProcessoWorkspacePanelActionsRegistry();
  const panelActions = registry?.panelActions;

  if (panelActions) {
    return (
      <div className="tm-processo-workspace-sidebar__footer">
        <div className="tm-processo-workspace-sidebar__actions tm-processo-workspace-sidebar__actions--panel">
          {panelActions}
        </div>
      </div>
    );
  }

  if (!processActions) return null;

  return (
    <div className="tm-processo-workspace-sidebar__footer">
      <div className="tm-processo-workspace-sidebar__actions tm-processo-workspace-sidebar__actions--process">
        {processActions}
      </div>
    </div>
  );
}
