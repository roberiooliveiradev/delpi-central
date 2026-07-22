import {
  type ComunicadoBlockStyle,
  type ComunicadoIconBlock,
} from "@delpi/tv-dashboard-presentation";
import {
  DECK_SHAPE_DEFAULTS,
  LucideIconField,
  LucideIconPickerPopover,
  ShapeFillMenu,
  ShapeOutlineMenu,
  ShapeShadowMenu,
  ShapeStyleMenu,
} from "@delpi/plugin-ui/index";
import { Sparkles } from "lucide-react";
import { useRef, useState } from "react";

import { COMUNICADO_BOX_SHADOW_PRESETS } from "../../content/comunicadoVisualPresets";
import { TV_DASHBOARD_HELP_TOOLTIPS } from "../../content/helpTooltips";
import { TV_DASHBOARD_ROOT_CLASS } from "../../constants/pluginRootClass";
import { useComunicadoEditor } from "../comunicadoEditorContext";
import { DeckField } from "../deck/DeckField";
import { DeckRangeField } from "../deck/DeckRangeField";
import { DeckRibbonGroup } from "../deck/DeckRibbonGroup";
import { DeckRibbonTile } from "../deck/DeckRibbonTile";
import { TvRibbonColorPicker } from "../deck/TvRibbonColorPicker";
import { FormatRibbonOpacityFields } from "../formatRibbon/FormatRibbonOrganizeSection";
import { ShapeMenuHint } from "../formatRibbon/ShapeMenuHint";
import { ShapeCornerRadiusControl } from "../ShapeCornerRadiusControl";
import { SelectionPaneSection } from "./SelectionPaneSection";
import type { SelectionSectionLayout } from "./types";

const H = TV_DASHBOARD_HELP_TOOLTIPS.ribbon;

const ICON_FIELD_LABELS = { clear: "Estrela (padrão)", close: "Fechar" } as const;

const SHADOW_MENU_PRESETS = COMUNICADO_BOX_SHADOW_PRESETS.map((preset) => ({
  id: preset.key,
  label: preset.label,
  value: preset.value,
}));

function isIconBlock(
  block: ReturnType<typeof useComunicadoEditor>["selected"],
): block is ComunicadoIconBlock {
  return block?.type === "icon";
}

function resolveIconBoxFill(block: ComunicadoIconBlock): string {
  return block.style?.fill ?? "transparent";
}

function resolveIconBoxStroke(block: ComunicadoIconBlock): string {
  return block.style?.stroke ?? "transparent";
}

function resolveIconBoxStrokeWidth(block: ComunicadoIconBlock): number {
  return block.style?.strokeWidth ?? 0;
}

function resolveIconGlyphStrokeWidth(block: ComunicadoIconBlock): number {
  const dedicated = block.style?.iconStrokeWidth;
  if (typeof dedicated === "number" && Number.isFinite(dedicated) && dedicated > 0) {
    return dedicated;
  }
  return 2;
}

