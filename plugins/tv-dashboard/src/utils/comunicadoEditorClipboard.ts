import {
  duplicateBlocksWithDataPolicy,
  type ComunicadoBlock,
  type DataSourceDuplicatePolicy,
} from "@delpi/tv-dashboard-presentation";

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
  policy: DataSourceDuplicatePolicy = "share_source",
): { blocks: ComunicadoBlock[]; pastedIds: string[] } {
  return duplicateBlocksWithDataPolicy(existingBlocks, clipboardBlocks, policy, offset);
}
