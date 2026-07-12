import { DECK_COLOR_BORDER, DECK_KPI_DEFAULTS, LucideIconPicker, NativeTextControl } from "@delpi/plugin-ui/index";
import {
  KPI_ICON_DEFAULT_RADIUS_PX,
  KPI_ICON_DEFAULT_SIZE_PX,
  clampKpiPartFrame,
  defaultKpiPartFrame,
  deleteKpiPart,
  getKpiPartState,
  kpiPartAllowsDelete,
  kpiPartAllowsFrame,
  mergeComunicadoKpiOptions,
  mergeKpiPartsWithOptions,
  partsToKpiOptions,
  serializeKpiPartRef,
  upsertKpiPartState,
  type ComunicadoKpiPartFrame,
  type ComunicadoKpiPartRef,
  type ComunicadoKpiViewBlock,
  type KpiFramePartKind,
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
  iconSize?: number;
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
  const frameable = kpiPartAllowsFrame(selectedKpiPart);
  const frameKind = selectedKpiPart.kind as KpiFramePartKind;
  const partFrame = clampKpiPartFrame(
    partState?.frame ?? (frameable ? defaultKpiPartFrame(frameKind) : { x: 0, y: 0, w: 20, h: 20 }),
  );

  const persistPart = (patch: {
    content?: string;
    style?: PartStylePatch;
    visible?: boolean;
    frame?: ComunicadoKpiPartFrame | null;
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

  const persistPartFrame = (patch: Partial<ComunicadoKpiPartFrame>) => {
    persistPart({ frame: clampKpiPartFrame({ ...partFrame, ...patch }) });
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
              variant="fill"
              label="Fundo"
              value={partState?.style?.fill ?? options.backgroundColor ?? DECK_KPI_DEFAULTS.backgroundColor}
              onChange={(color) => persistPart({ style: { fill: color } })}
            />
          </DeckField>
          <DeckField id="td-kpi-part-card-stroke" label="Contorno">
            <TvRibbonColorPicker
              inline
              variant="outline"
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
            <DeckField id="td-kpi-part-card-radius" label="Raio px">
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
        <>
          <DeckField id="td-kpi-part-value-color" label="Cor do valor">
            <TvRibbonColorPicker
              inline
              variant="text"
              contrastBackground={
                partState?.style?.fill && partState.style.fill !== "transparent"
                  ? partState.style.fill
                  : (options.backgroundColor ??
                    getKpiPartState(block.kpiParts, { kind: "card" })?.style?.fill ??
                    DECK_KPI_DEFAULTS.backgroundColor)
              }
              label="Cor do valor"
              value={partState?.style?.color ?? options.valueColor ?? DECK_KPI_DEFAULTS.valueColor}
              onChange={(color) => persistPart({ style: { color } })}
            />
          </DeckField>
          <DeckField id="td-kpi-part-value-fill" label="Preenchimento">
            <TvRibbonColorPicker
              inline
              variant="fill"
              label="Preenchimento"
              value={partState?.style?.fill ?? "transparent"}
              onChange={(color) => persistPart({ style: { fill: color } })}
              onNoFill={() => persistPart({ style: { fill: "transparent" } })}
            />
          </DeckField>
          <DeckField id="td-kpi-part-value-stroke" label="Contorno">
            <TvRibbonColorPicker
              inline
              variant="outline"
              label="Contorno"
              value={partState?.style?.stroke ?? "transparent"}
              onChange={(color) => persistPart({ style: { stroke: color, strokeWidth: partState?.style?.strokeWidth ?? 1 } })}
              onNoFill={() => persistPart({ style: { stroke: "transparent", strokeWidth: 0 } })}
            />
          </DeckField>
        </>
      ) : null}

      {selectedKpiPart.kind === "icon" ? (
        <DeckField id="td-kpi-part-icon" label="Ícone Lucide">
          <LucideIconPicker
            embedded
            curatedOnly={false}
            nameFormat="pascal"
            value={options.iconName ?? "Gauge"}
            onChange={(name) => {
              const nextOptions = mergeComunicadoKpiOptions({
                ...options,
                iconName: name?.trim() || "Gauge",
                showIcon: true,
              });
              updateSelected({
                kpiOptions: nextOptions,
                kpiParts: mergeKpiPartsWithOptions(block.kpiParts, nextOptions),
              } as Partial<typeof block>);
            }}
            labels={{
              clear: "Usar ícone padrão",
            }}
          />
        </DeckField>
      ) : null}

      {frameable ? (
        <>
          <div className="td-part-inspector-toolbar__fields-row">
            <DeckField id={`td-kpi-part-${selectedKpiPart.kind}-x`} label="Posição X (%)">
              <NativeTextControl
                id={`td-kpi-part-${selectedKpiPart.kind}-x`}
                type="number"
                min={0}
                max={100}
                step={0.5}
                value={Number(partFrame.x.toFixed(1))}
                onChange={(value) => persistPartFrame({ x: Number(value) || 0 })}
              />
            </DeckField>
            <DeckField id={`td-kpi-part-${selectedKpiPart.kind}-y`} label="Posição Y (%)">
              <NativeTextControl
                id={`td-kpi-part-${selectedKpiPart.kind}-y`}
                type="number"
                min={0}
                max={100}
                step={0.5}
                value={Number(partFrame.y.toFixed(1))}
                onChange={(value) => persistPartFrame({ y: Number(value) || 0 })}
              />
            </DeckField>
          </div>
          <div className="td-part-inspector-toolbar__fields-row">
            <DeckField id={`td-kpi-part-${selectedKpiPart.kind}-w`} label="Largura (%)">
              <NativeTextControl
                id={`td-kpi-part-${selectedKpiPart.kind}-w`}
                type="number"
                min={4}
                max={96}
                step={0.5}
                value={Number((partFrame.w ?? 20).toFixed(1))}
                onChange={(value) => persistPartFrame({ w: Number(value) || 4 })}
              />
            </DeckField>
            <DeckField id={`td-kpi-part-${selectedKpiPart.kind}-h`} label="Altura (%)">
              <NativeTextControl
                id={`td-kpi-part-${selectedKpiPart.kind}-h`}
                type="number"
                min={4}
                max={96}
                step={0.5}
                value={Number((partFrame.h ?? 20).toFixed(1))}
                onChange={(value) => persistPartFrame({ h: Number(value) || 4 })}
              />
            </DeckField>
          </div>
          {selectedKpiPart.kind === "icon" ? (
            <DeckField id="td-kpi-part-icon-size" label="Tamanho fixo (px)">
              <NativeTextControl
                id="td-kpi-part-icon-size"
                type="number"
                min={16}
                max={160}
                value={partState?.style?.iconSize ?? KPI_ICON_DEFAULT_SIZE_PX}
                onChange={(value) => {
                  const size = Math.max(16, Math.min(160, Number(value) || KPI_ICON_DEFAULT_SIZE_PX));
                  persistPart({ style: { iconSize: size }, frame: null });
                }}
              />
            </DeckField>
          ) : null}
          <DeckField id={`td-kpi-part-${selectedKpiPart.kind}-radius`} label="Raio px">
            <NativeTextControl
              id={`td-kpi-part-${selectedKpiPart.kind}-radius`}
              type="number"
              min={0}
              max={64}
              value={
                partState?.style?.borderRadius ??
                (selectedKpiPart.kind === "icon" ? KPI_ICON_DEFAULT_RADIUS_PX : 0)
              }
              onChange={(value) =>
                persistPart({ style: { borderRadius: Math.max(0, Number(value) || 0) } })
              }
            />
          </DeckField>
        </>
      ) : null}

      {selectedKpiPart.kind === "icon" ? (
        <>
          <DeckField id="td-kpi-part-icon-fill" label="Fundo do ícone">
            <TvRibbonColorPicker
              inline
              variant="fill"
              label="Fundo"
              value={partState?.style?.fill ?? "transparent"}
              onChange={(color) => persistPart({ style: { fill: color } })}
              onNoFill={() => persistPart({ style: { fill: "transparent" } })}
            />
          </DeckField>
          <DeckField id="td-kpi-part-icon-color" label="Cor do ícone">
            <TvRibbonColorPicker
              inline
              variant="text"
              contrastBackground={
                partState?.style?.fill && partState.style.fill !== "transparent"
                  ? partState.style.fill
                  : (options.backgroundColor ??
                    getKpiPartState(block.kpiParts, { kind: "card" })?.style?.fill ??
                    DECK_KPI_DEFAULTS.backgroundColor)
              }
              label="Cor do ícone"
              value={partState?.style?.color ?? DECK_KPI_DEFAULTS.valueColor}
              onChange={(color) => persistPart({ style: { color } })}
            />
          </DeckField>
          <DeckField id="td-kpi-part-icon-stroke" label="Contorno">
            <TvRibbonColorPicker
              inline
              variant="outline"
              label="Contorno"
              value={partState?.style?.stroke ?? DECK_COLOR_BORDER}
              onChange={(color) => persistPart({ style: { stroke: color } })}
              onNoFill={() => persistPart({ style: { stroke: "transparent", strokeWidth: 0 } })}
            />
          </DeckField>
          <DeckField id="td-kpi-part-icon-stroke-width" label="Espessura">
            <NativeTextControl
              id="td-kpi-part-icon-stroke-width"
              type="number"
              min={0}
              max={12}
              step={0.5}
              value={partState?.style?.strokeWidth ?? 0}
              onChange={(value) => persistPart({ style: { strokeWidth: Number(value) || 0 } })}
            />
          </DeckField>
        </>
      ) : null}
    </DeckPropertySection>
  );
}
