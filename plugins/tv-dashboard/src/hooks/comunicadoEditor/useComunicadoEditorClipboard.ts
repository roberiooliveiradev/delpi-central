import { useCallback, useEffect, useRef, useState } from "react";

import {
  createBlock,
  needsDataSourceDuplicateChoice,
  type ComunicadoBlock,
  type DataSourceDuplicatePolicy,
} from "@delpi/tv-dashboard-presentation";

import { adminMediaUrl, uploadPlaylistMedia } from "../../api/tvDashboardApi";
import { isEditableKeyboardTarget } from "../../keyboard";
import { cloneBlocksForClipboard, pasteClipboardBlocks } from "../../utils/comunicadoEditorClipboard";
import {
  assignPasteStack,
  planExternalClipboardPaste,
  serializeInternalBlocksPayload,
  type ExternalPastePlan,
} from "../../utils/externalClipboardPaste";

type Options = {
  playlistId: string;
  getSources: () => ComunicadoBlock[];
  getExistingBlocks: () => ComunicadoBlock[];
  selectBlocksByIds: (ids: string[]) => void;
  updateBlocks: (blocks: ComunicadoBlock[]) => void;
  removeSelected: () => void;
  chooseDataSourceDuplicatePolicy?: () => Promise<DataSourceDuplicatePolicy | null>;
  /** Id do bloco em edição inline — paste nativo no contentEditable. */
  getEditingTextId?: () => string | null;
};

async function writeBlocksToSystemClipboard(blocks: ComunicadoBlock[]): Promise<void> {
  if (typeof navigator === "undefined" || !navigator.clipboard?.writeText) return;
  try {
    await navigator.clipboard.writeText(serializeInternalBlocksPayload(blocks));
  } catch {
    // Sem permissão / contexto inseguro — clipboard interno em memória permanece.
  }
}

export function useComunicadoEditorClipboard({
  playlistId,
  getSources,
  getExistingBlocks,
  selectBlocksByIds,
  updateBlocks,
  removeSelected,
  chooseDataSourceDuplicatePolicy,
  getEditingTextId,
}: Options) {
  const [clipboardRevision, setClipboardRevision] = useState(0);
  const [pastingExternal, setPastingExternal] = useState(false);
  const clipboardRef = useRef<ComunicadoBlock[]>([]);
  const pastingRef = useRef(false);

  const insertBlocks = useCallback(
    async (incoming: ComunicadoBlock[]) => {
      if (incoming.length === 0) return;

      let policy: DataSourceDuplicatePolicy = "share_source";
      if (needsDataSourceDuplicateChoice(incoming) && chooseDataSourceDuplicatePolicy) {
        const choice = await chooseDataSourceDuplicatePolicy();
        if (!choice) return;
        policy = choice;
      }

      const existing = getExistingBlocks();
      const stacked = assignPasteStack(incoming, existing);
      const { blocks: nextBlocks, pastedIds } = pasteClipboardBlocks(
        existing,
        stacked,
        { x: 2, y: 2 },
        policy,
      );
      selectBlocksByIds(pastedIds);
      updateBlocks(nextBlocks);
    },
    [
      chooseDataSourceDuplicatePolicy,
      getExistingBlocks,
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
          const url = adminMediaUrl(playlistId, asset.id);
          const block = createBlock("image");
          const col = index % 2;
          const row = Math.floor(index / 2);
          created.push({
            ...block,
            assetId: asset.id,
            url,
            frame: {
              x: Math.min(55, 10 + col * 40),
              y: Math.min(50, 15 + row * 35),
              w: 36,
              h: 32,
            },
            style: { ...block.style, zIndex: z + 1 + index },
          } as ComunicadoBlock);
        }

        const nextBlocks = [...existing, ...created];
        selectBlocksByIds(created.map((block) => block.id));
        updateBlocks(nextBlocks);
      } finally {
        setPastingExternal(false);
      }
    },
    [getExistingBlocks, playlistId, selectBlocksByIds, updateBlocks],
  );

  const applyPastePlan = useCallback(
    async (plan: ExternalPastePlan): Promise<boolean> => {
      if (plan.kind === "empty") return false;
      if (plan.kind === "images") {
        await insertImageFiles(plan.files);
        return true;
      }
      if (plan.kind === "internal-blocks" || plan.kind === "blocks") {
        await insertBlocks(plan.blocks);
        return true;
      }
      return false;
    },
    [insertBlocks, insertImageFiles],
  );

  const copySelected = useCallback(() => {
    const sources = getSources();
    if (sources.length === 0) return;
    const cloned = cloneBlocksForClipboard(sources);
    clipboardRef.current = cloned;
    setClipboardRevision((tick) => tick + 1);
    void writeBlocksToSystemClipboard(cloned);
  }, [getSources]);

  const pasteSelected = useCallback(async () => {
    if (clipboardRef.current.length === 0) return;
    await insertBlocks(clipboardRef.current);
  }, [insertBlocks]);

  /**
   * Cola do SO (Ctrl+V / menu): payload Delpi, imagem, HTML/texto/TSV;
   * se o SO estiver vazio, cai no clipboard interno da sessão.
   */
  const pasteFromClipboardData = useCallback(
    async (data: DataTransfer | null | undefined): Promise<boolean> => {
      const plan = planExternalClipboardPaste(data);
      if (plan.kind !== "empty") {
        return applyPastePlan(plan);
      }
      if (clipboardRef.current.length > 0) {
        await pasteSelected();
        return true;
      }
      return false;
    },
    [applyPastePlan, pasteSelected],
  );

  const pasteFromSystemClipboard = useCallback(async (): Promise<boolean> => {
    if (typeof navigator === "undefined" || !navigator.clipboard) {
      return pasteFromClipboardData(null);
    }
    try {
      if (navigator.clipboard.read) {
        const items = await navigator.clipboard.read();
        const dt = new DataTransfer();
        for (const item of items) {
          for (const type of item.types) {
            if (type.startsWith("image/")) {
              const blob = await item.getType(type);
              const ext = type.split("/")[1] || "png";
              dt.items.add(new File([blob], `clipboard.${ext}`, { type }));
            } else if (type === "text/plain" || type === "text/html") {
              const blob = await item.getType(type);
              const text = await blob.text();
              dt.setData(type, text);
            }
          }
        }
        return pasteFromClipboardData(dt);
      }
      const text = await navigator.clipboard.readText();
      const dt = new DataTransfer();
      dt.setData("text/plain", text);
      return pasteFromClipboardData(dt);
    } catch {
      return pasteFromClipboardData(null);
    }
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
      void pasteFromClipboardData(event.clipboardData)
        .catch(() => undefined)
        .finally(() => {
          pastingRef.current = false;
        });
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
    /** Colar: tenta SO (menu) e cai no interno. */
    pasteFromSystemClipboard,
    pasteFromClipboardData,
    canPaste,
    pastingExternal,
  };
}
