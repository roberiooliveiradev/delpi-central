import {
  DECK_COLOR_BORDER,
  DECK_COLOR_SURFACE,
  DECK_TABLE_DEFAULTS,
  NativeTextControl,
} from "@delpi/plugin-ui/index";
import {
  deleteTablePart,
  getTablePartState,
  mergeComunicadoTableOptions,
  mergeTablePartsWithOptions,
  partsToTableOptions,
  resolveTableFrameStyle,
  serializeTablePartRef,
  tablePartAllowsDelete,
  upsertTablePartState,
  applyTablePartStyleToSiblingParts,
  type ComunicadoTablePartRef,
  type ComunicadoTableViewBlock,
} from "@delpi/tv-dashboard-presentation";

import { useComunicadoEditor } from "./comunicadoEditorContext";
import { PartInspectorToolbar } from "./PartInspectorToolbar";
import { TvRibbonColorPicker } from "./deck/TvRibbonColorPicker";
import { DeckField } from "./deck/DeckField";
import { DeckPropertySection } from "./deck/DeckPropertySection";

type Props = {
  pane?: boolean;
  block: ComunicadoTableViewBlock;
};

function tablePartLabel(part: ComunicadoTablePartRef): string {
  switch (part.kind) {
    case "frame":
      return "Moldura";
    case "title":
      return "Título";
    case "header":
      return "Cabeçalho";
    case "headerCell":
      return `Coluna ${part.colIndex + 1}`;
    case "cell":
      return `Célula ${part.rowIndex + 1}:${part.colIndex + 1}`;
    default:
      return serializeTablePartRef(part);
  }
}

type PartStylePatch = {
  fill?: string;
  color?: string;
  stroke?: string;
  strokeWidth?: number;
  borderRadius?: number;
  fontWeight?: string | number;
};

