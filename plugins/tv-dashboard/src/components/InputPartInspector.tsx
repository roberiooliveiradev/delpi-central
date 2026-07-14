import { NativeTextControl } from "@delpi/plugin-ui/index";
import {
  INPUT_ICON_DEFAULT_SIZE_PX,
  clearInputPartsFreeLayoutFrames,
  clampInputPartFrame,
  defaultInputPartFrame,
  formatDesignPx,
  getInputPartState,
  hostRelativeFrameToPageBottomLeftPx,
  inputPartAllowsDelete,
  inputPartAllowsFrame,
  inputPartBoxChromeLabels,
  inputPartSupportsTypography,
  patchHostRelativeFramePageBottomLeftPx,
  resolveInputContrastBackground,
  resolveInputPartFontSize,
  resolveInputPartFrame,
  resolveViewportPixelSize,
  upsertInputPartState,
  type ComunicadoFrame,
  type ComunicadoInputBlock,
  type ComunicadoInputPartFrame,
  type ComunicadoInputPartState,
  type InputTextPartKind,
} from "@delpi/tv-dashboard-presentation";

import { enableInputFreeLayoutFromDom } from "../utils/enableInputFreeLayoutFromDom";
import { inputPartSelectionLabel } from "../utils/resolveSelectionChromeMode";
import { useComunicadoEditor } from "./comunicadoEditorContext";
import { PartInspectorToolbar } from "./PartInspectorToolbar";
import { TvRibbonColorPicker } from "./deck/TvRibbonColorPicker";
import { DeckField } from "./deck/DeckField";
import { DeckPropertySection } from "./deck/DeckPropertySection";

type Props = {
  pane?: boolean;
  block: ComunicadoInputBlock;
};

