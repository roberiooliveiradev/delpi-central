/**
 * Policy unificada de interação do palco (Fase 1 — seleção nivelada).
 *
 * Fonte única para gestos que mudam nível (L0–L5). Pointerdown de grupo e Esc
 * continuam nos resolvers canônicos de `stageGroupedSelection`; este módulo
 * agrega o contrato e define o dblclick (editar texto vs isolar filho).
 */

import type { ComunicadoBlock } from "@delpi/tv-dashboard-presentation";

import { resolveClosedGroupSelection } from "./comunicadoGrouping";
import {
  resolveEscapeHierarchyAction,
  resolveGroupedBlockPointerDownAction,
  resolveTapWithoutDragSelectionAction,
  type GroupedBlockPointerDownAction,
} from "./stageGroupedSelection";

export type StageDblClickAction =
  | { type: "enter-text-edit"; blockId: string }
  | { type: "isolate-child"; blockId: string }
  | { type: "none" };

export type StageEscapeAction = ReturnType<typeof resolveEscapeHierarchyAction>;

export type StagePointerDownAction = GroupedBlockPointerDownAction;

/** Blocos que aceitam edição inline (L5) no duplo clique. */
export function isInlineTextEditableBlock(block: ComunicadoBlock): boolean {
  return block.type === "heading" || block.type === "text" || block.type === "shape";
}

/**
 * Prioridade de hit no palco (Grida-like):
 * 1. stage pan · 2. handles resize/rotate · 3. conteúdo L5 ·
 * 4. wrap do bloco · 5. marquee no fundo.
 *
 * Tap-deselect no 2º toque compete com dblclick → L5; em texto/shape não armar.
 */
export function shouldArmTapDeselectOnDragCurrent(block: ComunicadoBlock): boolean {
  return !isInlineTextEditableBlock(block);
}

/**
 * Duplo clique no alvo sob o cursor:
 * - texto/título/shape → enter-text-edit (L5; isola se estiver em grupo)
 * - outro membro de grupo → isolate-child (L3)
 * - resto → none
 *
 * Alinha a Canva/PowerPoint/Illustrator: conteúdo editável tem prioridade sobre
 * isolation genérica.
 */
export function resolveStageDblClickAction(params: {
  block: ComunicadoBlock;
  blocks: ComunicadoBlock[];
  selectedIds: string[];
}): StageDblClickAction {
  const { block, blocks, selectedIds } = params;

  if (isInlineTextEditableBlock(block)) {
    return { type: "enter-text-edit", blockId: block.id };
  }

  if (!block.groupId) return { type: "none" };

  const closed = resolveClosedGroupSelection(blocks, selectedIds);
  const inClosedGroup = Boolean(closed && closed.groupId === block.groupId);
  const alreadyIsolated = selectedIds.length === 1 && selectedIds[0] === block.id;
  if (alreadyIsolated && !inClosedGroup) return { type: "none" };

  return { type: "isolate-child", blockId: block.id };
}

/** Facade — pointerdown de bloco no palco. */
export function resolveStagePointerDownAction(
  params: Parameters<typeof resolveGroupedBlockPointerDownAction>[0],
): StagePointerDownAction {
  return resolveGroupedBlockPointerDownAction(params);
}

/** Facade — Esc sobe um nível. */
export function resolveStageEscapeAction(
  params: Parameters<typeof resolveEscapeHierarchyAction>[0],
): StageEscapeAction {
  return resolveEscapeHierarchyAction(params);
}

/** Facade — tap sem drag. */
export function resolveStageTapWithoutDragAction(
  params: Parameters<typeof resolveTapWithoutDragSelectionAction>[0],
): ReturnType<typeof resolveTapWithoutDragSelectionAction> {
  return resolveTapWithoutDragSelectionAction(params);
}
