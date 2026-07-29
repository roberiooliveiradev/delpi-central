import {
  duplicateBlocksWithDataPolicy,
  enrichClipboardWithLinkedDataSources,
  type ComunicadoBlock,
  type DataSourceDuplicatePolicy,
} from "@delpi/tv-dashboard-presentation";

/** Deslocamento ao colar no mesmo slide — deixa a cópia visível sobre a origem. */
export const SAME_SLIDE_PASTE_OFFSET = { x: 2, y: 2 } as const;
export const CROSS_SLIDE_PASTE_OFFSET = { x: 0, y: 0 } as const;

/**
 * Offset de frame no colar: só desloca no mesmo slide.
 * Em outro slide mantém X/Y — senão o usuário acha que a cópia falhou.
 */
export function resolvePasteFrameOffset(options: {
  sourceSlideId?: string | null;
  targetSlideId?: string | null;
}): { x: number; y: number } {
  const source = typeof options.sourceSlideId === "string" ? options.sourceSlideId.trim() : "";
  const target = typeof options.targetSlideId === "string" ? options.targetSlideId.trim() : "";
  if (source && target && source === target) {
    return { ...SAME_SLIDE_PASTE_OFFSET };
  }
  return { ...CROSS_SLIDE_PASTE_OFFSET };
}

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
  offset: { x: number; y: number } = SAME_SLIDE_PASTE_OFFSET,
  policy: DataSourceDuplicatePolicy = "share_source",
): { blocks: ComunicadoBlock[]; pastedIds: string[] } {
  /* groupId é remapeado em duplicateBlocksWithDataPolicy — cópia fica agrupada,
   * sem entrar no grupo da origem. */
  return duplicateBlocksWithDataPolicy(existingBlocks, clipboardBlocks, policy, offset);
}
