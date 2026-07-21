import type { ComunicadoBlock } from "@delpi/tv-dashboard-presentation";

import type { ComunicadoEditorKeyboardActions } from "../components/comunicadoEditorTypes";
import { isEditableKeyboardTarget, useEditorShortcut } from "../keyboard";
import { expandSelectionWithGroups } from "../utils/comunicadoGrouping";

/** Atalhos do editor — recebe ações do provider (sem importar o contexto, evita ciclo ESM). */
export function useComunicadoEditorKeyboard({
  selectedIds,
  editingTextId,
  hasPartSelection = false,
  clearPartSelection,
  blocks = [],
  selectBlocksByIds,
  undo,
  redo,
  canUndo,
  canRedo,
  duplicateSelected,
  removeSelected,
  cutSelected,
  copySelected,
  pasteSelected: _pasteSelected,
  canPaste: _canPaste,
  nudgeSelected,
  enableHistoryShortcuts = true,
}: ComunicadoEditorKeyboardActions & {
  enableHistoryShortcuts?: boolean;
  blocks?: ComunicadoBlock[];
  selectBlocksByIds?: (ids: string[]) => void;
}) {
  const hasSelection = selectedIds.length > 0;

  useEditorShortcut(
    "comunicado-editor",
    (event) => {
      if (isEditableKeyboardTarget(event.target)) return;
      if (editingTextId) return;

      const mod = event.ctrlKey || event.metaKey;
      const key = event.key.toLowerCase();

      if (event.key === "Escape" && hasPartSelection) {
        clearPartSelection?.();
        return { handled: true };
      }

      // Filho isolado do grupo (Camadas) → Esc volta à seleção pai.
      if (event.key === "Escape" && selectBlocksByIds && selectedIds.length === 1) {
        const alone = blocks.find((block) => block.id === selectedIds[0]);
        if (alone?.groupId) {
          selectBlocksByIds(expandSelectionWithGroups(blocks, [alone.id]));
          return { handled: true };
        }
      }

      if (mod && key === "z" && !event.shiftKey) {
        if (!enableHistoryShortcuts || !canUndo) return;
        undo();
        return { handled: true };
      }

      if ((mod && key === "y") || (mod && event.shiftKey && key === "z")) {
        if (!enableHistoryShortcuts || !canRedo) return;
        redo();
        return { handled: true };
      }

      if (mod && key === "x" && hasSelection) {
        cutSelected();
        return { handled: true };
      }

      if (mod && key === "c" && hasSelection) {
        copySelected();
        return { handled: true };
      }

      if (mod && key === "v") {
        // Colar é tratado pelo listener `paste` (SO + clipboard interno).
        return;
      }

      if (mod && key === "d") {
        if (!hasSelection) return;
        duplicateSelected();
        return { handled: true };
      }

      if ((event.key === "Delete" || event.key === "Backspace") && hasSelection) {
        removeSelected();
        return { handled: true };
      }

      if (!hasSelection) return;

      const step = event.shiftKey ? 10 : 1;
      if (event.key === "ArrowLeft") {
        nudgeSelected(-step, 0);
        return { handled: true };
      }
      if (event.key === "ArrowRight") {
        nudgeSelected(step, 0);
        return { handled: true };
      }
      if (event.key === "ArrowUp") {
        nudgeSelected(0, -step);
        return { handled: true };
      }
      if (event.key === "ArrowDown") {
        nudgeSelected(0, step);
        return { handled: true };
      }
    },
    { phase: "bubble", priority: 40 },
  );
}
