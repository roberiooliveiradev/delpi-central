import { useCallback, useRef, useState } from "react";

import type { ComunicadoBlock } from "@delpi/tv-dashboard-presentation";

import { cloneBlocksForClipboard, pasteClipboardBlocks } from "../../utils/comunicadoEditorClipboard";

type Options = {
  getSources: () => ComunicadoBlock[];
  getExistingBlocks: () => ComunicadoBlock[];
  selectBlocksByIds: (ids: string[]) => void;
  updateBlocks: (blocks: ComunicadoBlock[]) => void;
  removeSelected: () => void;
};

export function useComunicadoEditorClipboard({
  getSources,
  getExistingBlocks,
  selectBlocksByIds,
  updateBlocks,
  removeSelected,
}: Options) {
  const [clipboardRevision, setClipboardRevision] = useState(0);
  const clipboardRef = useRef<ComunicadoBlock[]>([]);

  const copySelected = useCallback(() => {
    const sources = getSources();
    if (sources.length === 0) return;
    clipboardRef.current = cloneBlocksForClipboard(sources);
    setClipboardRevision((tick) => tick + 1);
  }, [getSources]);

  const pasteSelected = useCallback(() => {
    if (clipboardRef.current.length === 0) return;
    const { blocks: nextBlocks, pastedIds } = pasteClipboardBlocks(
      getExistingBlocks(),
      clipboardRef.current,
    );
    selectBlocksByIds(pastedIds);
    updateBlocks(nextBlocks);
  }, [getExistingBlocks, selectBlocksByIds, updateBlocks]);

  const cutSelected = useCallback(() => {
    copySelected();
    removeSelected();
  }, [copySelected, removeSelected]);

  const canPaste = clipboardRef.current.length > 0;
  void clipboardRevision;

  return {
    clipboardRevision,
    clipboardRef,
    copySelected,
    cutSelected,
    pasteSelected,
    canPaste,
  };
}
