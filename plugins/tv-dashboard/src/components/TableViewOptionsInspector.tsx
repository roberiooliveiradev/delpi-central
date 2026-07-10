import { NativeSelectControl } from "@delpi/plugin-ui/index";
import type { ReactNode } from "react";
import {
  TABLE_ELEMENT_CATALOG,
  TABLE_TEXT_ALIGN_OPTIONS,
  TABLE_VALUE_FORMAT_OPTIONS,
  isTableElementEnabled,
  mergeComunicadoTableOptions,
  setTableElementEnabled,
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
    <details className="td-chart-element" open={enabled}>
      <summary className="td-chart-element__summary">
        <label className="td-chart-element__toggle" onClick={(event) => event.stopPropagation()}>
          <input
            type="checkbox"
            checked={enabled}
            aria-label={`Exibir ${label}`}
            onChange={(event) => onToggle(event.target.checked)}
          />
        </label>
        <span className="td-chart-element__label" id={`td-table-element-${elementId}`}>
          {label}
        </span>
        {hint ? <span className="td-chart-element__hint">{hint}</span> : null}
      </summary>
      {enabled && children ? <div className="td-chart-element__body">{children}</div> : null}
    </details>
  );
}

export function TableViewOptionsInspector({ pane = false }: Props) {
  const { selected, updateSelected } = useComunicadoEditor();
  if (!selected || selected.type !== "table_view") return null;

  const block = selected as ComunicadoTableViewBlock;
  const options = mergeComunicadoTableOptions(block.tableOptions, block.tablePreset);

  const setOptions = (patch: Partial<ComunicadoTableOptions>) => {
    updateSelected({
      tableOptions: updateTableOptions(block.tableOptions, block.tablePreset, patch),
    } as Partial<typeof selected>);
  };

  const toggleElement = (elementId: TableElementId, enabled: boolean) => {
    setOptions(setTableElementEnabled(elementId, enabled));
  };

  return (
    <>
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
                    <input
                      id="td-table-title"
                      type="text"
                      value={options.title ?? ""}
                      placeholder="Ex.: Top produtos"
                      onChange={(event) => setOptions({ title: event.target.value, showTitle: true })}
                    />
                  </DeckField>
                ) : null}

                {element.id === "header" ? (
                  <DeckField id="td-table-header-uppercase" label="Estilo do cabeçalho">
                    <label className="td-deck-inspector__checkbox">
                      <input
                        id="td-table-header-uppercase"
                        type="checkbox"
                        checked={options.headerUppercase !== false}
                        onChange={(event) => setOptions({ headerUppercase: event.target.checked })}
                      />
                      <span>Texto em maiúsculas</span>
                    </label>
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
          <input
            id="td-table-font-size"
            type="number"
            min={8}
            max={24}
            step={1}
            value={options.fontSize ?? ""}
            placeholder="Automático"
            onChange={(event) => {
              const raw = event.target.value.trim();
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
