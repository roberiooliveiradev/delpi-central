import { createContext, useContext, type RefObject } from "react";
import type { PointerEvent as ReactPointerEvent } from "react";

import type {
  ComunicadoBlock,
  ComunicadoConfig,
  ComunicadoDataFilters,
  ComunicadoListType,
  ComunicadoNamedTextStyle,
  ComunicadoShapeKind,
  ComunicadoTextBlock,
  ContentRunListSelectionState,
  ContentRunNamedStyleSelectionState,
  ContentRunSelectionStyleState,
  ContentRunStyleToggleKey,
  ComunicadoContentRun,
} from "@delpi/tv-dashboard-presentation";

import type { MediaAsset } from "../api/tvDashboardApi";
import type { ComunicadoSlideTheme } from "../content/comunicadoSlideThemes";
import type { LayoutAlignCommand } from "../utils/comunicadoLayoutAlign";
import type { BlockDragMode } from "./useCanvasBlockInteraction";
import type { MediaLibraryTarget } from "./comunicadoEditorTypes";

export type TextEditSelection = {
  blockId: string;
  start: number;
  end: number;
};

export type TextEditorBridge = {
  applyPartialStyleToggle: (toggleKey: ContentRunStyleToggleKey) => void;
  applyListToggle: (listType: ComunicadoListType) => void;
  applyNamedStyleToggle: (namedStyle: ComunicadoNamedTextStyle) => void;
  refreshSelectionState: () => void;
  /** Persiste o rascunho do contentEditable antes de sair do modo edição. */
  commitPending?: () => void;
};

/** Contrato do editor — separado do Provider para evitar ciclos ESM com hooks/modais. */
export type ComunicadoEditorContextValue = {
  config: ComunicadoConfig;
  blocks: ComunicadoBlock[];
  selectedIds: string[];
  selectedId: string | null;
  selected: ComunicadoBlock | null;
  selectedBlocks: ComunicadoBlock[];
  isBlockSelected: (blockId: string) => boolean;
  selectBlock: (blockId: string, options?: { additive?: boolean }) => void;
  selectBlocksByIds: (blockIds: string[]) => void;
  clearSelection: () => void;
  setSelectedId: (id: string | null) => void;
  editingTextId: string | null;
  setEditingTextId: (id: string | null) => void;
  textEditSelection: TextEditSelection | null;
  textEditSelectionStyle: ContentRunSelectionStyleState | null;
  textEditListSelection: ContentRunListSelectionState | null;
  textEditNamedStyleSelection: ContentRunNamedStyleSelectionState | null;
  registerTextEditorBridge: (blockId: string, bridge: TextEditorBridge | null) => void;
  reportTextEditSelection: (
    selection: TextEditSelection | null,
    runs?: ComunicadoContentRun[],
  ) => void;
  toggleEditingTextRunStyle: (toggleKey: ContentRunStyleToggleKey) => void;
  toggleSelectedTextListType: (listType: ComunicadoListType) => void;
  applySelectedNamedTextStyle: (namedStyle: ComunicadoNamedTextStyle) => void;
  uploading: boolean;
  shapeMenuOpen: boolean;
  setShapeMenuOpen: (open: boolean) => void;
  background: ComunicadoConfig["background"];
  canvasRef: RefObject<HTMLDivElement | null>;
  startDrag: (event: ReactPointerEvent, block: ComunicadoBlock, mode: BlockDragMode) => void;
  addBlock: (type: ComunicadoBlock["type"]) => void;
  addDataBlock: (block: ComunicadoBlock) => void;
  addShape: (shape: ComunicadoShapeKind) => void;
  addIconBlock: (iconName: string) => void;
  groupSelected: () => void;
  ungroupSelected: () => void;
  setDataFilters: (filters: ComunicadoDataFilters | undefined) => void;
  updateSelected: (patch: Partial<ComunicadoBlock>) => void;
  updateBlock: (blockId: string, patch: Partial<ComunicadoBlock>) => void;
  updateBlockContent: (blockId: string, content: string) => void;
  updateBlockTextFields: (
    blockId: string,
    fields: Pick<ComunicadoTextBlock, "content" | "contentRuns">,
  ) => void;
  updateBlockLink: (blockId: string, href: string | undefined) => void;
  updateSelectedStyle: (patch: NonNullable<ComunicadoBlock["style"]>) => void;
  removeSelected: () => void;
  duplicateSelected: () => void;
  replaceSelectedDataRoute: (block: ComunicadoBlock) => void;
  moveLayer: (direction: "up" | "down") => void;
  reorderBlockLayer: (blockId: string, targetIndex: number) => void;
  nudgeSelected: (dx: number, dy: number) => void;
  undo: () => void;
  redo: () => void;
  canUndo: boolean;
  canRedo: boolean;
  playlistId: string;
  mediaLibraryOpen: boolean;
  mediaLibraryTarget: MediaLibraryTarget;
  openMediaLibrary: (target: MediaLibraryTarget) => void;
  closeMediaLibrary: () => void;
  applyMediaAsset: (asset: MediaAsset) => void;
  triggerUpload: (target: "block" | "background") => void;
  setBackgroundColor: (value: string) => void;
  setBackgroundGradient: (from: string, to: string, angle?: number) => void;
  applySlideTemplate: (nativeConfig: Record<string, unknown>) => void;
  applySlideTheme: (theme: ComunicadoSlideTheme) => void;
  alignSelected: (command: LayoutAlignCommand) => void;
  stageZoom: number;
  setStageZoom: (zoom: number) => void;
  fitStageToView: () => void;
  canvasWrapRef: RefObject<HTMLDivElement | null>;
  showStageRulers: boolean;
  setShowStageRulers: (show: boolean) => void;
  showStageGrid: boolean;
  setShowStageGrid: (show: boolean) => void;
  showStageGuides: boolean;
  setShowStageGuides: (show: boolean) => void;
  snapEnabled: boolean;
  setSnapEnabled: (enabled: boolean) => void;
  fileInputRef: RefObject<HTMLInputElement | null>;
  handleUploadFile: (file: File, target: "block" | "background") => void;
  dataPreviewLoading: boolean;
  dataPreviewError: string | null;
};

export const ComunicadoEditorContext = createContext<ComunicadoEditorContextValue | null>(null);

export function useComunicadoEditor(): ComunicadoEditorContextValue {
  const ctx = useContext(ComunicadoEditorContext);
  if (!ctx) {
    throw new Error("useComunicadoEditor deve ser usado dentro de ComunicadoEditorProvider");
  }
  return ctx;
}
