import type { ReactNode } from "react";
import {
  Columns3,
  Database,
  Eraser,
  Grid3x3,
  Heading2,
  Minus,
  MousePointer2,
  Paintbrush,
  RemoveFormatting,
  Rows3,
  Settings2,
  Square,
  TableCellsMerge,
  TableCellsSplit,
  type LucideIcon,
} from "lucide-react";
import {
  ComboboxNumberControl,
  NativeTextControl,
  ToolbarSelectField,
} from "@delpi/plugin-ui/index";
import {
  canMergeRect,
  canvasTableCellPlainText,
  canvasTablePresetOptions,
  mergeCanvasTableOptions,
  nextCanvasTableWhiteSpaceToggle,
  normalizeCanvasTableCell,
  normalizeCanvasTableCells,
  remapCanvasTableMerges,
  type CanvasTableCell,
  type CanvasTableCellKind,
  type CanvasTableStylePresetId,
} from "@delpi/tv-dashboard-presentation";

import { TV_DASHBOARD_HELP_TOOLTIPS } from "../../content/helpTooltips";
import {
  primaryCanvasTableCellRef,
  summarizeCanvasTableCellSelection,
} from "../../utils/canvasTableCellSelection";
import { canUnmergeCanvasTableSelection } from "../../utils/canvasTableMergeCommands";
import {
  applyCanvasTableMergeToBlock,
  clearCanvasTableSelectionContent,
  clearCanvasTableSelectionFormats,
  insertCanvasTableBand,
  patchCanvasTableCellsStyle,
} from "../../utils/canvasTableSelectionCommands";
import { CanvasTableCellFormatMenu } from "../CanvasTableCellFormatMenu";
import { useComunicadoEditor } from "../comunicadoEditorContext";
import { DeckRibbonGroup } from "../deck/DeckRibbonGroup";
import { DeckRibbonTile } from "../deck/DeckRibbonTile";
import { DeckRibbonTilePopover } from "../deck/DeckRibbonTilePopover";
import { TdRibbonSelect } from "../tdRibbonUi";
import { SelectionPaneSection } from "./SelectionPaneSection";
import type { SelectionSectionLayout } from "./types";

const H = TV_DASHBOARD_HELP_TOOLTIPS.ribbon;

const PRESET_TILES: {
  id: CanvasTableStylePresetId;
  label: string;
  icon: LucideIcon;
  hint: string;
}[] = [
  {
    id: "grid",
    label: "Grade",
    icon: Grid3x3,
    hint: "Preset clássico com bordas em todas as células.",
  },
  {
    id: "minimal",
    label: "Minimalista",
    icon: Minus,
    hint: "Visual limpo, sem faixas e com bordas discretas.",
  },
  {
    id: "banded",
    label: "Faixas",
    icon: Rows3,
    hint: "Linhas alternadas para leitura em listas densas.",
  },
];

const KIND_OPTIONS: { value: CanvasTableCellKind; label: string }[] = [
  { value: "text", label: "Texto" },
  { value: "number", label: "Número" },
  { value: "sparkline", label: "Sparkline" },
];

const ROW_PRESETS = [2, 3, 4, 5, 6, 8, 10] as const;
const COL_PRESETS = [2, 3, 4, 5, 6, 8] as const;

function resolveActiveCanvasTablePreset(
  opts: ReturnType<typeof mergeCanvasTableOptions>,
): CanvasTableStylePresetId | null {
  for (const id of ["grid", "minimal", "banded"] as const) {
    const preset = canvasTablePresetOptions(id);
    if (
      opts.bandedRows === Boolean(preset.bandedRows) &&
      opts.bandedColumns === Boolean(preset.bandedColumns) &&
      opts.headerStyle === (preset.headerStyle ?? "subtle") &&
      opts.borderStyle === (preset.borderStyle ?? "all")
    ) {
      return id;
    }
  }
  return null;
}

function wrapSection(
  layout: SelectionSectionLayout,
  groupId: string,
  title: string,
  hint: string | undefined,
  body: ReactNode,
  defaultOpen = true,
) {
  if (layout === "pane") {
    return (
      <SelectionPaneSection title={title} hint={hint} defaultOpen={defaultOpen}>
        {body}
      </SelectionPaneSection>
    );
  }
  return (
    <DeckRibbonGroup groupId={groupId} label={title} hint={hint}>
      {body}
    </DeckRibbonGroup>
  );
}

