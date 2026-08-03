import { useCallback, useRef } from "react";
import {
  DATA_PREVIEW_AUTO_REFRESH_DEBOUNCE_MS,
  type ComunicadoInputBlock,
} from "@delpi/tv-dashboard-presentation";

type Options = {
  clearStaleForSourceIds?: (blockIds: string[]) => void;
};

/**
 * Compatibilidade com chamadas explícitas após patch de filtro de input.
 * O fluxo canônico de atualização é:
 *   fingerprint (`buildDataPreviewFingerprint`) → `planDataPreviewRefresh` →
 *   `useComunicadoDataPreview` → `requestDataPreviewBlock`.
 * Estas funções existem só para não quebrar call sites do inspetor/palco.
 */
export function useInputFilterDataRefresh({
  clearStaleForSourceIds,
}: Options) {
  const clearStaleRef = useRef(clearStaleForSourceIds);
  clearStaleRef.current = clearStaleForSourceIds;

  const scheduleInputFilterRefresh = useCallback((_block: ComunicadoInputBlock) => {
    // no-op: fingerprint + planDataPreviewRefresh cobrem o refresh.
  }, []);

  const scheduleInputFilterRefreshById = useCallback((_blockId: string) => {
    // no-op: fingerprint + planDataPreviewRefresh cobrem o refresh.
  }, []);

  return {
    scheduleInputFilterRefresh,
    scheduleInputFilterRefreshById,
    clearStaleForSourceIds: clearStaleRef.current,
  };
}

/** @deprecated Use DATA_PREVIEW_AUTO_REFRESH_DEBOUNCE_MS de @delpi/tv-dashboard-presentation */
export const INPUT_FILTER_REFRESH_DEBOUNCE_MS = DATA_PREVIEW_AUTO_REFRESH_DEBOUNCE_MS;
