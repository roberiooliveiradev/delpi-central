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

/**
 * Cola no palco: cópias nascem desagrupadas (sem `groupId`).
 * Agrupar de novo é ação explícita do usuário — não herdar o grupo da origem.
 */
export function detachClipboardGroupIds(blocks: ComunicadoBlock[]): ComunicadoBlock[] {
  return blocks.map((block) => {
    if (!block.groupId) return block;
    const { groupId: _omit, ...rest } = block;
    return rest as ComunicadoBlock;
  });
}

export function pasteClipboardBlocks(
  existingBlocks: ComunicadoBlock[],
  clipboardBlocks: ComunicadoBlock[],
  offset = { x: 2, y: 2 },
  policy: DataSourceDuplicatePolicy = "share_source",
): { blocks: ComunicadoBlock[]; pastedIds: string[] } {
  return duplicateBlocksWithDataPolicy(
    existingBlocks,
    detachClipboardGroupIds(clipboardBlocks),
    policy,
    offset,
  );
}
