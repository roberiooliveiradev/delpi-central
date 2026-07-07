export type MediaLibraryTarget = "block" | "background" | "insert-image" | "insert-video";

export type ComunicadoEditorKeyboardActions = {
  selectedIds: string[];
  editingTextId: string | null;
  undo: () => void;
  redo: () => void;
  canUndo: boolean;
  canRedo: boolean;
  duplicateSelected: () => void;
  removeSelected: () => void;
  nudgeSelected: (dx: number, dy: number) => void;
};
