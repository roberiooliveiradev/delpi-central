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
  createShapeBlock,
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
import { enrichComunicadoConfigForEditor } from "./slideCardPreview";
import { useCanvasBlockInteraction } from "./useCanvasBlockInteraction";

type ComunicadoEditorContextValue = {
  config: ComunicadoConfig;
  blocks: ComunicadoBlock[];
  selected: ComunicadoBlock | null;
  selectedId: string | null;
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
  setDataFilters: (filters: ComunicadoDataFilters | undefined) => void;
  updateSelected: (patch: Partial<ComunicadoBlock>) => void;
  updateBlockContent: (blockId: string, content: string) => void;
  updateSelectedStyle: (patch: NonNullable<ComunicadoBlock["style"]>) => void;
  removeSelected: () => void;
  moveLayer: (direction: "up" | "down") => void;
  triggerUpload: (target: "block" | "background") => void;
  setBackgroundColor: (value: string) => void;
  fileInputRef: React.RefObject<HTMLInputElement | null>;
  handleUploadFile: (file: File, target: "block" | "background") => void;
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
  value: Record<string, unknown>;
  onChange: (config: Record<string, unknown>) => void;
  children: ReactNode;
};

export function ComunicadoEditorProvider({ playlistId, value, onChange, children }: ProviderProps) {
  const [config, setConfig] = useState<ComunicadoConfig>(() =>
    enrichComunicadoConfigForEditor(value, playlistId),
  );
  const [selectedId, setSelectedIdState] = useState<string | null>(config.blocks?.[0]?.id ?? null);
  const [editingTextId, setEditingTextId] = useState<string | null>(null);
  const [uploading, setUploading] = useState(false);

  const setSelectedId = useCallback((id: string | null) => {
    setSelectedIdState(id);
    setEditingTextId((current) => (id === current ? current : null));
  }, []);
  const [shapeMenuOpen, setShapeMenuOpen] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const uploadTargetRef = useRef<"block" | "background">("block");

  useEffect(() => {
    setConfig(enrichComunicadoConfigForEditor(value, playlistId));
  }, [value, playlistId]);

  const blocks = useMemo(() => sortBlocksByZIndex(config.blocks ?? []), [config.blocks]);

  const selected = useMemo(
    () => config.blocks?.find((block) => block.id === selectedId) ?? null,
    [config.blocks, selectedId],
  );

  function commit(next: ComunicadoConfig) {
    setConfig(next);
    onChange(serializeComunicadoConfig(next));
  }

  function updateBlocks(nextBlocks: ComunicadoBlock[]) {
    commit({ ...config, blocks: nextBlocks });
  }

  const handleUpdateFrame = (blockId: string, frame: ComunicadoBlock["frame"]) => {
    const nextBlocks = (config.blocks ?? []).map((block) =>
      block.id === blockId ? { ...block, frame } : block,
    );
    updateBlocks(nextBlocks);
  };

  const { canvasRef, startDrag } = useCanvasBlockInteraction({ onUpdateFrame: handleUpdateFrame });

  function addBlock(type: ComunicadoBlock["type"]) {
    const block = createBlock(
      type,
      type === "heading" ? "Novo título" : type === "text" ? "Texto" : "",
    );
    block.style = { ...block.style, zIndex: nextZIndex(config.blocks ?? []) };
    setSelectedId(block.id);
    updateBlocks([...(config.blocks ?? []), block]);
  }

  function addDataBlock(block: ComunicadoBlock) {
    const withZ = {
      ...block,
      style: { ...block.style, zIndex: nextZIndex(config.blocks ?? []) },
    };
    setSelectedId(withZ.id);
    updateBlocks([...(config.blocks ?? []), withZ]);
  }

  function setDataFilters(filters: ComunicadoDataFilters | undefined) {
    commit({ ...config, dataFilters: filters, version: Math.max(config.version ?? 3, 4) });
  }

  function addShape(shape: ComunicadoShapeKind) {
    const block = createShapeBlock(shape);
    block.style = { ...block.style, zIndex: nextZIndex(config.blocks ?? []) };
    setSelectedId(block.id);
    setShapeMenuOpen(false);
    updateBlocks([...(config.blocks ?? []), block]);
  }

  function updateSelected(patch: Partial<ComunicadoBlock>) {
    if (!selected) return;
    const nextBlocks = (config.blocks ?? []).map((block) =>
      block.id === selected.id ? ({ ...block, ...patch } as ComunicadoBlock) : block,
    );
    updateBlocks(nextBlocks);
  }

  function updateBlockContent(blockId: string, content: string) {
    const nextBlocks = (config.blocks ?? []).map((block) => {
      if (block.id !== blockId) return block;
      if (block.type === "heading" || block.type === "text" || block.type === "shape") {
        return { ...block, content } as ComunicadoBlock;
      }
      return block;
    });
    updateBlocks(nextBlocks);
  }

  function updateSelectedStyle(patch: NonNullable<ComunicadoBlock["style"]>) {
    if (!selected) return;
    updateSelected({ style: { ...selected.style, ...patch } } as Partial<ComunicadoBlock>);
  }

  function removeSelected() {
    if (!selected) return;
    const nextBlocks = (config.blocks ?? []).filter((block) => block.id !== selected.id);
    setSelectedId(nextBlocks[0]?.id ?? null);
    updateBlocks(nextBlocks);
  }

  function moveLayer(direction: "up" | "down") {
    if (!selected) return;
    const currentZ = selected.style?.zIndex ?? 1;
    updateSelectedStyle({ zIndex: Math.max(1, currentZ + (direction === "up" ? 1 : -1)) });
  }

  async function handleUploadFile(file: File, target: "block" | "background") {
    setUploading(true);
    try {
      const asset: MediaAsset = await uploadPlaylistMedia(playlistId, file);
      const url = adminMediaUrl(playlistId, asset.id);
      if (target === "background") {
        commit({ ...config, background: { type: "image", assetId: asset.id, url } });
        return;
      }
      if (!selected || (selected.type !== "image" && selected.type !== "video")) return;
      const nextBlocks = (config.blocks ?? []).map((block) =>
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
    commit({ ...config, background: { type: "color", value: color } });
  }

  const background = config.background ?? { type: "color", value: "#0f172a" };

  const ctxValue: ComunicadoEditorContextValue = {
    config,
    blocks,
    selected,
    selectedId,
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
    setDataFilters,
    updateSelected,
    updateBlockContent,
    updateSelectedStyle,
    removeSelected,
    moveLayer,
    triggerUpload,
    setBackgroundColor,
    fileInputRef,
    handleUploadFile,
  };

  return (
    <ComunicadoEditorContext.Provider value={ctxValue}>
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
