import {
  isDataSourceBlockType,
  isDataViewBlockType,
  isCanvasTableDataBoundBlockType,
  isFetchableDataBlockType,
  isTextDataBoundBlockType,
} from "./comunicadoDataArchitecture";
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

/** Fontes referenciadas por views, texto ligado ou inputs de escopo sources. */
export function referencedDataSourceIds(blocks: ComunicadoBlock[]): Set<string> {
  const ids = new Set<string>();
  for (const block of blocks) {
    if (isDataViewBlockType(block.type) && block.dataSourceId?.trim()) {
      ids.add(block.dataSourceId.trim());
    }
    if (isTextDataBoundBlockType(block.type) && block.dataSourceId?.trim()) {
      ids.add(block.dataSourceId.trim());
    }
    if (isCanvasTableDataBoundBlockType(block.type) && "dataSourceId" in block && block.dataSourceId?.trim()) {
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

/**
 * Inclui no payload de cópia as `data_source` ligadas que ainda não estavam selecionadas.
 * Necessário para colar em outro slide (cada slide tem suas próprias fontes).
 */
export function enrichClipboardWithLinkedDataSources(
  selected: ComunicadoBlock[],
  slideBlocks: ComunicadoBlock[],
): ComunicadoBlock[] {
  if (selected.length === 0) return [];
  const selectedIds = new Set(selected.map((block) => block.id));
  const byId = new Map(slideBlocks.map((block) => [block.id, block]));
  const extras: ComunicadoBlock[] = [];
  for (const sourceId of referencedDataSourceIds(selected)) {
    if (selectedIds.has(sourceId)) continue;
    const source = byId.get(sourceId);
    if (!source || !isDataSourceBlockType(source.type)) continue;
    extras.push(source);
    selectedIds.add(sourceId);
  }
  return [...extras, ...selected];
}

/** Exibe prompt quando a duplicação envolve vínculo ou bloco de dados. */
export function needsDataSourceDuplicateChoice(sources: ComunicadoBlock[]): boolean {
  for (const block of sources) {
    if (isDataSourceBlockType(block.type)) return true;
    if (block.type.startsWith("data_")) return true;
    if (isDataViewBlockType(block.type) && block.dataSourceId?.trim()) return true;
    if (isTextDataBoundBlockType(block.type) && block.dataSourceId?.trim()) return true;
    if (
      isCanvasTableDataBoundBlockType(block.type) &&
      "dataSourceId" in block &&
      block.dataSourceId?.trim()
    ) {
      return true;
    }
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

/**
 * Slides não compartilham fontes: se alguma referência/fonte do payload
 * não existe no slide alvo, é obrigatório clonar (criar fonte no slide novo).
 */
export function mustCloneDataSourcesForTarget(
  incoming: ComunicadoBlock[],
  targetBlocks: ComunicadoBlock[],
): boolean {
  const targetIds = new Set(targetBlocks.map((block) => block.id));
  for (const block of incoming) {
    if (isDataSourceBlockType(block.type) && !targetIds.has(block.id)) {
      return true;
    }
  }
  for (const refId of referencedDataSourceIds(incoming)) {
    if (!targetIds.has(refId)) return true;
  }
  return false;
}

export type ResolveBlockPasteDataPolicyResult = {
  policy: DataSourceDuplicatePolicy;
  /** true = perguntar share vs clone (somente mesmo slide). */
  requiresUserChoice: boolean;
};

/**
 * Política canônica de cola/duplicação de blocos com dados.
 * Cross-slide → sempre `clone_source` (sem modal).
 */
export function resolveBlockPasteDataPolicy(input: {
  incoming: ComunicadoBlock[];
  targetBlocks: ComunicadoBlock[];
  /** Preferência já escolhida pelo usuário (mesmo slide). */
  userPolicy?: DataSourceDuplicatePolicy | null;
}): ResolveBlockPasteDataPolicyResult {
  const { incoming, targetBlocks, userPolicy } = input;
  if (!needsDataSourceDuplicateChoice(incoming)) {
    return { policy: "share_source", requiresUserChoice: false };
  }
  if (mustCloneDataSourcesForTarget(incoming, targetBlocks)) {
    return { policy: "clone_source", requiresUserChoice: false };
  }
  if (userPolicy === "share_source" || userPolicy === "clone_source") {
    return { policy: userPolicy, requiresUserChoice: false };
  }
  return { policy: "share_source", requiresUserChoice: true };
}

function findDataSourceBlock(
  refId: string,
  pools: ComunicadoBlock[][],
): ComunicadoDataSourceBlock | undefined {
  for (const pool of pools) {
    const found = pool.find(
      (block): block is ComunicadoDataSourceBlock =>
        block.id === refId && isDataSourceBlockType(block.type),
    );
    if (found) return found;
  }
  return undefined;
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

  /* share: fontes já no slide ficam só como vínculo — não colar cópia órfã. */
  const existingIds = new Set(existingBlocks.map((block) => block.id));
  const effectiveSources =
    policy === "share_source"
      ? sources.filter(
          (block) => !(isDataSourceBlockType(block.type) && existingIds.has(block.id)),
        )
      : sources;

  if (effectiveSources.length === 0) {
    return { blocks: existingBlocks, pastedIds: [] };
  }

  let nextZ = nextZIndex(existingBlocks);
  const idMap = new Map<string, string>();
  for (const source of effectiveSources) {
    idMap.set(source.id, newBlockId());
  }

  const copies = effectiveSources.map((source) => {
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

  /* Duplicar: novos groupIds — cópias não entram no grupo da origem. */
  const groupIdMap = new Map<string, string>();
  for (const copy of copies) {
    const previous = copy.groupId?.trim();
    if (!previous) continue;
    let mapped = groupIdMap.get(previous);
    if (!mapped) {
      mapped = `grp_${newBlockId()}`;
      groupIdMap.set(previous, mapped);
    }
    copy.groupId = mapped;
  }

  const extraSources: ComunicadoDataSourceBlock[] = [];
  const sourceIdMap = new Map<string, string>();

  if (policy === "clone_source") {
    for (const [index, copy] of copies.entries()) {
      if (copy.type === "data_source") {
        sourceIdMap.set(effectiveSources[index]!.id, copy.id);
      }
    }

    for (const refId of referencedDataSourceIds(copies)) {
      if (sourceIdMap.has(refId)) continue;
      const original = findDataSourceBlock(refId, [effectiveSources, sources, existingBlocks]);
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
      if (isTextDataBoundBlockType(copy.type) && copy.dataSourceId?.trim()) {
        const mapped = sourceIdMap.get(copy.dataSourceId.trim());
        if (mapped) copy.dataSourceId = mapped;
      }
      if (
        isCanvasTableDataBoundBlockType(copy.type) &&
        "dataSourceId" in copy &&
        copy.dataSourceId?.trim()
      ) {
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
