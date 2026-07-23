import {
  NativeCheckboxControl,
  NativeSelectControl,
  NativeTextControl,
} from "@delpi/plugin-ui/index";
import {
  canvasTableCellPlainText,
  canvasTablePresetOptions,
  mergeCanvasTableOptions,
  normalizeCanvasTableCell,
  normalizeCanvasTableCells,
  type CanvasTableCell,
  type CanvasTableCellKind,
  type CanvasTableNumberFormat,
  type CanvasTableStylePresetId,
} from "@delpi/tv-dashboard-presentation";

import { TV_DASHBOARD_HELP_TOOLTIPS } from "../../content/helpTooltips";
import { useComunicadoEditor } from "../comunicadoEditorContext";
import { DeckField } from "../deck/DeckField";
import { DeckRibbonGroup } from "../deck/DeckRibbonGroup";
import { SelectionPaneSection } from "./SelectionPaneSection";
import type { SelectionSectionLayout } from "./types";

const H = TV_DASHBOARD_HELP_TOOLTIPS.ribbon;

const PRESET_OPTIONS: { value: CanvasTableStylePresetId; label: string }[] = [
  { value: "grid", label: "Grade" },
  { value: "minimal", label: "Minimalista" },
  { value: "banded", label: "Faixas" },
];

const KIND_OPTIONS: { value: CanvasTableCellKind; label: string }[] = [
  { value: "text", label: "Texto" },
  { value: "number", label: "Número" },
  { value: "sparkline", label: "Sparkline" },
];

const FORMAT_OPTIONS: { value: CanvasTableNumberFormat; label: string }[] = [
  { value: "plain", label: "Simples" },
  { value: "integer", label: "Inteiro" },
  { value: "decimal", label: "Decimal" },
  { value: "percent", label: "Percentual" },
  { value: "currency", label: "Moeda" },
];

