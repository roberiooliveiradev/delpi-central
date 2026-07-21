import {
  duplicateBlocksWithDataPolicy,
  enrichClipboardWithLinkedDataSources,
  type ComunicadoBlock,
  type DataSourceDuplicatePolicy,
} from "@delpi/tv-dashboard-presentation";

/**
 * Clona blocos para o clipboard, incluindo fontes ligadas do slide
 * (cada slide tem suas fontes — cola em outro slide precisa do payload completo).
 */
export function cloneBlocksForClipboard(
  blocks: ComunicadoBlock[],
  slideBlocks: ComunicadoBlock[] = blocks,
): ComunicadoBlock[] {
  const enriched = enrichClipboardWithLinkedDataSources(blocks, slideBlocks);
  return enriched.map((block) => {
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
  /* groupId é remapeado em duplicateBlocksWithDataPolicy — cópia fica agrupada,
   * sem entrar no grupo da origem. */
  return duplicateBlocksWithDataPolicy(existingBlocks, clipboardBlocks, policy, offset);
}
