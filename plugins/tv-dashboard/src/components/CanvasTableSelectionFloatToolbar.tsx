import {
  canMergeRect,
  canvasTablePresetOptions,
  mergeCanvasTableOptions,
  type ComunicadoCanvasTableBlock,
} from "@delpi/tv-dashboard-presentation";

import { ComplexSelectionFloatToolbar } from "./ComplexSelectionFloatToolbar";
import {
  CanvasTableBlockStylesMenu,
  type CanvasTableBlockStyleActionId,
} from "./CanvasTableBlockStylesMenu";
import { CanvasTableDataMenu } from "./CanvasTableDataMenu";
import {
  CanvasTableStructureMenu,
  type CanvasTableStructureActionId,
} from "./CanvasTableStructureMenu";
import { useComunicadoEditor } from "./comunicadoEditorContext";
import { canUnmergeCanvasTableSelection } from "../utils/canvasTableMergeCommands";
import {
  applyCanvasTableMergeToBlock,
  insertCanvasTableBand,
} from "../utils/canvasTableSelectionCommands";

type Props = {
  block: ComunicadoCanvasTableBlock;
};

/**
 * Float da Grade — + estrutura, pincel bloco, funil dados.
 * Chrome chart/table (`td-chart-*`); dispatcher célula em S22.
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
  const opts = mergeCanvasTableOptions(block.canvasTableOptions);

  function insert(axis: "row" | "col", placement: "before" | "after") {
    updateBlock(block.id, insertCanvasTableBand({ block, axis, placement, focus }));
  }

  function applyMerge(mode: "merge" | "unmerge") {
    const patch = applyCanvasTableMergeToBlock({ block, selection: cells, mode });
    if (!patch) return;
    updateBlock(block.id, patch);
  }

  function onStructure(actionId: CanvasTableStructureActionId) {
    switch (actionId) {
      case "insert-row-before":
        insert("row", "before");
        break;
      case "insert-row-after":
        insert("row", "after");
        break;
      case "insert-col-before":
        insert("col", "before");
        break;
      case "insert-col-after":
        insert("col", "after");
        break;
      case "merge":
        applyMerge("merge");
        break;
      case "unmerge":
        applyMerge("unmerge");
        break;
      default:
        break;
    }
  }

  function patchOptions(patch: Partial<typeof opts>) {
    updateBlock(block.id, {
      canvasTableOptions: {
        ...(block.canvasTableOptions ?? {}),
        ...patch,
      },
    });
  }

  function onBlockStyle(actionId: CanvasTableBlockStyleActionId) {
    switch (actionId) {
      case "preset-grid":
      case "preset-minimal":
      case "preset-banded": {
        const preset = actionId.replace("preset-", "") as "grid" | "minimal" | "banded";
        updateBlock(block.id, {
          canvasTableOptions: {
            ...(block.canvasTableOptions ?? {}),
            ...canvasTablePresetOptions(preset),
          },
        });
        break;
      }
      case "toggle-banded-rows":
        patchOptions({ bandedRows: !opts.bandedRows });
        break;
      case "toggle-banded-cols":
        patchOptions({ bandedColumns: !opts.bandedColumns });
        break;
      case "header-subtle":
        patchOptions({ headerStyle: "subtle" });
        break;
      case "header-accent":
        patchOptions({ headerStyle: "accent" });
        break;
      case "header-none":
        patchOptions({ headerStyle: "none" });
        break;
      case "borders-all":
        patchOptions({ borderStyle: "all" });
        break;
      case "borders-horizontal":
        patchOptions({ borderStyle: "horizontal" });
        break;
      case "borders-none":
        patchOptions({ borderStyle: "none" });
        break;
      default:
        break;
    }
  }

  return (
    <ComplexSelectionFloatToolbar
      blockId={block.id}
      frame={block.frame}
      labels={{
        elements: "Estrutura da Grade",
        style: "Estilo da Grade",
        data: "Dados da Grade",
      }}
      renderElements={(close) => (
        <CanvasTableStructureMenu
          canMerge={canMerge}
          canUnmerge={canUnmerge}
          onSelect={(actionId) => {
            onStructure(actionId);
            close();
          }}
        />
      )}
      renderStyle={(close) => (
        <CanvasTableBlockStylesMenu
          options={block.canvasTableOptions}
          headerRow={Boolean(block.headerRow)}
          onToggleHeaderRow={() => {
            updateBlock(block.id, { headerRow: !block.headerRow });
            close();
          }}
          onSelect={(actionId) => {
            onBlockStyle(actionId);
            close();
          }}
        />
      )}
      renderData={(close) => (
        <CanvasTableDataMenu
          onSelect={() => {
            openDataPanel();
            setSelectionPanelTab("data");
            close();
          }}
        />
      )}
    />
  );
}