/** Ícone Lucide no palco — glifo + chrome de caixa (paridade com formas). */
export function IconSection({ layout }: { layout: SelectionSectionLayout }) {
  const { selected, updateSelected, updateSelectedStyle } = useComunicadoEditor();
  const [pickerOpen, setPickerOpen] = useState(false);
  const trocarAnchorRef = useRef<HTMLDivElement>(null);

  if (!isIconBlock(selected)) return null;

  const block = selected;
  const iconColor = block.style?.color ?? DECK_SHAPE_DEFAULTS.fill;
  const glyphStrokeWidth = resolveIconGlyphStrokeWidth(block);
  const fillValue = resolveIconBoxFill(block);
  const strokeValue = resolveIconBoxStroke(block);
  const boxStrokeWidth = resolveIconBoxStrokeWidth(block);
  const borderRadius = block.style?.borderRadius ?? 0;
  const resolvedIconName = block.iconName?.trim() || "Star";

  const patchStyle = (patch: Partial<ComunicadoBlockStyle>) => updateSelectedStyle(patch);

  const applyIconName = (name: string | null) => {
    updateSelected({ iconName: name?.trim() || "Star" } as Partial<ComunicadoIconBlock>);
  };

  const colorControl = (
    <TvRibbonColorPicker
      hint={H.iconColor}
      inline={layout === "ribbon"}
      variant="text"
      label="Cor do ícone"
      value={iconColor}
      onChange={(color) => patchStyle({ color })}
    />
  );

  const glyphStrokeControl = (
    <DeckRangeField
      id={layout === "pane" ? "td-icon-stroke-width" : "td-icon-stroke-ribbon"}
      label={layout === "pane" ? "Espessura do traço" : "Traço"}
      hint={H.iconStrokeWidth}
      min={0.5}
      max={6}
      step={0.25}
      density={layout === "ribbon" ? "compact" : undefined}
      value={glyphStrokeWidth}
      onChange={(value) => patchStyle({ iconStrokeWidth: value })}
    />
  );

  const formaMenus = (
    <div className="td-deck-ribbon__tiles td-deck-ribbon__tiles--compact td-deck-ribbon__tiles--shape-menus">
      <ShapeMenuHint hint={H.shapeStyles} ariaLabel="Ajuda: Estilos da caixa do ícone">
        <ShapeStyleMenu
          triggerLabel="Estilos"
          onSelect={(preset) =>
            patchStyle({
              fill: preset.fill,
              stroke: preset.stroke,
              strokeWidth: preset.strokeWidth,
              boxShadow: preset.boxShadow,
            })
          }
        />
      </ShapeMenuHint>
      <ShapeMenuHint hint={H.boxShadow} ariaLabel="Ajuda: Sombra da caixa do ícone">
        <ShapeShadowMenu
          value={block.style?.boxShadow}
          presets={SHADOW_MENU_PRESETS}
          shadowLabel="Sombra"
          onChange={(boxShadow) => patchStyle({ boxShadow })}
        />
      </ShapeMenuHint>
      <ShapeMenuHint hint={H.shapeFill} ariaLabel="Ajuda: Fundo da caixa do ícone">
        <ShapeFillMenu
          value={fillValue === "transparent" ? undefined : fillValue}
          fillLabel="Fundo"
          onChange={(color) => patchStyle({ fill: color })}
          onNoFill={() => patchStyle({ fill: "transparent" })}
        />
      </ShapeMenuHint>
      <ShapeMenuHint hint={H.shapeOutline} ariaLabel="Ajuda: Contorno da caixa do ícone">
        <ShapeOutlineMenu
          color={strokeValue === "transparent" ? undefined : strokeValue}
          strokeWidth={boxStrokeWidth}
          minWidth={0}
          maxWidth={20}
          outlineLabel="Contorno"
          onColorChange={(color) =>
            patchStyle({
              stroke: color,
              strokeWidth: Math.max(1, boxStrokeWidth || 1),
            })
          }
          onNoOutline={() => patchStyle({ stroke: "transparent", strokeWidth: 0 })}
          onStrokeWidthChange={(width) => patchStyle({ strokeWidth: width })}
        />
      </ShapeMenuHint>
    </div>
  );

  const formaBody = (
    <>
      {formaMenus}
      <div className="td-deck-ribbon__organize-props td-forma-opacity">
        <ShapeCornerRadiusControl
          id="td-icon-forma-corner-radius"
          value={borderRadius}
          onChange={(radius) => patchStyle({ borderRadius: radius })}
          embedded
        />
        <FormatRibbonOpacityFields className="td-forma-opacity__slot" />
      </div>
    </>
  );

  if (layout === "pane") {
    return (
      <>
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
              portalScopeClassName={TV_DASHBOARD_ROOT_CLASS}
            />
          </DeckField>
          <DeckField id="td-icon-color" label="Cor do ícone" hint={H.iconColor}>
            {colorControl}
          </DeckField>
          {glyphStrokeControl}
        </SelectionPaneSection>
        <SelectionPaneSection title="Forma" hint={H.shapeForma} defaultOpen>
          {formaBody}
        </SelectionPaneSection>
      </>
    );
  }

  return (
    <>
      <DeckRibbonGroup groupId="shape-icon" label="Ícone" hint={H.iconEditor}>
        <div className="td-deck-ribbon__tiles td-deck-ribbon__tiles--compact">
          <div ref={trocarAnchorRef} className="td-composer__dropdown">
            <DeckRibbonTile
              icon={Sparkles}
              label="Trocar"
              hint={H.iconPicker}
              active={pickerOpen}
              onClick={() => setPickerOpen((open) => !open)}
            />
          </div>
          {colorControl}
          {glyphStrokeControl}
        </div>
        <LucideIconPickerPopover
          open={pickerOpen}
          onOpenChange={setPickerOpen}
          anchorRef={trocarAnchorRef}
          value={resolvedIconName}
          nameFormat="pascal"
          curatedOnly={false}
          title="Ícones"
          labels={ICON_FIELD_LABELS}
          portalScopeClassName={TV_DASHBOARD_ROOT_CLASS}
          ariaLabel="Biblioteca de ícones"
          onChange={(name) => {
            applyIconName(name);
            setPickerOpen(false);
          }}
        />
      </DeckRibbonGroup>
      <DeckRibbonGroup groupId="shape-forma" label="Forma" hint={H.shapeForma}>
        {formaBody}
      </DeckRibbonGroup>
    </>
  );
}
