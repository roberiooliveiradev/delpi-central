import { useState } from "react";
import {
  FormSelectControl,
  NativeCheckboxControl,
  NativeTextControl,
  DECK_TABLE_DEFAULTS,
} from "@delpi/plugin-ui/index";
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
  type ComunicadoBlock,
} from "@delpi/tv-dashboard-presentation";
import { AlignLeft, Layers, Palette } from "lucide-react";

import { TV_DASHBOARD_HELP_TOOLTIPS } from "../content/helpTooltips";
import { useComunicadoEditor } from "./comunicadoEditorContext";
import { InspectorElementRow } from "./InspectorElementRow";
import { TablePartInspector } from "./TablePartInspector";
import { TvRibbonColorPicker } from "./deck/TvRibbonColorPicker";
import { DeckField } from "./deck/DeckField";
import { DeckPropertySection } from "./deck/DeckPropertySection";

type Props = {
  pane?: boolean;
  /** Quando true, omite elementos/aparência já cobertos pelo SelectionSectionsHost (Design). */
  omitDesignChrome?: boolean;
  /** Quando true, omite alinhamento (já em tableLayoutAlign no host). */
  omitCellAlign?: boolean;
};

const TABLE_PANE_ICONS = [
  { id: "elements", label: "Elementos", Icon: Layers },
  { id: "cells", label: "Células", Icon: AlignLeft },
  { id: "appearance", label: "Aparência", Icon: Palette },
] as const;

function updateTableOptions(
  current: ComunicadoTableOptions | undefined,
  preset: ComunicadoTableViewBlock["tablePreset"],
  patch: Partial<ComunicadoTableOptions>,
): ComunicadoTableOptions {
  return { ...mergeComunicadoTableOptions(current, preset), ...patch };
}

