import { useMemo, useState } from "react";
import {
  AlignCenter,
  AlignLeft,
  AlignRight,
  Columns3,
  Database,
  Grid3x3,
  Rows3,
  WrapText,
} from "lucide-react";
import {
  distributeTableProjectionColumnWidths,
  mergeComunicadoTableOptions,
  mergeTablePartsWithOptions,
  resizeTableProjectionColumns,
  resolveEditableTableProjectionColumns,
  selectedTableProjectionColumnKeys,
  type ComunicadoBlock,
  type ComunicadoTableOptions,
  type ComunicadoTableViewBlock,
} from "@delpi/tv-dashboard-presentation";
import { ComboboxNumberControl } from "@delpi/plugin-ui/index";

import { TV_DASHBOARD_HELP_TOOLTIPS } from "../../content/helpTooltips";
import { useComunicadoEditor } from "../comunicadoEditorContext";
import { DeckRibbonGroup } from "../deck/DeckRibbonGroup";
import { DeckRibbonTile } from "../deck/DeckRibbonTile";
import { TdRibbonSelect } from "../tdRibbonUi";
import { SelectionPaneSection } from "./SelectionPaneSection";
import type { SelectionSectionLayout } from "./types";

const H = TV_DASHBOARD_HELP_TOOLTIPS.ribbon;
const D = TV_DASHBOARD_HELP_TOOLTIPS.data;
const TABLE_ROW_HEIGHT_PRESETS = [20, 24, 28, 32, 40, 48] as const;
const TABLE_COLUMN_WIDTH_PRESETS = [10, 15, 20, 25, 33.3, 50, 75] as const;

function useTableLayoutControls() {
  const { selected, updateSelected, openDataPanel } = useComunicadoEditor();
  if (!selected || selected.type !== "table_view") return null;

  const block = selected as ComunicadoTableViewBlock;
  const options = mergeComunicadoTableOptions(block.tableOptions, block.tablePreset);

  const applyOptions = (patch: Partial<ComunicadoTableOptions>) => {
    const nextOptions = {
      ...mergeComunicadoTableOptions(block.tableOptions, block.tablePreset),
      ...patch,
    };
    updateSelected({
      tableOptions: nextOptions,
      tableParts: mergeTablePartsWithOptions(block.tableParts, nextOptions),
    } as Partial<ComunicadoBlock>);
  };

  return { block, options, applyOptions, updateSelected, openDataPanel };
}

/** Dados + toggle de grade (aba Layout). */
export function TableLayoutDataSection({ layout }: { layout: SelectionSectionLayout }) {
  const ctrl = useTableLayoutControls();
  if (!ctrl) return null;
  const { options, applyOptions, openDataPanel } = ctrl;

  const tiles = (
    <div className="td-deck-ribbon__tiles td-deck-ribbon__tiles--compact">
      <DeckRibbonTile
        icon={Database}
        label="Selecionar dados"
        hint="Abre o painel de fontes de dados."
        onClick={() => openDataPanel()}
      />
      <DeckRibbonTile
        icon={Grid3x3}
        label="Grade"
        hint="Exibe ou oculta as linhas de grade (bordas)."
        active={options.showBorders !== false}
        onClick={() => applyOptions({ showBorders: options.showBorders === false })}
      />
    </div>
  );

  if (layout === "pane") {
    return (
      <SelectionPaneSection title="Tabela" hint={H.tableData ?? H.chartData} defaultOpen>
        {tiles}
      </SelectionPaneSection>
    );
  }

  return (
    <DeckRibbonGroup label="Tabela" hint={H.tableData ?? H.chartData}>
      {tiles}
    </DeckRibbonGroup>
  );
}

/** Alinhamento horizontal + quebra de texto (Excel Alinhamento). */
export function TableLayoutAlignSection({ layout }: { layout: SelectionSectionLayout }) {
  const ctrl = useTableLayoutControls();
  if (!ctrl) return null;
  const { options, applyOptions } = ctrl;
  const align = options.textAlign ?? "left";
  const wrapActive = Boolean(options.wrapText);

  const tiles = (
    <div className="td-deck-ribbon__tiles td-deck-ribbon__tiles--compact">
      <DeckRibbonTile
        icon={AlignLeft}
        label="Esquerda"
        active={align === "left"}
        onClick={() => applyOptions({ textAlign: "left" })}
      />
      <DeckRibbonTile
        icon={AlignCenter}
        label="Centro"
        active={align === "center"}
        onClick={() => applyOptions({ textAlign: "center" })}
      />
      <DeckRibbonTile
        icon={AlignRight}
        label="Direita"
        active={align === "right"}
        onClick={() => applyOptions({ textAlign: "right" })}
      />
      <DeckRibbonTile
        icon={WrapText}
        label="Quebrar texto"
        hint={D.tableWrapText}
        active={wrapActive}
        onClick={() => applyOptions({ wrapText: !wrapActive })}
      />
    </div>
  );

  if (layout === "pane") {
    return (
      <SelectionPaneSection
        title="Alinhamento"
        hint="Alinhamento horizontal e quebra automática do texto nas células."
        defaultOpen={false}
      >
        {tiles}
      </SelectionPaneSection>
    );
  }

  return (
    <DeckRibbonGroup
      label="Alinhamento"
      hint="Alinhamento horizontal e quebra automática do texto nas células."
    >
      {tiles}
    </DeckRibbonGroup>
  );
}