/** Inspetor da parte selecionada do filtro. */
export function InputPartInspector({ pane = false, block }: Props) {
  const {
    selectedInputPart,
    clearInputPartSelection,
    updateSelected,
    viewportProfile,
  } = useComunicadoEditor();

  if (!selectedInputPart) return null;

  const partState = getInputPartState(block.inputParts, selectedInputPart);
  const canHide = inputPartAllowsDelete(selectedInputPart);
  const isText = inputPartSupportsTypography(selectedInputPart);
  const boxLabels = inputPartBoxChromeLabels(selectedInputPart.kind);
  const title = inputPartSelectionLabel(selectedInputPart);
  const blockContrastBg = resolveInputContrastBackground(block.inputParts, block.style);
  const partFill = partState?.style?.fill?.trim();
  const textContrastBg =
    partFill && partFill !== "transparent" && partFill !== "none"
      ? partFill
      : blockContrastBg;
  const frameable = inputPartAllowsFrame(selectedInputPart);
  const explicitFrame = resolveInputPartFrame(partState);
  const slideDesign = resolveViewportPixelSize(viewportProfile);
  const partFramePct = clampInputPartFrame(
    explicitFrame ?? defaultInputPartFrame(selectedInputPart.kind),
  );
  const partFrame: ComunicadoFrame = {
    x: partFramePct.x,
    y: partFramePct.y,
    w: partFramePct.w ?? 20,
    h: partFramePct.h ?? 20,
  };
  const partFramePx = hostRelativeFrameToPageBottomLeftPx(
    partFrame,
    block.frame,
    slideDesign,
  );

  const persist = (
    patch: Omit<ComunicadoInputPartState, "frame" | "style"> & {
      style?: ComunicadoInputPartState["style"];
      frame?: ComunicadoInputPartFrame | null;
    },
  ) => {
    updateSelected({
      inputParts: upsertInputPartState(block.inputParts, selectedInputPart, patch),
    } as Partial<typeof block>);
  };

  const persistPartFramePx = (key: "x" | "y" | "w" | "h", rawPx: number) => {
    const nextPct = patchHostRelativeFramePageBottomLeftPx(
      partFrame,
      block.frame,
      key,
      rawPx,
      slideDesign,
    );
    persist({ frame: clampInputPartFrame(nextPct) });
  };

  const enableFreePosition = () => {
    enableInputFreeLayoutFromDom(block.id, block.inputParts, (next) => {
      updateSelected({ inputParts: next } as Partial<typeof block>);
    });
  };

  const clearFreePosition = () => {
    updateSelected({
      inputParts: clearInputPartsFreeLayoutFrames(block.inputParts),
    } as Partial<typeof block>);
  };

  const fontSize = isText
    ? resolveInputPartFontSize(selectedInputPart.kind as InputTextPartKind, partState?.style)
    : undefined;

  return (
    <DeckPropertySection
      pane={pane}
      title={title}
      hint="Estilo da subparte do filtro. Binding (parâmetro/valor) fica na seção Campo / Filtro."
      defaultOpen
    >
      <PartInspectorToolbar
        onBack={clearInputPartSelection}
        backLabel="Voltar ao filtro"
        onHide={
          canHide
            ? () => {
                persist({ visible: false });
                clearInputPartSelection();
              }
            : undefined
        }
        hideLabel="Ocultar parte"
        hideDanger
      />

      {selectedInputPart.kind === "frame" || selectedInputPart.kind === "icon" ? (
        <>
          <DeckField id="td-input-part-fill" label={boxLabels.fill}>
            <TvRibbonColorPicker
              label={boxLabels.fill}
              value={partState?.style?.fill ?? ""}
              onChange={(color) => persist({ style: { fill: color } })}
            />
          </DeckField>
          <DeckField id="td-input-part-stroke" label={boxLabels.stroke}>
            <TvRibbonColorPicker
              label={boxLabels.stroke}
              value={partState?.style?.stroke ?? ""}
              onChange={(color) => persist({ style: { stroke: color } })}
            />
          </DeckField>
          <DeckField id="td-input-part-radius" label="Cantos (px)">
            <NativeTextControl
              id="td-input-part-radius"
              type="number"
              min={0}
              max={80}
              value={String(partState?.style?.borderRadius ?? 0)}
              onChange={(value) =>
                persist({ style: { borderRadius: Math.max(0, Number(value) || 0) } })
              }
            />
          </DeckField>
        </>
      ) : null}

      {selectedInputPart.kind === "icon" ? (
        <DeckField id="td-input-part-icon-size" label="Tamanho do ícone (px)">
          <NativeTextControl
            id="td-input-part-icon-size"
            type="number"
            min={8}
            max={160}
            value={String(partState?.style?.iconSize ?? INPUT_ICON_DEFAULT_SIZE_PX)}
            onChange={(value) =>
              persist({
                style: {
                  iconSize: Math.max(8, Math.min(160, Number(value) || INPUT_ICON_DEFAULT_SIZE_PX)),
                },
              })
            }
          />
        </DeckField>
      ) : null}

      {frameable ? (
        <>
          <p className="td-deck-inspector__hint">
            Posição absoluta na página (px de design), origem no canto inferior esquerdo
          </p>
          {!explicitFrame ? (
            <button type="button" className="td-btn td-btn--sm" onClick={enableFreePosition}>
              Posicionar livremente no filtro…
            </button>
          ) : (
            <>
              <div className="td-part-inspector-toolbar__fields-row">
                <DeckField id="td-input-part-x" label="Posição X (px)">
                  <NativeTextControl
                    id="td-input-part-x"
                    type="number"
                    min={0}
                    max={slideDesign.width}
                    step={1}
                    value={formatDesignPx(partFramePx.x)}
                    onChange={(value) => persistPartFramePx("x", Number(value) || 0)}
                  />
                </DeckField>
                <DeckField id="td-input-part-y" label="Posição Y (px)">
                  <NativeTextControl
                    id="td-input-part-y"
                    type="number"
                    min={0}
                    max={slideDesign.height}
                    step={1}
                    value={formatDesignPx(partFramePx.y)}
                    onChange={(value) => persistPartFramePx("y", Number(value) || 0)}
                  />
                </DeckField>
              </div>
              <div className="td-part-inspector-toolbar__fields-row">
                <DeckField id="td-input-part-w" label="Largura (px)">
                  <NativeTextControl
                    id="td-input-part-w"
                    type="number"
                    min={1}
                    max={slideDesign.width}
                    step={1}
                    value={formatDesignPx(partFramePx.w)}
                    onChange={(value) => persistPartFramePx("w", Number(value) || 1)}
                  />
                </DeckField>
                <DeckField id="td-input-part-h" label="Altura (px)">
                  <NativeTextControl
                    id="td-input-part-h"
                    type="number"
                    min={1}
                    max={slideDesign.height}
                    step={1}
                    value={formatDesignPx(partFramePx.h)}
                    onChange={(value) => persistPartFramePx("h", Number(value) || 1)}
                  />
                </DeckField>
              </div>
              <button
                type="button"
                className="td-btn td-btn--sm td-btn--ghost"
                onClick={clearFreePosition}
              >
                Voltar ao fluxo automático
              </button>
            </>
          )}
        </>
      ) : null}

      {isText ? (
        <>
          <DeckField id="td-input-part-color" label="Cor do texto">
            <TvRibbonColorPicker
              label="Cor do texto"
              variant="text"
              contrastBackground={textContrastBg}
              value={partState?.style?.color ?? ""}
              onChange={(color) => persist({ style: { color } })}
            />
          </DeckField>
          <DeckField id="td-input-part-font-size" label="Tamanho (px)">
            <NativeTextControl
              id="td-input-part-font-size"
              type="number"
              min={10}
              max={72}
              value={String(fontSize ?? 14)}
              onChange={(value) =>
                persist({ style: { fontSize: Math.max(10, Math.min(72, Number(value) || 14)) } })
              }
            />
          </DeckField>
        </>
      ) : null}
    </DeckPropertySection>
  );
}
