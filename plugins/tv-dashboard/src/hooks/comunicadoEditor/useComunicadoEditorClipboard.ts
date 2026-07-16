import { useCallback, useRef, useState } from "react";

import {
  needsDataSourceDuplicateChoice,
  type ComunicadoBlock,
  type DataSourceDuplicatePolicy,
} from "@delpi/tv-dashboard-presentation";

import { cloneBlocksForClipboard, pasteClipboardBlocks } from "../../utils/comunicadoEditorClipboard";

type Options = {
  getSources: () => ComunicadoBlock[];
  getExistingBlocks: () => ComunicadoBlock[];
  selectBlocksByIds: (ids: string[]) => void;
  updateBlocks: (blocks: ComunicadoBlock[]) => void;
  removeSelected: () => void;
  chooseDataSourceDuplicatePolicy?: () => Promise<DataSourceDuplicatePolicy | null>;
};

export function useComunicadoEditorClipboard({
  getSources,
  getExistingBlocks,
  selectBlocksByIds,
  updateBlocks,
  removeSelected,
  chooseDataSourceDuplicatePolicy,
}: Options) {
  const [clipboardRevision, setClipboardRevision] = useState(0);
  const clipboardRef = useRef<ComunicadoBlock[]>([]);

  const copySelected = useCallback(() => {
    const sources = getSources();
    if (sources.length === 0) return;
    clipboardRef.current = cloneBlocksForClipboard(sources);
    setClipboardRevision((tick) => tick + 1);
  }, [getSources]);

  const pasteSelected = useCallback(async () => {
    if (clipboardRef.current.length === 0) return;

    let policy: DataSourceDuplicatePolicy = "share_source";
    if (needsDataSourceDuplicateChoice(clipboardRef.current) && chooseDataSourceDuplicatePolicy) {
      const choice = await chooseDataSourceDuplicatePolicy();
      if (!choice) return;
      policy = choice;
    }

    const { blocks: nextBlocks, pastedIds } = pasteClipboardBlocks(
      getExistingBlocks(),
      clipboardRef.current,
      { x: 2, y: 2 },
      policy,
    );
    selectBlocksByIds(pastedIds);
    updateBlocks(nextBlocks);
  }, [
    chooseDataSourceDuplicatePolicy,
    getExistingBlocks,
    selectBlocksByIds,
    updateBlocks,
  ]);

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
