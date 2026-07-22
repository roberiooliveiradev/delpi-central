import {
  getInputPartState,
  getKpiPartState,
  inputPartBoxChromeLabels,
  kpiPartBoxChromeLabels,
  mergeComunicadoKpiOptions,
  mergeKpiPartsWithOptions,
  partsToKpiOptions,
  resolveBlockShapeChromeBoxShadow,
  resolveInputShapeChromePartRef,
  resolveKpiShapeChromePartRef,
  upsertInputPartState,
  upsertKpiPartState,
  type ComunicadoBlock,
  type ComunicadoInputBlock,
  type ComunicadoKpiViewBlock,
} from "@delpi/tv-dashboard-presentation";
import {
  DECK_COLOR_BORDER,
  DECK_COLOR_SURFACE,
  DECK_INPUT_DEFAULTS,
  ShapeFillMenu,
  ShapeOutlineMenu,
  ShapeShadowMenu,
  ShapeStyleMenu,
} from "@delpi/plugin-ui/index";

import { TV_DASHBOARD_HELP_TOOLTIPS } from "../../content/helpTooltips";
import { COMUNICADO_BOX_SHADOW_PRESETS } from "../../content/comunicadoVisualPresets";
import {
  isPartSelectionChrome,
  resolveSelectionChromeMode,
} from "../../utils/resolveSelectionChromeMode";
import { useComunicadoEditor } from "../comunicadoEditorContext";
import { FormatRibbonOpacityFields } from "../formatRibbon/FormatRibbonOrganizeSection";
import { VisualBoxFormaChrome } from "../formatRibbon/VisualBoxFormaChrome";
import { ShapeMenuHint } from "../formatRibbon/ShapeMenuHint";
import { ShapeCornerRadiusControl } from "../ShapeCornerRadiusControl";
import { DeckRibbonGroup } from "../deck/DeckRibbonGroup";
import { PartSelectionNav } from "./PartSelectionNav";
import { SelectionPaneSection } from "./SelectionPaneSection";
import type { SelectionSectionLayout } from "./types";

const H = TV_DASHBOARD_HELP_TOOLTIPS.ribbon;
const FORMA_HINT = H.shapeForma;

const SHADOW_MENU_PRESETS = COMUNICADO_BOX_SHADOW_PRESETS.map((preset) => ({
  id: preset.key,
  label: preset.label,
  value: preset.value,
}));

/**
 * Chrome de preenchimento/contorno — visual box (texto/shape), KPI (parte) e input.
 * Texto e forma usam o mesmo `VisualBoxFormaChrome` (texto nasce sem fundo).
 */
export function ShapeChromeSection({ layout }: { layout: SelectionSectionLayout }) {
  const {
    selected,
    selectedKpiPart,
    selectedInputPart,
    selectedChartPart,
    selectedTablePart,
    updateSelected,
    updateSelectedStyle,
    clearKpiPartSelection,
    clearInputPartSelection,
  } = useComunicadoEditor();

  if (!selected) return null;

  if (selected.type === "shape" || selected.type === "text" || selected.type === "heading") {
    return <VisualBoxFormaChrome layout={layout} />;
  }

  if (selected.type === "kpi_view") {
    return (
      <KpiShapeChrome
        layout={layout}
        block={selected as ComunicadoKpiViewBlock}
        selectedKpiPart={selectedKpiPart}
        onClearPart={clearKpiPartSelection}
        updateSelected={updateSelected}
        updateSelectedStyle={updateSelectedStyle}
      />
    );
  }

  if (selected.type === "input") {
    const chromeMode = resolveSelectionChromeMode({
      selected,
      selectedKpiPart,
      selectedChartPart,
      selectedTablePart,
      selectedInputPart,
    });
    return (
      <InputShapeChrome
        layout={layout}
        block={selected as ComunicadoInputBlock}
        selectedInputPart={selectedInputPart}
        partChrome={isPartSelectionChrome(chromeMode) ? chromeMode : null}
        onClearPart={clearInputPartSelection}
        updateSelected={updateSelected}
      />
    );
  }

  return null;
}

