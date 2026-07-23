export type MediaLibraryTarget =
  | "block"
  | "background"
  | "insert-image"
  | "insert-video"
  | "custom-font";

export type ComunicadoEditorKeyboardActions = {
  selectedIds: string[];
  editingTextId: string | null;
  /** Há parte de KPI/chart/tabela selecionada (Esc volta ao escopo global). */
  hasPartSelection?: boolean;
  clearPartSelection?: () => void;
  clearSelection?: () => void;
  /** Isola e entra em edição inline (F2 / Enter em texto). */
  enterTextEdit?: (blockId: string) => void;
  /** Sai da edição inline (F2 toggle). */
  exitTextEdit?: () => void;
  /** Isola filho sem expandir grupo (Enter em grupo). */
  isolateChild?: (blockId: string) => void;
  undo: () => void;
  redo: () => void;
  canUndo: boolean;
  canRedo: boolean;
  duplicateSelected: () => void;
  removeSelected: () => void;
  cutSelected: () => void;
  copySelected: () => void;
  pasteSelected: () => void;
  canPaste: boolean;
  groupSelected?: () => void;
  ungroupSelected?: () => void;
  nudgeSelected: (dx: number, dy: number) => void;
};
