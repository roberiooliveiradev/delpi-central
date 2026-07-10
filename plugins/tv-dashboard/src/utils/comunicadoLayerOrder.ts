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
