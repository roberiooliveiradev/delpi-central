import { createContext, useContext, type ReactNode } from "react";

export type DeckEditorHistoryContextValue = {
  recordBeforeChange: (liveComunicadoOverride?: Record<string, unknown> | null) => void;
  undo: () => void;
  redo: () => void;
  canUndo: boolean;
  canRedo: boolean;
  /**
   * Incrementado em cada undo/redo do deck.
   * O editor de comunicado aceita o `value` externo correspondente (senão o gate
   * anti-eco stale rejeitaria o nativeConfig restaurado).
   */
  historyEpoch: number;
  setLiveComunicadoConfig: (config: Record<string, unknown> | null) => void;
};

const DeckEditorHistoryContext = createContext<DeckEditorHistoryContextValue | null>(null);

export function DeckEditorHistoryProvider({
  value,
  children,
}: {
  value: DeckEditorHistoryContextValue;
  children: ReactNode;
}) {
  return <DeckEditorHistoryContext.Provider value={value}>{children}</DeckEditorHistoryContext.Provider>;
}

export function useDeckEditorHistoryContext(): DeckEditorHistoryContextValue | null {
  return useContext(DeckEditorHistoryContext);
}