/** Inspetor da parte selecionada da tabela — espelho de KpiPartInspector / ChartPartInspector. */
export function TablePartInspector({ pane = false, block }: Props) {
  const { selectedTablePart, clearTablePartSelection, updateSelected } = useComunicadoEditor();

  if (!selectedTablePart) return null;

  const options = mergeComunicadoTableOptions({
    ...block.tableOptions,
    ...partsToTableOptions(block.tableParts),
  }, block.tablePreset);
  const partState = getTablePartState(block.tableParts, selectedTablePart);
  const canDelete = tablePartAllowsDelete(selectedTablePart);
  const frame = resolveTableFrameStyle(block.tableParts);

  const persistPart = (patch: {
    content?: string;
    style?: PartStylePatch;
    visible?: boolean;
  }) => {
    const nextParts = upsertTablePartState(block.tableParts, selectedTablePart, patch);
    const nextOptions = mergeComunicadoTableOptions({
      ...options,
      ...partsToTableOptions(nextParts),
    }, block.tablePreset);
    const nextStyle = { ...block.style };
    if (selectedTablePart.kind === "title" && patch.content !== undefined) {
      nextOptions.title = patch.content.trim() || undefined;
      nextOptions.showTitle = true;
    }
    if (selectedTablePart.kind === "frame" && patch.style?.borderRadius != null) {
      nextStyle.borderRadius = patch.style.borderRadius;
    }
    updateSelected({
      tableOptions: nextOptions,
      tableParts: mergeTablePartsWithOptions(nextParts, nextOptions),
      style: nextStyle,
    } as Partial<typeof block>);
  };

  const removePart = () => {
    const result = deleteTablePart(block.tableParts, selectedTablePart, options);
    updateSelected({
      tableParts: result.parts,
      tableOptions: result.options,
    } as Partial<typeof block>);
    clearTablePartSelection();
  };

  const showTextPaint =
    selectedTablePart.kind === "title" ||
    selectedTablePart.kind === "header" ||
    selectedTablePart.kind === "headerCell" ||
    selectedTablePart.kind === "cell";

  const defaultFill =
    selectedTablePart.kind === "header" || selectedTablePart.kind === "headerCell"
      ? options.headerBg ?? DECK_TABLE_DEFAULTS.headerBg
      : selectedTablePart.kind === "title"
        ? "transparent"
        : options.cellBg ?? DECK_TABLE_DEFAULTS.cellBg;

  const defaultColor =
    selectedTablePart.kind === "header" || selectedTablePart.kind === "headerCell"
      ? options.headerTextColor ?? DECK_TABLE_DEFAULTS.headerTextColor
      : options.cellTextColor ?? DECK_TABLE_DEFAULTS.cellTextColor;

  return (
    <DeckPropertySection
      pane={pane}
      title={`Parte: ${tablePartLabel(selectedTablePart)}`}
      hint="Ajuste esta parte. Contorno da moldura também na aba Forma."
      defaultOpen
    >
      <PartInspectorToolbar
        onBack={clearTablePartSelection}
        backLabel="Voltar aos elementos"
        onHide={canDelete ? removePart : undefined}
        hideLabel="Ocultar parte"
      />

      {selectedTablePart.kind === "title" ? (
        <DeckField id="td-table-part-title" label="Texto do título">
          <NativeTextControl
            id="td-table-part-title"
            value={partState?.content ?? options.title ?? ""}
            placeholder="Ex.: Top produtos"
            onChange={(value) => persistPart({ content: value, visible: true })}
          />
        </DeckField>
      ) : null}

      {selectedTablePart.kind === "frame" ? (
        <>
          <DeckField id="td-table-part-frame-fill" label="Fundo da moldura">
            <TvRibbonColorPicker
              inline
              variant="fill"
              label="Fundo da moldura"
              value={partState?.style?.fill ?? frame.fill ?? DECK_COLOR_SURFACE}
              onChange={(color) => persistPart({ style: { fill: color } })}
            />
          </DeckField>
          <DeckField id="td-table-part-frame-stroke" label="Contorno do bloco">
            <TvRibbonColorPicker
              inline
              variant="outline"
              label="Contorno do bloco"
              value={partState?.style?.stroke ?? frame.stroke ?? DECK_COLOR_BORDER}
              onChange={(color) => persistPart({ style: { stroke: color } })}
            />
          </DeckField>
          <div className="td-part-inspector-toolbar__fields-row">
            <DeckField id="td-table-part-frame-stroke-width" label="Espessura">
              <NativeTextControl
                id="td-table-part-frame-stroke-width"
                type="number"
                min={0}
                max={12}
                step={0.5}
                value={partState?.style?.strokeWidth ?? frame.strokeWidth ?? 1}
                onChange={(value) => persistPart({ style: { strokeWidth: Number(value) || 0 } })}
              />
            </DeckField>
            <DeckField id="td-table-part-frame-radius" label="Cantos (px)">
              <NativeTextControl
                id="td-table-part-frame-radius"
                type="number"
                min={0}
                max={64}
                value={partState?.style?.borderRadius ?? frame.borderRadius ?? 0}
                onChange={(value) =>
                  persistPart({ style: { borderRadius: Math.max(0, Number(value) || 0) } })
                }
              />
            </DeckField>
          </div>
        </>
      ) : null}

      {showTextPaint ? (
        <>
          <DeckField id="td-table-part-fill" label="Fundo">
            <TvRibbonColorPicker
              inline
              variant="fill"
              label="Fundo"
              value={partState?.style?.fill ?? defaultFill}
              onChange={(color) => persistPart({ style: { fill: color } })}
            />
          </DeckField>
          <DeckField id="td-table-part-color" label="Texto">
            <TvRibbonColorPicker
              inline
              variant="text"
              contrastBackground={partState?.style?.fill ?? defaultFill}
              label="Texto"
              value={partState?.style?.color ?? defaultColor}
              onChange={(color) => persistPart({ style: { color } })}
            />
          </DeckField>
        </>
      ) : null}

      {selectedTablePart.kind === "cell" || selectedTablePart.kind === "headerCell" ? (
        <button
          type="button"
          className="td-deck-btn"
          onClick={() => {
            const rows = block.resolved?.table?.rows?.length ?? 0;
            const cols = block.resolved?.table?.columns?.length ?? 0;
            const style = partState?.style ?? {};
            const nextParts = applyTablePartStyleToSiblingParts(block.tableParts, selectedTablePart, style, {
              rowCount: rows,
              colCount: cols,
            });
            updateSelected({
              tableParts: nextParts,
              tableOptions: mergeComunicadoTableOptions({
                ...options,
                ...partsToTableOptions(nextParts),
              }, block.tablePreset),
            } as Partial<typeof block>);
          }}
        >
          {selectedTablePart.kind === "cell"
            ? "Aplicar estilo a todas as células"
            : "Aplicar estilo a todos os cabeçalhos"}
        </button>
      ) : null}
    </DeckPropertySection>
  );
}
