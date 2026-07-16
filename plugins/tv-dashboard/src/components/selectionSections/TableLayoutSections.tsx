import { useMemo, useState } from "react";
import { AlignCenter, AlignLeft, AlignRight, Database, Grid3x3, WrapText } from "lucide-react";
import {
  applyViewProjection,
  mergeComunicadoTableOptions,
  mergeTablePartsWithOptions,
  resolveTableColumns,
  type ComunicadoBlock,
  type ComunicadoTableOptions,
  type ComunicadoTableViewBlock,
  type TableColumnProjection,
  type TableViewProjection,
} from "@delpi/tv-dashboard-presentation";

import { TV_DASHBOARD_HELP_TOOLTIPS } from "../../content/helpTooltips";
import { useComunicadoEditor } from "../comunicadoEditorContext";
import { DeckRibbonGroup } from "../deck/DeckRibbonGroup";
import { DeckRibbonTile } from "../deck/DeckRibbonTile";
import { SelectionPaneSection } from "./SelectionPaneSection";
import type { SelectionSectionLayout } from "./types";

const H = TV_DASHBOARD_HELP_TOOLTIPS.ribbon;
const D = TV_DASHBOARD_HELP_TOOLTIPS.data;

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

/** Truncamento visual maxRows / maxCols. */
export function TableLayoutDisplaySection({ layout }: { layout: SelectionSectionLayout }) {
  const ctrl = useTableLayoutControls();
  if (!ctrl) return null;
  const { block, updateSelected } = ctrl;

  const hint =
    "Truncamento visual das linhas e colunas resolvidas da fonte (não altera o ERP).";

  const fields = (
    <div className="td-deck-ribbon__frame-grid td-deck-ribbon__toolbar-row--dense">
      <label className="td-deck-ribbon__frame-field">
        <span className="td-deck-ribbon__field-label">Máx. linhas</span>
        <input
          type="number"
          className="td-deck-ribbon__number td-deck-ribbon__number--compact"
          min={1}
          placeholder="Todas"
          value={block.maxRows ?? ""}
          onChange={(event) => {
            const raw = event.target.value;
            updateSelected({
              maxRows: raw === "" ? undefined : Math.max(1, Number(raw) || 1),
            } as Partial<ComunicadoBlock>);
          }}
        />
      </label>
      <label className="td-deck-ribbon__frame-field">
        <span className="td-deck-ribbon__field-label">Máx. cols</span>
        <input
          type="number"
          className="td-deck-ribbon__number td-deck-ribbon__number--compact"
          min={1}
          placeholder="Todas"
          value={block.maxCols ?? ""}
          onChange={(event) => {
            const raw = event.target.value;
            updateSelected({
              maxCols: raw === "" ? undefined : Math.max(1, Number(raw) || 1),
            } as Partial<ComunicadoBlock>);
          }}
        />
      </label>
    </div>
  );

  if (layout === "pane") {
    return (
      <SelectionPaneSection title="Exibição" hint={hint} defaultOpen={false}>
        {fields}
      </SelectionPaneSection>
    );
  }

  return (
    <DeckRibbonGroup label="Exibição" hint={hint}>
      {fields}
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

function ensureTableProjectionColumns(
  block: ComunicadoTableViewBlock,
): TableColumnProjection[] {
  const existing = block.tableProjection?.columns;
  if (existing?.length) return existing.map((column) => ({ ...column }));

  const resolved = applyViewProjection(block.resolved, {
    tableProjection: block.tableProjection,
  });
  const rows = resolved?.table?.rows ?? [];
  const columns = resolveTableColumns(resolved, rows);
  return columns.map((column) => ({
    key: column.key,
    label: column.label,
    visible: true,
  }));
}

/** Altura de linha e largura por coluna (Excel Layout → Tamanho). */
export function TableLayoutSizeSection({ layout }: { layout: SelectionSectionLayout }) {
  const { selected, selectedTablePart, updateSelected } = useComunicadoEditor();
  const [columnKey, setColumnKey] = useState<string>("");
  const block = selected?.type === "table_view" ? (selected as ComunicadoTableViewBlock) : null;
  const options = block
    ? mergeComunicadoTableOptions(block.tableOptions, block.tablePreset)
    : null;

  const projectionColumns = useMemo(
    () => (block ? ensureTableProjectionColumns(block) : []),
    [block],
  );
  const activeKey = useMemo(() => {
    if (columnKey && projectionColumns.some((column) => column.key === columnKey)) {
      return columnKey;
    }
    if (
      selectedTablePart?.kind === "headerCell" &&
      selectedTablePart.colIndex != null &&
      projectionColumns[selectedTablePart.colIndex]
    ) {
      return projectionColumns[selectedTablePart.colIndex].key;
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
  const rowHeight = options.rowHeightPx ?? "";

  const patchColumnWidth = (widthPct: number | undefined) => {
    if (!activeKey) return;
    const nextColumns = ensureTableProjectionColumns(block).map((column) => {
      if (column.key !== activeKey) return column;
      const next: TableColumnProjection = { ...column };
      if (widthPct == null || widthPct <= 0) {
        delete next.widthPct;
      } else {
        next.widthPct = Math.max(1, Math.min(100, widthPct));
      }
      return next;
    });
    const nextProjection: TableViewProjection = { columns: nextColumns };
    updateSelected({ tableProjection: nextProjection } as Partial<ComunicadoBlock>);
  };

  const fields = (
    <div className="td-deck-ribbon__frame-grid td-deck-ribbon__toolbar-row--dense">
      <label className="td-deck-ribbon__frame-field">
        <span className="td-deck-ribbon__field-label">Altura linha (px)</span>
        <input
          type="number"
          className="td-deck-ribbon__number td-deck-ribbon__number--compact"
          min={16}
          max={200}
          placeholder="Auto"
          value={rowHeight}
          onChange={(event) => {
            const raw = event.target.value;
            applyOptions({
              rowHeightPx: raw === "" ? undefined : Math.max(16, Math.min(200, Number(raw) || 16)),
            });
          }}
        />
      </label>
      <label className="td-deck-ribbon__frame-field">
        <span className="td-deck-ribbon__field-label">Coluna</span>
        <select
          className="td-deck-ribbon__select td-deck-ribbon__select--compact"
          value={activeKey}
          disabled={projectionColumns.length === 0}
          onChange={(event) => setColumnKey(event.target.value)}
        >
          {projectionColumns.length === 0 ? (
            <option value="">Sem colunas</option>
          ) : (
            projectionColumns.map((column) => (
              <option key={column.key} value={column.key}>
                {column.label?.trim() || column.key}
              </option>
            ))
          )}
        </select>
      </label>
      <label className="td-deck-ribbon__frame-field">
        <span className="td-deck-ribbon__field-label">Largura (%)</span>
        <input
          type="number"
          className="td-deck-ribbon__number td-deck-ribbon__number--compact"
          min={1}
          max={100}
          placeholder="Auto"
          disabled={!activeKey}
          value={activeColumn?.widthPct ?? ""}
          onChange={(event) => {
            const raw = event.target.value;
            patchColumnWidth(raw === "" ? undefined : Number(raw) || undefined);
          }}
        />
      </label>
    </div>
  );

  const hint = D.tableColumnSize ?? "Altura das linhas e largura relativa de cada coluna.";

  if (layout === "pane") {
    return (
      <SelectionPaneSection title="Tamanho" hint={hint} defaultOpen>
        {fields}
      </SelectionPaneSection>
    );
  }

  return (
    <DeckRibbonGroup label="Tamanho" hint={hint}>
      {fields}
    </DeckRibbonGroup>
  );
}
