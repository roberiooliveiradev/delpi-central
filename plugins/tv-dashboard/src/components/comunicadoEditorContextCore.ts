import { createContext, useContext, type RefObject } from "react";
import type { PointerEvent as ReactPointerEvent } from "react";

import type {
  ComunicadoBlock,
  ComunicadoConfig,
  ComunicadoDataFilters,
  ComunicadoInputBlock,
  ComunicadoListType,
  ComunicadoNamedTextStyle,
  ComunicadoShapeKind,
  ComunicadoTextBlock,
  ComunicadoDataDisplayMode,
  ComunicadoChartType,
  ComunicadoChartPartRef,
  ComunicadoInputPartRef,
  ComunicadoKpiPartRef,
  ComunicadoTablePartRef,
  ComunicadoTablePreset,
  ContentRunListSelectionState,
  ContentRunNamedStyleSelectionState,
  ContentRunSelectionStyleState,
  ContentRunStyleToggleKey,
  ComunicadoContentRun,
  PresentationSelectionUpdateEvent,
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
  /** Tipografia de caractere no trecho (fonte, tamanho, cor, realce…). */
  applyPartialStylePatch?: (
    patch: import("@delpi/tv-dashboard-presentation").ContentRunStylePatch,
  ) => void;
  applyListToggle: (listType: ComunicadoListType) => void;
  applyNamedStyleToggle: (namedStyle: ComunicadoNamedTextStyle) => void;
  refreshSelectionState: () => void;
  /** Persiste o rascunho do contentEditable antes de sair do modo edição. */
  commitPending?: () => void;
  /** Insere run dinâmico (`dataRef`) na posição do cursor. */
  insertDataRefAtSelection?: (dataRef: import("@delpi/tv-dashboard-presentation").ComunicadoTextDataRef) => void;
};

/** Visual criado junto com a fonte no wizard «Como apresentar?». */
export type DataInsertPreferredView = "kpi" | "table" | "series" | "text" | "shape";

export type ComunicadoRibbonTabRequest =
  | "insert"
  | "format"
  | "chart"
  | "table"
  | "kpi"
  | "canvasTable"
  | "shape"
  | "element"
  | "tableDesign"
  | "tableLayout"
  | "data"
  | "layers"
  | "view";

/** Célula selecionada na Grade (`canvas_table`) — espelho de parte KPI. */
export type ComunicadoCanvasTableCellSelection = {
  blockId: string;
  row: number;
  col: number;
};

/** Abas espelhadas entre top bar contextual e painel lateral. */
export type SelectionPanelTab =
  | "element"
  | "tableDesign"
  | "tableLayout"
  | "data"
  | "layers";

/** Intenção ao abrir a aba Dados do painel lateral. */
export type DataPanelIntent = "binding" | "catalog";

/** Modo do modal de catálogo: inserir fonte nova ou trocar a rota da seleção. */
export type DataCatalogMode = "insert" | "replace";