function KpiShapeChrome({
  layout,
  block,
  selectedKpiPart,
  onClearPart,
  updateSelected,
  updateSelectedStyle,
}: {
  layout: SelectionSectionLayout;
  block: ComunicadoKpiViewBlock;
  selectedKpiPart: ReturnType<typeof useComunicadoEditor>["selectedKpiPart"];
  onClearPart: () => void;
  updateSelected: ReturnType<typeof useComunicadoEditor>["updateSelected"];
  updateSelectedStyle: ReturnType<typeof useComunicadoEditor>["updateSelectedStyle"];
}) {
  const chromePart = resolveKpiShapeChromePartRef(selectedKpiPart);
  if (!chromePart) {
    if (layout === "ribbon") {
      return (
        <p className="td-subtitle td-deck-ribbon__hint">
          Seleção global do KPI — posição, tamanho e organizar. Clique no fundo ou numa parte
          para formatar preenchimento e contorno.
        </p>
      );
    }
    return null;
  }

  const partState = getKpiPartState(block.kpiParts, chromePart);
  const isCardChrome = chromePart.kind === "card";
  const boxLabels = kpiPartBoxChromeLabels(chromePart.kind);
  const cardState = getKpiPartState(block.kpiParts, { kind: "card" });
  const fillValue = isCardChrome
    ? (cardState?.style?.fill ?? block.kpiOptions?.backgroundColor ?? DECK_COLOR_SURFACE)
    : (partState?.style?.fill ?? "transparent");
  const strokeValue = isCardChrome
    ? (cardState?.style?.stroke ?? DECK_COLOR_BORDER)
    : (partState?.style?.stroke ?? "transparent");
  const strokeWidth = isCardChrome
    ? (cardState?.style?.strokeWidth ?? 1)
    : (partState?.style?.strokeWidth ?? 0);
  const cornerRadius = isCardChrome
    ? (cardState?.style?.borderRadius ?? block.style?.borderRadius ?? 0)
    : (partState?.style?.borderRadius ?? 0);

  const patchChromeStyle = (style: Record<string, unknown>) => {
    const nextParts = upsertKpiPartState(block.kpiParts, chromePart, {
      style: style as never,
    });
    const fromParts = partsToKpiOptions(nextParts);
    const nextOptions = mergeComunicadoKpiOptions({
      ...block.kpiOptions,
      ...fromParts,
      ...(isCardChrome && typeof style.fill === "string"
        ? { backgroundColor: style.fill }
        : {}),
    });
    updateSelected({
      kpiParts: mergeKpiPartsWithOptions(nextParts, nextOptions),
      kpiOptions: nextOptions,
    } as Partial<ComunicadoBlock>);
  };

  const chromeMode = resolveSelectionChromeMode({
    selected: block,
    selectedKpiPart,
  });
  const nav =
    isPartSelectionChrome(chromeMode) && chromeMode.source === "kpi" ? (
      <PartSelectionNav chrome={chromeMode} onBack={onClearPart} />
    ) : null;

  const menus = (
    <div className="td-deck-ribbon__tiles td-deck-ribbon__tiles--compact td-deck-ribbon__tiles--shape-menus">
      <ShapeMenuHint hint={H.shapeStyles} ariaLabel="Ajuda: Estilos de forma">
        <ShapeStyleMenu
          triggerLabel="Estilos"
          onSelect={(preset) =>
            patchChromeStyle({
              fill: preset.fill,
              stroke: preset.stroke,
              strokeWidth: preset.strokeWidth,
            })
          }
        />
      </ShapeMenuHint>
      <ShapeMenuHint hint={H.shapeFill} ariaLabel="Ajuda: Preenchimento">
        <ShapeFillMenu
          value={fillValue}
          fillLabel={boxLabels.fillShort}
          onChange={(color) => patchChromeStyle({ fill: color })}
          onNoFill={() => patchChromeStyle({ fill: "transparent" })}
        />
      </ShapeMenuHint>
      <ShapeMenuHint hint={H.shapeOutline} ariaLabel="Ajuda: Contorno">
        <ShapeOutlineMenu
          color={strokeValue}
          strokeWidth={strokeWidth}
          minWidth={0}
          maxWidth={20}
          outlineLabel={boxLabels.strokeShort}
          onColorChange={(color) => patchChromeStyle({ stroke: color })}
          onNoOutline={() => patchChromeStyle({ stroke: "transparent", strokeWidth: 0 })}
          onStrokeWidthChange={(width) => patchChromeStyle({ strokeWidth: width })}
        />
      </ShapeMenuHint>
      {isCardChrome ? (
        <ShapeMenuHint hint={H.boxShadow} ariaLabel="Ajuda: Sombra">
          <ShapeShadowMenu
            value={resolveBlockShapeChromeBoxShadow(block)}
            presets={SHADOW_MENU_PRESETS}
            shadowLabel="Sombra"
            onChange={(boxShadow) => updateSelectedStyle({ boxShadow })}
          />
        </ShapeMenuHint>
      ) : null}
    </div>
  );

  const formaBody = (
    <>
      {menus}
      <div className="td-deck-ribbon__organize-props td-forma-opacity">
        <ShapeCornerRadiusControl
          id={`td-kpi-forma-radius-${chromePart.kind}`}
          value={cornerRadius}
          onChange={(radius) => {
            patchChromeStyle({ borderRadius: radius });
            if (isCardChrome) {
              updateSelectedStyle({ borderRadius: radius });
            }
          }}
          embedded
        />
        <FormatRibbonOpacityFields className="td-forma-opacity__slot" />
      </div>
    </>
  );

  const hint = isCardChrome
    ? FORMA_HINT
    : "Fundo e borda da caixa desta parte — não alteram o fundo do card.";

  if (layout === "pane") {
    return (
      <>
        {nav}
        <SelectionPaneSection title="Forma" hint={hint} defaultOpen>
          {formaBody}
        </SelectionPaneSection>
      </>
    );
  }

  return (
    <>
      {nav}
      <DeckRibbonGroup groupId="shape-forma" label="Forma" hint={hint}>
        {formaBody}
      </DeckRibbonGroup>
    </>
  );
}

