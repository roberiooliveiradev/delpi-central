import type { ComunicadoBlock, ComunicadoConfig } from "@delpi/tv-dashboard-presentation";

import { snapshotConfig } from "../hooks/comunicadoEditor/useComunicadoEditorHistory";

export type ComunicadoLiveBlockGestureApi = {
  snapshotEditorConfig: () => ComunicadoConfig;
  updateBlockLive: (blockId: string, patch: Partial<ComunicadoBlock>) => void;
  finalizeHistoryGesture: (before: ComunicadoConfig) => void;
};

/**
 * Gesto live de parte (move/resize): atualiza sem empilhar histórico a cada
 * pointermove; um único undo no pointerup se houve mudança.
 */
export function startLiveBlockPatchGesture(
  api: ComunicadoLiveBlockGestureApi,
  blockId: string,
) {
  const before = snapshotConfig(api.snapshotEditorConfig());
  let dirty = false;
  return {
    apply(patch: Partial<ComunicadoBlock>) {
      dirty = true;
      api.updateBlockLive(blockId, patch);
    },
    finish() {
      if (dirty) api.finalizeHistoryGesture(before);
    },
  };
}
