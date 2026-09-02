/**
 * Comandos canônicos da seleção da Grade — ribbon, float e menu só disparam.
 * Funções puras: devolvem patch de células / bloco; o caller chama updateBlock.
 */

import {
  clearCanvasTableCellsContent,
  clearCanvasTableCellsFormats,
  normalizeCanvasTableCell,
  type CanvasTableCell,
  type CanvasTableCellRef,
  type ComunicadoCanvasTableBlock,
} from "@delpi/tv-dashboard-presentation";

import {
  resolveCanvasTableMergeCommand,
} from "./canvasTableMergeCommands";
import {
  buildCanvasTableDeletePatch,
  buildCanvasTableInsertPatch,
  type CanvasTableStructureInsertAxis,
} from "./canvasTableStructureCommands";
import type { CanvasTableInsertPlacement } from "@delpi/tv-dashboard-presentation";

export type CanvasTableCellStylePatch = NonNullable<CanvasTableCell["style"]>;

/** Aplica patch de estilo em cada célula da seleção. */
export function patchCanvasTableCellsStyle(params: {
  cells: CanvasTableCell[][];
  selection: readonly CanvasTableCellRef[];
  stylePatch: CanvasTableCellStylePatch;
}): CanvasTableCell[][] {
  const next = params.cells.map((row) => row.map((cell) => normalizeCanvasTableCell(cell)));
  for (const { row, col } of params.selection) {
    const current = next[row]?.[col];
    if (current == null) continue;
    next[row]![col] = {
      ...current,
      style: { ...(current.style ?? {}), ...params.stylePatch },
    };
  }
  return next;
}

/** Mesclar / desmesclar — wrapper tipado do merge command (incl. merge-and-center). */
export function applyCanvasTableMergeToBlock(params: {
  block: ComunicadoCanvasTableBlock;
  selection: readonly CanvasTableCellRef[];
  mode: "merge" | "unmerge";
}): Partial<ComunicadoCanvasTableBlock> | null {
  if (!params.selection.length) return null;
  const next = resolveCanvasTableMergeCommand({
    merges: params.block.merges,
    cells: params.selection,
    mode: params.mode,
    cellMatrix: params.mode === "merge" ? params.block.cells : undefined,
  });
  if (!next) return null;
  return {
    merges: next.merges.length ? next.merges : undefined,
    ...(next.cells ? { cells: next.cells } : {}),
  };
}

/** Inserir linha/coluna na âncora — reusa structure commands. */
export function insertCanvasTableBand(params: {
  block: ComunicadoCanvasTableBlock;
  axis: CanvasTableStructureInsertAxis;
  placement: CanvasTableInsertPlacement;
  focus?: { row: number; col: number } | null;
}): Partial<ComunicadoCanvasTableBlock> {
  return buildCanvasTableInsertPatch(params);
}

/** Excluir linhas/colunas cobertas pela seleção — Delete key não usa isto. */
export function deleteCanvasTableBand(params: {
  block: ComunicadoCanvasTableBlock;
  axis: CanvasTableStructureInsertAxis;
  selection?: readonly CanvasTableCellRef[];
  focus?: { row: number; col: number } | null;
}): Partial<ComunicadoCanvasTableBlock> | null {
  return buildCanvasTableDeletePatch(params);
}

export function clearCanvasTableSelectionContent(params: {
  cells: CanvasTableCell[][];
  selection: readonly CanvasTableCellRef[];
}): CanvasTableCell[][] {
  return clearCanvasTableCellsContent(params.cells, params.selection);
}

export function clearCanvasTableSelectionFormats(params: {
  cells: CanvasTableCell[][];
  selection: readonly CanvasTableCellRef[];
}): CanvasTableCell[][] {
  return clearCanvasTableCellsFormats(params.cells, params.selection);
}

/**
 * Cor de bordas: com seleção → células; sem → `block.style.borderColor`.
 * `color` undefined remove a cor (célula herda bloco; bloco volta ao default do host).
 */
export function patchCanvasTableBorderColor(params: {
  block: ComunicadoCanvasTableBlock;
  selection?: readonly CanvasTableCellRef[] | null;
  color: string | undefined;
}): Partial<ComunicadoCanvasTableBlock> {
  const selection = params.selection ?? [];
  if (selection.length) {
    if (params.color != null) {
      return {
        cells: patchCanvasTableCellsStyle({
          cells: params.block.cells,
          selection,
          stylePatch: { borderColor: params.color },
        }),
      };
    }
    const next = params.block.cells.map((row) => row.map((cell) => normalizeCanvasTableCell(cell)));
    for (const { row, col } of selection) {
      const current = next[row]?.[col];
      if (current?.style?.borderColor == null) continue;
      const style = { ...current.style };
      delete style.borderColor;
      next[row]![col] = {
        ...current,
        style: Object.keys(style).length ? style : undefined,
      };
    }
    return { cells: next };
  }
  const nextStyle = { ...(params.block.style ?? {}) };
  if (params.color == null) {
    delete nextStyle.borderColor;
  } else {
    nextStyle.borderColor = params.color;
  }
  return { style: nextStyle };
}