/** Altura de linha e largura por coluna (Excel Layout → Tamanho). */
export function TableLayoutSizeSection({ layout }: { layout: SelectionSectionLayout }) {
  const { selected, selectedTablePart, selectedTableParts, selectTablePart, updateSelected } =
    useComunicadoEditor();
  const [columnKey, setColumnKey] = useState<string>("");
  const block = selected?.type === "table_view" ? (selected as ComunicadoTableViewBlock) : null;
  const options = block
    ? mergeComunicadoTableOptions(block.tableOptions, block.tablePreset)
    : null;

  const projectionColumns = useMemo(
    () =>
      block
        ? resolveEditableTableProjectionColumns(block).filter((column) => column.visible !== false)
        : [],
    [block],
  );
  const activeKey = useMemo(() => {
    if (
      selectedTablePart?.kind === "headerCell" &&
      selectedTablePart.colIndex != null &&
      projectionColumns[selectedTablePart.colIndex]
    ) {
      return projectionColumns[selectedTablePart.colIndex].key;
    }
    if (columnKey && projectionColumns.some((column) => column.key === columnKey)) {
      return columnKey;
    }
    return projectionColumns[0]?.key ?? "";
  }, [columnKey, projectionColumns, selectedTablePart]);

  if (!block || !options) return null;

  const applyOptions = (patch: Partial<ComunicadoTableOptions>) => {
    const nextOptions = {
      ...mergeComunicadoTableOptions(block.tableOptions, block.tablePreset),
      ...patch,
    };
    updateSelected({
      tableOptions: nextOptions,
      tableParts: mergeTablePartsWithOptions(block.tableParts, nextOptions),
    } as Partial<ComunicadoBlock>);
  };

  const activeColumn = projectionColumns.find((column) => column.key === activeKey);
  const multiSelectedKeys = selectedTableProjectionColumnKeys(block, selectedTableParts);
  const patchColumnWidth = (widthPct: number | undefined) => {
    if (!activeKey) return;
    /* Multi-seleção que inclui a coluna ativa → aplica a largura a todas. */
    const keys = multiSelectedKeys.includes(activeKey) ? multiSelectedKeys : [activeKey];
    updateSelected({
      tableProjection: resizeTableProjectionColumns(block, keys, widthPct),
    } as Partial<ComunicadoBlock>);
  };

  const fields = (
    <div className="td-deck-ribbon__frame-grid td-deck-ribbon__toolbar-row--dense">
      <label className="td-deck-ribbon__frame-field">
        <span className="td-deck-ribbon__field-label">Altura linha (px)</span>
        <ComboboxNumberControl
          className="td-deck-ribbon__number-combobox"
          compact
          square={false}
          min={16}
          max={200}
          placeholder="Auto"
          value={options.rowHeightPx}
          options={TABLE_ROW_HEIGHT_PRESETS}
          clamp={(value) => Math.max(16, Math.min(200, value))}
          portalScopeClassName="dashboard-tv-dashboard"
          aria-label="Altura da linha"
          onClear={() => applyOptions({ rowHeightPx: undefined })}
          onChange={(value) => applyOptions({ rowHeightPx: value })}
        />
      </label>
      <label className="td-deck-ribbon__frame-field">
        <span className="td-deck-ribbon__field-label">
          {multiSelectedKeys.length > 1 ? `Coluna (${multiSelectedKeys.length} sel.)` : "Coluna"}
        </span>
        <TdRibbonSelect
          value={activeKey}
          disabled={projectionColumns.length === 0}
          aria-label="Coluna da tabela"
          onChange={(nextKey) => {
            setColumnKey(nextKey);
            const colIndex = projectionColumns.findIndex((column) => column.key === nextKey);
            if (colIndex >= 0) selectTablePart(block.id, { kind: "headerCell", colIndex });
          }}
          options={
            projectionColumns.length === 0
              ? [{ value: "", label: "Sem colunas" }]
              : projectionColumns.map((column) => ({
                  value: column.key,
                  label: column.label?.trim() || column.key,
                }))
          }
        />
      </label>
      <label className="td-deck-ribbon__frame-field">
        <span className="td-deck-ribbon__field-label">Largura (%)</span>
        <ComboboxNumberControl
          className="td-deck-ribbon__number-combobox"
          compact
          square={false}
          min={1}
          max={100}
          placeholder="Auto"
          disabled={!activeKey}
          value={activeColumn?.widthPct}
          options={TABLE_COLUMN_WIDTH_PRESETS}
          clamp={(value) => Math.max(1, Math.min(100, value))}
          portalScopeClassName="dashboard-tv-dashboard"
          aria-label="Largura da coluna"
          onClear={() => patchColumnWidth(undefined)}
          onChange={patchColumnWidth}
        />
      </label>
    </div>
  );

  const distributeTiles = (
    <div className="td-deck-ribbon__tiles td-deck-ribbon__tiles--compact">
      <DeckRibbonTile
        icon={Rows3}
        label="Distribuir linhas"
        hint={D.tableDistributeRows}
        onClick={() => applyOptions({ rowHeightPx: undefined })}
      />
      <DeckRibbonTile
        icon={Columns3}
        label="Distribuir colunas"
        hint={D.tableDistributeColumns}
        disabled={projectionColumns.length === 0}
        onClick={() =>
          updateSelected({
            tableProjection: distributeTableProjectionColumnWidths(block),
          } as Partial<ComunicadoBlock>)
        }
      />
    </div>
  );

  const hint = D.tableColumnSize ?? "Altura das linhas e largura relativa de cada coluna.";

  if (layout === "pane") {
    return (
      <SelectionPaneSection title="Tamanho" hint={hint} defaultOpen>
        {fields}
        {distributeTiles}
      </SelectionPaneSection>
    );
  }

  return (
    <DeckRibbonGroup label="Tamanho" hint={hint}>
      {fields}
      {distributeTiles}
    </DeckRibbonGroup>
  );
}
