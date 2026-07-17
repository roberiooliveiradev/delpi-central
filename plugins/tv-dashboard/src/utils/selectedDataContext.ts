import {
  isDataSourceBlockType,
  isDataViewBlockType,
  isFetchableDataBlockType,
  isTextDataBoundBlockType,
  textBlockHasDataBinding,
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
   * Fonte cujos parâmetros editar:
   * - o próprio `data_source` selecionado
   * - a fonte ligada via `dataSourceId` de um visual ou texto/forma
   * - o bloco legado com `dataBinding`
   */
  bindingTarget: ComunicadoBlock | null;
  /** Mensagem quando kind === mixed. */
  message?: string;
};

function dataFingerprint(block: ComunicadoBlock): string {
  if (isDataViewBlockType(block.type)) {
    const sourceId = "dataSourceId" in block ? block.dataSourceId?.trim() : undefined;
    return sourceId ? `source:${sourceId}` : `unbound:${block.id}`;
  }
  if (isTextDataBoundBlockType(block.type) && textBlockHasDataBinding(block)) {
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
  if (isTextDataBoundBlockType(primary.type) && textBlockHasDataBinding(primary)) {
    const sourceId = "dataSourceId" in primary ? primary.dataSourceId?.trim() : undefined;
    if (!sourceId) return null;
    return blocks.find((block) => block.id === sourceId) ?? null;
  }
  if (isDataSourceBlockType(primary.type) || isFetchableDataBlockType(primary.type)) {
    return primary;
  }
  return null;
}

function isSelectedDataBlock(block: ComunicadoBlock): boolean {
  if (isDataViewBlockType(block.type)) return true;
  if (isFetchableDataBlockType(block.type)) return true;
  if (isTextDataBoundBlockType(block.type) && textBlockHasDataBinding(block)) return true;
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
    return { kind: "none", dataBlocks: [], primary: null, bindingTarget: null };
  }

  const primary = dataBlocks[dataBlocks.length - 1] ?? null;
  if (!primary) {
    return { kind: "none", dataBlocks: [], primary: null, bindingTarget: null };
  }

  if (dataBlocks.length === 1) {
    return {
      kind: "single",
      dataBlocks,
      primary,
      bindingTarget: resolveBindingTarget(blocks, primary),
    };
  }

  const fingerprints = new Set(dataBlocks.map(dataFingerprint));
  if (fingerprints.size === 1) {
    return {
      kind: "homogeneous",
      dataBlocks,
      primary,
      bindingTarget: resolveBindingTarget(blocks, primary),
    };
  }

  return {
    kind: "mixed",
    dataBlocks,
    primary,
    bindingTarget: null,
    message: "Seleção mista — escolha um bloco de dados por vez.",
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
