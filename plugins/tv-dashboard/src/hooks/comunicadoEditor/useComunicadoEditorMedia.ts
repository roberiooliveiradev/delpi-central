import { useCallback, useRef, useState, type MutableRefObject, type RefObject } from "react";

import {
  createBlock,
  ensureComunicadoCustomFontsLoaded,
  type ComunicadoBlock,
  type ComunicadoConfig,
} from "@delpi/tv-dashboard-presentation";

import { adminMediaUrl, uploadPlaylistMedia, type MediaAsset } from "../../api/tvDashboardApi";
import type { MediaLibraryTarget } from "../../components/comunicadoEditorTypes";
import { placeBlockInViewportCenter } from "../../utils/placeBlockInViewport";

type Options = {
  playlistId: string;
  configRef: MutableRefObject<ComunicadoConfig>;
  selectedId: string | null;
  selected: ComunicadoBlock | null;
  commitWithHistory: (next: ComunicadoConfig) => void;
  updateBlocks: (nextBlocks: ComunicadoBlock[]) => void;
  setSelectedId: (id: string | null) => void;
  canvasRef?: RefObject<HTMLElement | null>;
  canvasWrapRef?: RefObject<HTMLElement | null>;
};

function fontFamilyFromFilename(filename: string | null | undefined): string {
  const name = (filename ?? "Fonte personalizada").replace(/\.(woff2?|ttf|otf)$/i, "").trim();
  return name || "Fonte personalizada";
}

/**
 * Upload de mídia + biblioteca (estado + handlers para o Provider renderizar input/modal).
 */
export function useComunicadoEditorMedia({
  playlistId,
  configRef,
  selectedId,
  selected,
  commitWithHistory,
  updateBlocks,
  setSelectedId,
  canvasRef,
  canvasWrapRef,
}: Options) {
  const [uploading, setUploading] = useState(false);
  const [mediaLibraryOpen, setMediaLibraryOpen] = useState(false);
  const [mediaLibraryTarget, setMediaLibraryTarget] = useState<MediaLibraryTarget>("block");
  const fileInputRef = useRef<HTMLInputElement>(null);
  const uploadTargetRef = useRef<"block" | "background">("block");
  const mediaLibraryTargetRef = useRef<MediaLibraryTarget>("block");

  const applyMediaAsset = useCallback(
    (asset: MediaAsset, target?: MediaLibraryTarget) => {
      const resolvedTarget = target ?? mediaLibraryTargetRef.current;
      const url = adminMediaUrl(playlistId, asset.id);

      if (resolvedTarget === "custom-font" || asset.mediaKind === "font") {
        const familyName = fontFamilyFromFilename(asset.originalName ?? asset.storedName);
        const customFont = { assetId: asset.id, familyName, url };
        const current = configRef.current.customFonts ?? [];
        const nextFonts = [...current.filter((font) => font.assetId !== asset.id), customFont];
        ensureComunicadoCustomFontsLoaded(
          nextFonts.flatMap((font) =>
            font.url ? [{ familyName: font.familyName, url: font.url }] : [],
          ),
        );
        commitWithHistory({ ...configRef.current, customFonts: nextFonts });
        return;
      }

      if (resolvedTarget === "background") {
        commitWithHistory({
          ...configRef.current,
          background: { type: "image", assetId: asset.id, url },
        });
        return;
      }

      if (resolvedTarget === "insert-image") {
        const block = placeBlockInViewportCenter(
          { ...createBlock("image"), assetId: asset.id, url } as ComunicadoBlock,
          canvasRef?.current,
          canvasWrapRef?.current,
        );
        const nextBlocks = [...(configRef.current.blocks ?? []), block];
        updateBlocks(nextBlocks);
        setSelectedId(block.id);
        return;
      }

      if (resolvedTarget === "insert-video") {
        const block = placeBlockInViewportCenter(
          { ...createBlock("video"), assetId: asset.id, url } as ComunicadoBlock,
          canvasRef?.current,
          canvasWrapRef?.current,
        );
        const nextBlocks = [...(configRef.current.blocks ?? []), block];
        updateBlocks(nextBlocks);
        setSelectedId(block.id);
        return;
      }

      const currentSelected =
        configRef.current.blocks?.find((block) => block.id === selectedId) ?? selected;
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
    },
    [canvasRef, canvasWrapRef, commitWithHistory, configRef, playlistId, selected, selectedId, setSelectedId, updateBlocks],
  );

  const handleUploadFile = useCallback(
    async (file: File, target: "block" | "background") => {
      setUploading(true);
      try {
        const asset: MediaAsset = await uploadPlaylistMedia(playlistId, file);
        applyMediaAsset(asset, target);
      } finally {
        setUploading(false);
      }
    },
    [applyMediaAsset, playlistId],
  );

  const uploadCustomFont = useCallback(
    async (file: File) => {
      setUploading(true);
      try {
        const asset = await uploadPlaylistMedia(playlistId, file);
        applyMediaAsset(asset, "custom-font");
      } finally {
        setUploading(false);
      }
    },
    [applyMediaAsset, playlistId],
  );

  const openMediaLibrary = useCallback((target: MediaLibraryTarget) => {
    mediaLibraryTargetRef.current = target;
    setMediaLibraryTarget(target);
    setMediaLibraryOpen(true);
  }, []);

  const closeMediaLibrary = useCallback(() => {
    setMediaLibraryOpen(false);
  }, []);

  const triggerUpload = useCallback((target: "block" | "background") => {
    uploadTargetRef.current = target;
    fileInputRef.current?.click();
  }, []);

  return {
    uploading,
    mediaLibraryOpen,
    mediaLibraryTarget,
    fileInputRef: fileInputRef as RefObject<HTMLInputElement | null>,
    uploadTargetRef,
    openMediaLibrary,
    closeMediaLibrary,
    applyMediaAsset,
    triggerUpload,
    handleUploadFile,
    uploadCustomFont,
  };
}
