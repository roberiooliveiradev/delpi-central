/**
 * Seleção hierárquica unificada no palco.
 *
 * Contrato de produto: **widget complexo ≡ grupo**.
 * - Seleção «pai» → um chrome externo (bbox do grupo ou wrap do complexo).
 * - Seleção «filho(s)» → chrome nos filhos; controles do pai desativados
 *   (sem dúvida de quem está selecionado).
 *
 * Grupo de blocos: `groupId` + `selectedIds`.
 * Complexo (KPI/chart/table/input): um `blockId` + partes (`selected*Part(s)`).
 */

import {
  isComplexViewBlockType,
  type ComunicadoBlock,
} from "@delpi/tv-dashboard-presentation";

import {
  isCompositeContentPart,
  isMolduraPartSelection,
  shouldUsePartChromeInsteadOfBlock,
} from "./compositePartSelection";
import {
  expandSelectionWithGroups,
  resolveClosedGroupSelection,
  resolveGroupChildrenSelection,
} from "./comunicadoGrouping";

export type StagePartRef = { kind: string };

export type StageSelectionHierarchy =
  | { mode: "none" }
  | {
      mode: "parent";
      unit: "block" | "group" | "complex";
      blockIds: string[];
    }
  | {
      mode: "children";
      unit: "group" | "complex";
      /** Blocos do grupo (subset) ou o único bloco complexo. */
      blockIds: string[];
      /** Chaves estáveis das partes (só unit=complex). */
      partKinds?: string[];
    };

export function partSelectionKey(part: StagePartRef): string {
  return part.kind;
}

/**
 * Resolve se a seleção atual é unidade pai ou filhos isolados.
 * Fonte única para chrome do wrap / Esc / ribbon.
 */
export function resolveStageSelectionHierarchy(params: {
  blocks: ComunicadoBlock[];
  selectedIds: string[];
  selectedPart?: StagePartRef | null;
  selectedParts?: StagePartRef[] | null;
}): StageSelectionHierarchy {
  const { blocks, selectedIds } = params;
  if (selectedIds.length === 0) return { mode: "none" };

  const closed = resolveClosedGroupSelection(blocks, selectedIds);
  if (closed) {
    return {
      mode: "parent",
      unit: "group",
      blockIds: closed.memberIds,
    };
  }

  const groupChildren = resolveGroupChildrenSelection(blocks, selectedIds);
  if (groupChildren) {
    return {
      mode: "children",
      unit: "group",
      blockIds: groupChildren.memberIds,
    };
  }

  if (selectedIds.length === 1) {
    const block = blocks.find((item) => item.id === selectedIds[0]);
    if (block && isComplexViewBlockType(block.type)) {
      const parts = normalizeSelectedParts(params.selectedParts, params.selectedPart);
      const contentParts = parts.filter((part) =>
        isCompositeContentPart(block.type, part),
      );
      if (contentParts.length > 0) {
        return {
          mode: "children",
          unit: "complex",
          blockIds: [block.id],
          partKinds: contentParts.map(partSelectionKey),
        };
      }
      return {
        mode: "parent",
        unit: "complex",
        blockIds: [block.id],
      };
    }
    return {
      mode: "parent",
      unit: "block",
      blockIds: selectedIds,
    };
  }

  return {
    mode: "parent",
    unit: "block",
    blockIds: selectedIds,
  };
}

/**
 * Ids efetivos do gesto multi (move/resize).
 * Filhos isolados **não** reexpandem o grupo — só a seleção pai fechada
 * (ou blocos soltos) usa `expandSelectionWithGroups`.
 */
export function resolveMultiDragBlockIds(
  blocks: ComunicadoBlock[],
  selectedIds: string[],
): string[] {
  if (selectedIds.length === 0) return [];
  const hierarchy = resolveStageSelectionHierarchy({ blocks, selectedIds });
  if (hierarchy.mode === "children") {
    return [...selectedIds];
  }
  return expandSelectionWithGroups(blocks, selectedIds);
}

