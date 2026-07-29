import { useCallback, useEffect, useRef, useState, type RefObject } from "react";

import {
  createBlock,
  resolveBlockPasteDataPolicy,
  type ComunicadoBlock,
  type DataSourceDuplicatePolicy,
} from "@delpi/tv-dashboard-presentation";

import { uploadPlaylistMedia } from "../../api/tvDashboardApi";
import { resolveEditorMediaUrl } from "../../components/slideCardPreview";
import { isEditableKeyboardTarget } from "../../keyboard";
import {
  cloneBlocksForClipboard,
  pasteClipboardBlocks,
  resolvePasteFrameOffset,
} from "../../utils/comunicadoEditorClipboard";
import {
  assignPasteStack,
  hasExternalClipboardPayload,
  planExternalClipboardPaste,
  serializeInternalBlocksPayload,
  type ExternalPastePlan,
} from "../../utils/externalClipboardPaste";
import { frameForImageNaturalSize, readImageNaturalSize } from "../../utils/imagePasteFrame";
import {
  placeFrameCenteredAt,
  resolveViewportCenterCanvasPercent,
} from "../../utils/placeBlockInViewport";
import { readSystemClipboardDataTransfer } from "../../utils/readSystemClipboardDataTransfer";

type Options = {
  playlistId: string;
  /** Slide atual — usado para deslocar só no mesmo slide ao colar. */
  getSlideId?: () => string | null | undefined;
  getSources: () => ComunicadoBlock[];
  getExistingBlocks: () => ComunicadoBlock[];
  selectBlocksByIds: (ids: string[]) => void;
  updateBlocks: (blocks: ComunicadoBlock[]) => void;
  removeSelected: () => void;
  chooseDataSourceDuplicatePolicy?: () => Promise<DataSourceDuplicatePolicy | null>;
  /** Id do bloco em edição inline — paste nativo no contentEditable. */
  getEditingTextId?: () => string | null;
  canvasRef?: RefObject<HTMLElement | null>;
  canvasWrapRef?: RefObject<HTMLElement | null>;
};

type PasteOptions = {
  /**
   * Só usa clipboard interno da sessão quando o SO não trouxe payload externo.
   * Default true. False no 1º passo do Ctrl+V (evita colar «Poliana» no lugar do Google).
   */
  allowInternalFallback?: boolean;
};

async function writeBlocksToSystemClipboard(
  blocks: ComunicadoBlock[],
  sourceSlideId?: string | null,
): Promise<void> {
  if (typeof navigator === "undefined" || !navigator.clipboard?.writeText) return;
  try {
    await navigator.clipboard.writeText(serializeInternalBlocksPayload(blocks, sourceSlideId));
  } catch {
    // Sem permissão / contexto inseguro — clipboard interno em memória permanece.
  }
}

