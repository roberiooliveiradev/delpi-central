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
  nudgeSelected: (dx: number, dy: number) => void;
};
