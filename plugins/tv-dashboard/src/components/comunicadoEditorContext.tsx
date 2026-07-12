import {
  useCallback,
  useEffect,
  useMemo,
  useRef,
  useState,
  type ReactNode,
} from "react";

import {
  createBlock,
  createIconBlock,
  createShapeBlock,
  createChartViewBlock,
  createTableViewBlock,
  isDataBlockType,
  isFetchableDataBlockType,
  isDataViewBlockType,
  newBlockId,
  nextZIndex,
  parseComunicadoConfig,
  ComunicadoListType,
  ComunicadoNamedTextStyle,
  type ComunicadoDataDisplayMode,
  applyNamedStyleInRange,
  applyNamedStyleOnAllLines,
  defaultNamedStyleForBlockType,
  resolveTextBlockDisplayRuns,
  resolveNamedStyleSelectionForBlock,
  selectionListTypeState,
  selectionNamedStyleState,
  selectionRunStyleState,
  serializeComunicadoConfig,
  sortBlocksByZIndex,
  syncTextBlockFields,
  syncTextBlockFromRuns,
  clampFrameForBlock,
  isLineShapeKind,
  syncLineVerticesFromFrame,
  toggleListTypeOnAllLines,
  type ComunicadoBlock,
  type ComunicadoConfig,
  type ComunicadoDataFilters,
  type ComunicadoShapeKind,
  type ComunicadoTextBlock,
  type ContentRunStyleToggleKey,
  type ComunicadoContentRun,
  type ComunicadoListType,
  type ComunicadoChartType,
  type ComunicadoChartPartRef,
  type ComunicadoTablePartRef,
  type ComunicadoTablePreset,
  chartOptionsToParts,
  mergeComunicadoChartOptions,
  partsToChartOptions,
  upsertChartPartState,
  chartPartAllowsDelete,
  chartPartAllowsMove,
  deleteChartPart,
  deleteTablePart,
  tablePartAllowsDelete,
  nudgeChartPartFrame,
} from "@delpi/tv-dashboard-presentation";

import { adminMediaUrl, uploadPlaylistMedia, type MediaAsset, type PlaylistMasterConfig } from "../api/tvDashboardApi";
import { useDeckEditorHistoryContext } from "../context/deckEditorHistoryContext";
import { useComunicadoDataPreview } from "../hooks/useComunicadoDataPreview";
import { useComunicadoEditorKeyboard } from "../hooks/useComunicadoEditorKeyboard";
import { MediaLibraryModal } from "./MediaLibraryModal";
import { enrichComunicadoConfigForEditor, resolveMasterForPreview } from "./slideCardPreview";
import { useCanvasBlockInteraction } from "./useCanvasBlockInteraction";
import { snapComunicadoFrame } from "../utils/comunicadoSnap";
import { alignComunicadoBlocks, type LayoutAlignCommand } from "../utils/comunicadoLayoutAlign";
import { cloneBlocksForClipboard, pasteClipboardBlocks } from "../utils/comunicadoEditorClipboard";
import {
  bringForward,
  bringToFront,
  sendBackward,
  sendToBack,
} from "../utils/comunicadoLayerOrder";
import { computeFitStageZoom } from "../utils/stageViewport";
import {
  expandSelectionWithGroups,
  groupBlocks,
  selectedHasGroup,
  ungroupBlocks,
} from "../utils/comunicadoGrouping";
import { applyComunicadoSlideTheme, type ComunicadoSlideTheme } from "../content/comunicadoSlideThemes";
import {
  ComunicadoEditorContext,
  useComunicadoEditor,
  type ComunicadoEditorContextValue,
  type ComunicadoRibbonTabRequest,
  type TextEditorBridge,
  type TextEditSelection,
} from "./comunicadoEditorContextCore";
import type { MediaLibraryTarget } from "./comunicadoEditorTypes";

export type { MediaLibraryTarget } from "./comunicadoEditorTypes";
export {
  useComunicadoEditor,
  useOptionalComunicadoEditor,
  type ComunicadoEditorContextValue,
} from "./comunicadoEditorContextCore";

const HISTORY_LIMIT = 50;

function snapshotConfig(config: ComunicadoConfig): ComunicadoConfig {
  return parseComunicadoConfig(serializeComunicadoConfig(config));
}

type ProviderProps = {
  playlistId: string;
  slideId?: string;
  globalRefreshSec?: number;
  masterConfig?: PlaylistMasterConfig;
  value: Record<string, unknown>;
  onChange: (config: Record<string, unknown>) => void;
  children: ReactNode;
};

function ComunicadoEditorKeyboardBridge() {
  const deckHistory = useDeckEditorHistoryContext();
  const {
    selectedIds,
    editingTextId,
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
  } = useComunicadoEditor();
  useComunicadoEditorKeyboard({
    selectedIds,
    editingTextId,
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
    enableHistoryShortcuts: !deckHistory,
  });
  return null;
}