/** Re-export para consumidores do fluxo unificado. */
export {
  isGroupChildrenSelection,
  resolveGroupChildrenSelection,
} from "./comunicadoGrouping";

function normalizeSelectedParts(
  selectedParts: StagePartRef[] | null | undefined,
  selectedPart: StagePartRef | null | undefined,
): StagePartRef[] {
  if (selectedParts && selectedParts.length > 0) return selectedParts;
  if (selectedPart) return [selectedPart];
  return [];
}

/**
 * Chrome do wrap do bloco: handles/outline do «pai» só quando a unidade pai está ativa.
 * Com filhos complexos selecionados, o wrap fica mudo (paridade com membro de grupo).
 * Edição de texto inline **mantém** outline + resize (paridade Figma/Canva).
 */
export function resolveBlockWrapChromeFlags(params: {
  hierarchy: StageSelectionHierarchy;
  blockId: string;
  blockType: string | undefined;
  isSelected: boolean;
  closedGroupActive: boolean;
  selectedPart?: StagePartRef | null;
}): {
  showOutline: boolean;
  showHandles: boolean;
  mutedAsGroupMember: boolean;
  partChildrenActive: boolean;
} {
  const {
    hierarchy,
    blockId,
    blockType,
    isSelected,
    closedGroupActive,
    selectedPart,
  } = params;

  if (!isSelected) {
    return {
      showOutline: false,
      showHandles: false,
      mutedAsGroupMember: false,
      partChildrenActive: false,
    };
  }

  if (closedGroupActive) {
    return {
      showOutline: false,
      showHandles: false,
      mutedAsGroupMember: true,
      partChildrenActive: false,
    };
  }

  const partChildrenActive =
    hierarchy.mode === "children" &&
    hierarchy.unit === "complex" &&
    hierarchy.blockIds.includes(blockId) &&
    shouldUsePartChromeInsteadOfBlock(blockType, selectedPart);

  if (partChildrenActive) {
    return {
      showOutline: false,
      showHandles: false,
      mutedAsGroupMember: false,
      partChildrenActive: true,
    };
  }

  return {
    showOutline: true,
    showHandles: true,
    mutedAsGroupMember: false,
    partChildrenActive: false,
  };
}

/**
 * Esc: limpa partes → sobe filhos de grupo para o pai → limpa a seleção.
 */
export function resolveEscapeHierarchyAction(params: {
  blocks: ComunicadoBlock[];
  selectedIds: string[];
  hasPartSelection: boolean;
}):
  | { type: "clear-parts" }
  | { type: "select-ids"; ids: string[] }
  | { type: "clear-selection" }
  | { type: "none" } {
  if (params.hasPartSelection) {
    return { type: "clear-parts" };
  }
  const children = resolveGroupChildrenSelection(params.blocks, params.selectedIds);
  if (children) {
    return {
      type: "select-ids",
      ids: expandSelectionWithGroups(params.blocks, [children.memberIds[0]]),
    };
  }
  if (params.selectedIds.length > 0) {
    return { type: "clear-selection" };
  }
  return { type: "none" };
}

/**
 * Clique / pointerdown em bloco no palco — fonte única para grupo ↔ subitens.
 *
 * Contrato:
 * - 1º clique em membro → seleciona o grupo (pai).
 * - Com o grupo selecionado, 2º clique no membro → isola o subitem.
 * - Shift/Ctrl em irmão do **mesmo** grupo já presente na seleção → alterna
 *   o membro (`toggle-child`, `expandGroup: false`) — permite multi-selecionar
 *   dois filhos sem desligar o grupo inteiro.
 * - Shift fora do grupo → multi-seleção de grupos/blocos soltos.
 * - Ctrl fora do grupo → remove da seleção.
 * - Alt → isola (atalho).
 */
