import { useEffect, useRef } from "react";

import {
  getEditorShortcutSession,
  type EditorShortcutHandler,
  type EditorShortcutPhase,
} from "./editorShortcutSession";

/**
 * Registra um handler na sessão central de atalhos enquanto o componente está montado.
 * Cleanup remove o handler; se for o último, a session solta o listener do window.
 */
export function useEditorShortcut(
  id: string,
  handler: EditorShortcutHandler,
  options?: { phase?: EditorShortcutPhase; priority?: number; enabled?: boolean },
): void {
  const handlerRef = useRef(handler);
  handlerRef.current = handler;
  const phase = options?.phase ?? "bubble";
  const priority = options?.priority ?? 0;
  const enabled = options?.enabled ?? true;

  useEffect(() => {
    if (!enabled) return;
    const session = getEditorShortcutSession();
    return session.register(
      id,
      (event) => handlerRef.current(event),
      { phase, priority },
    );
  }, [enabled, id, phase, priority]);
}
