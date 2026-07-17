import { useCallback, useEffect, useRef } from "react";
import type { ComunicadoBlock, ComunicadoInputBlock } from "@delpi/tv-dashboard-presentation";

type Options = {
  blocks: ComunicadoBlock[] | undefined;
  refreshDataPreview: (options?: { force?: boolean; blockIds?: string[] }) => Promise<void>;
  /** Evita badge «Dados desatualizados» enquanto refresh corre. */
  clearStaleForSourceIds?: (blockIds: string[]) => void;
};

/**
 * Compatibilidade com chamadas explícitas após patch de filtro.
 * O refetch automático é feito por `useComunicadoDataPreview` (fingerprint).
 */
export function useInputFilterDataRefresh({
  clearStaleForSourceIds,
}: Pick<Options, "clearStaleForSourceIds">) {
  const clearStaleRef = useRef(clearStaleForSourceIds);
  clearStaleRef.current = clearStaleForSourceIds;

  useEffect(() => {
    return () => undefined;
  }, []);

  const scheduleInputFilterRefresh = useCallback((_block: ComunicadoInputBlock) => {
    // Fingerprint + useComunicadoDataPreview cobrem filtros e fontes.
  }, []);

  const scheduleInputFilterRefreshById = useCallback((_blockId: string) => {
    // Fingerprint + useComunicadoDataPreview cobrem filtros e fontes.
  }, []);

  return {
    scheduleInputFilterRefresh,
    scheduleInputFilterRefreshById,
    clearStaleForSourceIds: clearStaleRef.current,
  };
}

export const INPUT_FILTER_REFRESH_DEBOUNCE_MS = 400;
