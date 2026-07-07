import {
  createContext,
  useCallback,
  useContext,
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
  isDataBlockType,
  newBlockId,
  nextZIndex,
  parseComunicadoConfig,
  serializeComunicadoConfig,
  sortBlocksByZIndex,
  type ComunicadoBlock,
  type ComunicadoConfig,
  type ComunicadoDataFilters,
  type ComunicadoShapeKind,
} from "@delpi/tv-dashboard-presentation";

import { adminMediaUrl, uploadPlaylistMedia, type MediaAsset } from "../api/tvDashboardApi";
import { useComunicadoDataPreview } from "../hooks/useComunicadoDataPreview";
import { useComunicadoEditorKeyboard } from "../hooks/useComunicadoEditorKeyboard";
import { enrichComunicadoConfigForEditor } from "./slideCardPreview";
import { useCanvasBlockInteraction } from "./useCanvasBlockInteraction";
import { snapComunicadoFrame } from "../utils/comunicadoSnap";
import { alignComunicadoBlocks, type LayoutAlignCommand } from "../utils/comunicadoLayoutAlign";
import {
  expandSelectionWithGroups,
  groupBlocks,
  selectedHasGroup,
  ungroupBlocks,
} from "../utils/comunicadoGrouping";
import { applyComunicadoSlideTheme, type ComunicadoSlideTheme } from "../content/comunicadoSlideThemes";

const HISTORY_LIMIT = 50;

function snapshotConfig(config: ComunicadoConfig): ComunicadoConfig {
  return parseComunicadoConfig(serializeComunicadoConfig(config));
}

type ComunicadoEditorContextValue = {
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
  uploading: boolean;
  shapeMenuOpen: boolean;
  setShapeMenuOpen: (open: boolean) => void;
  background: ComunicadoConfig["background"];
  canvasRef: ReturnType<typeof useCanvasBlockInteraction>["canvasRef"];
  startDrag: ReturnType<typeof useCanvasBlockInteraction>["startDrag"];
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
  triggerUpload: (target: "block" | "background") => void;
  setBackgroundColor: (value: string) => void;
  setBackgroundGradient: (from: string, to: string, angle?: number) => void;
  applySlideTemplate: (nativeConfig: Record<string, unknown>) => void;
  applySlideTheme: (theme: ComunicadoSlideTheme) => void;
  alignSelected: (command: LayoutAlignCommand) => void;
  stageZoom: number;
  setStageZoom: (zoom: number) => void;
  fileInputRef: React.RefObject<HTMLInputElement | null>;
  handleUploadFile: (file: File, target: "block" | "background") => void;
  dataPreviewLoading: boolean;
  dataPreviewError: string | null;
};

const ComunicadoEditorContext = createContext<ComunicadoEditorContextValue | null>(null);

export function useComunicadoEditor() {
  const ctx = useContext(ComunicadoEditorContext);
  if (!ctx) {
    throw new Error("useComunicadoEditor deve ser usado dentro de ComunicadoEditorProvider");
  }
  return ctx;
}

type ProviderProps = {
  playlistId: string;
  slideId?: string;
  value: Record<string, unknown>;
  onChange: (config: Record<string, unknown>) => void;
  children: ReactNode;
};

function ComunicadoEditorKeyboardBridge() {
  useComunicadoEditorKeyboard();
  return null;
}

