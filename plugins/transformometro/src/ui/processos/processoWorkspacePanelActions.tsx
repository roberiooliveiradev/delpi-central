import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";

type SetPanelActions = (actions: ReactNode) => void;

const PanelActionsStateContext = createContext<ReactNode>(null);
const PanelActionsDispatchContext = createContext<SetPanelActions | null>(null);

export function ProcessoWorkspacePanelActionsProvider({ children }: { children: ReactNode }) {
  const [panelActions, setPanelActionsState] = useState<ReactNode>(null);

  const setPanelActions = useCallback<SetPanelActions>((actions) => {
    setPanelActionsState(actions);
  }, []);

  return (
    <PanelActionsDispatchContext.Provider value={setPanelActions}>
      <PanelActionsStateContext.Provider value={panelActions}>
        {children}
      </PanelActionsStateContext.Provider>
    </PanelActionsDispatchContext.Provider>
  );
}

/** Leitura das ações do painel ativo (sidebar). */
export function useProcessoWorkspacePanelActionsRegistry() {
  const panelActions = useContext(PanelActionsStateContext);
  const setPanelActions = useContext(PanelActionsDispatchContext);
  return useMemo(
    () => (setPanelActions ? { panelActions, setPanelActions } : null),
    [panelActions, setPanelActions]
  );
}

/**
 * Registra ações do painel no footer da sidebar.
 * Usa só o dispatch estável — não re-renderiza quando `panelActions` muda
 * (evita loop React #185 Maximum update depth exceeded).
 */
export function useProcessoWorkspacePanelActions(actions: ReactNode, enabled: boolean) {
  const setPanelActions = useContext(PanelActionsDispatchContext);

  useEffect(() => {
    if (!setPanelActions || !enabled) return;
    setPanelActions(actions);
    return () => setPanelActions(null);
  }, [actions, enabled, setPanelActions]);
}