/** Opções ao abrir o catálogo de fontes (popover ancorado). */
export type OpenDataCatalogOptions = {
  /** Gatilho do popover — tipicamente `event.currentTarget` do botão. */
  anchor?: HTMLElement | null;
};

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
  /**
   * Modo filhos do grupo (`expandGroup: false`): permite selecionar todos os
   * irmãos sem promover ao chrome do grupo fechado.
   */
  preferGroupChildrenSelection: boolean;
  /** Seleções de outros editores no slide atual (chrome remoto, somente leitura). */
  remoteSelections: PresentationSelectionUpdateEvent[];
  isBlockSelected: (blockId: string) => boolean;
  selectBlock: (blockId: string, options?: { additive?: boolean; subtract?: boolean; expandGroup?: boolean }) => void;
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
  commitChartPartContent: (
    content: string,
    meta?: { contentRuns?: import("@delpi/plugin-ui/index").DeckContentRun[] },
  ) => void;
  cancelEditChartPart: () => void;
  /** Onda 4G.8 — subseleção de parte da tabela. */
  selectedTablePart: ComunicadoTablePartRef | null;
  /** Multi-seleção de colunas (Ctrl/Shift no cabeçalho) — o último item é a parte primária. */
  selectedTableParts: ComunicadoTablePartRef[];
  selectTablePart: (
    blockId: string,
    part: ComunicadoTablePartRef,
    options?: { additive?: boolean; range?: boolean },
  ) => void;
  clearTablePartSelection: () => void;
  /** Edição inline do rótulo do cabeçalho (headerCell) → fieldLabels da fonte. */
  editingTablePart: ComunicadoTablePartRef | null;
  beginEditTablePart: (blockId: string, part: ComunicadoTablePartRef) => void;
  cancelEditTablePart: () => void;
  /** KPI — subseleção de parte do card (título, valor, ícone…). */
  selectedKpiPart: ComunicadoKpiPartRef | null;
  /** Multi-seleção de partes KPI — o último item é a parte primária. */
  selectedKpiParts: ComunicadoKpiPartRef[];
  selectKpiPart: (
    blockId: string,
    part: ComunicadoKpiPartRef,
    options?: { additive?: boolean },
  ) => void;
  clearKpiPartSelection: () => void;
  editingKpiPart: ComunicadoKpiPartRef | null;
  beginEditKpiPart: (blockId: string, part: ComunicadoKpiPartRef) => void;
  commitKpiPartContent: (
    content: string,
    meta?: { contentRuns?: import("@delpi/plugin-ui/index").DeckContentRun[] },
  ) => void;
  cancelEditKpiPart: () => void;
  /** Filtro — subseleção de parte (frame/icon/label/badge/control). */
  selectedInputPart: ComunicadoInputPartRef | null;
  selectedInputParts: ComunicadoInputPartRef[];
  selectInputPart: (
    blockId: string,
    part: ComunicadoInputPartRef,
    options?: { additive?: boolean },
  ) => void;
  clearInputPartSelection: () => void;
  /** Grade — célula selecionada (chrome + inspetor). */
  selectedCanvasTableCell: ComunicadoCanvasTableCellSelection | null;
  selectCanvasTableCell: (
    blockId: string,
    cell: { row: number; col: number } | null,
  ) => void;
  clearCanvasTableCellSelection: () => void;
  editingTextId: string | null;
  setEditingTextId: (id: string | null) => void;
  /** Isola o bloco e entra em edição inline (texto/título/shape). */
  enterTextEdit: (blockId: string) => void;
  textEditSelection: TextEditSelection | null;
  /**
   * Última seleção parcial da edição inline — usada pela ribbon quando o Range
   * do DOM some no clique do botão (evita formatar o bloco inteiro).
   */
  lastPartialTextEditSelection: TextEditSelection | null;
  textEditSelectionStyle: ContentRunSelectionStyleState | null;
  textEditListSelection: ContentRunListSelectionState | null;
  textEditNamedStyleSelection: ContentRunNamedStyleSelectionState | null;
  registerTextEditorBridge: (blockId: string, bridge: TextEditorBridge | null) => void;
  reportTextEditSelection: (
    selection: TextEditSelection | null,
    runs?: ComunicadoContentRun[],
  ) => void;
  toggleEditingTextRunStyle: (toggleKey: ContentRunStyleToggleKey) => void;
  /** Aplica tipografia de caractere no trecho em edição (fonte/tamanho/cor/realce). */
  applyEditingTextRunStylePatch: (
    patch: import("@delpi/tv-dashboard-presentation").ContentRunStylePatch,
  ) => void;
  toggleSelectedTextListType: (listType: ComunicadoListType) => void;
  applySelectedNamedTextStyle: (namedStyle: ComunicadoNamedTextStyle) => void;
  uploading: boolean;
  shapeMenuOpen: boolean;
  setShapeMenuOpen: (open: boolean) => void;
  /**
   * Ferramenta de desenho no palco (Inserir → Linha).
   * `null` = interação normal (seleção/marquee).
   */
  stageDrawTool: import("@delpi/tv-dashboard-presentation").ComunicadoLineToolId | null;
  setStageDrawTool: (
    tool: import("@delpi/tv-dashboard-presentation").ComunicadoLineToolId | null,
  ) => void;
  background: ComunicadoConfig["background"];
  canvasRef: RefObject<HTMLDivElement | null>;
  startDrag: (event: ReactPointerEvent, block: ComunicadoBlock, mode: BlockDragMode) => void;
  /** Arma seleção multi antes do drag (evita race com setState). */
  armMultiDragSelection: (ids: string[]) => void;
  /** Marca limpeza de seleção se o toque não virar arraste. */
  armTapDeselect: (blockId: string | null) => void;
  /** Cancela limpeza atrasada (ex.: clique duplo isolando filho). */
  cancelPendingTapDeselect: () => void;
  addBlock: (type: ComunicadoBlock["type"]) => void;
  addDataBlock: (block: ComunicadoBlock) => void;
  addDataSourceBlock: (
    block: ComunicadoBlock,
    options?: { preferredView?: DataInsertPreferredView },
  ) => void;
  addChartViewBlock: (chartType: ComunicadoChartType) => void;
  addCanvasTableBlock: (rows?: number, cols?: number) => void;
  addInputBlock: () => void;
  addTableViewBlock: (rows: number, cols: number, preset: ComunicadoTablePreset) => void;
  addKpiViewBlock: () => void;
  openDataPanel: () => void;
  /** Abre o painel lateral na aba Camadas (sem modal). */
  openLayersPanel: () => void;
  /**
   * Abre o catálogo em popover (Inserir / Trocar rota).
   * Passe `options.anchor` (ex.: `event.currentTarget`) para posicionar junto ao gatilho.
   */
  openDataCatalog: (mode?: DataCatalogMode, options?: OpenDataCatalogOptions) => void;
  dataCatalogModalOpen: boolean;
  setDataCatalogModalOpen: (open: boolean) => void;
  /** Elemento âncora do popover do catálogo (null = fallback central). */
  dataCatalogAnchor: HTMLElement | null;
  setDataCatalogAnchor: (anchor: HTMLElement | null) => void;
  dataCatalogMode: DataCatalogMode;
  setDataCatalogMode: (mode: DataCatalogMode) => void;
  dataPanelOpen: boolean;
  setDataPanelOpen: (open: boolean) => void;
  dataPanelIntent: DataPanelIntent;
  setDataPanelIntent: (intent: DataPanelIntent) => void;
  /** Aba Elemento/Dados/Camadas compartilhada entre ribbon e painel lateral. */
  selectionPanelTab: SelectionPanelTab;
  setSelectionPanelTab: (tab: SelectionPanelTab) => void;
  addShape: (shape: ComunicadoShapeKind) => void;
  /** Shape já com frame/vertices (gesto de desenho no palco). */
  addPreparedShapeBlock: (
    block: import("@delpi/tv-dashboard-presentation").ComunicadoShapeBlock,
  ) => void;
  addIconBlock: (iconName: string) => void;
  groupSelected: () => void;
  ungroupSelected: () => void;
  regroupSelected: () => void;
  lastUngroupedIds: string[];
  /** Liga os dois blocos selecionados com uma seta (MVP conector). */
  connectSelected: () => void;
  setDataFilters: (filters: ComunicadoDataFilters | undefined) => void;
  /** Atualiza input + espelho dataFilters (escopo slide) num único commit. */
  patchInputBlock: (
    blockId: string,
    inputPatch: Partial<ComunicadoInputBlock["input"]>,
    filterBundle?: Record<string, string | number | boolean | null | undefined>,
  ) => void;
  /** Debounce refresh das fontes amarradas ao filtro. */
  scheduleInputFilterRefresh: (block: ComunicadoInputBlock) => void;
  scheduleInputFilterRefreshById: (blockId: string) => void;
  setSpeakerNotes: (notes: string) => void;
  updateSelected: (patch: Partial<ComunicadoBlock>) => void;
  updateBlock: (blockId: string, patch: Partial<ComunicadoBlock>) => void;
  /** Patch live sem empilhar histórico (gesto de parte no palco). */
  updateBlockLive: (blockId: string, patch: Partial<ComunicadoBlock>) => void;
  /** Snapshot atual do config (antes de gesto live). */
  snapshotEditorConfig: () => ComunicadoConfig;
  /** Empilha undo do estado anterior após gesto live. */
  finalizeHistoryGesture: (before: ComunicadoConfig) => void;
  /** Aplica patches de vários blocos em um único commit de config/histórico. */
  updateBlocksAtomically: (
    patches: ReadonlyArray<{ blockId: string; patch: Partial<ComunicadoBlock> }>,
  ) => void;
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
  /** Insere run dinâmico no cursor do texto em edição (requer fonte + campo). */
  insertDataFieldAtCursor: () => void;
  removeSelected: () => void;
  duplicateSelected: () => void;
  cutSelected: () => void;
  copySelected: () => void;
  pasteSelected: () => void | Promise<void>;
  /** Cola do SO (imagem/HTML/texto) ou do clipboard interno. */
  pasteFromSystemClipboard: () => Promise<boolean>;
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
  /** Clipboard do SO tem imagem (probe assíncrono). */
  probeClipboardHasImage: () => Promise<boolean>;
  /** Troca mídia do bloco selecionado pela imagem do clipboard (mantém frame). */
  replaceSelectedMediaFromClipboard: () => Promise<boolean>;
  setBackgroundColor: (value: string) => void;
  setBackgroundGradient: (from: string, to: string, angle?: number) => void;
  /** Vincula texto/forma selecionado à fonte preferida do slide (ou abre catálogo). */
  bindSelectedVisualBoxToData: () => void;
  /** Insere bloco de texto e vincula campo dinâmico quando há fonte no slide. */
  insertTextDataFieldBlock: () => void;
  applySlideTemplate: (nativeConfig: Record<string, unknown>) => void;
  applySlideTheme: (theme: ComunicadoSlideTheme) => void;
  alignSelected: (command: LayoutAlignCommand) => void;
  rotateSelected: (deltaDeg: number) => void;
  flipSelectedHorizontal: () => void;
  flipSelectedVertical: () => void;
  setBlocksHidden: (blockIds: string[], hidden: boolean) => void;
  toggleBlockHidden: (blockId: string) => void;
  showAllBlocks: () => void;
  hideAllBlocks: () => void;
  focusFrameRotationField: () => void;
  stageZoom: number;
  setStageZoom: (zoom: number) => void;
  fitStageToView: () => void;
  restoreStageViewPosition: () => boolean;
  /** Load: restaura ou Ajustar + grava 1ª posição. */
  bootstrapStageViewPosition: () => void;
  /** false enquanto bootstrap — não compensar gutter sobre o restore. */
  stageViewReady: boolean;
  persistStageViewPosition: (options?: { immediate?: boolean }) => void;
  canvasWrapRef: RefObject<HTMLDivElement | null>;
  showStageRulers: boolean;
  setShowStageRulers: (show: boolean) => void;
  showStageGrid: boolean;
  setShowStageGrid: (show: boolean) => void;
  stageGridSizePercent: number;
  setStageGridSizePercent: (sizePercent: number) => void;
  showStageGuides: boolean;
  setShowStageGuides: (show: boolean) => void;
  /** Linhas de alinhamento entre componentes durante drag (smart guides). */
  activeSmartGuides: ReadonlyArray<{ orientation: "v" | "h"; position: number }>;
  /** Sites de conexão visíveis ao arrastar ponta de linha. */
  connectionSitesPreview: {
    blockId: string;
    endpointIndex: 0 | 1;
    point: { x: number; y: number };
    sites: ReadonlyArray<{
      blockId: string;
      id: string;
      x: number;
      y: number;
    }>;
    activeSite: {
      blockId: string;
      id: string;
      x: number;
      y: number;
    } | null;
  } | null;
  snapToGrid: boolean;
  setSnapToGrid: (enabled: boolean) => void;
  snapToObjects: boolean;
  setSnapToObjects: (enabled: boolean) => void;
  /** Ferramenta pan (arrastar o palco). */
  stagePanMode: boolean;
  setStagePanMode: (enabled: boolean) => void;
  fileInputRef: RefObject<HTMLInputElement | null>;
  handleUploadFile: (file: File, target: "block" | "background") => void;
  uploadCustomFont: (file: File) => Promise<void>;
  dataPreviewLoading: boolean;
  dataPreviewError: string | null;
  /** Preview desatualizado após falha de fetch — usar «Atualizar visual». */
  isDataPreviewStale: boolean;
  staleSourceIds: string[];
  /** Fontes com fetch em andamento (spinner do filtro). */
  refreshingSourceIds: string[];
  loadingMoreSourceIds: string[];
  /** Percentual 0–100 do fetch de dados em curso; `null` quando ocioso. */
  dataPreviewLoadingProgress: number | null;
  refreshDataPreview: (options?: { force?: boolean; blockIds?: string[] }) => Promise<void>;
  loadMoreDataPreview: (blockId: string) => Promise<void>;
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