/** Grade — estrutura, design e inspetor da célula (paridade visual Tabela/KPI). */
export function CanvasTableSection({ layout }: { layout: SelectionSectionLayout }) {
  const { selected, updateSelected, selectedCanvasTableCell, updateBlock, openDataPanel } =
    useComunicadoEditor();
  if (!selected || selected.type !== "canvas_table") return null;
  const table = selected;

  const opts = mergeCanvasTableOptions(table.canvasTableOptions);
  const activePreset = resolveActiveCanvasTablePreset(opts);
  const cellSelection =
    selectedCanvasTableCell?.blockId === table.id ? selectedCanvasTableCell : null;
  const primaryCellRef = primaryCanvasTableCellRef(cellSelection);
  const selectedCell =
    primaryCellRef != null
      ? normalizeCanvasTableCell(table.cells[primaryCellRef.row]?.[primaryCellRef.col])
      : null;
  const multiCell = (cellSelection?.cells.length ?? 0) > 1;

  function patchSelectedCells(updater: (cell: CanvasTableCell) => CanvasTableCell) {
    if (!cellSelection?.cells.length) return;
    const cells = table.cells.map((row) => row.map((cell) => normalizeCanvasTableCell(cell)));
    for (const { row, col } of cellSelection.cells) {
      const current = cells[row]?.[col];
      if (current != null) {
        cells[row]![col] = updater(normalizeCanvasTableCell(current));
      }
    }
    updateBlock(table.id, { cells });
  }

  function applyCellsStyle(stylePatch: NonNullable<CanvasTableCell["style"]>) {
    if (!cellSelection?.cells.length) return;
    updateBlock(table.id, {
      cells: patchCanvasTableCellsStyle({
        cells: table.cells,
        selection: cellSelection.cells,
        stylePatch,
      }),
    });
  }

  function resolveSharedCellTextAlign(): string {
    if (!cellSelection?.cells.length) return "";
    const aligns = cellSelection.cells.map(({ row, col }) => {
      const cell = normalizeCanvasTableCell(table.cells[row]?.[col]);
      return cell.style?.textAlign ?? "";
    });
    const first = aligns[0] ?? "";
    return aligns.every((align) => align === first) ? first : "mixed";
  }

  function patchOptions(patch: Partial<typeof opts>) {
    updateSelected({
      canvasTableOptions: {
        ...(table.canvasTableOptions ?? {}),
        ...patch,
      },
    });
  }

  function applyPreset(preset: CanvasTableStylePresetId) {
    updateSelected({
      canvasTableOptions: {
        ...(table.canvasTableOptions ?? {}),
        ...canvasTablePresetOptions(preset),
      },
    });
  }

  function patchSelectedCell(next: CanvasTableCell) {
    if (!primaryCellRef) return;
    patchSelectedCells(() => next);
  }

  const canMergeSelection = Boolean(
    cellSelection?.cells.length && canMergeRect(cellSelection.cells, table.merges),
  );
  const canUnmergeSelection = Boolean(
    cellSelection?.cells.length &&
      canUnmergeCanvasTableSelection(table.merges, cellSelection.cells),
  );

  function applyMergeCommand(mode: "merge" | "unmerge") {
    if (!cellSelection?.cells.length) return;
    const patch = applyCanvasTableMergeToBlock({
      block: table,
      selection: cellSelection.cells,
      mode,
    });
    if (!patch) return;
    updateBlock(table.id, patch);
  }

  const structureFields = (
    <div className="td-deck-ribbon__frame-grid td-deck-ribbon__toolbar-row--dense">
      <label className="td-deck-ribbon__frame-field">
        <span className="td-deck-ribbon__field-label">Linhas</span>
        <ComboboxNumberControl
          className="td-deck-ribbon__number-combobox"
          compact
          square={false}
          min={1}
          max={20}
          value={table.rows}
          options={ROW_PRESETS}
          clamp={(value) => Math.max(1, Math.min(20, value))}
          portalScopeClassName="dashboard-tv-dashboard"
          aria-label="Linhas da Grade"
          onChange={(value) => {
            const rows = Math.max(1, Math.min(20, value));
            const merges = remapCanvasTableMerges(table.merges, rows, table.cols);
            updateSelected({
              rows,
              cells: normalizeCanvasTableCells(table.cells, rows, table.cols),
              merges: merges.length ? merges : undefined,
            });
          }}
        />
      </label>
      <label className="td-deck-ribbon__frame-field">
        <span className="td-deck-ribbon__field-label">Colunas</span>
        <ComboboxNumberControl
          className="td-deck-ribbon__number-combobox"
          compact
          square={false}
          min={1}
          max={12}
          value={table.cols}
          options={COL_PRESETS}
          clamp={(value) => Math.max(1, Math.min(12, value))}
          portalScopeClassName="dashboard-tv-dashboard"
          aria-label="Colunas da Grade"
          onChange={(value) => {
            const cols = Math.max(1, Math.min(12, value));
            const merges = remapCanvasTableMerges(table.merges, table.rows, cols);
            updateSelected({
              cols,
              cells: normalizeCanvasTableCells(table.cells, table.rows, cols),
              merges: merges.length ? merges : undefined,
            });
          }}
        />
      </label>
      <div className="td-deck-ribbon__tiles td-deck-ribbon__tiles--compact">
        <DeckRibbonTile
          icon={Rows3}
          label="Linha +"
          hint="Insere linha abaixo da célula de foco (Shift+clique = acima)."
          onClick={(event) => {
            updateSelected(
              insertCanvasTableBand({
                block: table,
                axis: "row",
                placement: event.shiftKey ? "before" : "after",
                focus: primaryCellRef,
              }),
            );
          }}
        />
        <DeckRibbonTile
          icon={Columns3}
          label="Coluna +"
          hint="Insere coluna à direita do foco (Shift+clique = à esquerda)."
          onClick={(event) => {
            updateSelected(
              insertCanvasTableBand({
                block: table,
                axis: "col",
                placement: event.shiftKey ? "before" : "after",
                focus: primaryCellRef,
              }),
            );
          }}
        />
      </div>
    </div>
  );

  const structureTiles = (
    <div className="td-deck-ribbon__tiles td-deck-ribbon__tiles--compact">
      {layout === "ribbon" ? (
        <DeckRibbonTilePopover
          icon={Grid3x3}
          label="Estrutura"
          hint="Linhas, colunas e tamanho da fonte da Grade."
          panelLabel="Linhas, colunas e fonte"
          panelClassName="td-deck-ribbon-tile-popover--wide"
        >
          {structureFields}
        </DeckRibbonTilePopover>
      ) : null}
      <DeckRibbonTile
        icon={Heading2}
        label="Cabeçalho"
        hint="Usa a primeira linha como cabeçalho da Grade."
        active={Boolean(table.headerRow)}
        onClick={() => updateSelected({ headerRow: !table.headerRow })}
      />
      <DeckRibbonTile
        icon={Database}
        label="Dados"
        hint={H.openDataPanel}
        onClick={() => openDataPanel()}
      />
    </div>
  );

  const structure =
    layout === "pane" ? (
      <>
        {structureFields}
        {structureTiles}
      </>
    ) : (
      structureTiles
    );

  const design = (
    <>
      <div className="td-deck-ribbon__tiles td-deck-ribbon__tiles--compact">
        {PRESET_TILES.map((preset) => (
          <DeckRibbonTile
            key={preset.id}
            icon={preset.icon}
            label={preset.label}
            hint={preset.hint}
            active={activePreset === preset.id}
            onClick={() => applyPreset(preset.id)}
          />
        ))}
      </div>
      <div className="td-deck-ribbon__tiles td-deck-ribbon__tiles--compact">
        <DeckRibbonTile
          icon={Rows3}
          label="Linhas alt."
          hint="Alterna o fundo das linhas para facilitar a leitura."
          active={opts.bandedRows}
          onClick={() => patchOptions({ bandedRows: !opts.bandedRows })}
        />
        <DeckRibbonTile
          icon={Columns3}
          label="Colunas alt."
          hint="Alterna o fundo das colunas para facilitar a leitura."
          active={opts.bandedColumns}
          onClick={() => patchOptions({ bandedColumns: !opts.bandedColumns })}
        />
      </div>
      <div className="td-deck-ribbon__border-pen td-deck-ribbon__toolbar-row--dense">
        <ToolbarSelectField
          label="Cabeçalho"
          value={opts.headerStyle}
          allowEmptyOption={false}
          options={[
            { value: "subtle", label: "Sutil" },
            { value: "accent", label: "Destaque" },
            { value: "none", label: "Nenhum" },
          ]}
          onChange={(value) => {
            if (value === "subtle" || value === "accent" || value === "none") {
              patchOptions({ headerStyle: value });
            }
          }}
        />
      </div>
      <div className="td-deck-ribbon__tiles td-deck-ribbon__tiles--compact">
        <DeckRibbonTile
          icon={Grid3x3}
          label="Todas"
          hint="Mostra todas as bordas da Grade."
          active={opts.borderStyle === "all"}
          onClick={() => patchOptions({ borderStyle: "all" })}
        />
        <DeckRibbonTile
          icon={Minus}
          label="Horizontais"
          hint="Mantém apenas as bordas horizontais."
          active={opts.borderStyle === "horizontal"}
          onClick={() => patchOptions({ borderStyle: "horizontal" })}
        />
        <DeckRibbonTile
          icon={Square}
          label="Nenhuma"
          hint="Remove as linhas separadoras das células."
          active={opts.borderStyle === "none"}
          onClick={() => patchOptions({ borderStyle: "none" })}
        />
      </div>
    </>
  );

  const cellAlign = resolveSharedCellTextAlign();

  const cellTypeFields =
    !multiCell && selectedCell ? (
      <>
        <div className="td-deck-ribbon__border-pen td-deck-ribbon__toolbar-row--dense">
          <label className="td-deck-ribbon__frame-field">
            <span className="td-deck-ribbon__field-label">Tipo</span>
            <TdRibbonSelect
              id="td-canvas-table-cell-kind"
              value={selectedCell.kind}
              aria-label="Tipo da célula"
              onChange={(value) => {
                if (value !== "text" && value !== "number" && value !== "sparkline") return;
                if (value === "text") {
                  patchSelectedCell({
                    kind: "text",
                    text: canvasTableCellPlainText(selectedCell),
                    style: selectedCell.style,
                  });
                  return;
                }
                if (value === "number") {
                  const n =
                    selectedCell.value ??
                    Number(String(selectedCell.text ?? "").replace(",", "."));
                  patchSelectedCell({
                    kind: "number",
                    value: Number.isFinite(n) ? n : 0,
                    format: selectedCell.format ?? "decimal",
                    text: selectedCell.text,
                    style: selectedCell.style,
                  });
                  return;
                }
                const series =
                  selectedCell.series?.length && selectedCell.series.length >= 5
                    ? selectedCell.series
                    : [1, 2, 3, 4, 5, 6];
                patchSelectedCell({
                  kind: "sparkline",
                  series,
                  value: series[series.length - 1] ?? null,
                  format: selectedCell.format ?? "decimal",
                  text: series.join(" "),
                  style: selectedCell.style,
                });
              }}
              options={KIND_OPTIONS}
            />
          </label>
        </div>
        {selectedCell.kind === "sparkline" ? (
          <label className="td-deck-ribbon__frame-field">
            <span className="td-deck-ribbon__field-label">Série (CSV)</span>
            <NativeTextControl
              id="td-canvas-table-cell-series"
              value={(selectedCell.series ?? []).join(", ")}
              onChange={(value) => {
                const series = value
                  .split(/[;,\s]+/)
                  .map((part) => Number(part.replace(",", ".")))
                  .filter((n) => Number.isFinite(n))
                  .slice(0, 60);
                patchSelectedCell({
                  ...selectedCell,
                  kind: "sparkline",
                  series,
                  value: series[series.length - 1] ?? selectedCell.value ?? null,
                  text: value,
                });
              }}
            />
          </label>
        ) : null}
      </>
    ) : null;

  const cellFormatMenu = selectedCell ? (
    <CanvasTableCellFormatMenu
      textAlign={
        cellAlign === "left" || cellAlign === "center" || cellAlign === "right"
          ? cellAlign
          : undefined
      }
      verticalAlign={selectedCell.style?.verticalAlign}
      whiteSpace={selectedCell.style?.whiteSpace}
      color={selectedCell.style?.color}
      backgroundColor={selectedCell.style?.backgroundColor}
      onAlign={(align) => applyCellsStyle({ textAlign: align })}
      onVerticalAlign={(align) => applyCellsStyle({ verticalAlign: align })}
      onToggleWrap={() =>
        applyCellsStyle({
          whiteSpace: nextCanvasTableWhiteSpaceToggle(selectedCell.style?.whiteSpace),
        })
      }
      onSetNowrap={() => applyCellsStyle({ whiteSpace: "nowrap" })}
      onColorChange={(color) => applyCellsStyle({ color })}
      onBackgroundChange={(color) => applyCellsStyle({ backgroundColor: color })}
      onNoFill={() => applyCellsStyle({ backgroundColor: undefined })}
    />
  ) : null;

  const cellActionTiles = (
    <div className="td-deck-ribbon__tiles td-deck-ribbon__tiles--compact">
      <DeckRibbonTile
        icon={TableCellsMerge}
        label="Mesclar"
        hint="Mescla o retângulo selecionado (Ctrl+M)."
        disabled={!canMergeSelection}
        onClick={() => applyMergeCommand("merge")}
      />
      <DeckRibbonTile
        icon={TableCellsSplit}
        label="Desmesclar"
        hint="Desfaz merges cobertos pela seleção (Ctrl+Shift+M)."
        disabled={!canUnmergeSelection}
        onClick={() => applyMergeCommand("unmerge")}
      />
      {layout === "ribbon" ? (
        <DeckRibbonTilePopover
          icon={Paintbrush}
          label="Formato"
          hint="Alinhamento, quebra e cores da célula."
          panelLabel="Formato da célula"
          panelVariant="menu"
          panelClassName="td-chart-float__popover--style"
        >
          {(close) => (
            <div
              onClick={(event) => {
                const target = event.target as HTMLElement | null;
                if (target?.closest("button[role='menuitemradio'],button[role='menuitemcheckbox']")) {
                  close();
                }
              }}
            >
              {cellFormatMenu}
            </div>
          )}
        </DeckRibbonTilePopover>
      ) : null}
      <DeckRibbonTile
        icon={Eraser}
        label="Limpar"
        hint="Limpa o conteúdo das células selecionadas (mantém estilo e binding)."
        disabled={!cellSelection?.cells.length}
        onClick={() => {
          if (!cellSelection?.cells.length) return;
          updateBlock(table.id, {
            cells: clearCanvasTableSelectionContent({
              cells: table.cells,
              selection: cellSelection.cells,
            }),
          });
        }}
      />
      <DeckRibbonTile
        icon={RemoveFormatting}
        label="Sem formato"
        hint="Remove estilos das células (mantém texto e binding)."
        disabled={!cellSelection?.cells.length}
        onClick={() => {
          if (!cellSelection?.cells.length) return;
          updateBlock(table.id, {
            cells: clearCanvasTableSelectionFormats({
              cells: table.cells,
              selection: cellSelection.cells,
            }),
          });
        }}
      />
    </div>
  );

  const cellRibbon =
    cellSelection?.cells.length && selectedCell ? (
      <div className="td-deck-ribbon__tiles td-deck-ribbon__tiles--compact td-canvas-table-cell-ribbon">
        {layout === "ribbon" && !multiCell ? (
          <DeckRibbonTilePopover
            icon={Settings2}
            label="Tipo"
            hint="Tipo de conteúdo da célula (texto, número ou sparkline)."
            panelLabel="Tipo da célula"
            panelClassName="td-deck-ribbon-tile-popover--wide"
          >
            {cellTypeFields}
          </DeckRibbonTilePopover>
        ) : null}
        {cellActionTiles}
      </div>
    ) : (
      <div className="td-deck-ribbon__tiles td-deck-ribbon__tiles--compact">
        <DeckRibbonTile
          icon={MousePointer2}
          label="Selecione"
          hint="Clique nas células. Ctrl alterna; Shift seleciona intervalo."
          disabled
        />
      </div>
    );

  const cellInspector =
    layout === "pane" ? (
      <>
        <p className="td-subtitle">
          {cellSelection?.cells.length
            ? summarizeCanvasTableCellSelection(cellSelection)
            : "Selecione células na Grade (Ctrl+clique para múltiplas; Shift+clique para intervalo)."}
        </p>
        {cellTypeFields}
        {cellSelection?.cells.length ? (
          <>
            {cellActionTiles}
            {cellFormatMenu}
          </>
        ) : null}
      </>
    ) : (
      cellRibbon
    );

  return (
    <>
      {wrapSection(layout, "canvas-table", "Grade", H.canvasTable, structure, true)}
      {wrapSection(layout, "canvas-table-design", "Estilo", H.canvasTablePreset, design, true)}
      {wrapSection(
        layout,
        "canvas-table-cell",
        "Célula",
        H.canvasTableCell,
        cellInspector,
        Boolean(cellSelection?.cells.length),
      )}
    </>
  );
}
