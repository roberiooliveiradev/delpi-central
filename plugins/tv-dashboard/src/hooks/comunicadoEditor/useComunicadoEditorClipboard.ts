import { useCallback, useEffect, useRef, useState } from "react";

import {
  createBlock,
  resolveBlockPasteDataPolicy,
  type ComunicadoBlock,
  type DataSourceDuplicatePolicy,
} from "@delpi/tv-dashboard-presentation";

import { adminMediaUrl, uploadPlaylistMedia } from "../../api/tvDashboardApi";
import { isEditableKeyboardTarget } from "../../keyboard";
import { cloneBlocksForClipboard, pasteClipboardBlocks } from "../../utils/comunicadoEditorClipboard";
import {
  assignPasteStack,
  hasExternalClipboardPayload,
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

type PasteOptions = {
  /**
   * Só usa clipboard interno da sessão quando o SO não trouxe payload externo.
   * Default true. False no 1º passo do Ctrl+V (evita colar «Poliana» no lugar do Google).
   */
  allowInternalFallback?: boolean;
};

async function writeBlocksToSystemClipboard(blocks: ComunicadoBlock[]): Promise<void> {
  if (typeof navigator === "undefined" || !navigator.clipboard?.writeText) return;
  try {
    await navigator.clipboard.writeText(serializeInternalBlocksPayload(blocks));
  } catch {
    // Sem permissão / contexto inseguro — clipboard interno em memória permanece.
  }
}

async function buildDataTransferFromClipboardItems(items: ClipboardItems): Promise<DataTransfer> {
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
  return dt;
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
      const { blocks: nextBlocks, pastedIds } = pasteClipboardBlocks(
        existing,
        stacked,
        { x: 2, y: 2 },
        plan.policy,
      );
      // Commit antes da seleção: selectBlocksByIds resolve contra configRef.
      updateBlocks(nextBlocks);
      selectBlocksByIds(pastedIds);
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
        updateBlocks(nextBlocks);
        selectBlocksByIds(created.map((block) => block.id));
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
    const cloned = cloneBlocksForClipboard(sources, getExistingBlocks());
    clipboardRef.current = cloned;
    setClipboardRevision((tick) => tick + 1);
    void writeBlocksToSystemClipboard(cloned);
  }, [getExistingBlocks, getSources]);

  const pasteSelected = useCallback(async () => {
    if (clipboardRef.current.length === 0) return;
    await insertBlocks(clipboardRef.current);
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

  const readSystemClipboardDataTransfer = useCallback(async (): Promise<DataTransfer | null> => {
    if (typeof navigator === "undefined" || !navigator.clipboard) return null;
    try {
      if (navigator.clipboard.read) {
        const items = await navigator.clipboard.read();
        return buildDataTransferFromClipboardItems(items);
      }
      const text = await navigator.clipboard.readText();
      const dt = new DataTransfer();
      dt.setData("text/plain", text);
      return dt;
    } catch {
      try {
        const text = await navigator.clipboard.readText();
        const dt = new DataTransfer();
        dt.setData("text/plain", text);
        return dt;
      } catch {
        return null;
      }
    }
  }, []);

  const pasteFromSystemClipboard = useCallback(async (): Promise<boolean> => {
    const dt = await readSystemClipboardDataTransfer();
    if (dt) {
      const applied = await pasteFromClipboardData(dt, { allowInternalFallback: false });
      if (applied) return true;
      // Payload externo ilegível — não cola a forma antiga do plugin.
      if (hasExternalClipboardPayload(dt)) return false;
    }
    return pasteFromClipboardData(null, { allowInternalFallback: true });
  }, [pasteFromClipboardData, readSystemClipboardDataTransfer]);

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
  }, [getEditingTextId, pasteFromClipboardData, readSystemClipboardDataTransfer]);

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