export type GroupedBlockPointerDownAction =
  | { type: "select-expand-group"; blockId: string }
  | { type: "isolate-child"; blockId: string }
  | { type: "toggle-child"; blockId: string }
  | { type: "toggle-group"; blockId: string }
  | { type: "subtract"; blockId: string }
  | { type: "drag-current-selection" };

function selectionSharesGroupId(
  blocks: ComunicadoBlock[],
  selectedIds: string[],
  groupId: string | undefined,
): boolean {
  if (!groupId) return false;
  return selectedIds.some((id) => blocks.find((item) => item.id === id)?.groupId === groupId);
}

export function resolveGroupedBlockPointerDownAction(params: {
  block: ComunicadoBlock;
  blocks: ComunicadoBlock[];
  selectedIds: string[];
  shiftKey: boolean;
  ctrlOrMeta: boolean;
  altKey: boolean;
}): GroupedBlockPointerDownAction {
  const { block, blocks, selectedIds, shiftKey, ctrlOrMeta, altKey } = params;

  if (altKey && block.groupId) {
    return { type: "isolate-child", blockId: block.id };
  }

  const closed = resolveClosedGroupSelection(blocks, selectedIds);
  const children = resolveGroupChildrenSelection(blocks, selectedIds);
  const inClosedGroup = Boolean(
    closed && block.groupId === closed.groupId && closed.memberIds.includes(block.id),
  );
  const inChildrenGroup = Boolean(children && block.groupId === children.groupId);
  const sameGroupInSelection = selectionSharesGroupId(blocks, selectedIds, block.groupId);

  if (ctrlOrMeta && !shiftKey) {
    /* Mesmo grupo já na seleção: Ctrl alterna o membro (paridade Shift / Camadas). */
    if (sameGroupInSelection) {
      return { type: "toggle-child", blockId: block.id };
    }
    return { type: "subtract", blockId: block.id };
  }

  if (shiftKey) {
    if (sameGroupInSelection || inChildrenGroup || inClosedGroup) {
      return { type: "toggle-child", blockId: block.id };
    }
    return { type: "toggle-group", blockId: block.id };
  }

  if (inClosedGroup) {
    /* 2º clique com o grupo selecionado → subitem. */
    return { type: "isolate-child", blockId: block.id };
  }

  if (inChildrenGroup) {
    if (selectedIds.includes(block.id)) {
      return { type: "drag-current-selection" };
    }
    /* Outro irmão no modo filhos → troca o subitem (não volta ao pai). */
    return { type: "isolate-child", blockId: block.id };
  }

  if (selectedIds.includes(block.id)) {
    return { type: "drag-current-selection" };
  }

  return { type: "select-expand-group", blockId: block.id };
}

/**
 * Segundo toque (pointerup sem arrastar) em item já selecionado.
 * - Filho isolado / bloco simples → limpa seleção.
 * - Grupo fechado (fallback) → isola o subitem (o pointerdown já deve ter isolado).
 */
export function resolveTapWithoutDragSelectionAction(params: {
  blocks?: ComunicadoBlock[];
  selectedIds: string[];
  targetBlockId: string;
  wasAlreadySelected: boolean;
}):
  | { type: "clear-selection" }
  | { type: "isolate-child"; blockId: string }
  | { type: "none" } {
  if (!params.wasAlreadySelected) return { type: "none" };
  if (!params.selectedIds.includes(params.targetBlockId)) return { type: "none" };

  const blocks = params.blocks ?? [];
  if (blocks.length > 0) {
    const closed = resolveClosedGroupSelection(blocks, params.selectedIds);
    const target = blocks.find((item) => item.id === params.targetBlockId);
    if (closed && target?.groupId === closed.groupId) {
      return { type: "isolate-child", blockId: params.targetBlockId };
    }
  }

  return { type: "clear-selection" };
}

export function isComplexMolduraOrParentPart(
  blockType: string | undefined,
  part: StagePartRef | null | undefined,
): boolean {
  return isMolduraPartSelection(blockType, part) || !part;
}
