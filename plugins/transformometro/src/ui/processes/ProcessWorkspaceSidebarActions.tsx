import type { ReactNode } from "react";

import { useProcessWorkspacePanelActionsRegistry } from "./processWorkspacePanelActions";

type Props = {
  processActions?: ReactNode;
  /** Always visible (e.g. open interaction room), even when panel actions replace process CRUD. */
  persistentActions?: ReactNode;
};

/**
 * Footer da sidebar: ações do escopo ativo + ações persistentes do processo.
 * Painel (melhoria/revisão) tem prioridade sobre CRUD do processo-mestre —
 * nunca empilha exclusão/duplicação no escopo errado.
 */
export function ProcessWorkspaceSidebarActions({ processActions, persistentActions }: Props) {
  const registry = useProcessWorkspacePanelActionsRegistry();
  const panelActions = registry?.panelActions;
  const scopedActions = panelActions ?? processActions;

  if (!scopedActions && !persistentActions) return null;

  return (
    <div className="tm-processo-workspace-sidebar__footer">
      {persistentActions ? (
        <div className="tm-processo-workspace-sidebar__actions tm-processo-workspace-sidebar__actions--persistent">
          {persistentActions}
        </div>
      ) : null}
      {scopedActions ? (
        <div
          className={`tm-processo-workspace-sidebar__actions ${
            panelActions
              ? "tm-processo-workspace-sidebar__actions--panel"
              : "tm-processo-workspace-sidebar__actions--process"
          }`}
        >
          {scopedActions}
        </div>
      ) : null}
    </div>
  );
}
