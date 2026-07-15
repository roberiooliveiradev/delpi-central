import { isEditableKeyboardTarget, useEditorShortcut } from "../keyboard";

/** Atalhos globais do editor da programação (undo/redo em toda a página). */
export function useDeckEditorKeyboard({
  undo,
  redo,
  canUndo,
  canRedo,
}: {
  undo: () => void;
  redo: () => void;
  canUndo: boolean;
  canRedo: boolean;
}) {
  useEditorShortcut(
    "deck-history",
    (event) => {
      if (isEditableKeyboardTarget(event.target)) return;
      const mod = event.ctrlKey || event.metaKey;
      if (mod && event.key.toLowerCase() === "z" && !event.shiftKey) {
        if (!canUndo) return;
        undo();
        return { handled: true };
      }
      if (
        (mod && event.key.toLowerCase() === "y") ||
        (mod && event.shiftKey && event.key.toLowerCase() === "z")
      ) {
        if (!canRedo) return;
        redo();
        return { handled: true };
      }
    },
    { phase: "bubble", priority: 50 },
  );
}
