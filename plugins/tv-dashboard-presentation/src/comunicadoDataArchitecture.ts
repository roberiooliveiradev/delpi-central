import {
  canvasTableHasDataBinding,
  isCanvasTableDataBoundBlock,
  isCanvasTableDataBoundBlockType,
} from "./canvasTableProjection";
import type { ComunicadoBlock, ComunicadoDataSourceBlock } from "./comunicadoTypes";
import { isTextDataBoundBlock, textBlockHasDataBinding } from "./textViewProjection";

const DATA_VIEW_BLOCK_TYPES = new Set(["chart_view", "table_view", "kpi_view"]);

export function isDataSourceBlockType(type: string): type is "data_source" {
  return type === "data_source";
}

export function isDataViewBlockType(type: string): type is "chart_view" | "table_view" | "kpi_view" {
  return DATA_VIEW_BLOCK_TYPES.has(type);
}

export function isTextDataBoundBlockType(type: string): boolean {
  return isTextDataBoundBlock({ type });
}

export { isCanvasTableDataBoundBlockType };

/**
 * Bloco que participa do fluxo de dados no editor (fonte, visual, texto/forma, Grade ou legado data_*).
 */
export function isDataBoundEditorBlockType(type: string): boolean {
  return (
    isDataViewBlockType(type) ||
    isFetchableDataBlockType(type) ||
    isTextDataBoundBlockType(type) ||
    isCanvasTableDataBoundBlockType(type)
  );
}

/** Blocos cujo binding dispara fetch na api-delpi. */
export function isFetchableDataBlockType(type: string): boolean {
  return type === "data_source" || type.startsWith("data_");
}

/** IDs de `data_source` referenciados por views ou texto/forma ligados. */
export function getLinkedDataSourceIds(blocks: ComunicadoBlock[]): Set<string> {
  const linked = new Set<string>();
  for (const block of blocks) {
    if (isDataViewBlockType(block.type)) {
      const sourceId = "dataSourceId" in block ? block.dataSourceId?.trim() : undefined;
      if (sourceId) linked.add(sourceId);
      continue;
    }
    if (isTextDataBoundBlock(block) && textBlockHasDataBinding(block)) {
      const sourceId = block.dataSourceId?.trim();
      if (sourceId) linked.add(sourceId);
      continue;
    }
    if (isCanvasTableDataBoundBlock(block) && canvasTableHasDataBinding(block)) {
      const sourceId = block.dataSourceId?.trim();
      if (sourceId) linked.add(sourceId);
    }
  }
  return linked;
}

/** Fonte oculta no palco quando algum visual ou texto está conectado. */
export function shouldHideDataSourceOnStage(dataSourceId: string, blocks: ComunicadoBlock[]): boolean {
  return getLinkedDataSourceIds(blocks).has(dataSourceId);
}

export function listDataSourceBlocks(blocks: ComunicadoBlock[]): ComunicadoDataSourceBlock[] {
  return blocks.filter((block): block is ComunicadoDataSourceBlock => block.type === "data_source");
}

/** Entrada mínima do catálogo para resolver rótulo vivo. */
export type DataSourceLabelRouteInfo = {
  label?: string | null;
  labelAliases?: string[] | null;
};

export type DataSourceLabelCatalog =
  | ReadonlyMap<string, DataSourceLabelRouteInfo>
  | Readonly<Record<string, DataSourceLabelRouteInfo>>;

function catalogRouteFor(
  catalog: DataSourceLabelCatalog | null | undefined,
  operationId: string,
): DataSourceLabelRouteInfo | null {
  if (!catalog || !operationId) return null;
  if (catalog instanceof Map) return catalog.get(operationId) ?? null;
  return catalog[operationId] ?? null;
}

/** True se o rótulo gravado é só eco do catálogo (atual ou alias de renome). */
export function isCatalogLikeDataSourceLabel(
  label: string | null | undefined,
  route: DataSourceLabelRouteInfo | null | undefined,
): boolean {
  const trimmed = String(label ?? "").trim();
  if (!trimmed) return true;
  if (!route) return false;
  const current = String(route.label ?? "").trim();
  if (current && trimmed === current) return true;
  const aliases = Array.isArray(route.labelAliases) ? route.labelAliases : [];
  return aliases.some((alias) => String(alias ?? "").trim() === trimmed);
}

/**
 * Rótulo exibido da fonte: override do usuário, senão label vivo do catálogo, senão operationId.
 * `dataBinding.label` só conta como override quando não é catalog-like.
 */
export function resolveDataSourceLabel(
  block: ComunicadoDataSourceBlock,
  catalog?: DataSourceLabelCatalog | null,
): string {
  const operationId = String(block.dataBinding.operationId ?? "").trim();
  const stored = String(block.dataBinding.label ?? "").trim();
  const route = catalogRouteFor(catalog, operationId);
  if (stored && !isCatalogLikeDataSourceLabel(stored, route)) {
    return stored;
  }
  const live = String(route?.label ?? "").trim();
  return live || operationId || "Fonte de dados";
}

/**
 * Fonte preferida ao inserir um visual ou vincular texto: a fonte selecionada, ou a única do slide.
 */
export function resolvePreferredDataSourceId(
  blocks: ComunicadoBlock[],
  selectedId?: string | null,
): string | undefined {
  if (selectedId) {
    const selected = blocks.find((block) => block.id === selectedId);
    if (selected && isDataSourceBlockType(selected.type)) {
      return selected.id;
    }
  }
  const sources = listDataSourceBlocks(blocks);
  if (sources.length === 1) return sources[0]?.id;
  return undefined;
}

export function dataSourceOptionsForInspector(
  blocks: ComunicadoBlock[],
  excludeViewBlockId?: string,
  catalog?: DataSourceLabelCatalog | null,
): Array<{ value: string; label: string }> {
  return listDataSourceBlocks(blocks)
    .filter((block) => block.id !== excludeViewBlockId)
    .map((block) => ({
      value: block.id,
      label: resolveDataSourceLabel(block, catalog),
    }));
}
