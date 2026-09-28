import {
  canvasTableHasDataBinding,
  isCanvasTableDataBoundBlock,
  isCanvasTableDataBoundBlockType,
} from "./canvasTableProjection";
import {
  bindingTargetId,
  type ComunicadoBlock,
  type ComunicadoConfig,
  type ComunicadoDataSourceBlock,
  type TvDataModel,
} from "./comunicadoTypes";
import { isTextDataBoundBlock, textBlockHasDataBinding } from "./textViewProjection";

const DATA_VIEW_BLOCK_TYPES = new Set(["chart_view", "table_view", "kpi_view"]);

export function isDataSourceBlockType(type: string): type is "data_source" {
  return type === "data_source";
}

/**
 * Bloco técnico de dados — objeto sem papel visual na apresentação.
 * `data_source` renderiza só o chip de authoring no editor; no palco/playback
 * o componente próprio já devolve null. DataModels nunca são blocos.
 */
export function isTechnicalDataBlockType(type: string): boolean {
  return type === "data_source";
}

/**
 * Semântica de renderização no palco/canvas do editor.
 * Objeto de dados técnico ≠ visual oculto (`hidden` é estado do usuário,
 * não classificação de tipo). DataModel não é bloco — nunca entra no loop.
 */
export function isRenderableBlockType(type: string): boolean {
  return !isTechnicalDataBlockType(type);
}

// `bindingTargetId`/`bindingTargetKind`/`BindingTargetSlice`/`BindingTargetKind`
// vivem em `comunicadoTypes` (leaf) — re-exportados aqui para API estável.
export {
  bindingTargetId,
  bindingTargetKind,
  type BindingTargetKind,
  type BindingTargetSlice,
} from "./comunicadoTypes";

/** Lookup de DataModel persistido (`nativeConfig.dataModels[]`). */
export function findDataModel(
  config: Pick<ComunicadoConfig, "dataModels"> | null | undefined,
  modelId: string | null | undefined,
): TvDataModel | null {
  const id = typeof modelId === "string" ? modelId.trim() : "";
  if (!id) return null;
  return (config?.dataModels ?? []).find((model) => model.id === id) ?? null;
}

/** Opções de modelo para seletores de binding (label → id). */
export function dataModelOptionsForInspector(
  config: Pick<ComunicadoConfig, "dataModels"> | null | undefined,
): Array<{ value: string; label: string }> {
  return (config?.dataModels ?? []).map((model) => ({
    value: model.id,
    label: model.label?.trim() || model.id,
  }));
}

export function isDataViewBlockType(type: string): type is "chart_view" | "table_view" | "kpi_view" {
  return DATA_VIEW_BLOCK_TYPES.has(type);
}

export function isTextDataBoundBlockType(type: string): boolean {
  return isTextDataBoundBlock({ type });
}

export { isCanvasTableDataBoundBlockType };

/**
 * Bloco que participa do fluxo de dados no editor (fonte, visual, texto/forma,
 * Grade, filtro `input` ou legado data_*).
 * Inclui `input` para a aba Dados expor alvo/parâmetro (página vs fontes).
 */
export function isDataBoundEditorBlockType(type: string): boolean {
  return (
    isDataViewBlockType(type) ||
    isFetchableDataBlockType(type) ||
    isTextDataBoundBlockType(type) ||
    isCanvasTableDataBoundBlockType(type) ||
    type === "input"
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
      const sourceId = bindingTargetId(block);
      if (sourceId) linked.add(sourceId);
      continue;
    }
    if (isTextDataBoundBlock(block) && textBlockHasDataBinding(block)) {
      const sourceId = bindingTargetId(block);
      if (sourceId) linked.add(sourceId);
      continue;
    }
    if (isCanvasTableDataBoundBlock(block) && canvasTableHasDataBinding(block)) {
      const sourceId = bindingTargetId(block);
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
  if (
    catalog instanceof Map ||
    typeof (catalog as ReadonlyMap<string, DataSourceLabelRouteInfo>).get === "function"
  ) {
    return (catalog as ReadonlyMap<string, DataSourceLabelRouteInfo>).get(operationId) ?? null;
  }
  return (catalog as Readonly<Record<string, DataSourceLabelRouteInfo>>)[operationId] ?? null;
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
  // Enrich stamp wins (G12) — authoring catalog is fallback only.
  const fromResolved = String(block.resolved?.resolvedRouteLabel ?? "").trim();
  if (fromResolved) return fromResolved;
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
