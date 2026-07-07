import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";

type PanelActionsContextValue = {
  panelActions: ReactNode;
  setPanelActions: (actions: ReactNode) => void;
};

const ProcessoWorkspacePanelActionsContext = createContext<PanelActionsContextValue | null>(null);

export function ProcessoWorkspacePanelActionsProvider({ children }: { children: ReactNode }) {
  const [panelActions, setPanelActionsState] = useState<ReactNode>(null);

  const setPanelActions = useCallback((actions: ReactNode) => {
    setPanelActionsState(actions);
  }, []);

  const value = useMemo(
    () => ({ panelActions, setPanelActions }),
    [panelActions, setPanelActions]
  );

  return (
    <ProcessoWorkspacePanelActionsContext.Provider value={value}>
      {children}
    </ProcessoWorkspacePanelActionsContext.Provider>
  );
}

export function useProcessoWorkspacePanelActionsRegistry() {
  return useContext(ProcessoWorkspacePanelActionsContext);
}

export function useProcessoWorkspacePanelActions(actions: ReactNode, enabled: boolean) {
  const registry = useProcessoWorkspacePanelActionsRegistry();

  useEffect(() => {
    if (!registry || !enabled) return;
    registry.setPanelActions(actions);
    return () => registry.setPanelActions(null);
  }, [actions, enabled, registry]);
}
