import type { ComunicadoBlock, ComunicadoDataSourceBlock } from "./comunicadoTypes";

const DATA_VIEW_BLOCK_TYPES = new Set(["chart_view", "table_view"]);

export function isDataSourceBlockType(type: string): type is "data_source" {
  return type === "data_source";
}

export function isDataViewBlockType(type: string): type is "chart_view" | "table_view" {
  return DATA_VIEW_BLOCK_TYPES.has(type);
}

/** Blocos cujo binding dispara fetch na api-delpi. */
export function isFetchableDataBlockType(type: string): boolean {
  return type === "data_source" || type.startsWith("data_");
}

/** IDs de `data_source` referenciados por `chart_view` / `table_view`. */
export function getLinkedDataSourceIds(blocks: ComunicadoBlock[]): Set<string> {
  const linked = new Set<string>();
  for (const block of blocks) {
    if (block.type === "chart_view" || block.type === "table_view") {
      const sourceId = block.dataSourceId?.trim();
      if (sourceId) linked.add(sourceId);
    }
  }
  return linked;
}

/** Fonte oculta no palco quando algum visual está conectado (continua nas camadas). */
export function shouldHideDataSourceOnStage(dataSourceId: string, blocks: ComunicadoBlock[]): boolean {
  return getLinkedDataSourceIds(blocks).has(dataSourceId);
}

export function listDataSourceBlocks(blocks: ComunicadoBlock[]): ComunicadoDataSourceBlock[] {
  return blocks.filter((block): block is ComunicadoDataSourceBlock => block.type === "data_source");
}

export function resolveDataSourceLabel(block: ComunicadoDataSourceBlock): string {
  return block.dataBinding.label ?? block.dataBinding.operationId ?? "Fonte de dados";
}

export function dataSourceOptionsForInspector(
  blocks: ComunicadoBlock[],
  excludeViewBlockId?: string,
): Array<{ value: string; label: string }> {
  return listDataSourceBlocks(blocks)
    .filter((block) => block.id !== excludeViewBlockId)
    .map((block) => ({
      value: block.id,
      label: resolveDataSourceLabel(block),
    }));
}
