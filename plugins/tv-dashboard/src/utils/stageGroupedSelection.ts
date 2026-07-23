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
 */
export function resolveBlockWrapChromeFlags(params: {
  hierarchy: StageSelectionHierarchy;
  blockId: string;
  blockType: string | undefined;
  isSelected: boolean;
  editingText: boolean;
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
    editingText,
    closedGroupActive,
    selectedPart,
  } = params;

  if (!isSelected || editingText) {
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
 * Esc: limpa partes → sobe de filhos de grupo para seleção pai.
 */
export function resolveEscapeHierarchyAction(params: {
  blocks: ComunicadoBlock[];
  selectedIds: string[];
  hasPartSelection: boolean;
}): { type: "clear-parts" } | { type: "select-ids"; ids: string[] } | { type: "none" } {
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
  return { type: "none" };
}

export function isComplexMolduraOrParentPart(
  blockType: string | undefined,
  part: StagePartRef | null | undefined,
): boolean {
  return isMolduraPartSelection(blockType, part) || !part;
}
