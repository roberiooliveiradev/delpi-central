import {
  clearInputPartsFreeLayoutFrames,
  findInputBlockHostInDocument,
  materializeInputPartsFreeLayoutFromRoot,
  seedInputPartsFreeLayoutFrames,
  type ComunicadoInputPartsMap,
} from "@delpi/tv-dashboard-presentation";

/**
 * Ativa free-layout medindo o flex no DOM (evita frames % default altos demais).
 * Fluxo: limpa frames → reflow → materializa bbox real → fallback seed.
 */
export function enableInputFreeLayoutFromDom(
  blockId: string,
  currentParts: ComunicadoInputPartsMap | null | undefined,
  apply: (next: ComunicadoInputPartsMap) => void,
): void {
  const cleared = clearInputPartsFreeLayoutFrames(currentParts);
  apply(cleared);
  requestAnimationFrame(() => {
    requestAnimationFrame(() => {
      const host = findInputBlockHostInDocument(blockId);
      if (host) {
        apply(materializeInputPartsFreeLayoutFromRoot(host, cleared));
        return;
      }
      apply(seedInputPartsFreeLayoutFrames(cleared));
    });
  });
}