export function useComunicadoEditorClipboard({
  playlistId,
  getSlideId,
  getSources,
  getExistingBlocks,
  selectBlocksByIds,
  updateBlocks,
  removeSelected,
  chooseDataSourceDuplicatePolicy,
  getEditingTextId,
  canvasRef,
  canvasWrapRef,
}: Options) {
  const [clipboardRevision, setClipboardRevision] = useState(0);
  const [pastingExternal, setPastingExternal] = useState(false);
  const clipboardRef = useRef<ComunicadoBlock[]>([]);
  const clipboardSourceSlideIdRef = useRef<string | null>(null);
  const pastingRef = useRef(false);

  const insertBlocks = useCallback(
    async (incoming: ComunicadoBlock[], sourceSlideId?: string | null) => {
      if (incoming.length === 0) return;

      const existing = getExistingBlocks();
      let plan = resolveBlockPasteDataPolicy({
        incoming,
        targetBlocks: existing,
      });
      if (plan.requiresUserChoice) {
        if (!chooseDataSourceDuplicatePolicy) {
          plan = { policy: "clone_source", requiresUserChoice: false };
        } else {
          const choice = await chooseDataSourceDuplicatePolicy();
          if (!choice) return;
          plan = resolveBlockPasteDataPolicy({
            incoming,
            targetBlocks: existing,
            userPolicy: choice,
          });
        }
      }

      const stacked = assignPasteStack(incoming, existing);
      const offset = resolvePasteFrameOffset({
        sourceSlideId,
        targetSlideId: getSlideId?.() ?? null,
      });
      const { blocks: nextBlocks, pastedIds } = pasteClipboardBlocks(
        existing,
        stacked,
        offset,
        plan.policy,
      );
      // Commit antes da seleção: selectBlocksByIds resolve contra configRef.
      updateBlocks(nextBlocks);
      selectBlocksByIds(pastedIds);
    },
    [
      chooseDataSourceDuplicatePolicy,
      getExistingBlocks,
      getSlideId,
      selectBlocksByIds,
      updateBlocks,
    ],
  );

  const insertImageFiles = useCallback(
    async (files: File[]) => {
      if (files.length === 0) return;
      setPastingExternal(true);
      try {
        const existing = getExistingBlocks();
        const created: ComunicadoBlock[] = [];
        let z = existing.reduce((max, block) => {
          const value = block.style?.zIndex;
          return typeof value === "number" && value > max ? value : max;
        }, 1);

        for (let index = 0; index < files.length; index += 1) {
          const file = files[index];
          const asset = await uploadPlaylistMedia(playlistId, file);
          const url = resolveEditorMediaUrl(playlistId, asset.id) ?? "";
          const block = createBlock("image");
          const col = index % 2;
          const row = Math.floor(index / 2);
          const natural = await readImageNaturalSize(file);
          const baseFrame = frameForImageNaturalSize(
            natural?.width ?? 0,
            natural?.height ?? 0,
          );
          const viewportCenter = resolveViewportCenterCanvasPercent(
            canvasRef?.current,
            canvasWrapRef?.current,
          );
          const centered = viewportCenter
            ? placeFrameCenteredAt(baseFrame, {
                x: viewportCenter.x + col * 8,
                y: viewportCenter.y + row * 8,
              })
            : {
                ...baseFrame,
                x: Math.min(55, baseFrame.x + col * 40),
                y: Math.min(50, baseFrame.y + row * 35),
              };
          created.push({
            ...block,
            assetId: asset.id,
            url,
            frame: centered,
            style: {
              ...block.style,
              objectFit: "contain",
              zIndex: z + 1 + index,
            },
          } as ComunicadoBlock);
        }

        const nextBlocks = [...existing, ...created];
        updateBlocks(nextBlocks);
        selectBlocksByIds(created.map((block) => block.id));
      } finally {
        setPastingExternal(false);
      }
    },
    [canvasRef, canvasWrapRef, getExistingBlocks, playlistId, selectBlocksByIds, updateBlocks],
  );

  const applyPastePlan = useCallback(
    async (plan: ExternalPastePlan): Promise<boolean> => {
      if (plan.kind === "empty") return false;
      if (plan.kind === "images") {
        await insertImageFiles(plan.files);
        return true;
      }
      if (plan.kind === "internal-blocks" || plan.kind === "blocks") {
        const sourceSlideId =
          plan.kind === "internal-blocks"
            ? (plan.sourceSlideId ?? clipboardSourceSlideIdRef.current)
            : clipboardSourceSlideIdRef.current;
        await insertBlocks(plan.blocks, sourceSlideId);
        return true;
      }
      return false;
    },
    [insertBlocks, insertImageFiles],
  );

  const copySelected = useCallback(() => {
    const sources = getSources();
    if (sources.length === 0) return;
    const cloned = cloneBlocksForClipboard(sources, getExistingBlocks());
    const sourceSlideId = getSlideId?.() ?? null;
    clipboardRef.current = cloned;
    clipboardSourceSlideIdRef.current =
      typeof sourceSlideId === "string" && sourceSlideId.trim()
        ? sourceSlideId.trim()
        : null;
    setClipboardRevision((tick) => tick + 1);
    void writeBlocksToSystemClipboard(cloned, clipboardSourceSlideIdRef.current);
  }, [getExistingBlocks, getSlideId, getSources]);

  const pasteSelected = useCallback(async () => {
    if (clipboardRef.current.length === 0) return;
    await insertBlocks(clipboardRef.current, clipboardSourceSlideIdRef.current);
  }, [insertBlocks]);

  /**
   * Cola a partir de um DataTransfer (evento paste ou montado via Clipboard API).
   * Anti-padrão: cair no clipboard interno quando o SO trouxe HTML/imagem externos.
   */
  const pasteFromClipboardData = useCallback(
    async (
      data: DataTransfer | null | undefined,
      options?: PasteOptions,
    ): Promise<boolean> => {
      const allowInternalFallback = options?.allowInternalFallback !== false;
      const plan = planExternalClipboardPaste(data);
      if (plan.kind !== "empty") {
        return applyPastePlan(plan);
      }
      // SO trouxe algo externo que ainda não viramos bloco — nunca substituir pela última forma do plugin.
      if (hasExternalClipboardPayload(data)) {
        return false;
      }
      if (allowInternalFallback && clipboardRef.current.length > 0) {
        await pasteSelected();
        return true;
      }
      return false;
    },
    [applyPastePlan, pasteSelected],
  );

  const pasteFromSystemClipboard = useCallback(async (): Promise<boolean> => {
    const dt = await readSystemClipboardDataTransfer();
    if (dt) {
      const applied = await pasteFromClipboardData(dt, { allowInternalFallback: false });
      if (applied) return true;
      // Payload externo ilegível — não cola a forma antiga do plugin.
      if (hasExternalClipboardPayload(dt)) return false;
    }
    return pasteFromClipboardData(null, { allowInternalFallback: true });
  }, [pasteFromClipboardData]);

  const cutSelected = useCallback(() => {
    copySelected();
    removeSelected();
  }, [copySelected, removeSelected]);

  useEffect(() => {
    const onPaste = (event: ClipboardEvent) => {
      if (isEditableKeyboardTarget(event.target)) return;
      if (getEditingTextId?.()) return;
      if (pastingRef.current) return;

      event.preventDefault();
      pastingRef.current = true;
      void (async () => {
        try {
          // 1) Evento paste (text/html/plain; arquivos quando o browser expõe).
          const fromEvent = await pasteFromClipboardData(event.clipboardData, {
            allowInternalFallback: false,
          });
          if (fromEvent) return;

          // 2) Clipboard API — Google Slides costuma colocar PNG só aqui, não no evento.
          const systemDt = await readSystemClipboardDataTransfer();
          if (systemDt) {
            const fromSystem = await pasteFromClipboardData(systemDt, {
              allowInternalFallback: false,
            });
            if (fromSystem) return;
            if (
              hasExternalClipboardPayload(systemDt) ||
              hasExternalClipboardPayload(event.clipboardData)
            ) {
              return;
            }
          } else if (hasExternalClipboardPayload(event.clipboardData)) {
            return;
          }

          // 3) Só então: memória da sessão (última cópia dentro do plugin).
          await pasteFromClipboardData(null, { allowInternalFallback: true });
        } finally {
          pastingRef.current = false;
        }
      })();
    };
    window.addEventListener("paste", onPaste);
    return () => window.removeEventListener("paste", onPaste);
  }, [getEditingTextId, pasteFromClipboardData]);

  const canPaste = true;
  void clipboardRevision;
  void pastingExternal;

  return {
    clipboardRevision,
    clipboardRef,
    copySelected,
    cutSelected,
    pasteSelected,
    /** Colar: tenta SO (menu) e cai no interno só se o SO estiver vazio. */
    pasteFromSystemClipboard,
    pasteFromClipboardData,
    canPaste,
    pastingExternal,
  };
}
