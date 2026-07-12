import { NativeCheckboxControl, NativeSelectControl, NativeTextControl } from "@delpi/plugin-ui/index";
import type { ReactNode } from "react";
import {
  TABLE_ELEMENT_CATALOG,
  TABLE_TEXT_ALIGN_OPTIONS,
  TABLE_VALUE_FORMAT_OPTIONS,
  isTableElementEnabled,
  mergeComunicadoTableOptions,
  mergeTablePartsWithOptions,
  setTableElementEnabled,
  tableElementPrimaryPartRef,
  type ComunicadoTableOptions,
  type ComunicadoTableViewBlock,
  type TableElementId,
} from "@delpi/tv-dashboard-presentation";

import { TV_DASHBOARD_HELP_TOOLTIPS } from "../content/helpTooltips";
import { useComunicadoEditor } from "./comunicadoEditorContext";
import { TvRibbonColorPicker } from "./deck/TvRibbonColorPicker";
import { DeckField } from "./deck/DeckField";
import { DeckPropertySection } from "./deck/DeckPropertySection";

type Props = {
  pane?: boolean;
};

function updateTableOptions(
  current: ComunicadoTableOptions | undefined,
  preset: ComunicadoTableViewBlock["tablePreset"],
  patch: Partial<ComunicadoTableOptions>,
): ComunicadoTableOptions {
  return { ...mergeComunicadoTableOptions(current, preset), ...patch };
}

function TableElementPanel({
  elementId,
  enabled,
  onToggle,
  children,
  label,
  hint,
}: {
  elementId: TableElementId;
  enabled: boolean;
  onToggle: (next: boolean) => void;
  children?: ReactNode;
  label: string;
  hint?: string;
}) {
  return (
    <div
      className={[
        "td-chart-element",
        "td-chart-element--row",
        enabled && children ? "td-chart-element--expanded" : null,
      ]
        .filter(Boolean)
        .join(" ")}
    >
      <div className="td-chart-element__summary">
        <span className="td-chart-element__toggle" onClick={(event) => event.stopPropagation()}>
          <NativeCheckboxControl
            checked={enabled}
            aria-label={`Exibir ${label}`}
            onChange={onToggle}
          />
        </span>
        <span className="td-chart-element__label" id={`td-table-element-${elementId}`} title={hint}>
          {label}
        </span>
      </div>
      {enabled && children ? <div className="td-chart-element__body">{children}</div> : null}
    </div>
  );
}

