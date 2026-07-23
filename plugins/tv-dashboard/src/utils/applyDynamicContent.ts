import {
  applyCanvasTableDataRef,
  dynamicContentToDataRef,
  isComunicadoVisualBoxBlock,
  type ComunicadoBlock,
  type ComunicadoCanvasTableBlock,
  type DynamicContentSpec,
} from "@delpi/tv-dashboard-presentation";

import type { TextEditorBridge } from "../components/comunicadoEditorContextCore";
import type { ComunicadoCanvasTableCellSelection } from "../components/comunicadoEditorContextCore";

export type ApplyDynamicContentContext = {
  blocks: ComunicadoBlock[];
  editingTextId: string | null;
  selectedCanvasTableCell: ComunicadoCanvasTableCellSelection | null;
  getTextEditorBridge: (blockId: string) => TextEditorBridge | null | undefined;
  updateBlock: (blockId: string, patch: Partial<ComunicadoBlock>) => void;
};

export type ApplyDynamicContentResult =
  | { ok: true; target: "text_run" | "canvas_table_cell" }
  | { ok: false; reason: "unsupported_kind" | "no_target" | "missing_field" | "bridge_unavailable" };

/**
 * Aplica spec de conteúdo dinâmico no alvo ativo:
 * - edição inline (heading/text/shape) → run com dataRef
 * - célula da Grade selecionada → dataRef da célula
 */
export function applyDynamicContent(
  spec: DynamicContentSpec,
  ctx: ApplyDynamicContentContext,
): ApplyDynamicContentResult {
  if (!isDynamicContentKindImplementedGuard(spec)) {
    return { ok: false, reason: "unsupported_kind" };
  }

  const dataRef = dynamicContentToDataRef(spec);
  if (!dataRef) return { ok: false, reason: "missing_field" };

  if (ctx.editingTextId) {
    const block = ctx.blocks.find((item) => item.id === ctx.editingTextId);
    if (!block || !isComunicadoVisualBoxBlock(block)) {
      return { ok: false, reason: "no_target" };
    }
    const bridge = ctx.getTextEditorBridge(ctx.editingTextId);
    if (!bridge?.insertDataRefAtSelection) {
      return { ok: false, reason: "bridge_unavailable" };
    }
    bridge.insertDataRefAtSelection(dataRef);
    return { ok: true, target: "text_run" };
  }

  const cell = ctx.selectedCanvasTableCell;
  if (cell) {
    const table = ctx.blocks.find((item) => item.id === cell.blockId);
    if (!table || table.type !== "canvas_table") {
      return { ok: false, reason: "no_target" };
    }
    const next = applyCanvasTableDataRef(
      table as ComunicadoCanvasTableBlock,
      { row: cell.row, col: cell.col },
      dataRef,
      "cell",
    );
    ctx.updateBlock(table.id, { cells: next.cells });
    return { ok: true, target: "canvas_table_cell" };
  }

  return { ok: false, reason: "no_target" };
}

function isDynamicContentKindImplementedGuard(spec: DynamicContentSpec): boolean {
  return spec.kind === "data_field";
}

/** Alvos onde o atalho `{ }` pode inserir conteúdo dinâmico. */
export function canOpenDynamicContentPicker(ctx: {
  editingTextId: string | null;
  selected: ComunicadoBlock | null;
  selectedCanvasTableCell: ComunicadoCanvasTableCellSelection | null;
}): boolean {
  if (ctx.editingTextId) {
    return (
      ctx.selected != null &&
      isComunicadoVisualBoxBlock(ctx.selected) &&
      ctx.selected.id === ctx.editingTextId
    );
  }
  return (
    ctx.selected?.type === "canvas_table" &&
    ctx.selectedCanvasTableCell != null &&
    ctx.selectedCanvasTableCell.blockId === ctx.selected.id
  );
}
