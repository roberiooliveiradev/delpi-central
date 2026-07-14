import { useCallback, useEffect, useRef } from "react";
import {
  isComunicadoInputBlock,
  resolveInputRefreshSourceIds,
  type ComunicadoBlock,
  type ComunicadoInputBlock,
} from "@delpi/tv-dashboard-presentation";

const INPUT_FILTER_REFRESH_DEBOUNCE_MS = 400;

type Options = {
  blocks: ComunicadoBlock[] | undefined;
  refreshDataPreview: (options?: { force?: boolean; blockIds?: string[] }) => Promise<void>;
  /** Evita badge «Dados desatualizados» enquanto o debounce do filtro corre. */
  clearStaleForSourceIds?: (blockIds: string[]) => void;
};

/**
 * Após patch do filtro, agenda refresh só das fontes amarradas (debounce).
 * Ícone/rótulo/layout não entram aqui — só quem chama schedule após mudanca efetiva.
 */
export function useInputFilterDataRefresh({
  blocks,
  refreshDataPreview,
  clearStaleForSourceIds,
}: Options) {
  const timerRef = useRef<number | null>(null);
  const blocksRef = useRef(blocks);
  blocksRef.current = blocks;
  const refreshRef = useRef(refreshDataPreview);
  refreshRef.current = refreshDataPreview;
  const clearStaleRef = useRef(clearStaleForSourceIds);
  clearStaleRef.current = clearStaleForSourceIds;

  useEffect(() => {
    return () => {
      if (timerRef.current != null) window.clearTimeout(timerRef.current);
    };
  }, []);

  const scheduleInputFilterRefresh = useCallback((block: ComunicadoInputBlock) => {
    const blockIds = resolveInputRefreshSourceIds(block, blocksRef.current);
    if (blockIds.length === 0) return;
    clearStaleRef.current?.(blockIds);
    if (timerRef.current != null) window.clearTimeout(timerRef.current);
    timerRef.current = window.setTimeout(() => {
      timerRef.current = null;
      void refreshRef.current({ force: true, blockIds });
    }, INPUT_FILTER_REFRESH_DEBOUNCE_MS);
  }, []);

  const scheduleInputFilterRefreshById = useCallback((blockId: string) => {
    const block = (blocksRef.current ?? []).find((item) => item.id === blockId);
    if (!block || !isComunicadoInputBlock(block)) return;
    scheduleInputFilterRefresh(block);
  }, [scheduleInputFilterRefresh]);

  return {
    scheduleInputFilterRefresh,
    scheduleInputFilterRefreshById,
  };
}

export { INPUT_FILTER_REFRESH_DEBOUNCE_MS };
