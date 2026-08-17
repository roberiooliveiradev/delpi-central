import {
  createContext,
  useCallback,
  useContext,
  useMemo,
  useState,
  type ReactNode,
} from "react";

import {
  readCopilotDockVisible,
  writeCopilotDockVisible,
} from "../hooks/deckSidePanelLayout";

type TvCopilotDockContextValue = {
  /** Sidebar montada (aberta ou colapsada no rail). */
  visible: boolean;
  setVisible: (visible: boolean) => void;
  /** Incrementa para forçar expandir (aba da top bar). */
  expandToken: number;
  /** Abre a sidebar e solicita expansão. */
  openDock: () => void;
  /** Fecha por completo (sem rail). */
  closeDock: () => void;
};

const TvCopilotDockContext = createContext<TvCopilotDockContextValue | null>(null);

export function TvCopilotDockProvider({ children }: { children: ReactNode }) {
  const [visible, setVisibleState] = useState(() => readCopilotDockVisible());
  const [expandToken, setExpandToken] = useState(0);

  const setVisible = useCallback((next: boolean) => {
    setVisibleState(next);
    writeCopilotDockVisible(next);
  }, []);

  const openDock = useCallback(() => {
    setVisibleState(true);
    writeCopilotDockVisible(true);
    setExpandToken((n) => n + 1);
  }, []);

  const closeDock = useCallback(() => {
    setVisibleState(false);
    writeCopilotDockVisible(false);
  }, []);

  const value = useMemo(
    () => ({ visible, setVisible, expandToken, openDock, closeDock }),
    [visible, setVisible, expandToken, openDock, closeDock],
  );

  return (
    <TvCopilotDockContext.Provider value={value}>{children}</TvCopilotDockContext.Provider>
  );
}

export function useTvCopilotDock(): TvCopilotDockContextValue {
  const ctx = useContext(TvCopilotDockContext);
  if (!ctx) {
    throw new Error("useTvCopilotDock deve ser usado dentro de TvCopilotDockProvider");
  }
  return ctx;
}

export function useOptionalTvCopilotDock(): TvCopilotDockContextValue | null {
  return useContext(TvCopilotDockContext);
}
