import {
  createContext,
  createElement,
  useContext,
  useEffect,
  useMemo,
  type ReactNode,
} from "react";

import {
  disposeEditorShortcutSession,
  getEditorShortcutSession,
} from "./editorShortcutSession";

type EditorShortcutsContextValue = {
  /** false = editor montado mas inativo (ex.: sob prévia); atalhos não engolem teclas. */
  active: boolean;
};

const EditorShortcutsContext = createContext<EditorShortcutsContextValue>({ active: true });

/**
 * Porta de entrada dos atalhos do deck.
 * - `active=false` enquanto o editor fica montado sob a prévia (keep-alive).
 * - No unmount, dispose garante que nenhum listener global sobreviva ao sair do Gerenciar.
 */
export function EditorShortcutsProvider({
  children,
  active = true,
}: {
  children: ReactNode;
  active?: boolean;
}) {
  useEffect(() => {
    getEditorShortcutSession().setEnabled(active);
  }, [active]);

  useEffect(() => {
    return () => {
      disposeEditorShortcutSession();
    };
  }, []);

  const value = useMemo(() => ({ active }), [active]);
  return createElement(EditorShortcutsContext.Provider, { value }, children);
}

export function useEditorShortcutsActive(): boolean {
  return useContext(EditorShortcutsContext).active;
}
