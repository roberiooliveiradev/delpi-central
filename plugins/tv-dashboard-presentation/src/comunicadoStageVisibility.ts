import {
  isDataSourceBlockType,
  isDataViewBlockType,
  shouldHideDataSourceOnStage,
} from "./comunicadoDataArchitecture";
import type { ComunicadoBlock } from "./comunicadoTypes";

/** Motivo canônico de ocultação no palco (extensível). */
export type StageHideReason = "linked_data_source" | "user_hidden";

/**
 * Fonte de verdade: um bloco oculto no palco não participa de hit-test,
 * marquee, chrome de seleção nem render no editor/apresentação.
 */
export function resolveBlockStageHideReason(
  block: ComunicadoBlock,
  blocks: ComunicadoBlock[],
): StageHideReason | null {
  if (block.hidden === true) return "user_hidden";
  if (isDataSourceBlockType(block.type) && shouldHideDataSourceOnStage(block.id, blocks)) {
    return "linked_data_source";
  }
  return null;
}

export function isBlockHiddenOnStage(block: ComunicadoBlock, blocks: ComunicadoBlock[]): boolean {
  return resolveBlockStageHideReason(block, blocks) != null;
}

export function isBlockSelectableOnStage(
  block: ComunicadoBlock,
  blocks: ComunicadoBlock[],
): boolean {
  return !isBlockHiddenOnStage(block, blocks);
}

export function filterBlocksVisibleOnStage(blocks: ComunicadoBlock[]): ComunicadoBlock[] {
  return blocks.filter((block) => !isBlockHiddenOnStage(block, blocks));
}

export function filterStageSelectableIds(ids: string[], blocks: ComunicadoBlock[]): string[] {
  const byId = new Map(blocks.map((block) => [block.id, block]));
  return ids.filter((id) => {
    const block = byId.get(id);
    return block != null && isBlockSelectableOnStage(block, blocks);
  });
}

/** Visuais ligados a uma `data_source` (para redirecionar seleção / painel Dados). */
export function listViewsLinkedToDataSource(
  dataSourceId: string,
  blocks: ComunicadoBlock[],
): ComunicadoBlock[] {
  const wanted = dataSourceId.trim();
  if (!wanted) return [];
  return blocks.filter((block) => {
    if (!isDataViewBlockType(block.type)) return false;
    const sourceId = "dataSourceId" in block ? block.dataSourceId?.trim() : undefined;
    return sourceId === wanted;
  });
}

/**
 * Resolve o alvo de seleção quando o clique/camada aponta para um bloco oculto.
 * Fontes vinculadas → primeiro visual ligado (dados continuam editáveis pelo visual).
 */
export function resolveStageSelectionTargetId(
  blockId: string,
  blocks: ComunicadoBlock[],
): string | null {
  const block = blocks.find((item) => item.id === blockId);
  if (!block) return null;
  if (isBlockSelectableOnStage(block, blocks)) return block.id;
  if (isDataSourceBlockType(block.type)) {
    return listViewsLinkedToDataSource(block.id, blocks)[0]?.id ?? null;
  }
  return null;
}
