import {
  isCanvasTableDataBoundBlockType,
  isDataSourceBlockType,
  isDataViewBlockType,
  isFetchableDataBlockType,
  isTextDataBoundBlockType,
  type ComunicadoBlock,
  type ComunicadoDataSourceBlock,
} from "@delpi/tv-dashboard-presentation";

export type SelectedDataContextKind = "none" | "single" | "homogeneous" | "mixed";

export type SelectedDataContext = {
  kind: SelectedDataContextKind;
  /** Blocos selecionados que têm relação com dados. */
  dataBlocks: ComunicadoBlock[];
  /** Representante para UI (último selecionado com dados, ou o comum). */
  primary: ComunicadoBlock | null;
  /**
   * Fonte cujos parâmetros editar (seleção única / homogênea):
   * - o próprio `data_source` selecionado
   * - a fonte ligada via `dataSourceId` de um visual ou texto/forma
   * - o bloco legado com `dataBinding`
   */
  bindingTarget: ComunicadoBlock | null;
  /**
   * Fontes únicas resolvidas da seleção (multi-seleção mista → união de filtros).
   * Ordem estável pela ordem de seleção.
   */
  bindingTargets: ComunicadoBlock[];
  /** Mensagem auxiliar (ribbon / empty). */
  message?: string;
};

function dataFingerprint(block: ComunicadoBlock): string {
  if (isDataViewBlockType(block.type)) {
    const sourceId = "dataSourceId" in block ? block.dataSourceId?.trim() : undefined;
    return sourceId ? `source:${sourceId}` : `unbound:${block.id}`;
  }
  if (isTextDataBoundBlockType(block.type) || isCanvasTableDataBoundBlockType(block.type)) {
    const sourceId = "dataSourceId" in block ? block.dataSourceId?.trim() : undefined;
    return sourceId ? `source:${sourceId}` : `text-unbound:${block.id}`;
  }
  if (isDataSourceBlockType(block.type)) {
    return `source:${block.id}`;
  }
  if (isFetchableDataBlockType(block.type) && "dataBinding" in block) {
    return `op:${block.dataBinding.operationId}`;
  }
  return `id:${block.id}`;
}

function resolveBindingTarget(
  blocks: ComunicadoBlock[],
  primary: ComunicadoBlock,
): ComunicadoBlock | null {
  if (isDataViewBlockType(primary.type)) {
    const sourceId = "dataSourceId" in primary ? primary.dataSourceId?.trim() : undefined;
    if (!sourceId) return null;
    return blocks.find((block) => block.id === sourceId) ?? null;
  }
  if (isTextDataBoundBlockType(primary.type) || isCanvasTableDataBoundBlockType(primary.type)) {
    const sourceId = "dataSourceId" in primary ? primary.dataSourceId?.trim() : undefined;
    if (!sourceId) return null;
    return blocks.find((block) => block.id === sourceId) ?? null;
  }
  if (isDataSourceBlockType(primary.type) || isFetchableDataBlockType(primary.type)) {
    return primary;
  }
  return null;
}

function collectBindingTargets(
  blocks: ComunicadoBlock[],
  dataBlocks: ComunicadoBlock[],
): ComunicadoBlock[] {
  const seen = new Set<string>();
  const targets: ComunicadoBlock[] = [];
  for (const block of dataBlocks) {
    const target = resolveBindingTarget(blocks, block);
    if (!target || !("dataBinding" in target)) continue;
    if (seen.has(target.id)) continue;
    seen.add(target.id);
    targets.push(target);
  }
  return targets;
}

function isSelectedDataBlock(block: ComunicadoBlock): boolean {
  if (isDataViewBlockType(block.type)) return true;
  if (isFetchableDataBlockType(block.type)) return true;
  // Texto/forma/título podem vincular fonte mesmo sem binding ainda (mesmo fluxo do KPI).
  if (isTextDataBoundBlockType(block.type)) return true;
  if (isCanvasTableDataBoundBlockType(block.type)) return true;
  return false;
}

/** Analisa a seleção atual para o painel / aba Dados. */
export function resolveSelectedDataContext(
  blocks: ComunicadoBlock[],
  selectedIds: string[],
): SelectedDataContext {
  const byId = new Map(blocks.map((block) => [block.id, block]));
  const dataBlocks = selectedIds
    .map((id) => byId.get(id))
    .filter((block): block is ComunicadoBlock => Boolean(block && isSelectedDataBlock(block)));

  if (dataBlocks.length === 0) {
    return {
      kind: "none",
      dataBlocks: [],
      primary: null,
      bindingTarget: null,
      bindingTargets: [],
    };
  }

  const primary = dataBlocks[dataBlocks.length - 1] ?? null;
  if (!primary) {
    return {
      kind: "none",
      dataBlocks: [],
      primary: null,
      bindingTarget: null,
      bindingTargets: [],
    };
  }

  const bindingTargets = collectBindingTargets(blocks, dataBlocks);
  const bindingTarget = resolveBindingTarget(blocks, primary);

  if (dataBlocks.length === 1) {
    return {
      kind: "single",
      dataBlocks,
      primary,
      bindingTarget,
      bindingTargets,
    };
  }

  const fingerprints = new Set(dataBlocks.map(dataFingerprint));
  if (fingerprints.size === 1) {
    return {
      kind: "homogeneous",
      dataBlocks,
      primary,
      bindingTarget,
      bindingTargets,
    };
  }

  return {
    kind: "mixed",
    dataBlocks,
    primary,
    bindingTarget: bindingTargets.length === 1 ? bindingTargets[0]! : null,
    bindingTargets,
    message:
      bindingTargets.length > 0
        ? "Seleção com várias fontes — filtros unificados abaixo."
        : "Seleção sem fontes ligadas — conecte uma fonte ou escolha um bloco.",
  };
}

export function resolveLinkedSourceForBlock(
  blocks: ComunicadoBlock[],
  block: ComunicadoBlock,
): ComunicadoDataSourceBlock | null {
  const target = resolveBindingTarget(blocks, block);
  if (target && isDataSourceBlockType(target.type)) return target;
  return null;
}