export function TableViewOptionsInspector({
  pane = false,
  omitDesignChrome = false,
  omitCellAlign = false,
}: Props) {
  const { selected, selectedTablePart, selectTablePart, updateSelected } = useComunicadoEditor();
  const [paneIcon, setPaneIcon] = useState<(typeof TABLE_PANE_ICONS)[number]["id"]>(
    omitDesignChrome ? "cells" : "elements",
  );

  if (!selected || selected.type !== "table_view") return null;

  const block = selected as ComunicadoTableViewBlock;
  const options = mergeComunicadoTableOptions(block.tableOptions, block.tablePreset);
  const hasPartSelection = Boolean(selectedTablePart);
  const paneIcons = omitDesignChrome
    ? TABLE_PANE_ICONS.filter((entry) => entry.id === "cells")
    : TABLE_PANE_ICONS;

  const setOptions = (patch: Partial<ComunicadoTableOptions>) => {
    const nextOptions = updateTableOptions(block.tableOptions, block.tablePreset, patch);
    updateSelected({
      tableOptions: nextOptions,
      tableParts: mergeTablePartsWithOptions(block.tableParts, nextOptions),
    } as Partial<ComunicadoBlock>);
  };

  const focusElement = (elementId: TableElementId) => {
    const part = tableElementPrimaryPartRef(elementId);
    if (part) selectTablePart(block.id, part);
  };

  const toggleElement = (elementId: TableElementId, enabled: boolean) => {
    setOptions(setTableElementEnabled(elementId, enabled));
    if (enabled) focusElement(elementId);
  };

  const elementFocused = (elementId: TableElementId): boolean => {
    const primary = tableElementPrimaryPartRef(elementId);
    if (!primary || !selectedTablePart) return false;
    if (primary.kind === "header") {
      return selectedTablePart.kind === "header" || selectedTablePart.kind === "headerCell";
    }
    return selectedTablePart.kind === primary.kind;
  };

  const scrollToPane = (id: (typeof TABLE_PANE_ICONS)[number]["id"]) => {
    setPaneIcon(id);
    document.getElementById(`td-table-pane-${id}`)?.scrollIntoView({ block: "nearest" });
  };

  return (
    <>
      <TablePartInspector pane={pane} block={block} />

      {!hasPartSelection ? (
        <>
          {paneIcons.length > 1 ? (
            <div className="td-format-pane-icons" role="tablist" aria-label="Categorias da tabela">
              {paneIcons.map(({ id, label, Icon }) => (
                <button
                  key={id}
                  type="button"
                  role="tab"
                  aria-selected={paneIcon === id}
                  aria-label={label}
                  title={label}
                  className={[
                    "td-format-pane-icons__btn",
                    paneIcon === id ? "td-format-pane-icons__btn--active" : "",
                  ]
                    .filter(Boolean)
                    .join(" ")}
                  onClick={() => scrollToPane(id)}
                >
                  <Icon size={16} aria-hidden="true" />
                </button>
              ))}
            </div>
          ) : null}
          {!omitDesignChrome ? (
            <p className="td-deck-inspector__hint td-deck-inspector__hint--stage">
              Duplo clique no palco para selecionar título, cabeçalho ou célula. Moldura: aba Forma
              ou item abaixo.
            </p>
          ) : (
            <p className="td-deck-inspector__hint td-deck-inspector__hint--stage">
              Design e layout (incluindo alinhamento) ficam acima. Aqui: células e formato de
              valores.
            </p>
          )}

          {!omitDesignChrome ? (
            <div id="td-table-pane-elements">
              <DeckPropertySection
                pane={pane}
                title="Elementos da tabela"
                hint={TV_DASHBOARD_HELP_TOOLTIPS.data.tableElements}
                defaultOpen
              >
                <div className="td-chart-elements" role="group" aria-label="Elementos da tabela">
                  <InspectorElementRow
                    id="td-table-element-frame"
                    label="Moldura (contorno do bloco)"
                    hint="Contorno e cantos do bloco (também na aba Forma)"
                    focused={selectedTablePart?.kind === "frame"}
                    onSelect={() => selectTablePart(block.id, { kind: "frame" })}
                  />
                  {TABLE_ELEMENT_CATALOG.map((element) => {
                    const enabled = isTableElementEnabled(element.id, options);
                    return (
                      <InspectorElementRow
                        key={element.id}
                        id={`td-table-element-${element.id}`}
                        label={element.label}
                        hint={element.hint}
                        enabled={enabled}
                        focused={elementFocused(element.id)}
                        onToggle={(next) => toggleElement(element.id, next)}
                        onSelect={() => focusElement(element.id)}
                      />
                    );
                  })}
                </div>
              </DeckPropertySection>
            </div>
          ) : null}

          <div id="td-table-pane-cells">
            <DeckPropertySection
              pane={pane}
              title="Células"
              hint={TV_DASHBOARD_HELP_TOOLTIPS.data.tableCells}
            >
              <DeckField id="td-table-value-format" label="Formato dos valores">
                <FormSelectControl
                  id="td-table-value-format"
                  ariaLabel="Formato dos valores"
                  value={options.valueFormat ?? "auto"}
                  onChange={(value) =>
                    setOptions({ valueFormat: value as ComunicadoTableOptions["valueFormat"] })
                  }
                  options={TABLE_VALUE_FORMAT_OPTIONS.map((entry) => ({
                    value: entry.value,
                    label: entry.label,
                  }))}
                />
              </DeckField>
              {!omitCellAlign ? (
                <DeckField id="td-table-text-align" label="Alinhamento">
                  <FormSelectControl
                    id="td-table-text-align"
                    ariaLabel="Alinhamento"
                    value={options.textAlign ?? "left"}
                    onChange={(value) =>
                      setOptions({ textAlign: value as ComunicadoTableOptions["textAlign"] })
                    }
                    options={TABLE_TEXT_ALIGN_OPTIONS.map((entry) => ({
                      value: entry.value,
                      label: entry.label,
                    }))}
                  />
                </DeckField>
              ) : null}
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
              <DeckField id="td-table-header-uppercase" label="Cabeçalho">
                <NativeCheckboxControl
                  id="td-table-header-uppercase"
                  checked={options.headerUppercase !== false}
                  label="Texto em maiúsculas"
                  onChange={(checked) => setOptions({ headerUppercase: checked })}
                />
              </DeckField>
            </DeckPropertySection>
          </div>

          {!omitDesignChrome ? (
            <div id="td-table-pane-appearance">
              <DeckPropertySection
                pane={pane}
                title="Aparência das células"
                hint={TV_DASHBOARD_HELP_TOOLTIPS.data.tableAppearance}
              >
                <p className="td-deck-inspector__hint">
                  Contorno do bloco (moldura) fica na aba Forma ou em «Moldura» acima. Aqui só cores
                  internas e bordas entre células.
                </p>
                <DeckField id="td-table-header-bg" label="Fundo do cabeçalho">
                  <TvRibbonColorPicker
                    inline
                    variant="fill"
                    label="Fundo do cabeçalho"
                    value={options.headerBg ?? DECK_TABLE_DEFAULTS.headerBg}
                    onChange={(color) => setOptions({ headerBg: color })}
                  />
                </DeckField>
                <DeckField id="td-table-header-color" label="Texto do cabeçalho">
                  <TvRibbonColorPicker
                    inline
                    variant="text"
                    contrastBackground={options.headerBg ?? DECK_TABLE_DEFAULTS.headerBg}
                    label="Texto do cabeçalho"
                    value={options.headerTextColor ?? DECK_TABLE_DEFAULTS.headerTextColor}
                    onChange={(color) => setOptions({ headerTextColor: color })}
                  />
                </DeckField>
                <DeckField id="td-table-cell-bg" label="Fundo das células">
                  <TvRibbonColorPicker
                    inline
                    variant="fill"
                    label="Fundo das células"
                    value={options.cellBg ?? DECK_TABLE_DEFAULTS.cellBg}
                    onChange={(color) => setOptions({ cellBg: color })}
                  />
                </DeckField>
                <DeckField id="td-table-cell-color" label="Texto das células">
                  <TvRibbonColorPicker
                    inline
                    variant="text"
                    contrastBackground={options.cellBg ?? DECK_TABLE_DEFAULTS.cellBg}
                    label="Texto das células"
                    value={options.cellTextColor ?? DECK_TABLE_DEFAULTS.cellTextColor}
                    onChange={(color) => setOptions({ cellTextColor: color })}
                  />
                </DeckField>
                <DeckField id="td-table-border-color" label="Bordas das células">
                  <TvRibbonColorPicker
                    inline
                    variant="outline"
                    label="Bordas das células"
                    value={options.borderColor ?? DECK_TABLE_DEFAULTS.borderColor}
                    onChange={(color) => setOptions({ borderColor: color })}
                  />
                </DeckField>
              </DeckPropertySection>
            </div>
          ) : null}
        </>
      ) : null}
    </>
  );
}