export function ComunicadoEditorProvider({ playlistId, value, onChange, children }: ProviderProps) {
  const [config, setConfig] = useState<ComunicadoConfig>(() =>
    enrichComunicadoConfigForEditor(value, playlistId),
  );
  const [selectedIds, setSelectedIds] = useState<string[]>(() => {
    const first = config.blocks?.[0]?.id;
    return first ? [first] : [];
  });
  const [editingTextId, setEditingTextId] = useState<string | null>(null);
  const [uploading, setUploading] = useState(false);
  const [historyTick, setHistoryTick] = useState(0);

  const pastRef = useRef<ComunicadoConfig[]>([]);
  const futureRef = useRef<ComunicadoConfig[]>([]);
  const dragSnapshotRef = useRef<ComunicadoConfig | null>(null);
  const multiDragRef = useRef<{ startFrames: Map<string, ComunicadoBlock["frame"]> } | null>(null);
  const configRef = useRef(config);
  configRef.current = config;

  const selectedId = selectedIds[selectedIds.length - 1] ?? null;

  const setSelectedId = useCallback((id: string | null) => {
    setSelectedIds(id ? [id] : []);
    setEditingTextId((current) => (id === current ? current : null));
  }, []);

  const selectBlocksByIds = useCallback((blockIds: string[]) => {
    const unique = [...new Set(blockIds.filter(Boolean))];
    setSelectedIds(unique);
    setEditingTextId(null);
  }, []);

  const selectBlock = useCallback(
    (blockId: string, options?: { additive?: boolean }) => {
      if (options?.additive) {
        setSelectedIds((current) => {
          const set = new Set(current);
          if (set.has(blockId)) set.delete(blockId);
          else set.add(blockId);
          return [...set];
        });
      } else {
        const block = configRef.current.blocks?.find((item) => item.id === blockId);
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
    },
    [],
  );

  const clearSelection = useCallback(() => {
    setSelectedIds([]);
    setEditingTextId(null);
  }, []);

  const isBlockSelected = useCallback(
    (blockId: string) => selectedIds.includes(blockId),
    [selectedIds],
  );
  const [shapeMenuOpen, setShapeMenuOpen] = useState(false);
  const [stageZoom, setStageZoom] = useState(1);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const uploadTargetRef = useRef<"block" | "background">("block");

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
    });

  const blocks = useMemo(() => {
    const sorted = sortBlocksByZIndex(config.blocks ?? []);
    return sorted.map((block) => {
      if (!isDataBlockType(block.type)) return block;
      const preview = resolvedByBlockId[block.id];
      if (!preview) return block;
      return { ...block, resolved: preview };
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
      onChange(serializeComunicadoConfig(next));
    },
    [onChange],
  );

  const pushPast = useCallback((snapshot: ComunicadoConfig) => {
    pastRef.current = [...pastRef.current.slice(-(HISTORY_LIMIT - 1)), snapshot];
    futureRef.current = [];
    setHistoryTick((tick) => tick + 1);
  }, []);

  const commitWithHistory = useCallback(
    (next: ComunicadoConfig) => {
      pushPast(snapshotConfig(configRef.current));
      applyConfig(next);
    },
    [applyConfig, pushPast],
  );

  const undo = useCallback(() => {
    const previous = pastRef.current.pop();
    if (!previous) return;
    futureRef.current.push(snapshotConfig(configRef.current));
    applyConfig(previous);
    setHistoryTick((tick) => tick + 1);
  }, [applyConfig]);

  const redo = useCallback(() => {
    const next = futureRef.current.pop();
    if (!next) return;
    pastRef.current.push(snapshotConfig(configRef.current));
    applyConfig(next);
    setHistoryTick((tick) => tick + 1);
  }, [applyConfig]);

  const canUndo = pastRef.current.length > 0;
  const canRedo = futureRef.current.length > 0;
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
        pastRef.current = [...pastRef.current.slice(-(HISTORY_LIMIT - 1)), before];
        futureRef.current = [];
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
        const snappedFrame = snapComunicadoFrame(nextBlocks[index].frame, mode);
        nextBlocks[index] = { ...nextBlocks[index], frame: snappedFrame };
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

      pastRef.current = [...pastRef.current.slice(-(HISTORY_LIMIT - 1)), before];
      futureRef.current = [];
      applyConfig(nextConfig);
      setHistoryTick((tick) => tick + 1);
    },
    [applyConfig],
  );

  const { canvasRef, startDrag } = useCanvasBlockInteraction({
    onUpdateFrame: handleUpdateFrame,
    onUpdateStyle: handleUpdateStyle,
    onInteractionStart: handleInteractionStart,
    onInteractionEnd: handleInteractionEnd,
  });

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
    setSelectedId(withZ.id);
    updateBlocks([...(configRef.current.blocks ?? []), withZ]);
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

  function updateBlockContent(blockId: string, content: string) {
    const nextBlocks = (configRef.current.blocks ?? []).map((block) => {
      if (block.id !== blockId) return block;
      if (block.type === "heading" || block.type === "text" || block.type === "shape") {
        return { ...block, content } as ComunicadoBlock;
      }
      return block;
    });
    updateBlocks(nextBlocks);
  }

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
      const url = adminMediaUrl(playlistId, asset.id);
      if (target === "background") {
        commitWithHistory({
          ...configRef.current,
          background: { type: "image", assetId: asset.id, url },
        });
        return;
      }
      if (!selected || (selected.type !== "image" && selected.type !== "video")) return;
      const nextBlocks = (configRef.current.blocks ?? []).map((block) =>
        block.id === selected.id
          ? ({ ...block, assetId: asset.id, url } as ComunicadoBlock)
          : block,
      );
      updateBlocks(nextBlocks);
    } finally {
      setUploading(false);
    }
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

  const background = config.background ?? { type: "color", value: "#0f172a" };

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
    editingTextId,
    setEditingTextId,
    uploading,
    shapeMenuOpen,
    setShapeMenuOpen,
    background,
    canvasRef,
    startDrag,
    addBlock,
    addDataBlock,
    addShape,
    addIconBlock,
    groupSelected,
    ungroupSelected,
    setDataFilters,
    updateSelected,
    updateBlock,
    updateBlockContent,
    updateBlockLink,
    updateSelectedStyle,
    removeSelected,
    duplicateSelected,
    replaceSelectedDataRoute,
    moveLayer,
    reorderBlockLayer,
    nudgeSelected,
    undo,
    redo,
    canUndo,
    canRedo,
    triggerUpload,
    setBackgroundColor,
    setBackgroundGradient,
    applySlideTemplate,
    applySlideTheme,
    alignSelected,
    stageZoom,
    setStageZoom,
    fileInputRef,
    handleUploadFile,
    dataPreviewLoading,
    dataPreviewError,
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
      {children}
    </ComunicadoEditorContext.Provider>
  );
}

export function parseCustomSlideConfig(raw: Record<string, unknown>): Record<string, unknown> {
  return serializeComunicadoConfig(parseComunicadoConfig(raw));
}
