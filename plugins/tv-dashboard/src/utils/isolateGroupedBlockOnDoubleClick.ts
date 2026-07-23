import type { ComunicadoBlock } from "@delpi/tv-dashboard-presentation";

import { resolveStageDblClickAction } from "./stageInteractionPolicy";

/**
 * Clique duplo em membro de grupo (não-texto) → isola o subitem.
 * Texto/título/shape: use `enterTextEdit` / `resolveStageDblClickAction`.
 *
 * @deprecated Preferir `resolveStageDblClickAction` + apply no Composer.
 */
export function isolateGroupedBlockOnDoubleClick(params: {
  block: ComunicadoBlock;
  blocks: ComunicadoBlock[];
  selectedIds: string[];
  selectBlock: (id: string, options?: { expandGroup?: boolean }) => void;
}): boolean {
  const action = resolveStageDblClickAction(params);
  if (action.type !== "isolate-child") return false;
  params.selectBlock(action.blockId, { expandGroup: false });
  return true;
}