export function TableViewOptionsInspector({ pane = false }: Props) {
  const { selected, selectedTablePart, selectTablePart, updateSelected } = useComunicadoEditor();
  if (!selected || selected.type !== "table_view") return null;

  const block = selected as ComunicadoTableViewBlock;
  const options = mergeComunicadoTableOptions(block.tableOptions, block.tablePreset);

  const setOptions = (patch: Partial<ComunicadoTableOptions>) => {
    const nextOptions = updateTableOptions(block.tableOptions, block.tablePreset, patch);
    updateSelected({
      tableOptions: nextOptions,
      tableParts: mergeTablePartsWithOptions(block.tableParts, nextOptions),
    } as Partial<typeof selected>);
  };

  const toggleElement = (elementId: TableElementId, enabled: boolean) => {
    setOptions(setTableElementEnabled(elementId, enabled));
    if (enabled) {
      const part = tableElementPrimaryPartRef(elementId);
      if (part) selectTablePart(block.id, part);
    }
  };

  const partLabel =
    selectedTablePart?.kind === "title"
      ? "Título"
      : selectedTablePart?.kind === "header"
        ? "Cabeçalho"
        : selectedTablePart?.kind === "headerCell"
          ? `Coluna ${selectedTablePart.colIndex + 1}`
          : selectedTablePart?.kind === "cell"
            ? `Célula ${selectedTablePart.rowIndex + 1}:${selectedTablePart.colIndex + 1}`
            : null;

  return (
    <>
      {partLabel ? (
        <DeckPropertySection pane={pane} title="Parte selecionada">
          <p className="td-subtitle">{partLabel} — duplo clique no palco seleciona título, cabeçalho ou célula.</p>
        </DeckPropertySection>
      ) : null}

      <DeckPropertySection pane={pane} title="Elementos da tabela" hint={TV_DASHBOARD_HELP_TOOLTIPS.data.tableElements}>
        <div className="td-chart-elements" role="group" aria-label="Elementos da tabela">
          {TABLE_ELEMENT_CATALOG.map((element) => {
            const enabled = isTableElementEnabled(element.id, options);
            return (
              <TableElementPanel
                key={element.id}
                elementId={element.id}
                label={element.label}
                hint={element.hint}
                enabled={enabled}
                onToggle={(next) => toggleElement(element.id, next)}
              >
                {element.id === "tableTitle" ? (
                  <DeckField id="td-table-title" label="Texto do título" hint={TV_DASHBOARD_HELP_TOOLTIPS.data.tableTitle}>
                    <NativeTextControl
                      id="td-table-title"
                      value={options.title ?? ""}
                      placeholder="Ex.: Top produtos"
                      onChange={(value) => setOptions({ title: value, showTitle: true })}
                    />
                  </DeckField>
                ) : null}

                {element.id === "header" ? (
                  <DeckField id="td-table-header-uppercase" label="Estilo do cabeçalho">
                    <NativeCheckboxControl
                      id="td-table-header-uppercase"
                      checked={options.headerUppercase !== false}
                      label="Texto em maiúsculas"
                      onChange={(checked) => setOptions({ headerUppercase: checked })}
                    />
                  </DeckField>
                ) : null}
              </TableElementPanel>
            );
          })}
        </div>
      </DeckPropertySection>

      <DeckPropertySection pane={pane} title="Células" hint={TV_DASHBOARD_HELP_TOOLTIPS.data.tableCells}>
        <DeckField id="td-table-value-format" label="Formato dos valores">
          <NativeSelectControl
            id="td-table-value-format"
            value={options.valueFormat ?? "auto"}
            onChange={(value) => setOptions({ valueFormat: value as ComunicadoTableOptions["valueFormat"] })}
            options={TABLE_VALUE_FORMAT_OPTIONS.map((entry) => ({
              value: entry.value,
              label: entry.label,
            }))}
          />
        </DeckField>
        <DeckField id="td-table-text-align" label="Alinhamento">
          <NativeSelectControl
            id="td-table-text-align"
            value={options.textAlign ?? "left"}
            onChange={(value) => setOptions({ textAlign: value as ComunicadoTableOptions["textAlign"] })}
            options={TABLE_TEXT_ALIGN_OPTIONS.map((entry) => ({
              value: entry.value,
              label: entry.label,
            }))}
          />
        </DeckField>
        <DeckField id="td-table-font-size" label="Tamanho da fonte (px)">
          <NativeTextControl
            id="td-table-font-size"
            type="number"
            min={8}
            max={24}
            step={1}
            value={options.fontSize ?? ""}
            placeholder="Automático"
            onChange={(value) => {
              const raw = value.trim();
              setOptions({ fontSize: raw ? Number(raw) : undefined });
            }}
          />
        </DeckField>
      </DeckPropertySection>

      <DeckPropertySection pane={pane} title="Aparência" hint={TV_DASHBOARD_HELP_TOOLTIPS.data.tableAppearance}>
        <DeckField id="td-table-header-bg" label="Fundo do cabeçalho">
          <TvRibbonColorPicker
            inline
            label="Fundo do cabeçalho"
            value={options.headerBg ?? "#1e293b"}
            onChange={(color) => setOptions({ headerBg: color })}
          />
        </DeckField>
        <DeckField id="td-table-header-color" label="Texto do cabeçalho">
          <TvRibbonColorPicker
            inline
            label="Texto do cabeçalho"
            value={options.headerTextColor ?? "#94a3b8"}
            onChange={(color) => setOptions({ headerTextColor: color })}
          />
        </DeckField>
        <DeckField id="td-table-cell-bg" label="Fundo das células">
          <TvRibbonColorPicker
            inline
            label="Fundo das células"
            value={options.cellBg ?? "#0f172a"}
            onChange={(color) => setOptions({ cellBg: color })}
          />
        </DeckField>
        <DeckField id="td-table-cell-color" label="Texto das células">
          <TvRibbonColorPicker
            inline
            label="Texto das células"
            value={options.cellTextColor ?? "#e2e8f0"}
            onChange={(color) => setOptions({ cellTextColor: color })}
          />
        </DeckField>
        <DeckField id="td-table-border-color" label="Cor das bordas">
          <TvRibbonColorPicker
            inline
            label="Cor das bordas"
            value={options.borderColor ?? "#334155"}
            onChange={(color) => setOptions({ borderColor: color })}
          />
        </DeckField>
      </DeckPropertySection>
    </>
  );
}
