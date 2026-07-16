import { isDataSourceBlockType, isDataViewBlockType, isFetchableDataBlockType } from "./comunicadoDataArchitecture";
import { isComunicadoInputBlock } from "./comunicadoInputFilters";
import { newBlockId, nextZIndex } from "./comunicadoHelpers";
import type {
  ComunicadoBlock,
  ComunicadoDataSourceBlock,
  ComunicadoShapeBlock,
} from "./comunicadoTypes";

export type DataSourceDuplicatePolicy = "share_source" | "clone_source";

function stripRuntimeFields(block: ComunicadoBlock): ComunicadoBlock {
  const { resolved: _resolved, url: _url, ...rest } = block as ComunicadoBlock & {
    resolved?: unknown;
    url?: string;
  };
  return structuredClone(rest) as ComunicadoBlock;
}

function cloneDataSourceBlock(source: ComunicadoDataSourceBlock, newId: string): ComunicadoDataSourceBlock {
  const copy = stripRuntimeFields(source) as ComunicadoDataSourceBlock;
  return { ...copy, id: newId };
}

function remapShapeConnector(
  block: ComunicadoShapeBlock,
  idMap: Map<string, string>,
): ComunicadoShapeBlock {
  if (!block.connector) return block;
  return {
    ...block,
    connector: {
      ...block.connector,
      fromBlockId: idMap.get(block.connector.fromBlockId) ?? block.connector.fromBlockId,
      toBlockId: idMap.get(block.connector.toBlockId) ?? block.connector.toBlockId,
    },
  };
}

function referencedDataSourceIds(blocks: ComunicadoBlock[]): Set<string> {
  const ids = new Set<string>();
  for (const block of blocks) {
    if (isDataViewBlockType(block.type) && block.dataSourceId?.trim()) {
      ids.add(block.dataSourceId.trim());
    }
    if (isComunicadoInputBlock(block) && block.input.targetScope === "sources") {
      for (const sourceId of block.input.targetSourceIds ?? []) {
        const trimmed = String(sourceId || "").trim();
        if (trimmed) ids.add(trimmed);
      }
    }
  }
  return ids;
}

/** Exibe prompt quando a duplicação envolve vínculo ou bloco de dados. */
export function needsDataSourceDuplicateChoice(sources: ComunicadoBlock[]): boolean {
  for (const block of sources) {
    if (isDataSourceBlockType(block.type)) return true;
    if (block.type.startsWith("data_")) return true;
    if (isDataViewBlockType(block.type) && block.dataSourceId?.trim()) return true;
    if (
      isComunicadoInputBlock(block) &&
      block.input.targetScope === "sources" &&
      (block.input.targetSourceIds?.length ?? 0) > 0
    ) {
      return true;
    }
  }
  return false;
}

export function duplicateBlocksWithDataPolicy(
  existingBlocks: ComunicadoBlock[],
  sources: ComunicadoBlock[],
  policy: DataSourceDuplicatePolicy,
  offset = { x: 2, y: 2 },
): { blocks: ComunicadoBlock[]; pastedIds: string[] } {
  if (sources.length === 0) {
    return { blocks: existingBlocks, pastedIds: [] };
  }

  let nextZ = nextZIndex(existingBlocks);
  const idMap = new Map<string, string>();
  for (const source of sources) {
    idMap.set(source.id, newBlockId());
  }

  const copies = sources.map((source) => {
    const copy = stripRuntimeFields(source);
    copy.id = idMap.get(source.id)!;
    copy.frame = {
      ...source.frame,
      x: Math.min(92, source.frame.x + offset.x),
      y: Math.min(92, source.frame.y + offset.y),
    };
    copy.style = { ...source.style, zIndex: nextZ };
    nextZ += 1;
    return copy;
  });

  const extraSources: ComunicadoDataSourceBlock[] = [];
  const sourceIdMap = new Map<string, string>();

  if (policy === "clone_source") {
    for (const [index, copy] of copies.entries()) {
      if (copy.type === "data_source") {
        sourceIdMap.set(sources[index]!.id, copy.id);
      }
    }

    for (const refId of referencedDataSourceIds(copies)) {
      if (sourceIdMap.has(refId)) continue;
      const original = existingBlocks.find(
        (block): block is ComunicadoDataSourceBlock =>
          block.id === refId && isDataSourceBlockType(block.type),
      );
      if (!original) continue;
      const newId = newBlockId();
      extraSources.push(cloneDataSourceBlock(original, newId));
      sourceIdMap.set(refId, newId);
    }

    for (const copy of copies) {
      if (isDataViewBlockType(copy.type) && copy.dataSourceId?.trim()) {
        const mapped = sourceIdMap.get(copy.dataSourceId.trim());
        if (mapped) copy.dataSourceId = mapped;
      }
      if (isComunicadoInputBlock(copy) && copy.input.targetScope === "sources") {
        copy.input = {
          ...copy.input,
          targetSourceIds: (copy.input.targetSourceIds ?? [])
            .map((sourceId) => sourceIdMap.get(String(sourceId).trim()) ?? String(sourceId).trim())
            .filter(Boolean),
        };
      }
      if (copy.type === "shape" && copy.connector) {
        Object.assign(copy, remapShapeConnector(copy as ComunicadoShapeBlock, idMap));
      }
    }
  } else {
    for (const copy of copies) {
      if (copy.type === "shape" && copy.connector) {
        Object.assign(copy, remapShapeConnector(copy as ComunicadoShapeBlock, idMap));
      }
    }
  }

  return {
    blocks: [...existingBlocks, ...extraSources, ...copies],
    pastedIds: copies.map((copy) => copy.id),
  };
}

/** Blocos fetchable legados (data_*) também pedem política de duplicação. */
export function isLegacyFetchableDataBlock(block: ComunicadoBlock): boolean {
  return isFetchableDataBlockType(block.type) && !isDataSourceBlockType(block.type);
}
