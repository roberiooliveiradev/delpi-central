import {
  type ComunicadoIconBlock,
} from "@delpi/tv-dashboard-presentation";
import {
  DECK_SHAPE_DEFAULTS,
  LucideIconField,
  LucideIconPicker,
  useLucideIconField,
} from "@delpi/plugin-ui/index";
import { Sparkles } from "lucide-react";
import { useState } from "react";

import { TV_DASHBOARD_HELP_TOOLTIPS } from "../../content/helpTooltips";
import { useComunicadoEditor } from "../comunicadoEditorContext";
import { DeckField } from "../deck/DeckField";
import { DeckRangeField } from "../deck/DeckRangeField";
import { DeckRibbonGroup } from "../deck/DeckRibbonGroup";
import { DeckRibbonTile } from "../deck/DeckRibbonTile";
import { TvRibbonColorPicker } from "../deck/TvRibbonColorPicker";
import { FormatRibbonOpacityFields } from "../formatRibbon/FormatRibbonOrganizeSection";
import { SelectionPaneSection } from "./SelectionPaneSection";
import type { SelectionSectionLayout } from "./types";

const H = TV_DASHBOARD_HELP_TOOLTIPS.ribbon;

const ICON_FIELD_LABELS = { clear: "Estrela (padrão)", close: "Fechar" } as const;

function isIconBlock(
  block: ReturnType<typeof useComunicadoEditor>["selected"],
): block is ComunicadoIconBlock {
  return block?.type === "icon";
}

/** Ícone Lucide no palco — trocar glifo, cor (padrão formas) e traço. */
export function IconSection({ layout }: { layout: SelectionSectionLayout }) {
  const { selected, updateSelected, updateSelectedStyle } = useComunicadoEditor();
  const [pickerOpen, setPickerOpen] = useState(false);

  if (!isIconBlock(selected)) return null;

  const block = selected;
  const iconColor = block.style?.color ?? DECK_SHAPE_DEFAULTS.fill;
  const strokeWidth = block.style?.strokeWidth ?? 2;

  const applyIconName = (name: string | null) => {
    updateSelected({ iconName: name?.trim() || "Star" } as Partial<ComunicadoIconBlock>);
  };

  const iconField = useLucideIconField({
    value: block.iconName,
    defaultIcon: "Star",
    nameFormat: "pascal",
    curatedOnly: false,
    labels: ICON_FIELD_LABELS,
    onChange: applyIconName,
  });

  const colorControl = (
    <TvRibbonColorPicker
      hint={H.iconColor}
      inline={layout === "ribbon"}
      variant="text"
      label="Cor do ícone"
      value={iconColor}
      onChange={(color) => updateSelectedStyle({ color })}
    />
  );

  const strokeControl = (
    <DeckRangeField
      id="td-icon-stroke-width"
      label="Espessura do traço"
      hint={H.iconStrokeWidth}
      min={0.5}
      max={6}
      step={0.25}
      value={strokeWidth}
      onChange={(value) => updateSelectedStyle({ strokeWidth: value })}
    />
  );

  if (layout === "pane") {
    return (
      <SelectionPaneSection title="Ícone" hint={H.iconEditor} defaultOpen>
        <DeckField id="td-icon-name" label="Ícone Lucide" hint={H.iconPicker}>
          <LucideIconField
            value={block.iconName}
            defaultIcon="Star"
            nameFormat="pascal"
            curatedOnly={false}
            labels={ICON_FIELD_LABELS}
            onChange={applyIconName}
            ariaLabel="Selecionar ícone Lucide"
          />
        </DeckField>
        <DeckField id="td-icon-color" label="Cor" hint={H.iconColor}>
          {colorControl}
        </DeckField>
        {strokeControl}
        <FormatRibbonOpacityFields className="td-deck-ribbon__organize-props" />
      </SelectionPaneSection>
    );
  }

  return (
    <DeckRibbonGroup label="Ícone" hint={H.iconEditor}>
      <div className="td-deck-ribbon__tiles td-deck-ribbon__tiles--compact">
        <DeckRibbonTile
          icon={Sparkles}
          label="Trocar"
          hint={H.iconPicker}
          active={pickerOpen}
          onClick={() => setPickerOpen((open) => !open)}
        />
        {colorControl}
        <DeckRangeField
          id="td-icon-stroke-ribbon"
          label="Traço"
          hint={H.iconStrokeWidth}
          min={0.5}
          max={6}
          step={0.25}
          density="compact"
          value={strokeWidth}
          onChange={(value) => updateSelectedStyle({ strokeWidth: value })}
        />
      </div>
      {pickerOpen ? (
        <div className="td-icon-editor-picker">
          <LucideIconPicker
            {...iconField.pickerProps}
            onChange={(name) => {
              applyIconName(name);
              setPickerOpen(false);
            }}
            onClose={() => setPickerOpen(false)}
          />
        </div>
      ) : null}
    </DeckRibbonGroup>
  );
}
