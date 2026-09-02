import {
  canMergeRect,
  type ComunicadoCanvasTableBlock,
} from "@delpi/tv-dashboard-presentation";

import { ComplexSelectionFloatToolbar } from "./ComplexSelectionFloatToolbar";
import { FloatChecklist, FloatChecklistItem } from "./FloatChecklist";
import { TvRibbonColorPicker } from "./deck/TvRibbonColorPicker";
import { useComunicadoEditor } from "./comunicadoEditorContext";
import { canUnmergeCanvasTableSelection } from "../utils/canvasTableMergeCommands";
import {
  applyCanvasTableMergeToBlock,
  insertCanvasTableBand,
  patchCanvasTableCellsStyle,
  type CanvasTableCellStylePatch,
} from "../utils/canvasTableSelectionCommands";

type Props = {
  block: ComunicadoCanvasTableBlock;
};

/**
 * Float da Grade — + estrutura/merge, pincel fill/alinhamento, funil dados.
 * Mesmo shell dos charts (ComplexSelectionFloatToolbar + AnchoredPanelPortal).
 * Chrome legado FloatChecklist permanece até E8.S18; lógica já via commands.
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
    updateBlock(block.id, insertCanvasTableBand({ block, axis, placement, focus }));
  }

  function applyMerge(mode: "merge" | "unmerge") {
    const patch = applyCanvasTableMergeToBlock({ block, selection: cells, mode });
    if (!patch) return;
    updateBlock(block.id, patch);
  }

  function applyCellsStyle(stylePatch: CanvasTableCellStylePatch) {
    if (!cells.length) return;
    updateBlock(block.id, {
      cells: patchCanvasTableCellsStyle({
        cells: block.cells,
        selection: cells,
        stylePatch,
      }),
    });
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
                applyCellsStyle({ backgroundColor: color });
                close();
              }}
              onNoFill={() => {
                applyCellsStyle({ backgroundColor: undefined });
                close();
              }}
            />
          </div>
          <FloatChecklist aria-label="Alinhamento das células">
            <FloatChecklistItem
              label="Esquerda"
              disabled={!cells.length}
              onClick={() => {
                applyCellsStyle({ textAlign: "left" });
                close();
              }}
            />
            <FloatChecklistItem
              label="Centro"
              disabled={!cells.length}
              onClick={() => {
                applyCellsStyle({ textAlign: "center" });
                close();
              }}
            />
            <FloatChecklistItem
              label="Direita"
              disabled={!cells.length}
              onClick={() => {
                applyCellsStyle({ textAlign: "right" });
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