type PartChrome = Extract<
  ReturnType<typeof resolveSelectionChromeMode>,
  { mode: "part" }
>;

function InputShapeChrome({
  layout,
  block,
  selectedInputPart,
  partChrome,
  onClearPart,
  updateSelected,
}: {
  layout: SelectionSectionLayout;
  block: ComunicadoInputBlock;
  selectedInputPart: ReturnType<typeof useComunicadoEditor>["selectedInputPart"];
  partChrome: PartChrome | null;
  onClearPart: () => void;
  updateSelected: ReturnType<typeof useComunicadoEditor>["updateSelected"];
}) {
  const { updateSelectedStyle } = useComunicadoEditor();
  const chromePart = resolveInputShapeChromePartRef(selectedInputPart) ?? {
    kind: "frame" as const,
  };
  const partState = getInputPartState(block.inputParts, chromePart);
  const isFrameChrome = chromePart.kind === "frame";
  const boxLabels = inputPartBoxChromeLabels(chromePart.kind);
  const fillValue =
    partState?.style?.fill ??
    (isFrameChrome ? DECK_INPUT_DEFAULTS.backgroundColor : "transparent");
  const strokeValue =
    partState?.style?.stroke ??
    (isFrameChrome ? DECK_INPUT_DEFAULTS.borderColor : "transparent");
  const strokeWidth =
    partState?.style?.strokeWidth ??
    (isFrameChrome ? DECK_INPUT_DEFAULTS.borderWidth : 0);
  const cornerRadius = partState?.style?.borderRadius ?? block.style?.borderRadius ?? 0;

  const patchChromeStyle = (style: Record<string, unknown>) => {
    updateSelected({
      inputParts: upsertInputPartState(block.inputParts, chromePart, {
        style: style as never,
      }),
    } as Partial<ComunicadoBlock>);
  };

  const nav =
    partChrome && partChrome.source === "input" ? (
      <PartSelectionNav chrome={partChrome} onBack={onClearPart} />
    ) : null;

  const menus = (
    <div className="td-deck-ribbon__tiles td-deck-ribbon__tiles--compact td-deck-ribbon__tiles--shape-menus">
      <ShapeMenuHint hint={H.shapeFill} ariaLabel="Ajuda: Preenchimento">
        <ShapeFillMenu
          value={fillValue}
          fillLabel={boxLabels.fillShort}
          onChange={(color) => patchChromeStyle({ fill: color })}
          onNoFill={() => patchChromeStyle({ fill: "transparent" })}
        />
      </ShapeMenuHint>
      <ShapeMenuHint hint={H.shapeOutline} ariaLabel="Ajuda: Contorno">
        <ShapeOutlineMenu
          color={strokeValue}
          strokeWidth={strokeWidth}
          minWidth={0}
          maxWidth={20}
          outlineLabel={boxLabels.strokeShort}
          onColorChange={(color) => patchChromeStyle({ stroke: color })}
          onNoOutline={() => patchChromeStyle({ stroke: "transparent", strokeWidth: 0 })}
          onStrokeWidthChange={(width) => patchChromeStyle({ strokeWidth: width })}
        />
      </ShapeMenuHint>
      {isFrameChrome ? (
        <ShapeMenuHint hint={H.boxShadow} ariaLabel="Ajuda: Sombra">
          <ShapeShadowMenu
            value={resolveBlockShapeChromeBoxShadow(block)}
            presets={SHADOW_MENU_PRESETS}
            shadowLabel="Sombra"
            onChange={(boxShadow) => updateSelectedStyle({ boxShadow })}
          />
        </ShapeMenuHint>
      ) : null}
    </div>
  );

  const formaBody = (
    <>
      {menus}
      <div className="td-deck-ribbon__organize-props td-forma-opacity">
        <ShapeCornerRadiusControl
          id={`td-input-forma-radius-${chromePart.kind}`}
          value={cornerRadius}
          onChange={(radius) => {
            patchChromeStyle({ borderRadius: radius });
            if (isFrameChrome) {
              updateSelected({
                style: { ...block.style, borderRadius: radius },
              } as Partial<ComunicadoBlock>);
            }
          }}
          embedded
        />
        <FormatRibbonOpacityFields className="td-forma-opacity__slot" />
      </div>
    </>
  );

  if (layout === "pane") {
    return (
      <>
        {nav}
        <SelectionPaneSection title="Forma" hint={FORMA_HINT} defaultOpen>
          {formaBody}
        </SelectionPaneSection>
      </>
    );
  }

  return (
    <>
      {nav}
      <DeckRibbonGroup groupId="shape-forma" label="Forma" hint={FORMA_HINT}>
        {formaBody}
      </DeckRibbonGroup>
    </>
  );
}
