import { useCallback, useRef, useState, type MutableRefObject, type RefObject } from "react";

import {
  createBlock,
  ensureComunicadoCustomFontsLoaded,
  applyBackgroundImagePreservingUnderlay,
  type ComunicadoBlock,
  type ComunicadoConfig,
} from "@delpi/tv-dashboard-presentation";

import { uploadPlaylistMedia, type MediaAsset } from "../../api/tvDashboardApi";
import { validateMediaUploadFile } from "../../api/mediaUploadLimits";
import type { MediaLibraryTarget } from "../../components/comunicadoEditorTypes";
import { resolveEditorMediaUrl } from "../../components/slideCardPreview";
import {
  dataTransferHasImageFiles,
  firstDataTransferImageFile,
} from "../../utils/externalClipboardPaste";
import { collectCanvasMediaFiles, planCanvasMediaDrop } from "../../utils/canvasFileDrop";
import { placeBlockAtClientPoint, placeBlockInViewportCenter } from "../../utils/placeBlockInViewport";
import { readSystemClipboardDataTransfer } from "../../utils/readSystemClipboardDataTransfer";

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
  const [uploadProgress, setUploadProgress] = useState<number | null>(null);
  const [uploadStatusMessage, setUploadStatusMessage] = useState<string | null>(null);
  const [mediaLibraryOpen, setMediaLibraryOpen] = useState(false);
  const [mediaLibraryTarget, setMediaLibraryTarget] = useState<MediaLibraryTarget>("block");
  const fileInputRef = useRef<HTMLInputElement>(null);
  const uploadTargetRef = useRef<"block" | "background">("block");
  const mediaLibraryTargetRef = useRef<MediaLibraryTarget>("block");

  const applyMediaAsset = useCallback(
    (
      asset: MediaAsset,
      target?: MediaLibraryTarget,
      options?: { clientX?: number; clientY?: number; cascadeIndex?: number },
    ) => {
      const resolvedTarget = target ?? mediaLibraryTargetRef.current;
      const url = resolveEditorMediaUrl(playlistId, asset.id) ?? "";

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
          background: applyBackgroundImagePreservingUnderlay(configRef.current.background, {
            assetId: asset.id,
            url,
          }),
        });
        return;
      }

      if (resolvedTarget === "playlist") {
        return;
      }

      if (resolvedTarget === "insert-image" || resolvedTarget === "insert-video") {
        const blockType = resolvedTarget === "insert-video" ? "video" : "image";
        let block = {
          ...createBlock(blockType),
          assetId: asset.id,
          url,
        } as ComunicadoBlock;
        const cascade = options?.cascadeIndex ?? 0;
        if (
          typeof options?.clientX === "number" &&
          typeof options?.clientY === "number" &&
          canvasRef?.current
        ) {
          block = placeBlockAtClientPoint(
            block,
            canvasRef.current,
            options.clientX,
            options.clientY,
          );
          if (cascade > 0) {
            block = {
              ...block,
              frame: {
                ...block.frame,
                x: Math.min(100 - block.frame.w, block.frame.x + cascade * 2),
                y: Math.min(100 - block.frame.h, block.frame.y + cascade * 2),
              },
            };
          }
        } else {
          block = placeBlockInViewportCenter(block, canvasRef?.current, canvasWrapRef?.current);
        }
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
      const validationError = validateMediaUploadFile(
        file,
        target === "background" ? ["image"] : ["image", "video"],
      );
      if (validationError) {
        setUploadStatusMessage(validationError);
        return;
      }
      setUploading(true);
      setUploadProgress(0);
      setUploadStatusMessage(null);
      try {
        const asset: MediaAsset = await uploadPlaylistMedia(playlistId, file, {
          onProgress: (ratio) => setUploadProgress(ratio),
        });
        /* "block" cai no ramo de substituir mídia selecionada (não é MediaLibraryTarget). */
        applyMediaAsset(asset, target === "background" ? "background" : ("block" as MediaLibraryTarget));
      } catch (err) {
        setUploadStatusMessage(err instanceof Error ? err.message : "Falha ao enviar arquivo.");
      } finally {
        setUploading(false);
        setUploadProgress(null);
      }
    },
    [applyMediaAsset, playlistId],
  );

  const insertDroppedMediaFiles = useCallback(
    async (data: DataTransfer, clientX: number, clientY: number) => {
      const files = collectCanvasMediaFiles(data);
      const { accepted, errors } = planCanvasMediaDrop(files);
      if (errors.length) {
        setUploadStatusMessage(errors[0] ?? null);
      }
      if (!accepted.length) return;
      setUploading(true);
      setUploadStatusMessage(null);
      try {
        for (let index = 0; index < accepted.length; index += 1) {
          const file = accepted[index]!;
          setUploadProgress(0);
          const asset = await uploadPlaylistMedia(playlistId, file, {
            onProgress: (ratio) => setUploadProgress(ratio),
          });
          const target: MediaLibraryTarget =
            asset.mediaKind === "video" ? "insert-video" : "insert-image";
          applyMediaAsset(asset, target, { clientX, clientY, cascadeIndex: index });
        }
      } catch (err) {
        setUploadStatusMessage(err instanceof Error ? err.message : "Falha ao enviar arquivo.");
      } finally {
        setUploading(false);
        setUploadProgress(null);
      }
    },
    [applyMediaAsset, playlistId],
  );

  const uploadCustomFont = useCallback(
    async (file: File) => {
      const validationError = validateMediaUploadFile(file, ["font"]);
      if (validationError) {
        setUploadStatusMessage(validationError);
        return;
      }
      setUploading(true);
      setUploadProgress(0);
      try {
        const asset = await uploadPlaylistMedia(playlistId, file, {
          onProgress: (ratio) => setUploadProgress(ratio),
        });
        applyMediaAsset(asset, "custom-font");
      } catch (err) {
        setUploadStatusMessage(err instanceof Error ? err.message : "Falha ao enviar fonte.");
      } finally {
        setUploading(false);
        setUploadProgress(null);
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

  /** Probe para enablement do menu «Da área de transferência». */
  const probeClipboardHasImage = useCallback(async (): Promise<boolean> => {
    const dt = await readSystemClipboardDataTransfer();
    return dataTransferHasImageFiles(dt);
  }, []);

  /**
   * Substitui a mídia do bloco selecionado pela imagem do clipboard,
   * mantendo frame/estilo (paridade Change Picture do Office).
   */
  const replaceSelectedMediaFromClipboard = useCallback(async (): Promise<boolean> => {
    const dt = await readSystemClipboardDataTransfer();
    const file = firstDataTransferImageFile(dt);
    if (!file) return false;
    await handleUploadFile(file, "block");
    return true;
  }, [handleUploadFile]);

  return {
    uploading,
    uploadProgress,
    uploadStatusMessage,
    clearUploadStatusMessage: () => setUploadStatusMessage(null),
    mediaLibraryOpen,
    mediaLibraryTarget,
    fileInputRef: fileInputRef as RefObject<HTMLInputElement | null>,
    uploadTargetRef,
    openMediaLibrary,
    closeMediaLibrary,
    applyMediaAsset,
    triggerUpload,
    handleUploadFile,
    insertDroppedMediaFiles,
    uploadCustomFont,
    probeClipboardHasImage,
    replaceSelectedMediaFromClipboard,
  };
}
