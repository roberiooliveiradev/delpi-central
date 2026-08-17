import { sortBlocksByZIndex, type ComunicadoBlock } from "@delpi/tv-dashboard-presentation";

function reindexZ(blocks: ComunicadoBlock[]): ComunicadoBlock[] {
  return blocks.map((block, index) => ({
    ...block,
    style: { ...block.style, zIndex: index + 1 },
  }));
}

export function bringToFront(blocks: ComunicadoBlock[], selectedIds: string[]): ComunicadoBlock[] {
  if (selectedIds.length === 0) return blocks;
  const selectedSet = new Set(selectedIds);
  const sorted = sortBlocksByZIndex(blocks);
  const nonSelected = sorted.filter((block) => !selectedSet.has(block.id));
  const selected = sorted.filter((block) => selectedSet.has(block.id));
  return reindexZ([...nonSelected, ...selected]);
}

export function sendToBack(blocks: ComunicadoBlock[], selectedIds: string[]): ComunicadoBlock[] {
  if (selectedIds.length === 0) return blocks;
  const selectedSet = new Set(selectedIds);
  const sorted = sortBlocksByZIndex(blocks);
  const nonSelected = sorted.filter((block) => !selectedSet.has(block.id));
  const selected = sorted.filter((block) => selectedSet.has(block.id));
  return reindexZ([...selected, ...nonSelected]);
}

export function bringForward(blocks: ComunicadoBlock[], selectedIds: string[]): ComunicadoBlock[] {
  if (selectedIds.length === 0) return blocks;
  const selectedSet = new Set(selectedIds);
  const sorted = sortBlocksByZIndex(blocks);
  const next = [...sorted];
  let changed = false;

  for (let index = next.length - 2; index >= 0; index -= 1) {
    if (selectedSet.has(next[index].id) && !selectedSet.has(next[index + 1].id)) {
      [next[index], next[index + 1]] = [next[index + 1], next[index]];
      changed = true;
    }
  }

  return changed ? reindexZ(next) : blocks;
}

/**
 * Move um ou mais ids (grupo = todos os memberIds) para o alvo, no espaço z-asc.
 * Ordem relativa dos movidos é preservada. Drop no próprio conjunto é no-op.
 */
export function reorderLayerIds(
  blocks: ComunicadoBlock[],
  movedIds: readonly string[],
  targetId: string,
  edge?: "before" | "after",
): ComunicadoBlock[] {
  if (movedIds.length === 0) return blocks;
  const moveSet = new Set(movedIds);
  if (moveSet.has(targetId)) return blocks;

  const sorted = sortBlocksByZIndex(blocks);
  const fromIndexes = movedIds
    .map((id) => sorted.findIndex((block) => block.id === id))
    .filter((index) => index >= 0);
  const targetIndex = sorted.findIndex((block) => block.id === targetId);
  if (fromIndexes.length === 0 || targetIndex < 0) return blocks;

  const fromIndex = Math.min(...fromIndexes);
  const moving = sorted.filter((block) => moveSet.has(block.id));
  const rest = sorted.filter((block) => !moveSet.has(block.id));
  const targetInRest = rest.findIndex((block) => block.id === targetId);
  if (targetInRest < 0) return blocks;
  /* Lista visual é z-desc: before = acima = z maior = depois do alvo no array asc. */
  const insertAt =
    edge === "before"
      ? targetInRest + 1
      : edge === "after"
        ? targetInRest
        : fromIndex < targetIndex
          ? targetInRest + 1
          : targetInRest;
  return reindexZ([...rest.slice(0, insertAt), ...moving, ...rest.slice(insertAt)]);
}

export function sendBackward(blocks: ComunicadoBlock[], selectedIds: string[]): ComunicadoBlock[] {
  if (selectedIds.length === 0) return blocks;
  const selectedSet = new Set(selectedIds);
  const sorted = sortBlocksByZIndex(blocks);
  const next = [...sorted];
  let changed = false;

  for (let index = 1; index < next.length; index += 1) {
    if (selectedSet.has(next[index].id) && !selectedSet.has(next[index - 1].id)) {
      [next[index], next[index - 1]] = [next[index - 1], next[index]];
      changed = true;
    }
  }

  return changed ? reindexZ(next) : blocks;
}
