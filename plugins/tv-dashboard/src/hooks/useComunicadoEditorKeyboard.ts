import { useEffect } from "react";

import type { ComunicadoEditorKeyboardActions } from "../components/comunicadoEditorTypes";

function isEditableTarget(target: EventTarget | null): boolean {
  if (!(target instanceof HTMLElement)) return false;
  const tag = target.tagName;
  return tag === "INPUT" || tag === "TEXTAREA" || tag === "SELECT" || target.isContentEditable;
}

/** Atalhos do editor — recebe ações do provider (sem importar o contexto, evita ciclo ESM). */
export function useComunicadoEditorKeyboard({
  selectedIds,
  editingTextId,
  hasPartSelection = false,
  clearPartSelection,
  undo,
  redo,
  canUndo,
  canRedo,
  duplicateSelected,
  removeSelected,
  cutSelected,
  copySelected,
  pasteSelected,
  canPaste,
  nudgeSelected,
  enableHistoryShortcuts = true,
}: ComunicadoEditorKeyboardActions & { enableHistoryShortcuts?: boolean }) {
  const hasSelection = selectedIds.length > 0;

  useEffect(() => {
    function onKeyDown(event: KeyboardEvent) {
      if (isEditableTarget(event.target)) return;
      if (editingTextId) return;

      const mod = event.ctrlKey || event.metaKey;
      const key = event.key.toLowerCase();

      if (event.key === "Escape" && hasPartSelection) {
        event.preventDefault();
        clearPartSelection?.();
        return;
      }

      if (mod && key === "z" && !event.shiftKey) {
        if (!enableHistoryShortcuts || !canUndo) return;
        event.preventDefault();
        undo();
        return;
      }

      if ((mod && key === "y") || (mod && event.shiftKey && key === "z")) {
        if (!enableHistoryShortcuts || !canRedo) return;
        event.preventDefault();
        redo();
        return;
      }

      if (mod && key === "x" && hasSelection) {
        event.preventDefault();
        cutSelected();
        return;
      }

      if (mod && key === "c" && hasSelection) {
        event.preventDefault();
        copySelected();
        return;
      }

      if (mod && key === "v" && canPaste) {
        event.preventDefault();
        pasteSelected();
        return;
      }

      if (mod && key === "d") {
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
    canPaste,
    canRedo,
    canUndo,
    clearPartSelection,
    copySelected,
    cutSelected,
    duplicateSelected,
    editingTextId,
    hasPartSelection,
    hasSelection,
    enableHistoryShortcuts,
    nudgeSelected,
    pasteSelected,
    redo,
    removeSelected,
    undo,
  ]);
}
