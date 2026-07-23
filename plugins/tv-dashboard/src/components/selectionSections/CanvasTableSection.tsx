import type { ReactNode } from "react";
import {
  AlignCenter,
  AlignLeft,
  AlignRight,
  Columns3,
  Database,
  Grid3x3,
  Heading2,
  Minus,
  Rows3,
  Square,
  type LucideIcon,
} from "lucide-react";
import {
  ComboboxNumberControl,
  NativeTextControl,
  ToolbarSelectField,
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
import { DeckRibbonGroup } from "../deck/DeckRibbonGroup";
import { DeckRibbonTile } from "../deck/DeckRibbonTile";
import { TvRibbonColorPicker } from "../deck/TvRibbonColorPicker";
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

const FORMAT_OPTIONS: { value: CanvasTableNumberFormat; label: string }[] = [
  { value: "plain", label: "Simples" },
  { value: "integer", label: "Inteiro" },
  { value: "decimal", label: "Decimal" },
  { value: "percent", label: "Percentual" },
  { value: "currency", label: "Moeda" },
];

const FONT_SIZE_PRESETS = [10, 12, 14, 16, 18, 20, 24, 28, 32] as const;
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
              updateSelected({
                rows,
                cells: normalizeCanvasTableCells(table.cells, rows, table.cols),
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
              updateSelected({
                cols,
                cells: normalizeCanvasTableCells(table.cells, table.rows, cols),
              });
            }}
          />
        </label>
        <label className="td-deck-ribbon__frame-field">
          <span className="td-deck-ribbon__field-label">Fonte (px)</span>
          <ComboboxNumberControl
            className="td-deck-ribbon__number-combobox"
            compact
            square={false}
            min={8}
            max={96}
            value={opts.fontSize}
            options={FONT_SIZE_PRESETS}
            clamp={(value) => Math.max(8, Math.min(96, value))}
            portalScopeClassName="dashboard-tv-dashboard"
            aria-label="Tamanho da fonte da Grade"
            onChange={(fontSize) => {
              updateSelected({
                canvasTableOptions: {
                  ...(table.canvasTableOptions ?? {}),
                  fontSize,
                },
                style: { ...(table.style ?? {}), fontSize },
              });
            }}
          />
        </label>
      </div>
      <div className="td-deck-ribbon__tiles td-deck-ribbon__tiles--compact">
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
    </>
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

  const cellAlign = selectedCell?.style?.textAlign ?? "";

  const cellInspector =
    cellSel && selectedCell ? (
      <>
        <p className="td-subtitle">
          Célula {cellSel.row + 1}×{cellSel.col + 1}
        </p>
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
          {(selectedCell.kind === "number" || selectedCell.kind === "sparkline") && (
            <label className="td-deck-ribbon__frame-field">
              <span className="td-deck-ribbon__field-label">Formato</span>
              <TdRibbonSelect
                id="td-canvas-table-cell-format"
                value={selectedCell.format ?? "decimal"}
                aria-label="Formato numérico"
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
            </label>
          )}
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
        <div className="td-deck-ribbon__tiles td-deck-ribbon__tiles--compact">
          <DeckRibbonTile
            icon={AlignLeft}
            label="Esquerda"
            active={cellAlign === "left"}
            onClick={() =>
              patchSelectedCell({
                ...selectedCell,
                style: { ...(selectedCell.style ?? {}), textAlign: "left" },
              })
            }
          />
          <DeckRibbonTile
            icon={AlignCenter}
            label="Centro"
            active={cellAlign === "center"}
            onClick={() =>
              patchSelectedCell({
                ...selectedCell,
                style: { ...(selectedCell.style ?? {}), textAlign: "center" },
              })
            }
          />
          <DeckRibbonTile
            icon={AlignRight}
            label="Direita"
            active={cellAlign === "right"}
            onClick={() =>
              patchSelectedCell({
                ...selectedCell,
                style: { ...(selectedCell.style ?? {}), textAlign: "right" },
              })
            }
          />
        </div>
        <div className="td-deck-ribbon__tiles td-deck-ribbon__tiles--compact td-deck-ribbon__tiles--color-pickers">
          <TvRibbonColorPicker
            label="Texto"
            variant="text"
            showAutomatic
            value={selectedCell.style?.color}
            onChange={(color) =>
              patchSelectedCell({
                ...selectedCell,
                style: { ...(selectedCell.style ?? {}), color },
              })
            }
            onAutomatic={(color) =>
              patchSelectedCell({
                ...selectedCell,
                style: { ...(selectedCell.style ?? {}), color },
              })
            }
          />
          <TvRibbonColorPicker
            label="Fundo"
            variant="fill"
            showNoFill
            value={selectedCell.style?.backgroundColor}
            onChange={(color) =>
              patchSelectedCell({
                ...selectedCell,
                style: { ...(selectedCell.style ?? {}), backgroundColor: color },
              })
            }
            onNoFill={() =>
              patchSelectedCell({
                ...selectedCell,
                style: { ...(selectedCell.style ?? {}), backgroundColor: undefined },
              })
            }
          />
        </div>
      </>
    ) : (
      <p className="td-subtitle">Selecione uma célula na Grade para editar tipo e estilo.</p>
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
        Boolean(cellSel),
      )}
    </>
  );
}
