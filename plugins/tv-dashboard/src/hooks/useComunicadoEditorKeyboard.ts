import type { ComunicadoBlock } from "@delpi/tv-dashboard-presentation";

import type { ComunicadoEditorKeyboardActions } from "../components/comunicadoEditorTypes";
import { isEditableKeyboardTarget, useEditorShortcut } from "../keyboard";
import {
  resolveStageEnterKeyAction,
  resolveStageEscapeAction,
  resolveStageF2KeyAction,
} from "../utils/stageInteractionPolicy";

/** Atalhos do editor — recebe ações do provider (sem importar o contexto, evita ciclo ESM). */
export function useComunicadoEditorKeyboard({
  selectedIds,
  editingTextId,
  preferGroupChildrenSelection = false,
  hasPartSelection = false,
  clearPartSelection,
  clearSelection,
  enterTextEdit,
  exitTextEdit,
  isolateChild,
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
  groupSelected,
  ungroupSelected,
  nudgeSelected,
  enableHistoryShortcuts = true,
  stageDrawTool = null,
  clearStageDrawTool,
}: ComunicadoEditorKeyboardActions & {
  enableHistoryShortcuts?: boolean;
  blocks?: ComunicadoBlock[];
  selectBlocksByIds?: (ids: string[]) => void;
  stageDrawTool?: string | null;
  clearStageDrawTool?: () => void;
}) {
  const hasSelection = selectedIds.length > 0;

  useEditorShortcut(
    "comunicado-editor",
    (event) => {
      if (isEditableKeyboardTarget(event.target)) {
        /* Em contentEditable, F2 ainda alterna para seleção do objeto (PowerPoint). */
        if (editingTextId && event.key === "F2") {
          exitTextEdit?.();
          return { handled: true };
        }
        /*
         * Esc com filho selecionado (célula da Grade, parte KPI…): mesmo fluxo
         * do palco — sobe um nível — mesmo com caret em contentEditable.
         */
        if (event.key === "Escape" && hasPartSelection) {
          clearPartSelection?.();
          if (event.target instanceof HTMLElement) event.target.blur();
          return { handled: true };
        }
        return;
      }

      if (editingTextId) {
        if (event.key === "F2") {
          exitTextEdit?.();
          return { handled: true };
        }
        return;
      }

      const mod = event.ctrlKey || event.metaKey;
      const key = event.key.toLowerCase();

      if (event.key === "Escape") {
        if (stageDrawTool && clearStageDrawTool) {
          clearStageDrawTool();
          return { handled: true };
        }
        const escape = resolveStageEscapeAction({
          blocks,
          selectedIds,
          hasPartSelection,
          preferGroupChildrenSelection,
        });
        if (escape.type === "clear-parts") {
          clearPartSelection?.();
          return { handled: true };
        }
        if (escape.type === "select-ids" && selectBlocksByIds) {
          selectBlocksByIds(escape.ids);
          return { handled: true };
        }
        if (escape.type === "clear-selection") {
          clearSelection?.();
          return { handled: true };
        }
      }

      if (event.key === "F2") {
        const action = resolveStageF2KeyAction({
          blocks,
          selectedIds,
          editingTextId,
        });
        if (action.type === "enter-text-edit") {
          enterTextEdit?.(action.blockId);
          return { handled: true };
        }
        if (action.type === "exit-text-edit") {
          exitTextEdit?.();
          return { handled: true };
        }
      }

      if (event.key === "Enter" && !mod) {
        const action = resolveStageEnterKeyAction({ blocks, selectedIds });
        if (action.type === "enter-text-edit") {
          enterTextEdit?.(action.blockId);
          return { handled: true };
        }
        if (action.type === "isolate-child") {
          isolateChild?.(action.blockId);
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

      if (mod && key === "g") {
        if (!hasSelection) return;
        if (event.shiftKey) {
          ungroupSelected?.();
        } else {
          groupSelected?.();
        }
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
    /* Acima do deck-history (50): Ctrl+Z do slide é local/imediato. */
    { phase: "bubble", priority: 60 },
  );
}