/** Grade — estrutura, design e inspetor da célula selecionada. */
export function CanvasTableSection({ layout }: { layout: SelectionSectionLayout }) {
  const { selected, updateSelected, selectedCanvasTableCell, updateBlock } = useComunicadoEditor();
  if (!selected || selected.type !== "canvas_table") return null;
  const table = selected;

  const opts = mergeCanvasTableOptions(table.canvasTableOptions);
  const cellSel =
    selectedCanvasTableCell?.blockId === table.id ? selectedCanvasTableCell : null;
  const selectedCell =
    cellSel != null
      ? normalizeCanvasTableCell(table.cells[cellSel.row]?.[cellSel.col])
      : null;

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
    if (!cellSel) return;
    const cells = table.cells.map((row) =>
      row.map((cell) => normalizeCanvasTableCell(cell)),
    );
    cells[cellSel.row]![cellSel.col] = next;
    updateBlock(table.id, { cells });
  }

  const structure = (
    <>
      <DeckField id="td-canvas-table-rows" label="Linhas">
        <NativeTextControl
          id="td-canvas-table-rows"
          type="number"
          min={1}
          max={20}
          value={table.rows}
          onChange={(value) => {
            const rows = Math.max(1, Math.min(20, Number(value) || 1));
            updateSelected({
              rows,
              cells: normalizeCanvasTableCells(table.cells, rows, table.cols),
            });
          }}
        />
      </DeckField>
      <DeckField id="td-canvas-table-cols" label="Colunas">
        <NativeTextControl
          id="td-canvas-table-cols"
          type="number"
          min={1}
          max={12}
          value={table.cols}
          onChange={(value) => {
            const cols = Math.max(1, Math.min(12, Number(value) || 1));
            updateSelected({
              cols,
              cells: normalizeCanvasTableCells(table.cells, table.rows, cols),
            });
          }}
        />
      </DeckField>
      <NativeCheckboxControl
        id="td-canvas-table-header-row"
        className="td-deck-inspector__checkbox"
        checked={table.headerRow ?? false}
        label="Primeira linha como cabeçalho"
        onChange={(checked) => updateSelected({ headerRow: checked })}
      />
      <DeckField id="td-canvas-table-font-size" label="Tamanho da fonte">
        <NativeTextControl
          id="td-canvas-table-font-size"
          type="number"
          min={8}
          max={96}
          value={opts.fontSize}
          onChange={(value) => {
            const fontSize = Math.max(8, Math.min(96, Number(value) || 18));
            updateSelected({
              canvasTableOptions: {
                ...(table.canvasTableOptions ?? {}),
                fontSize,
              },
              style: { ...(table.style ?? {}), fontSize },
            });
          }}
        />
      </DeckField>
    </>
  );

  const design = (
    <>
      <DeckField id="td-canvas-table-preset" label="Preset">
        <NativeSelectControl
          id="td-canvas-table-preset"
          value=""
          placeholderOption="Aplicar preset…"
          onChange={(value) => {
            if (value === "grid" || value === "minimal" || value === "banded") {
              applyPreset(value);
            }
          }}
          options={PRESET_OPTIONS}
        />
      </DeckField>
      <NativeCheckboxControl
        id="td-canvas-table-banded-rows"
        className="td-deck-inspector__checkbox"
        checked={opts.bandedRows}
        label="Linhas alternadas"
        onChange={(checked) => patchOptions({ bandedRows: checked })}
      />
      <NativeCheckboxControl
        id="td-canvas-table-banded-cols"
        className="td-deck-inspector__checkbox"
        checked={opts.bandedColumns}
        label="Colunas alternadas"
        onChange={(checked) => patchOptions({ bandedColumns: checked })}
      />
      <DeckField id="td-canvas-table-header-style" label="Estilo do cabeçalho">
        <NativeSelectControl
          id="td-canvas-table-header-style"
          value={opts.headerStyle}
          onChange={(value) => {
            if (value === "subtle" || value === "accent" || value === "none") {
              patchOptions({ headerStyle: value });
            }
          }}
          options={[
            { value: "subtle", label: "Sutil" },
            { value: "accent", label: "Destaque" },
            { value: "none", label: "Nenhum" },
          ]}
        />
      </DeckField>
      <DeckField id="td-canvas-table-border-style" label="Bordas">
        <NativeSelectControl
          id="td-canvas-table-border-style"
          value={opts.borderStyle}
          onChange={(value) => {
            if (value === "all" || value === "horizontal" || value === "none") {
              patchOptions({ borderStyle: value });
            }
          }}
          options={[
            { value: "all", label: "Todas" },
            { value: "horizontal", label: "Horizontais" },
            { value: "none", label: "Nenhuma" },
          ]}
        />
      </DeckField>
    </>
  );

  const cellInspector =
    cellSel && selectedCell ? (
      <>
        <p className="td-subtitle">
          Célula {cellSel.row + 1}×{cellSel.col + 1}
        </p>
        <DeckField id="td-canvas-table-cell-kind" label="Tipo">
          <NativeSelectControl
            id="td-canvas-table-cell-kind"
            value={selectedCell.kind}
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
        </DeckField>
        {(selectedCell.kind === "number" || selectedCell.kind === "sparkline") && (
          <DeckField id="td-canvas-table-cell-format" label="Formato">
            <NativeSelectControl
              id="td-canvas-table-cell-format"
              value={selectedCell.format ?? "decimal"}
              onChange={(value) => {
                if (
                  value === "plain" ||
                  value === "integer" ||
                  value === "decimal" ||
                  value === "percent" ||
                  value === "currency"
                ) {
                  patchSelectedCell({ ...selectedCell, format: value });
                }
              }}
              options={FORMAT_OPTIONS}
            />
          </DeckField>
        )}
        {selectedCell.kind === "sparkline" && (
          <DeckField id="td-canvas-table-cell-series" label="Série (CSV)">
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
          </DeckField>
        )}
        <DeckField id="td-canvas-table-cell-align" label="Alinhamento">
          <NativeSelectControl
            id="td-canvas-table-cell-align"
            value={selectedCell.style?.textAlign ?? ""}
            onChange={(value) => {
              const textAlign =
                value === "left" || value === "center" || value === "right" ? value : undefined;
              patchSelectedCell({
                ...selectedCell,
                style: {
                  ...(selectedCell.style ?? {}),
                  ...(textAlign ? { textAlign } : { textAlign: undefined }),
                },
              });
            }}
            options={[
              { value: "", label: "Herdar" },
              { value: "left", label: "Esquerda" },
              { value: "center", label: "Centro" },
              { value: "right", label: "Direita" },
            ]}
          />
        </DeckField>
        <DeckField id="td-canvas-table-cell-color" label="Cor do texto">
          <NativeTextControl
            id="td-canvas-table-cell-color"
            value={selectedCell.style?.color ?? ""}
            placeholder="#0f172a"
            onChange={(value) => {
              patchSelectedCell({
                ...selectedCell,
                style: {
                  ...(selectedCell.style ?? {}),
                  color: value.trim() || undefined,
                },
              });
            }}
          />
        </DeckField>
        <DeckField id="td-canvas-table-cell-bg" label="Fundo da célula">
          <NativeTextControl
            id="td-canvas-table-cell-bg"
            value={selectedCell.style?.backgroundColor ?? ""}
            placeholder="#ffffff"
            onChange={(value) => {
              patchSelectedCell({
                ...selectedCell,
                style: {
                  ...(selectedCell.style ?? {}),
                  backgroundColor: value.trim() || undefined,
                },
              });
            }}
          />
        </DeckField>
      </>
    ) : (
      <p className="td-subtitle">Selecione uma célula na Grade para editar tipo e estilo.</p>
    );

  if (layout === "pane") {
    return (
      <>
        <SelectionPaneSection title="Grade" hint={H.canvasTable} defaultOpen>
          {structure}
        </SelectionPaneSection>
        <SelectionPaneSection title="Estilo da Grade" hint={H.canvasTablePreset} defaultOpen>
          {design}
        </SelectionPaneSection>
        <SelectionPaneSection title="Célula" hint={H.canvasTableCell} defaultOpen={Boolean(cellSel)}>
          {cellInspector}
        </SelectionPaneSection>
      </>
    );
  }

  return (
    <>
      <DeckRibbonGroup groupId="canvas-table" label="Grade" hint={H.canvasTable}>
        {structure}
      </DeckRibbonGroup>
      <DeckRibbonGroup groupId="canvas-table-design" label="Estilo" hint={H.canvasTablePreset}>
        {design}
      </DeckRibbonGroup>
      <DeckRibbonGroup groupId="canvas-table-cell" label="Célula" hint={H.canvasTableCell}>
        {cellInspector}
      </DeckRibbonGroup>
    </>
  );
}