export function ComunicadoEditorProvider({
  playlistId,
  globalRefreshSec = 300,
  masterConfig,
  value,
  onChange,
  children,
}: ProviderProps) {
  const deckHistory = useDeckEditorHistoryContext();
  const [config, setConfig] = useState<ComunicadoConfig>(() =>
    enrichComunicadoConfigForEditor(value, playlistId),
  );
  const [selectedIds, setSelectedIds] = useState<string[]>(() => {
    const first = config.blocks?.[0]?.id;
    return first ? [first] : [];
  });
  const [editingTextId, setEditingTextId] = useState<string | null>(null);
  const [selectedChartPart, setSelectedChartPart] = useState<ComunicadoChartPartRef | null>(null);
  const [editingChartPart, setEditingChartPart] = useState<ComunicadoChartPartRef | null>(null);
  const [selectedTablePart, setSelectedTablePart] = useState<ComunicadoTablePartRef | null>(null);
  const [lastDataDisplayMode, setLastDataDisplayMode] = useState<ComunicadoDataDisplayMode>("kpi");
  const [dataPanelOpen, setDataPanelOpen] = useState(false);
  const [textEditSelection, setTextEditSelection] = useState<TextEditSelection | null>(null);
  const [textEditSelectionStyle, setTextEditSelectionStyle] = useState<
    ComunicadoEditorContextValue["textEditSelectionStyle"]
  >(null);
  const [textEditListSelection, setTextEditListSelection] = useState<
    ComunicadoEditorContextValue["textEditListSelection"]
  >(null);
  const [textEditNamedStyleSelection, setTextEditNamedStyleSelection] = useState<
    ComunicadoEditorContextValue["textEditNamedStyleSelection"]
  >(null);
  const [uploading, setUploading] = useState(false);
  const [historyTick, setHistoryTick] = useState(0);

  const pastRef = useRef<ComunicadoConfig[]>([]);
  const futureRef = useRef<ComunicadoConfig[]>([]);
  const dragSnapshotRef = useRef<ComunicadoConfig | null>(null);
  const multiDragRef = useRef<{ startFrames: Map<string, ComunicadoBlock["frame"]> } | null>(null);
  const configRef = useRef(config);
  configRef.current = config;
  const textEditorBridgesRef = useRef<Map<string, TextEditorBridge>>(new Map());
  const editingTextIdRef = useRef<string | null>(editingTextId);
  editingTextIdRef.current = editingTextId;

  const flushActiveTextEdit = useCallback((blockId?: string | null) => {
    const activeId = blockId ?? editingTextIdRef.current;
    if (!activeId) return;
    textEditorBridgesRef.current.get(activeId)?.commitPending?.();
  }, []);

  const selectedId = selectedIds[selectedIds.length - 1] ?? null;

  const setSelectedId = useCallback((id: string | null) => {
    if (editingTextIdRef.current && editingTextIdRef.current !== id) {
      flushActiveTextEdit(editingTextIdRef.current);
    }
    setSelectedIds(id ? [id] : []);
    setEditingTextId((current) => (id === current ? current : null));
    setSelectedChartPart(null);
    setEditingChartPart(null);
    setSelectedTablePart(null);
    if (!id) {
      setTextEditSelection(null);
      setTextEditSelectionStyle(null);
      setTextEditListSelection(null);
      setTextEditNamedStyleSelection(null);
    }
  }, [flushActiveTextEdit]);

  const selectBlocksByIds = useCallback((blockIds: string[]) => {
    flushActiveTextEdit();
    const unique = [...new Set(blockIds.filter(Boolean))];
    setSelectedIds(unique);
    setEditingTextId(null);
    setSelectedChartPart(null);
    setEditingChartPart(null);
    setSelectedTablePart(null);
  }, [flushActiveTextEdit]);

  const selectBlock = useCallback(
    (blockId: string, options?: { additive?: boolean }) => {
      flushActiveTextEdit();
      let selectedBlockType: string | undefined;
      if (options?.additive) {
        setSelectedIds((current) => {
          const set = new Set(current);
          if (set.has(blockId)) set.delete(blockId);
          else set.add(blockId);
          return [...set];
        });
      } else {
        const block = configRef.current.blocks?.find((item) => item.id === blockId);
        selectedBlockType = block?.type;
        if (block?.groupId) {
          const memberIds =
            configRef.current.blocks
              ?.filter((item) => item.groupId === block.groupId)
              .map((item) => item.id) ?? [blockId];
          setSelectedIds(memberIds);
        } else {
          setSelectedIds([blockId]);
        }
      }
      setEditingTextId(null);
      setSelectedChartPart(null);
      setEditingChartPart(null);
      if (selectedBlockType === "chart_view") {
        setRibbonTabRequest("chart");
      } else if (selectedBlockType === "shape") {
        setRibbonTabRequest("shape");
      }
    },
    [flushActiveTextEdit],
  );

  const clearSelection = useCallback(() => {
    flushActiveTextEdit();
    setSelectedIds([]);
    setEditingTextId(null);
    setSelectedChartPart(null);
    setEditingChartPart(null);
    setSelectedTablePart(null);
  }, [flushActiveTextEdit]);

  const selectChartPart = useCallback(
    (blockId: string, part: ComunicadoChartPartRef) => {
      flushActiveTextEdit();
      setSelectedIds([blockId]);
      setEditingTextId(null);
      setSelectedTablePart(null);
      setSelectedChartPart(part);
      setEditingChartPart(null);
      const primitiveKinds = new Set([
        "marker",
        "series",
        "chartArea",
        "plotArea",
        "axis",
        "grid",
      ]);
      setRibbonTabRequest(primitiveKinds.has(part.kind) ? "shape" : "chart");
    },
    [flushActiveTextEdit],
  );

  const clearChartPartSelection = useCallback(() => {
    setSelectedChartPart(null);
    setEditingChartPart(null);
    setSelectedTablePart(null);
  }, []);

  const selectTablePart = useCallback(
    (blockId: string, part: ComunicadoTablePartRef) => {
      flushActiveTextEdit();
      setSelectedIds([blockId]);
      setEditingTextId(null);
      setSelectedChartPart(null);
      setEditingChartPart(null);
      setSelectedTablePart(part);
      setRibbonTabRequest("format");
    },
    [flushActiveTextEdit],
  );

  const clearTablePartSelection = useCallback(() => {
    setSelectedTablePart(null);
  }, []);

  const beginEditChartPart = useCallback(
    (blockId: string, part: ComunicadoChartPartRef) => {
      flushActiveTextEdit();
      setSelectedIds([blockId]);
      setEditingTextId(null);
      setSelectedChartPart(part);
      setEditingChartPart(part);
    },
    [flushActiveTextEdit],
  );

  const cancelEditChartPart = useCallback(() => {
    setEditingChartPart(null);
  }, []);

  const isBlockSelected = useCallback(
    (blockId: string) => selectedIds.includes(blockId),
    [selectedIds],
  );
  const [shapeMenuOpen, setShapeMenuOpen] = useState(false);
  const [stageZoom, setStageZoom] = useState(1);
  const [showStageRulers, setShowStageRulers] = useState(true);
  const [showStageGrid, setShowStageGrid] = useState(false);
  const [showStageGuides, setShowStageGuides] = useState(true);
  const canvasWrapRef = useRef<HTMLDivElement | null>(null);
  const [snapEnabled, setSnapEnabled] = useState(true);
  const snapEnabledRef = useRef(true);
  const [mediaLibraryOpen, setMediaLibraryOpen] = useState(false);
  const [mediaLibraryTarget, setMediaLibraryTarget] = useState<MediaLibraryTarget>("block");
  const [ribbonTabRequest, setRibbonTabRequest] = useState<ComunicadoRibbonTabRequest | null>(null);
  const [clipboardRevision, setClipboardRevision] = useState(0);
  const clipboardRef = useRef<ComunicadoBlock[]>([]);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const uploadTargetRef = useRef<"block" | "background">("block");
  const mediaLibraryTargetRef = useRef<MediaLibraryTarget>("block");

  useEffect(() => {
    snapEnabledRef.current = snapEnabled;
  }, [snapEnabled]);

  useEffect(() => {
    const enriched = enrichComunicadoConfigForEditor(value, playlistId);
    setConfig(enriched);
    pastRef.current = [];
    futureRef.current = [];
    dragSnapshotRef.current = null;
    setHistoryTick((tick) => tick + 1);
  }, [value, playlistId]);

  const { resolvedByBlockId, loading: dataPreviewLoading, error: dataPreviewError } =
    useComunicadoDataPreview({
      playlistId,
      config,
      globalRefreshSec,
    });

  const blocks = useMemo(() => {
    const sorted = sortBlocksByZIndex(config.blocks ?? []);
    return sorted.map((block) => {
      if (isFetchableDataBlockType(block.type) && "dataBinding" in block) {
        const preview = resolvedByBlockId[block.id];
        if (preview) return { ...block, resolved: preview };
        return block;
      }
      if (isDataViewBlockType(block.type) && block.dataSourceId) {
        const preview = resolvedByBlockId[block.dataSourceId];
        if (preview) return { ...block, resolved: preview };
      }
      if (isDataBlockType(block.type)) {
        const preview = resolvedByBlockId[block.id];
        if (preview) return { ...block, resolved: preview };
      }
      return block;
    });
  }, [config.blocks, resolvedByBlockId]);

  const selected = useMemo(
    () => (selectedId ? blocks.find((block) => block.id === selectedId) ?? null : null),
    [blocks, selectedId],
  );

  const selectedBlocks = useMemo(
    () => blocks.filter((block) => selectedIds.includes(block.id)),
    [blocks, selectedIds],
  );

  const applyConfig = useCallback(
    (next: ComunicadoConfig) => {
      setConfig(next);
      const serialized = serializeComunicadoConfig(next);
      deckHistory?.setLiveComunicadoConfig(serialized);
      onChange(serialized);
    },
    [deckHistory, onChange],
  );

  const pushPast = useCallback((snapshot: ComunicadoConfig) => {
    pastRef.current = [...pastRef.current.slice(-(HISTORY_LIMIT - 1)), snapshot];
    futureRef.current = [];
    setHistoryTick((tick) => tick + 1);
  }, []);

  const commitWithHistory = useCallback(
    (next: ComunicadoConfig) => {
      if (deckHistory) {
        deckHistory.recordBeforeChange();
      } else {
        pushPast(snapshotConfig(configRef.current));
      }
      applyConfig(next);
    },
    [applyConfig, deckHistory, pushPast],
  );

  const undo = useCallback(() => {
    if (deckHistory) {
      deckHistory.undo();
      return;
    }
    const previous = pastRef.current.pop();
    if (!previous) return;
    futureRef.current.push(snapshotConfig(configRef.current));
    applyConfig(previous);
    setHistoryTick((tick) => tick + 1);
  }, [applyConfig, deckHistory]);

  const redo = useCallback(() => {
    if (deckHistory) {
      deckHistory.redo();
      return;
    }
    const next = futureRef.current.pop();
    if (!next) return;
    pastRef.current.push(snapshotConfig(configRef.current));
    applyConfig(next);
    setHistoryTick((tick) => tick + 1);
  }, [applyConfig, deckHistory]);

  const canUndo = deckHistory ? deckHistory.canUndo : pastRef.current.length > 0;
  const canRedo = deckHistory ? deckHistory.canRedo : futureRef.current.length > 0;
  void historyTick;

  function updateBlocks(nextBlocks: ComunicadoBlock[]) {
    commitWithHistory({ ...configRef.current, blocks: nextBlocks });
  }

  function updateBlocksSilent(nextBlocks: ComunicadoBlock[]) {
    applyConfig({ ...configRef.current, blocks: nextBlocks });
  }

  const handleUpdateStyle = useCallback(
    (blockId: string, patch: NonNullable<ComunicadoBlock["style"]>) => {
      const nextBlocks = (configRef.current.blocks ?? []).map((block) =>
        block.id === blockId ? ({ ...block, style: { ...block.style, ...patch } } as ComunicadoBlock) : block,
      );
      updateBlocksSilent(nextBlocks);
    },
    [applyConfig],
  );

  const handleUpdateFrame = useCallback(
    (blockId: string, frame: ComunicadoBlock["frame"]) => {
      const multi = multiDragRef.current;
      if (multi && multi.startFrames.has(blockId)) {
        const origin = multi.startFrames.get(blockId);
        if (!origin) return;
        const dx = frame.x - origin.x;
        const dy = frame.y - origin.y;
        const isResize = frame.w !== origin.w || frame.h !== origin.h;
        const nextBlocks = (configRef.current.blocks ?? []).map((block) => {
          if (!multi.startFrames.has(block.id)) return block;
          const start = multi.startFrames.get(block.id)!;
          if (block.id === blockId && isResize) {
            return { ...block, frame };
          }
          return {
            ...block,
            frame: {
              ...start,
              x: start.x + dx,
              y: start.y + dy,
              w: start.w,
              h: start.h,
            },
          };
        });
        updateBlocksSilent(nextBlocks);
        return;
      }
      const nextBlocks = (configRef.current.blocks ?? []).map((block) =>
        block.id === blockId ? { ...block, frame } : block,
      );
      updateBlocksSilent(nextBlocks);
    },
    [applyConfig],
  );

  const handleInteractionStart = useCallback(() => {
    dragSnapshotRef.current = snapshotConfig(configRef.current);
    const baseIds = selectedIds.length > 0 ? selectedIds : selectedId ? [selectedId] : [];
    const activeIds = expandSelectionWithGroups(configRef.current.blocks ?? [], baseIds);
    if (activeIds.length > 1) {
      const startFrames = new Map<string, ComunicadoBlock["frame"]>();
      for (const id of activeIds) {
        const block = configRef.current.blocks?.find((item) => item.id === id);
        if (block) startFrames.set(id, { ...block.frame });
      }
      multiDragRef.current = { startFrames };
    } else {
      multiDragRef.current = null;
    }
  }, [selectedId, selectedIds]);

  const handleInteractionEnd = useCallback(
    (blockId: string, _frame: ComunicadoBlock["frame"], mode: "move" | "resize" | "rotate") => {
      const before = dragSnapshotRef.current;
      dragSnapshotRef.current = null;
      const multi = multiDragRef.current;
      multiDragRef.current = null;
      if (!before) return;

      if (mode === "rotate") {
        const beforeBlock = before.blocks?.find((block) => block.id === blockId);
        const afterBlock = configRef.current.blocks?.find((block) => block.id === blockId);
        const unchanged =
          (beforeBlock?.style?.rotation ?? 0) === (afterBlock?.style?.rotation ?? 0);
        if (unchanged) {
          applyConfig(configRef.current);
          return;
        }
        if (deckHistory) {
          deckHistory.recordBeforeChange(serializeComunicadoConfig(before));
        } else {
          pastRef.current = [...pastRef.current.slice(-(HISTORY_LIMIT - 1)), before];
          futureRef.current = [];
        }
        applyConfig(configRef.current);
        setHistoryTick((tick) => tick + 1);
        return;
      }

      const idsToFinalize =
        multi && multi.startFrames.size > 1
          ? [...multi.startFrames.keys()]
          : [blockId];

      let nextBlocks = [...(configRef.current.blocks ?? [])];
      for (const id of idsToFinalize) {
        const index = nextBlocks.findIndex((block) => block.id === id);
        if (index < 0) continue;
        const current = nextBlocks[index];
        const snappedFrame = snapEnabledRef.current
          ? snapComunicadoFrame(current, current.frame, mode)
          : clampFrameForBlock(current, current.frame);
        let updated: ComunicadoBlock = { ...current, frame: snappedFrame };
        if (
          updated.type === "shape" &&
          isLineShapeKind(updated.shape) &&
          mode === "resize"
        ) {
          updated = {
            ...updated,
            vertices: syncLineVerticesFromFrame(updated, snappedFrame),
          };
        }
        nextBlocks[index] = updated;
      }

      const nextConfig = { ...configRef.current, blocks: nextBlocks };
      const unchanged = idsToFinalize.every((id) => {
        const beforeBlock = before.blocks?.find((block) => block.id === id);
        const afterBlock = nextBlocks.find((block) => block.id === id);
        if (!beforeBlock || !afterBlock) return true;
        return (
          beforeBlock.frame.x === afterBlock.frame.x &&
          beforeBlock.frame.y === afterBlock.frame.y &&
          beforeBlock.frame.w === afterBlock.frame.w &&
          beforeBlock.frame.h === afterBlock.frame.h
        );
      });

      if (unchanged) {
        applyConfig(nextConfig);
        return;
      }

      if (deckHistory) {
        deckHistory.recordBeforeChange(serializeComunicadoConfig(before));
      } else {
        pastRef.current = [...pastRef.current.slice(-(HISTORY_LIMIT - 1)), before];
        futureRef.current = [];
      }
      applyConfig(nextConfig);
      setHistoryTick((tick) => tick + 1);
    },
    [applyConfig, deckHistory],
  );

  const { canvasRef, startDrag } = useCanvasBlockInteraction({
    onUpdateFrame: handleUpdateFrame,
    onUpdateStyle: handleUpdateStyle,
    onInteractionStart: handleInteractionStart,
    onInteractionEnd: handleInteractionEnd,
    resolveBlock: (blockId) => configRef.current.blocks?.find((block) => block.id === blockId),
  });

  const fitStageToView = useCallback(() => {
    const wrap = canvasWrapRef.current;
    const canvas = canvasRef.current;
    if (!wrap || !canvas) return;
    setStageZoom(computeFitStageZoom(wrap, canvas));
  }, [canvasRef]);

  function addBlock(type: ComunicadoBlock["type"]) {
    const block = createBlock(
      type,
      type === "heading" ? "Novo título" : type === "text" ? "Texto" : "",
    );
    block.style = { ...block.style, zIndex: nextZIndex(configRef.current.blocks ?? []) };
    setSelectedId(block.id);
    updateBlocks([...(configRef.current.blocks ?? []), block]);
  }

  function addDataBlock(block: ComunicadoBlock) {
    const withZ = {
      ...block,
      style: { ...block.style, zIndex: nextZIndex(configRef.current.blocks ?? []) },
    };
    if (isDataBlockType(withZ.type) && "dataBinding" in withZ) {
      const mode = withZ.dataBinding.displayMode;
      if (mode && mode !== "auto") {
        setLastDataDisplayMode(mode);
      }
    }
    setSelectedId(withZ.id);
    updateBlocks([...(configRef.current.blocks ?? []), withZ]);
  }

  function addDataSourceBlock(block: ComunicadoBlock) {
    addDataBlock(block);
    setDataPanelOpen(false);
  }

  function addChartViewBlock(chartType: ComunicadoChartType) {
    const block = createChartViewBlock(chartType);
    block.style = { ...block.style, zIndex: nextZIndex(configRef.current.blocks ?? []) };
    setSelectedId(block.id);
    updateBlocks([...(configRef.current.blocks ?? []), block]);
  }

  function addTableViewBlock(rows: number, cols: number, preset: ComunicadoTablePreset) {
    const block = createTableViewBlock(rows, cols, preset);
    block.style = { ...block.style, zIndex: nextZIndex(configRef.current.blocks ?? []) };
    setSelectedId(block.id);
    updateBlocks([...(configRef.current.blocks ?? []), block]);
  }

  function openDataPanel() {
    setDataPanelOpen(true);
    setRibbonTabRequest("insert");
  }

  function setDataFilters(filters: ComunicadoDataFilters | undefined) {
    commitWithHistory({
      ...configRef.current,
      dataFilters: filters,
      version: Math.max(configRef.current.version ?? 3, 4),
    });
  }

  function addShape(shape: ComunicadoShapeKind) {
    const block = createShapeBlock(shape);
    block.style = { ...block.style, zIndex: nextZIndex(configRef.current.blocks ?? []) };
    setSelectedId(block.id);
    setShapeMenuOpen(false);
    setRibbonTabRequest("shape");
    updateBlocks([...(configRef.current.blocks ?? []), block]);
  }

  function addIconBlock(iconName: string) {
    const block = createIconBlock(iconName);
    block.style = { ...block.style, zIndex: nextZIndex(configRef.current.blocks ?? []) };
    setSelectedId(block.id);
    updateBlocks([...(configRef.current.blocks ?? []), block]);
  }

  function groupSelected() {
    if (selectedIds.length < 2) return;
    updateBlocks(groupBlocks(configRef.current.blocks ?? [], selectedIds));
  }

  function ungroupSelected() {
    if (selectedIds.length === 0) return;
    updateBlocks(ungroupBlocks(configRef.current.blocks ?? [], selectedIds));
  }

  function updateSelected(patch: Partial<ComunicadoBlock>) {
    if (selectedIds.length === 0) return;
    const idSet = new Set(selectedIds);
    const nextBlocks = (configRef.current.blocks ?? []).map((block) =>
      idSet.has(block.id) ? ({ ...block, ...patch } as ComunicadoBlock) : block,
    );
    updateBlocks(nextBlocks);
  }

  function updateBlock(blockId: string, patch: Partial<ComunicadoBlock>) {
    const nextBlocks = (configRef.current.blocks ?? []).map((block) =>
      block.id === blockId ? ({ ...block, ...patch } as ComunicadoBlock) : block,
    );
    updateBlocks(nextBlocks);
  }

  const commitChartPartContent = useCallback(
    (content: string) => {
      const part = editingChartPart;
      const blockId = selectedIds[selectedIds.length - 1] ?? null;
      setEditingChartPart(null);
      if (!part || !blockId) return;
      const block = configRef.current.blocks?.find((item) => item.id === blockId);
      if (!block || block.type !== "chart_view") return;

      const nextParts = upsertChartPartState(block.chartParts, part, {
        content,
        visible: true,
      });
      const nextOptions = mergeComunicadoChartOptions({
        ...block.chartOptions,
        ...partsToChartOptions(nextParts),
      });
      if (part.kind === "title") {
        nextOptions.title = content;
        nextOptions.showTitle = true;
      } else if (part.kind === "legend" || part.kind === "series") {
        nextOptions.seriesName = content;
      } else if (part.kind === "axisTitle" && part.axis === "x") {
        nextOptions.xAxisTitle = content;
        nextOptions.showXAxisTitle = true;
      } else if (part.kind === "axisTitle" && part.axis === "y") {
        nextOptions.yAxisTitle = content;
        nextOptions.showYAxisTitle = true;
      }
      // Garante projeção completa options ↔ parts
      const syncedParts = chartOptionsToParts(nextOptions);
      updateBlock(blockId, {
        chartParts: { ...nextParts, ...syncedParts },
        chartOptions: nextOptions,
      } as Partial<ComunicadoBlock>);
    },
    [editingChartPart, selectedIds],
  );

  function updateBlockContent(blockId: string, content: string) {
    updateBlockTextFields(blockId, syncTextBlockFields(content, undefined));
  }

  function updateBlockTextFields(
    blockId: string,
    fields: Pick<ComunicadoTextBlock, "content" | "contentRuns">,
  ) {
    const textFields = syncTextBlockFields(fields.content, fields.contentRuns);
    const nextBlocks = (configRef.current.blocks ?? []).map((block) => {
      if (block.id !== blockId) return block;
      if (block.type === "heading" || block.type === "text") {
        return { ...block, ...textFields } as ComunicadoBlock;
      }
      if (block.type === "shape") {
        return { ...block, content: textFields.content } as ComunicadoBlock;
      }
      return block;
    });
    updateBlocks(nextBlocks);
  }

  function setEditingTextIdWithSelection(id: string | null) {
    if (editingTextIdRef.current && editingTextIdRef.current !== id) {
      flushActiveTextEdit(editingTextIdRef.current);
    }
    setEditingTextId(id);
    if (!id) {
      setTextEditSelection(null);
      setTextEditSelectionStyle(null);
      setTextEditListSelection(null);
      setTextEditNamedStyleSelection(null);
    }
  }

  const registerTextEditorBridge = useCallback((blockId: string, bridge: TextEditorBridge | null) => {
    if (bridge) textEditorBridgesRef.current.set(blockId, bridge);
    else textEditorBridgesRef.current.delete(blockId);
  }, []);

  const reportTextEditSelection = useCallback((
    selection: TextEditSelection | null,
    runs?: ComunicadoContentRun[],
  ) => {
    setTextEditSelection(selection);
    if (!selection) {
      setTextEditSelectionStyle(null);
      setTextEditListSelection(null);
      setTextEditNamedStyleSelection(null);
      return;
    }

    const resolvedBlock = configRef.current.blocks?.find((item) => item.id === selection.blockId);
    const resolvedRuns = (() => {
      if (runs) return runs;
      if (!resolvedBlock || (resolvedBlock.type !== "heading" && resolvedBlock.type !== "text")) {
        return null;
      }
      return resolveTextBlockDisplayRuns(resolvedBlock);
    })();

    if (!resolvedRuns || !resolvedBlock || (resolvedBlock.type !== "heading" && resolvedBlock.type !== "text")) {
      setTextEditSelectionStyle(null);
      setTextEditListSelection(null);
      setTextEditNamedStyleSelection(null);
      return;
    }

    if (selection.start >= selection.end) {
      setTextEditSelectionStyle(null);
      setTextEditListSelection(
        selectionListTypeState(resolvedRuns, selection.start, selection.start),
      );
      setTextEditNamedStyleSelection(
        resolveNamedStyleSelectionForBlock(resolvedBlock, selection.start, selection.start),
      );
      return;
    }

    setTextEditSelectionStyle(
      selectionRunStyleState(resolvedRuns, selection.start, selection.end),
    );
    setTextEditListSelection(
      selectionListTypeState(resolvedRuns, selection.start, selection.end),
    );
    setTextEditNamedStyleSelection(
      selectionNamedStyleState(resolvedRuns, selection.start, selection.end) ??
        defaultNamedStyleForBlockType(resolvedBlock.type),
    );
  }, []);

  const toggleEditingTextRunStyle = useCallback((toggleKey: ContentRunStyleToggleKey) => {
    if (!editingTextId) return;
    const bridge = textEditorBridgesRef.current.get(editingTextId);
    bridge?.applyPartialStyleToggle(toggleKey);
  }, [editingTextId]);

  const toggleSelectedTextListType = useCallback((listType: ComunicadoListType) => {
    const target =
      editingTextId != null
        ? configRef.current.blocks?.find((block) => block.id === editingTextId)
        : selected && (selected.type === "heading" || selected.type === "text")
          ? selected
          : null;
    if (!target || (target.type !== "heading" && target.type !== "text")) return;

    if (editingTextId === target.id) {
      const bridge = textEditorBridgesRef.current.get(editingTextId);
      bridge?.applyListToggle(listType);
      return;
    }

    const runs = resolveTextBlockDisplayRuns(target);
    const nextRuns = toggleListTypeOnAllLines(runs, listType);
    updateBlockTextFields(target.id, syncTextBlockFromRuns(nextRuns));
  }, [editingTextId, selected, updateBlockTextFields]);

  const applySelectedNamedTextStyle = useCallback((namedStyle: ComunicadoNamedTextStyle) => {
    const target =
      editingTextId != null
        ? configRef.current.blocks?.find((block) => block.id === editingTextId)
        : selected && (selected.type === "heading" || selected.type === "text")
          ? selected
          : null;
    if (!target || (target.type !== "heading" && target.type !== "text")) return;

    if (editingTextId === target.id) {
      const bridge = textEditorBridgesRef.current.get(editingTextId);
      bridge?.applyNamedStyleToggle(namedStyle);
      return;
    }

    const runs = resolveTextBlockDisplayRuns(target);
    const nextRuns = applyNamedStyleOnAllLines(runs, namedStyle);
    updateBlockTextFields(target.id, syncTextBlockFromRuns(nextRuns));
  }, [editingTextId, selected, updateBlockTextFields]);

  function updateBlockLink(blockId: string, href: string | undefined) {
    const nextBlocks = (configRef.current.blocks ?? []).map((block) => {
      if (block.id !== blockId) return block;
      if (
        block.type !== "heading" &&
        block.type !== "text" &&
        block.type !== "image" &&
        block.type !== "video" &&
        block.type !== "shape" &&
        block.type !== "icon"
      ) {
        return block;
      }
      return {
        ...block,
        href: href?.trim() || undefined,
        linkTarget: href?.trim() ? "_blank" : undefined,
      } as ComunicadoBlock;
    });
    updateBlocks(nextBlocks);
  }

  function updateSelectedStyle(patch: NonNullable<ComunicadoBlock["style"]>) {
    const targets = selectedBlocks.length > 0 ? selectedBlocks : selected ? [selected] : [];
    if (targets.length === 0) return;
    const idSet = new Set(targets.map((block) => block.id));
    const nextBlocks = (configRef.current.blocks ?? []).map((block) =>
      idSet.has(block.id)
        ? ({ ...block, style: { ...block.style, ...patch } } as ComunicadoBlock)
        : block,
    );
    updateBlocks(nextBlocks);
  }

  function duplicateSelected() {
    const sources = selectedBlocks.length > 0 ? selectedBlocks : selected ? [selected] : [];
    if (sources.length === 0) return;
    let nextZ = nextZIndex(configRef.current.blocks ?? []);
    const copies: ComunicadoBlock[] = sources.map((source) => {
      const { resolved: _omit, url: _url, ...rest } = source as ComunicadoBlock & {
        resolved?: unknown;
        url?: string;
      };
      const copy = {
        ...rest,
        id: newBlockId(),
        frame: {
          ...source.frame,
          x: Math.min(92, source.frame.x + 2),
          y: Math.min(92, source.frame.y + 2),
        },
        style: { ...source.style, zIndex: nextZ },
      } as ComunicadoBlock;
      nextZ += 1;
      return copy;
    });
    selectBlocksByIds(copies.map((copy) => copy.id));
    updateBlocks([...(configRef.current.blocks ?? []), ...copies]);
  }

  function copySelected() {
    const sources = selectedBlocks.length > 0 ? selectedBlocks : selected ? [selected] : [];
    if (sources.length === 0) return;
    clipboardRef.current = cloneBlocksForClipboard(sources);
    setClipboardRevision((tick) => tick + 1);
  }

  function cutSelected() {
    copySelected();
    removeSelected();
  }

  function pasteSelected() {
    if (clipboardRef.current.length === 0) return;
    const { blocks: nextBlocks, pastedIds } = pasteClipboardBlocks(
      configRef.current.blocks ?? [],
      clipboardRef.current,
    );
    selectBlocksByIds(pastedIds);
    updateBlocks(nextBlocks);
  }

  const canPaste = clipboardRef.current.length > 0;
  void clipboardRevision;

  function replaceSelectedDataRoute(block: ComunicadoBlock) {
    if (!selected || !isDataBlockType(selected.type) || !isDataBlockType(block.type)) return;
    if (!("dataBinding" in selected) || !("dataBinding" in block)) return;
    updateSelected({
      type: block.type,
      frame: block.frame,
      dataBinding: {
        ...selected.dataBinding,
        operationId: block.dataBinding.operationId,
        label: block.dataBinding.label,
        displayMode: block.dataBinding.displayMode,
        params: { ...(block.dataBinding.params ?? {}) },
      },
    } as Partial<typeof selected>);
    setSelectedId(selected.id);
  }

  function removeSelected() {
    const chartBlock =
      selected?.type === "chart_view" ? selected : selectedBlocks.find((b) => b.type === "chart_view");
    if (
      selectedChartPart &&
      chartBlock &&
      chartBlock.type === "chart_view" &&
      selectedIds.includes(chartBlock.id) &&
      chartPartAllowsDelete(selectedChartPart)
    ) {
      const result = deleteChartPart(chartBlock.chartParts, selectedChartPart, chartBlock.chartOptions);
      updateBlock(chartBlock.id, {
        chartParts: result.parts,
        chartOptions: result.options,
      } as Partial<ComunicadoBlock>);
      setSelectedChartPart(null);
      setEditingChartPart(null);
      setSelectedTablePart(null);
      return;
    }

    const tableBlock =
      selected?.type === "table_view" ? selected : selectedBlocks.find((b) => b.type === "table_view");
    if (
      selectedTablePart &&
      tableBlock &&
      tableBlock.type === "table_view" &&
      selectedIds.includes(tableBlock.id) &&
      tablePartAllowsDelete(selectedTablePart)
    ) {
      const result = deleteTablePart(tableBlock.tableParts, selectedTablePart, tableBlock.tableOptions);
      updateBlock(tableBlock.id, {
        tableParts: result.parts,
        tableOptions: result.options,
      } as Partial<ComunicadoBlock>);
      setSelectedTablePart(null);
      return;
    }

    if (selectedIds.length === 0) return;
    const removeSet = new Set(selectedIds);
    const nextBlocks = (configRef.current.blocks ?? []).filter((block) => !removeSet.has(block.id));
    selectBlocksByIds(nextBlocks[0]?.id ? [nextBlocks[0].id] : []);
    updateBlocks(nextBlocks);
  }

  function moveLayer(direction: "up" | "down") {
    if (!selected) return;
    const currentZ = selected.style?.zIndex ?? 1;
    updateSelectedStyle({ zIndex: Math.max(1, currentZ + (direction === "up" ? 1 : -1)) });
  }

  function applyLayerOrder(
    transform: (blocks: ComunicadoBlock[], selectedIds: string[]) => ComunicadoBlock[],
  ) {
    if (selectedIds.length === 0) return;
    const nextBlocks = transform(configRef.current.blocks ?? [], selectedIds);
    updateBlocks(nextBlocks);
  }

  function bringToFrontSelected() {
    applyLayerOrder(bringToFront);
  }

  function sendToBackSelected() {
    applyLayerOrder(sendToBack);
  }

  function bringForwardSelected() {
    applyLayerOrder(bringForward);
  }

  function sendBackwardSelected() {
    applyLayerOrder(sendBackward);
  }

  const requestRibbonTab = useCallback((tab: ComunicadoRibbonTabRequest) => {
    setRibbonTabRequest(tab);
  }, []);

  const clearRibbonTabRequest = useCallback(() => {
    setRibbonTabRequest(null);
  }, []);

  function reorderBlockLayer(blockId: string, targetIndex: number) {
    const sorted = sortBlocksByZIndex(configRef.current.blocks ?? []);
    const fromIndex = sorted.findIndex((block) => block.id === blockId);
    if (fromIndex < 0 || fromIndex === targetIndex) return;
    const reordered = [...sorted];
    const [moved] = reordered.splice(fromIndex, 1);
    reordered.splice(targetIndex, 0, moved);
    const nextBlocks = reordered.map((block, index) => ({
      ...block,
      style: { ...block.style, zIndex: index + 1 },
    }));
    updateBlocks(nextBlocks);
  }

  function nudgeSelected(dx: number, dy: number) {
    const chartBlock =
      selected?.type === "chart_view" ? selected : selectedBlocks.find((b) => b.type === "chart_view");
    if (
      selectedChartPart &&
      chartBlock &&
      chartBlock.type === "chart_view" &&
      selectedIds.includes(chartBlock.id) &&
      chartPartAllowsMove(selectedChartPart)
    ) {
      const nextParts = nudgeChartPartFrame(chartBlock.chartParts, selectedChartPart, dx, dy);
      updateBlock(chartBlock.id, { chartParts: nextParts } as Partial<ComunicadoBlock>);
      return;
    }

    const targets = selectedBlocks.length > 0 ? selectedBlocks : selected ? [selected] : [];
    if (targets.length === 0) return;
    const idSet = new Set(targets.map((block) => block.id));
    const nextBlocks = (configRef.current.blocks ?? []).map((block) => {
      if (!idSet.has(block.id)) return block;
      return {
        ...block,
        frame: {
          ...block.frame,
          x: Math.max(0, Math.min(100 - block.frame.w, block.frame.x + dx)),
          y: Math.max(0, Math.min(100 - block.frame.h, block.frame.y + dy)),
        },
      };
    });
    updateBlocks(nextBlocks);
  }

  function applySlideTemplate(nativeConfig: Record<string, unknown>) {
    const parsed = parseComunicadoConfig(nativeConfig);
    const blocksWithIds = (parsed.blocks ?? []).map((block) => ({
      ...block,
      id: newBlockId(),
    }));
    commitWithHistory({
      ...configRef.current,
      version: Math.max(parsed.version ?? 4, 4),
      background: parsed.background ?? configRef.current.background,
      dataFilters: parsed.dataFilters ?? configRef.current.dataFilters,
      blocks: blocksWithIds,
    });
    selectBlocksByIds(blocksWithIds[0]?.id ? [blocksWithIds[0].id] : []);
  }

  function applySlideTheme(theme: ComunicadoSlideTheme) {
    commitWithHistory(applyComunicadoSlideTheme(configRef.current, theme));
  }

  function alignSelected(command: LayoutAlignCommand) {
    if (selectedIds.length === 0) return;
    const nextBlocks = alignComunicadoBlocks(configRef.current.blocks ?? [], selectedIds, command);
    updateBlocks(nextBlocks);
  }

  async function handleUploadFile(file: File, target: "block" | "background") {
    setUploading(true);
    try {
      const asset: MediaAsset = await uploadPlaylistMedia(playlistId, file);
      applyMediaAsset(asset, target);
    } finally {
      setUploading(false);
    }
  }

  function applyMediaAsset(asset: MediaAsset, target?: MediaLibraryTarget) {
    const resolvedTarget = target ?? mediaLibraryTargetRef.current;
    const url = adminMediaUrl(playlistId, asset.id);

    if (resolvedTarget === "background") {
      commitWithHistory({
        ...configRef.current,
        background: { type: "image", assetId: asset.id, url },
      });
      return;
    }

    if (resolvedTarget === "insert-image") {
      const block = createBlock("image");
      const withMedia = { ...block, assetId: asset.id, url } as ComunicadoBlock;
      const nextBlocks = [...(configRef.current.blocks ?? []), withMedia];
      updateBlocks(nextBlocks);
      setSelectedId(block.id);
      return;
    }

    if (resolvedTarget === "insert-video") {
      const block = createBlock("video");
      const withMedia = { ...block, assetId: asset.id, url } as ComunicadoBlock;
      const nextBlocks = [...(configRef.current.blocks ?? []), withMedia];
      updateBlocks(nextBlocks);
      setSelectedId(block.id);
      return;
    }

    const currentSelected = configRef.current.blocks?.find((block) => block.id === selectedId) ?? selected;
    if (!currentSelected || (currentSelected.type !== "image" && currentSelected.type !== "video")) {
      return;
    }
    const nextBlocks = (configRef.current.blocks ?? []).map((block) =>
      block.id === currentSelected.id
        ? ({
            ...block,
            assetId: asset.id,
            url,
            ...(block.type === "image" ? { imageCrop: undefined } : {}),
          } as ComunicadoBlock)
        : block,
    );
    updateBlocks(nextBlocks);
  }

  function openMediaLibrary(target: MediaLibraryTarget) {
    mediaLibraryTargetRef.current = target;
    setMediaLibraryTarget(target);
    setMediaLibraryOpen(true);
  }

  function closeMediaLibrary() {
    setMediaLibraryOpen(false);
  }

  function triggerUpload(target: "block" | "background") {
    uploadTargetRef.current = target;
    fileInputRef.current?.click();
  }

  function setBackgroundColor(color: string) {
    commitWithHistory({ ...configRef.current, background: { type: "color", value: color } });
  }

  function setBackgroundGradient(from: string, to: string, angle = 180) {
    commitWithHistory({
      ...configRef.current,
      background: { type: "gradient", from, to, angle },
    });
  }

  const resolvedMaster = useMemo(
    () => resolveMasterForPreview(masterConfig, playlistId),
    [masterConfig, playlistId],
  );

  const background = config.background
    ?? (resolvedMaster?.background as ComunicadoConfig["background"] | undefined)
    ?? { type: "color", value: "#ffffff" };
  const masterLogo =
    resolvedMaster && typeof resolvedMaster.logo === "object" && resolvedMaster.logo
      ? (resolvedMaster.logo as {
          url?: string;
          frame?: { x?: number; y?: number; w?: number; h?: number };
          opacity?: number;
        })
      : null;

  const ctxValue: ComunicadoEditorContextValue = {
    config,
    blocks,
    selectedIds,
    selectedId,
    selected,
    selectedBlocks,
    isBlockSelected,
    selectBlock,
    selectBlocksByIds,
    clearSelection,
    setSelectedId,
    selectedChartPart,
    selectChartPart,
    clearChartPartSelection,
    editingChartPart,
    beginEditChartPart,
    commitChartPartContent,
    cancelEditChartPart,
    selectedTablePart,
    selectTablePart,
    clearTablePartSelection,
    editingTextId,
    setEditingTextId: setEditingTextIdWithSelection,
    textEditSelection,
    textEditSelectionStyle,
    textEditListSelection,
    textEditNamedStyleSelection,
    registerTextEditorBridge,
    reportTextEditSelection,
    toggleEditingTextRunStyle,
    toggleSelectedTextListType,
    applySelectedNamedTextStyle,
    uploading,
    shapeMenuOpen,
    setShapeMenuOpen,
    background,
    canvasRef,
    startDrag,
    addBlock,
    addDataBlock,
    addDataSourceBlock,
    addChartViewBlock,
    addTableViewBlock,
    openDataPanel,
    dataPanelOpen,
    setDataPanelOpen,
    addShape,
    addIconBlock,
    groupSelected,
    ungroupSelected,
    setDataFilters,
    updateSelected,
    updateBlock,
    updateBlockContent,
    updateBlockTextFields,
    updateBlockLink,
    updateSelectedStyle,
    removeSelected,
    duplicateSelected,
    cutSelected,
    copySelected,
    pasteSelected,
    canPaste,
    bringToFront: bringToFrontSelected,
    sendToBack: sendToBackSelected,
    bringForward: bringForwardSelected,
    sendBackward: sendBackwardSelected,
    requestRibbonTab,
    ribbonTabRequest,
    clearRibbonTabRequest,
    replaceSelectedDataRoute,
    moveLayer,
    reorderBlockLayer,
    nudgeSelected,
    undo,
    redo,
    canUndo,
    canRedo,
    playlistId,
    masterLogo,
    mediaLibraryOpen,
    mediaLibraryTarget,
    openMediaLibrary,
    closeMediaLibrary,
    applyMediaAsset,
    triggerUpload,
    setBackgroundColor,
    setBackgroundGradient,
    applySlideTemplate,
    applySlideTheme,
    alignSelected,
    stageZoom,
    setStageZoom,
    fitStageToView,
    canvasWrapRef,
    showStageRulers,
    setShowStageRulers,
    showStageGrid,
    setShowStageGrid,
    showStageGuides,
    setShowStageGuides,
    snapEnabled,
    setSnapEnabled,
    fileInputRef,
    handleUploadFile,
    dataPreviewLoading,
    dataPreviewError,
    globalRefreshSec,
    lastDataDisplayMode,
    setLastDataDisplayMode,
  };

  return (
    <ComunicadoEditorContext.Provider value={ctxValue}>
      <ComunicadoEditorKeyboardBridge />
      <input
        ref={fileInputRef}
        type="file"
        accept="image/jpeg,image/png,image/webp,image/gif,video/mp4,video/webm"
        hidden
        onChange={(event) => {
          const file = event.target.files?.[0];
          event.target.value = "";
          if (file) void handleUploadFile(file, uploadTargetRef.current);
        }}
      />
      <MediaLibraryModal
        open={mediaLibraryOpen}
        target={mediaLibraryTarget}
        playlistId={playlistId}
        uploading={uploading}
        onClose={closeMediaLibrary}
        onPick={applyMediaAsset}
        onUploaded={() => {
          /* lista recarrega ao reabrir */
        }}
      />
      {children}
    </ComunicadoEditorContext.Provider>
  );
}

export function parseCustomSlideConfig(raw: Record<string, unknown>): Record<string, unknown> {
  return serializeComunicadoConfig(parseComunicadoConfig(raw));
}
