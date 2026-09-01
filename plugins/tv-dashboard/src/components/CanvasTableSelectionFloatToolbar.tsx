import {
  canMergeRect,
  normalizeCanvasTableCell,
  type ComunicadoCanvasTableBlock,
  type CanvasTableCell,
} from "@delpi/tv-dashboard-presentation";

import { ComplexSelectionFloatToolbar } from "./ComplexSelectionFloatToolbar";
import { FloatChecklist, FloatChecklistItem } from "./FloatChecklist";
import { TvRibbonColorPicker } from "./deck/TvRibbonColorPicker";
import { useComunicadoEditor } from "./comunicadoEditorContext";
import {
  canUnmergeCanvasTableSelection,
  resolveCanvasTableMergeCommand,
} from "../utils/canvasTableMergeCommands";
import { buildCanvasTableInsertPatch } from "../utils/canvasTableStructureCommands";

type Props = {
  block: ComunicadoCanvasTableBlock;
};

/**
 * Float da Grade — + estrutura/merge, pincel fill/alinhamento, funil dados.
 * Mesmo shell dos charts (ComplexSelectionFloatToolbar + AnchoredPanelPortal).
 */
export function CanvasTableSelectionFloatToolbar({ block }: Props) {
  const {
    updateBlock,
    openDataPanel,
    setSelectionPanelTab,
    selectedCanvasTableCell,
  } = useComunicadoEditor();

  const cellSelection =
    selectedCanvasTableCell?.blockId === block.id ? selectedCanvasTableCell : null;
  const cells = cellSelection?.cells ?? [];
  const focus = cellSelection?.focus ?? null;
  const canMerge = Boolean(cells.length && canMergeRect(cells, block.merges));
  const canUnmerge = Boolean(
    cells.length && canUnmergeCanvasTableSelection(block.merges, cells),
  );

  function insert(axis: "row" | "col", placement: "before" | "after") {
    updateBlock(
      block.id,
      buildCanvasTableInsertPatch({ block, axis, placement, focus }),
    );
  }

  function applyMerge(mode: "merge" | "unmerge") {
    if (!cells.length) return;
    const next = resolveCanvasTableMergeCommand({
      merges: block.merges,
      cells,
      mode,
    });
    if (!next) return;
    updateBlock(block.id, { merges: next.length ? next : undefined });
  }

  function patchSelectedCellsStyle(stylePatch: NonNullable<CanvasTableCell["style"]>) {
    if (!cells.length) return;
    const nextCells = block.cells.map((row) => row.map((cell) => normalizeCanvasTableCell(cell)));
    for (const { row, col } of cells) {
      const current = nextCells[row]?.[col];
      if (current == null) continue;
      nextCells[row]![col] = {
        ...normalizeCanvasTableCell(current),
        style: { ...(current.style ?? {}), ...stylePatch },
      };
    }
    updateBlock(block.id, { cells: nextCells });
  }

  return (
    <ComplexSelectionFloatToolbar
      blockId={block.id}
      frame={block.frame}
      labels={{
        elements: "Estrutura da Grade",
        style: "Estilo das células",
        data: "Dados da Grade",
      }}
      renderElements={(close) => (
        <FloatChecklist aria-label="Estrutura da Grade">
          <FloatChecklistItem
            label="Inserir linha acima"
            title="Insere uma linha acima da célula de foco (remap de merges e alturas)."
            onClick={() => {
              insert("row", "before");
              close();
            }}
          />
          <FloatChecklistItem
            label="Inserir linha abaixo"
            title="Insere uma linha abaixo da célula de foco (remap de merges e alturas)."
            onClick={() => {
              insert("row", "after");
              close();
            }}
          />
          <FloatChecklistItem
            label="Inserir coluna à esquerda"
            title="Insere uma coluna à esquerda do foco (remap de merges e larguras)."
            onClick={() => {
              insert("col", "before");
              close();
            }}
          />
          <FloatChecklistItem
            label="Inserir coluna à direita"
            title="Insere uma coluna à direita do foco (remap de merges e larguras)."
            onClick={() => {
              insert("col", "after");
              close();
            }}
          />
          <FloatChecklistItem
            label="Mesclar"
            title="Mescla o retângulo selecionado (Ctrl+M)."
            disabled={!canMerge}
            onClick={() => {
              applyMerge("merge");
              close();
            }}
          />
          <FloatChecklistItem
            label="Desmesclar"
            title="Desfaz merges cobertos pela seleção (Ctrl+Shift+M)."
            disabled={!canUnmerge}
            onClick={() => {
              applyMerge("unmerge");
              close();
            }}
          />
        </FloatChecklist>
      )}
      renderStyle={(close) => (
        <div className="td-deck-ribbon__float-panel">
          <div className="td-deck-ribbon__tiles td-deck-ribbon__tiles--compact td-deck-ribbon__tiles--color-pickers">
            <TvRibbonColorPicker
              label="Fundo"
              variant="fill"
              showNoFill
              onChange={(color) => {
                patchSelectedCellsStyle({ backgroundColor: color });
                close();
              }}
              onNoFill={() => {
                patchSelectedCellsStyle({ backgroundColor: undefined });
                close();
              }}
            />
          </div>
          <FloatChecklist aria-label="Alinhamento das células">
            <FloatChecklistItem
              label="Esquerda"
              disabled={!cells.length}
              onClick={() => {
                patchSelectedCellsStyle({ textAlign: "left" });
                close();
              }}
            />
            <FloatChecklistItem
              label="Centro"
              disabled={!cells.length}
              onClick={() => {
                patchSelectedCellsStyle({ textAlign: "center" });
                close();
              }}
            />
            <FloatChecklistItem
              label="Direita"
              disabled={!cells.length}
              onClick={() => {
                patchSelectedCellsStyle({ textAlign: "right" });
                close();
              }}
            />
          </FloatChecklist>
        </div>
      )}
      renderData={(close) => (
        <button
          type="button"
          className="td-deck-ribbon__cascade-item"
          onClick={() => {
            openDataPanel();
            setSelectionPanelTab("data");
            close();
          }}
        >
          Vincular dados…
        </button>
      )}
    />
  );
}
