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
  ComunicadoDataDisplayMode,
  ComunicadoChartType,
  ComunicadoChartPartRef,
  ComunicadoKpiPartRef,
  ComunicadoTablePartRef,
  ComunicadoTablePreset,
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

export type ComunicadoRibbonTabRequest =
  | "insert"
  | "format"
  | "chart"
  | "table"
  | "shape"
  | "element"
  | "data"
  | "layers"
  | "view";

/** Abas espelhadas entre top bar contextual e painel lateral. */
export type SelectionPanelTab = "element" | "data" | "layers";

/** Intenção ao abrir a aba Dados do painel lateral. */
export type DataPanelIntent = "binding" | "catalog";

/** Contrato do editor — separado do Provider para evitar ciclos ESM com hooks/modais. */
export type ComunicadoEditorContextValue = {
  config: ComunicadoConfig;
  /** Perfil de viewport da playlist — define o tamanho de design do palco. */
  viewportProfile: string;
  /** Slide cujo config já foi aplicado no provider (pode atrasar 1 frame vs selectedSlideId). */
  appliedSlideId?: string;
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
  /** Onda 4G — subseleção de parte do gráfico (título, série, marcador…). */
  selectedChartPart: ComunicadoChartPartRef | null;
  selectChartPart: (blockId: string, part: ComunicadoChartPartRef) => void;
  clearChartPartSelection: () => void;
  /** Edição inline de conteúdo da parte (título). */
  editingChartPart: ComunicadoChartPartRef | null;
  beginEditChartPart: (blockId: string, part: ComunicadoChartPartRef) => void;
  commitChartPartContent: (content: string) => void;
  cancelEditChartPart: () => void;
  /** Onda 4G.8 — subseleção de parte da tabela. */
  selectedTablePart: ComunicadoTablePartRef | null;
  selectTablePart: (blockId: string, part: ComunicadoTablePartRef) => void;
  clearTablePartSelection: () => void;
  /** KPI — subseleção de parte do card (título, valor, ícone…). */
  selectedKpiPart: ComunicadoKpiPartRef | null;
  selectKpiPart: (blockId: string, part: ComunicadoKpiPartRef) => void;
  clearKpiPartSelection: () => void;
  editingKpiPart: ComunicadoKpiPartRef | null;
  beginEditKpiPart: (blockId: string, part: ComunicadoKpiPartRef) => void;
  commitKpiPartContent: (content: string) => void;
  cancelEditKpiPart: () => void;
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
  addDataSourceBlock: (block: ComunicadoBlock) => void;
  addChartViewBlock: (chartType: ComunicadoChartType) => void;
  addCanvasTableBlock: (rows?: number, cols?: number) => void;
  addTableViewBlock: (rows: number, cols: number, preset: ComunicadoTablePreset) => void;
  addKpiViewBlock: () => void;
  openDataPanel: () => void;
  /** Abre o catálogo de inserção em modal (entrada pela top bar). */
  openDataCatalog: () => void;
  dataCatalogModalOpen: boolean;
  setDataCatalogModalOpen: (open: boolean) => void;
  dataPanelOpen: boolean;
  setDataPanelOpen: (open: boolean) => void;
  dataPanelIntent: DataPanelIntent;
  setDataPanelIntent: (intent: DataPanelIntent) => void;
  /** Aba Elemento/Dados/Camadas compartilhada entre ribbon e painel lateral. */
  selectionPanelTab: SelectionPanelTab;
  setSelectionPanelTab: (tab: SelectionPanelTab) => void;
  addShape: (shape: ComunicadoShapeKind) => void;
  addIconBlock: (iconName: string) => void;
  groupSelected: () => void;
  ungroupSelected: () => void;
  /** Liga os dois blocos selecionados com uma seta (MVP conector). */
  connectSelected: () => void;
  setDataFilters: (filters: ComunicadoDataFilters | undefined) => void;
  setSpeakerNotes: (notes: string) => void;
  updateSelected: (patch: Partial<ComunicadoBlock>) => void;
  updateBlock: (blockId: string, patch: Partial<ComunicadoBlock>) => void;
  updateBlockContent: (blockId: string, content: string) => void;
  updateBlockTextFields: (
    blockId: string,
    fields: Pick<ComunicadoTextBlock, "content" | "contentRuns">,
  ) => void;
  updateBlockLink: (blockId: string, href: string | undefined) => void;
  updateSelectedStyle: (patch: NonNullable<ComunicadoBlock["style"]>) => void;
  /** Tipografia Formatar — bloco text/heading ou parte textual KPI/chart. */
  updateSelectedTextFormatStyle: (patch: {
    fontFamily?: string;
    fontSize?: number;
    fontWeight?: string;
    fontStyle?: string;
    color?: string;
    textDecoration?: string;
    textHighlight?: string;
    textAlign?: string;
    verticalAlign?: string;
    textShadow?: string;
    textStrokeColor?: string;
    textStrokeWidth?: number;
    textReflection?: boolean;
  }) => void;
  removeSelected: () => void;
  duplicateSelected: () => void;
  cutSelected: () => void;
  copySelected: () => void;
  pasteSelected: () => void;
  canPaste: boolean;
  bringToFront: () => void;
  sendToBack: () => void;
  bringForward: () => void;
  sendBackward: () => void;
  requestRibbonTab: (tab: ComunicadoRibbonTabRequest) => void;
  ribbonTabRequest: ComunicadoRibbonTabRequest | null;
  clearRibbonTabRequest: () => void;
  replaceSelectedDataRoute: (block: ComunicadoBlock) => void;
  moveLayer: (direction: "up" | "down") => void;
  reorderBlockLayer: (blockId: string, targetIndex: number) => void;
  nudgeSelected: (dx: number, dy: number) => void;
  undo: () => void;
  redo: () => void;
  canUndo: boolean;
  canRedo: boolean;
  playlistId: string;
  /** Master slide da programação (fundo/logo herdados no palco — 4E.3). */
  masterLogo: {
    url?: string;
    frame?: { x?: number; y?: number; w?: number; h?: number };
    opacity?: number;
  } | null;
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
  /** Ferramenta pan (arrastar o palco). */
  stagePanMode: boolean;
  setStagePanMode: (enabled: boolean) => void;
  fileInputRef: RefObject<HTMLInputElement | null>;
  handleUploadFile: (file: File, target: "block" | "background") => void;
  uploadCustomFont: (file: File) => Promise<void>;
  dataPreviewLoading: boolean;
  dataPreviewError: string | null;
  globalRefreshSec: number;
  lastDataDisplayMode: ComunicadoDataDisplayMode;
  setLastDataDisplayMode: (mode: ComunicadoDataDisplayMode) => void;
};

export const ComunicadoEditorContext = createContext<ComunicadoEditorContextValue | null>(null);

export function useComunicadoEditor(): ComunicadoEditorContextValue {
  const ctx = useContext(ComunicadoEditorContext);
  if (!ctx) {
    throw new Error("useComunicadoEditor deve ser usado dentro de ComunicadoEditorProvider");
  }
  return ctx;
}

/** Chrome / hooks que existem fora do provider em slides nativos. */
export function useOptionalComunicadoEditor(): ComunicadoEditorContextValue | null {
  return useContext(ComunicadoEditorContext);
}
