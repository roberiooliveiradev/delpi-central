import { DECK_COLOR_BORDER, DECK_KPI_DEFAULTS, NativeTextControl } from "@delpi/plugin-ui/index";
import {
  deleteKpiPart,
  getKpiPartState,
  kpiPartAllowsDelete,
  mergeComunicadoKpiOptions,
  mergeKpiPartsWithOptions,
  partsToKpiOptions,
  serializeKpiPartRef,
  upsertKpiPartState,
  type ComunicadoKpiPartRef,
  type ComunicadoKpiViewBlock,
} from "@delpi/tv-dashboard-presentation";

import { useComunicadoEditor } from "./comunicadoEditorContext";
import { PartInspectorToolbar } from "./PartInspectorToolbar";
import { TvRibbonColorPicker } from "./deck/TvRibbonColorPicker";
import { DeckField } from "./deck/DeckField";
import { DeckPropertySection } from "./deck/DeckPropertySection";

type Props = {
  pane?: boolean;
  block: ComunicadoKpiViewBlock;
};

function kpiPartLabel(part: ComunicadoKpiPartRef): string {
  switch (part.kind) {
    case "card":
      return "Card";
    case "title":
      return "Título";
    case "value":
      return "Valor";
    case "hint":
      return "Subtítulo";
    case "icon":
      return "Ícone";
    default:
      return serializeKpiPartRef(part);
  }
}

type PartStylePatch = {
  fill?: string;
  color?: string;
  stroke?: string;
  strokeWidth?: number;
  borderRadius?: number;
};

/** Inspetor da parte selecionada do KPI — espelho de ChartPartInspector. */
export function KpiPartInspector({ pane = false, block }: Props) {
  const {
    selectedKpiPart,
    clearKpiPartSelection,
    beginEditKpiPart,
    updateSelected,
  } = useComunicadoEditor();

  if (!selectedKpiPart) return null;

  const options = mergeComunicadoKpiOptions({
    ...block.kpiOptions,
    ...partsToKpiOptions(block.kpiParts),
  });
  const partState = getKpiPartState(block.kpiParts, selectedKpiPart);
  const canDelete = kpiPartAllowsDelete(selectedKpiPart);
  const canEditOnStage = selectedKpiPart.kind === "title" || selectedKpiPart.kind === "hint";

  const persistPart = (patch: {
    content?: string;
    style?: PartStylePatch;
    visible?: boolean;
  }) => {
    const nextParts = upsertKpiPartState(block.kpiParts, selectedKpiPart, patch);
    const nextOptions = mergeComunicadoKpiOptions({
      ...options,
      ...partsToKpiOptions(nextParts),
    });
    const nextStyle = { ...block.style };
    if (selectedKpiPart.kind === "title" && patch.content !== undefined) {
      nextOptions.title = patch.content.trim() || undefined;
    }
    if (selectedKpiPart.kind === "hint" && patch.content !== undefined) {
      nextOptions.subtitle = patch.content.trim() || undefined;
    }
    if (selectedKpiPart.kind === "card" && patch.style?.fill !== undefined) {
      nextOptions.backgroundColor = patch.style.fill;
    }
    if (selectedKpiPart.kind === "card" && patch.style?.borderRadius != null) {
      nextStyle.borderRadius = patch.style.borderRadius;
    }
    if (selectedKpiPart.kind === "value" && patch.style?.color) {
      nextOptions.valueColor = patch.style.color;
    }
    updateSelected({
      kpiOptions: nextOptions,
      kpiParts: mergeKpiPartsWithOptions(nextParts, nextOptions),
      style: nextStyle,
    } as Partial<typeof block>);
  };

  const removePart = () => {
    const result = deleteKpiPart(block.kpiParts, selectedKpiPart, options);
    updateSelected({
      kpiParts: result.parts,
      kpiOptions: mergeComunicadoKpiOptions(result.options),
    } as Partial<typeof block>);
    clearKpiPartSelection();
  };

  return (
    <DeckPropertySection
      pane={pane}
      title={`Parte: ${kpiPartLabel(selectedKpiPart)}`}
      hint="Ajuste o conteúdo desta parte. Ocultar remove só a parte, não o KPI."
      defaultOpen
    >
      <PartInspectorToolbar
        onBack={clearKpiPartSelection}
        backLabel="Voltar aos elementos"
        onEditOnStage={
          canEditOnStage ? () => beginEditKpiPart(block.id, selectedKpiPart) : undefined
        }
        onHide={canDelete ? removePart : undefined}
        hideLabel="Ocultar parte"
      />

      {selectedKpiPart.kind === "title" ? (
        <DeckField id="td-kpi-part-title" label="Texto do título">
          <NativeTextControl
            id="td-kpi-part-title"
            value={partState?.content ?? options.title ?? ""}
            placeholder="Usar label da fonte"
            onChange={(value) => persistPart({ content: value, visible: true })}
          />
        </DeckField>
      ) : null}

      {selectedKpiPart.kind === "hint" ? (
        <DeckField id="td-kpi-part-hint" label="Subtítulo">
          <NativeTextControl
            id="td-kpi-part-hint"
            value={partState?.content ?? options.subtitle ?? ""}
            placeholder="Opcional"
            onChange={(value) => persistPart({ content: value, visible: true })}
          />
        </DeckField>
      ) : null}

      {selectedKpiPart.kind === "card" ? (
        <>
          <DeckField id="td-kpi-part-card-fill" label="Fundo">
            <TvRibbonColorPicker
              inline
              label="Fundo"
              value={partState?.style?.fill ?? options.backgroundColor ?? DECK_KPI_DEFAULTS.backgroundColor}
              onChange={(color) => persistPart({ style: { fill: color } })}
            />
          </DeckField>
          <DeckField id="td-kpi-part-card-stroke" label="Contorno">
            <TvRibbonColorPicker
              inline
              label="Contorno"
              value={partState?.style?.stroke ?? DECK_COLOR_BORDER}
              onChange={(color) => persistPart({ style: { stroke: color } })}
            />
          </DeckField>
          <div className="td-part-inspector-toolbar__fields-row">
            <DeckField id="td-kpi-part-card-stroke-width" label="Espessura">
              <NativeTextControl
                id="td-kpi-part-card-stroke-width"
                type="number"
                min={0}
                max={12}
                step={0.5}
                value={partState?.style?.strokeWidth ?? 1}
                onChange={(value) => persistPart({ style: { strokeWidth: Number(value) || 0 } })}
              />
            </DeckField>
            <DeckField id="td-kpi-part-card-radius" label="Cantos (px)">
              <NativeTextControl
                id="td-kpi-part-card-radius"
                type="number"
                min={0}
                max={64}
                value={partState?.style?.borderRadius ?? 0}
                onChange={(value) =>
                  persistPart({ style: { borderRadius: Math.max(0, Number(value) || 0) } })
                }
              />
            </DeckField>
          </div>
        </>
      ) : null}

      {selectedKpiPart.kind === "value" ? (
        <DeckField id="td-kpi-part-value-color" label="Cor do valor">
          <TvRibbonColorPicker
            inline
            label="Cor do valor"
            value={partState?.style?.color ?? options.valueColor ?? DECK_KPI_DEFAULTS.valueColor}
            onChange={(color) => persistPart({ style: { color } })}
          />
        </DeckField>
      ) : null}

      {selectedKpiPart.kind === "icon" ? (
        <p className="td-deck-inspector__hint">
          Ícone e tom ficam nas opções gerais do KPI. Use «Voltar aos elementos» ou oculte esta parte.
        </p>
      ) : null}
    </DeckPropertySection>
  );
}
