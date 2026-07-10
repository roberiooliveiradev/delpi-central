import { newBlockId, nextZIndex, type ComunicadoBlock } from "@delpi/tv-dashboard-presentation";

export function cloneBlocksForClipboard(blocks: ComunicadoBlock[]): ComunicadoBlock[] {
  return blocks.map((block) => {
    const { resolved: _resolved, url: _url, ...rest } = block as ComunicadoBlock & {
      resolved?: unknown;
      url?: string;
    };
    return structuredClone(rest) as ComunicadoBlock;
  });
}

export function pasteClipboardBlocks(
  existingBlocks: ComunicadoBlock[],
  clipboardBlocks: ComunicadoBlock[],
  offset = { x: 2, y: 2 },
): { blocks: ComunicadoBlock[]; pastedIds: string[] } {
  let nextZ = nextZIndex(existingBlocks);
  const pasted = clipboardBlocks.map((source) => {
    const copy = {
      ...source,
      id: newBlockId(),
      frame: {
        ...source.frame,
        x: Math.min(92, source.frame.x + offset.x),
        y: Math.min(92, source.frame.y + offset.y),
      },
      style: { ...source.style, zIndex: nextZ },
    } as ComunicadoBlock;
    nextZ += 1;
    return copy;
  });

  return {
    blocks: [...existingBlocks, ...pasted],
    pastedIds: pasted.map((block) => block.id),
  };
}
