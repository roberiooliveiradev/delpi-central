import { useEffect } from "react";

import { useComunicadoEditor } from "../components/comunicadoEditorContext";

function isEditableTarget(target: EventTarget | null): boolean {
  if (!(target instanceof HTMLElement)) return false;
  const tag = target.tagName;
  return tag === "INPUT" || tag === "TEXTAREA" || tag === "SELECT" || target.isContentEditable;
}

export function useComunicadoEditorKeyboard() {
  const {
    selectedIds,
    editingTextId,
    undo,
    redo,
    canUndo,
    canRedo,
    duplicateSelected,
    removeSelected,
    nudgeSelected,
  } = useComunicadoEditor();

  const hasSelection = selectedIds.length > 0;

  useEffect(() => {
    function onKeyDown(event: KeyboardEvent) {
      if (isEditableTarget(event.target)) return;
      if (editingTextId) return;

      const mod = event.ctrlKey || event.metaKey;

      if (mod && event.key.toLowerCase() === "z" && !event.shiftKey) {
        if (!canUndo) return;
        event.preventDefault();
        undo();
        return;
      }

      if ((mod && event.key.toLowerCase() === "y") || (mod && event.shiftKey && event.key.toLowerCase() === "z")) {
        if (!canRedo) return;
        event.preventDefault();
        redo();
        return;
      }

      if (mod && event.key.toLowerCase() === "d") {
        if (!hasSelection) return;
        event.preventDefault();
        duplicateSelected();
        return;
      }

      if ((event.key === "Delete" || event.key === "Backspace") && hasSelection) {
        event.preventDefault();
        removeSelected();
        return;
      }

      if (!hasSelection) return;

      const step = event.shiftKey ? 10 : 1;
      if (event.key === "ArrowLeft") {
        event.preventDefault();
        nudgeSelected(-step, 0);
      } else if (event.key === "ArrowRight") {
        event.preventDefault();
        nudgeSelected(step, 0);
      } else if (event.key === "ArrowUp") {
        event.preventDefault();
        nudgeSelected(0, -step);
      } else if (event.key === "ArrowDown") {
        event.preventDefault();
        nudgeSelected(0, step);
      }
    }

    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, [
    canRedo,
    canUndo,
    duplicateSelected,
    editingTextId,
    hasSelection,
    nudgeSelected,
    redo,
    removeSelected,
    undo,
  ]);
}
