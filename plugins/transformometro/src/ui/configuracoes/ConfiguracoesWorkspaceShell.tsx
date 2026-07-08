import { useCallback, useEffect, useMemo, useState, useSyncExternalStore, type CSSProperties, type ReactNode } from "react";

import {
  fetchFiliais,
  fetchRecursos,
  fetchSetores,
  type Filial,
  type RecursoCompartilhado,
  type Setor,
} from "../../data/api/transformometroApi";
import { TRANSFORMOMETRO_WORKSPACE_HASH_EVENT } from "../../utils/navigation";
import { ConfiguracoesWorkspaceSidebar } from "./ConfiguracoesWorkspaceSidebar";
import {
  buildConfiguracoesWorkspaceTree,
  parseRecursoSectionFromHash,
  type RecursoWorkspaceSectionId,
} from "./configuracoesWorkspaceNav";
import { useConfiguracoesWorkspaceSidebarLayout } from "./useConfiguracoesWorkspaceSidebarLayout";

type Props = {
  activeNodeId: string;
  getAccessToken?: () => string | undefined;
  onNavigate: (href: string) => void;
  backActions?: ReactNode;
  footerActions?: ReactNode;
  children: ReactNode;
};

export function ConfiguracoesWorkspaceShell({
  activeNodeId,
  getAccessToken,
  onNavigate,
  backActions,
  footerActions,
  children,
}: Props) {
  const [filiais, setFiliais] = useState<Filial[]>([]);
  const [setores, setSetores] = useState<Setor[]>([]);
  const [recursos, setRecursos] = useState<RecursoCompartilhado[]>([]);

  const loadSidebarData = useCallback(async () => {
    try {
      const [filiaisRes, setoresRes, recursosRes] = await Promise.all([
        fetchFiliais(getAccessToken, true),
        fetchSetores(getAccessToken),
        fetchRecursos(getAccessToken),
      ]);
      setFiliais(filiaisRes.items);
      setSetores(setoresRes.items);
      setRecursos(recursosRes.items);
    } catch {
      setFiliais([]);
      setSetores([]);
      setRecursos([]);
    }
  }, [getAccessToken]);

  useEffect(() => {
    void loadSidebarData();
  }, [loadSidebarData]);

  const treeNodes = useMemo(
    () => buildConfiguracoesWorkspaceTree({ filiais, setores, recursos }),
    [filiais, recursos, setores]
  );

  const { collapsed, toggleCollapsed, startResize, sidebarWidthPx } =
    useConfiguracoesWorkspaceSidebarLayout();

  const workspaceStyle = {
    "--tm-workspace-sidebar-width": `${sidebarWidthPx}px`,
  } as CSSProperties;

  return (
    <div
      className={`tm-processo-workspace${collapsed ? " tm-processo-workspace--sidebar-collapsed" : ""}`}
      style={workspaceStyle}
    >
      <div className="tm-processo-workspace-sidebar-shell">
        <ConfiguracoesWorkspaceSidebar
          nodes={treeNodes}
          activeNodeId={activeNodeId}
          onNavigate={onNavigate}
          backActions={backActions}
          footerActions={footerActions}
          collapsed={collapsed}
          onToggleCollapsed={toggleCollapsed}
        />
        {!collapsed ? (
          <div
            className="tm-processo-workspace-sidebar__resize-handle"
            role="separator"
            aria-orientation="vertical"
            aria-label="Redimensionar barra lateral"
            aria-valuenow={sidebarWidthPx}
            aria-valuemin={220}
            aria-valuemax={480}
            onPointerDown={startResize}
          />
        ) : null}
      </div>
      <div className="tm-processo-workspace__main">
        <div className="tm-processo-workspace__sections">{children}</div>
      </div>
    </div>
  );
}

function subscribeRecursoSection(onStoreChange: () => void) {
  window.addEventListener("hashchange", onStoreChange);
  window.addEventListener("popstate", onStoreChange);
  window.addEventListener(TRANSFORMOMETRO_WORKSPACE_HASH_EVENT, onStoreChange);
  return () => {
    window.removeEventListener("hashchange", onStoreChange);
    window.removeEventListener("popstate", onStoreChange);
    window.removeEventListener(TRANSFORMOMETRO_WORKSPACE_HASH_EVENT, onStoreChange);
  };
}

export function useRecursoWorkspaceSection(): RecursoWorkspaceSectionId {
  return useSyncExternalStore(
    subscribeRecursoSection,
    () => parseRecursoSectionFromHash(window.location.hash),
    () => "identificacao"
  );
}
