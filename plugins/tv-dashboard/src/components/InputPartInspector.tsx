import { NativeTextControl } from "@delpi/plugin-ui/index";
import {
  INPUT_ICON_DEFAULT_SIZE_PX,
  getInputPartState,
  inputPartAllowsDelete,
  inputPartBoxChromeLabels,
  inputPartSupportsTypography,
  resolveInputPartFontSize,
  upsertInputPartState,
  type ComunicadoInputBlock,
  type InputTextPartKind,
} from "@delpi/tv-dashboard-presentation";

import { useComunicadoEditor } from "./comunicadoEditorContext";
import { PartInspectorToolbar } from "./PartInspectorToolbar";
import { TvRibbonColorPicker } from "./deck/TvRibbonColorPicker";
import { DeckField } from "./deck/DeckField";
import { DeckPropertySection } from "./deck/DeckPropertySection";
import { inputPartSelectionLabel } from "../utils/resolveSelectionChromeMode";

type Props = {
  pane?: boolean;
  block: ComunicadoInputBlock;
};

/** Inspetor da parte selecionada do filtro. */
export function InputPartInspector({ pane = false, block }: Props) {
  const { selectedInputPart, clearInputPartSelection, updateSelected } = useComunicadoEditor();

  if (!selectedInputPart) return null;

  const partState = getInputPartState(block.inputParts, selectedInputPart);
  const canHide = inputPartAllowsDelete(selectedInputPart);
  const isText = inputPartSupportsTypography(selectedInputPart);
  const boxLabels = inputPartBoxChromeLabels(selectedInputPart.kind);
  const title = inputPartSelectionLabel(selectedInputPart);

  const persist = (patch: {
    visible?: boolean;
    style?: {
      fill?: string;
      color?: string;
      stroke?: string;
      strokeWidth?: number;
      borderRadius?: number;
      fontSize?: number;
      iconSize?: number;
    };
  }) => {
    updateSelected({
      inputParts: upsertInputPartState(block.inputParts, selectedInputPart, patch),
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
              value={partState?.style?.fill ?? ""}
              onChange={(color) => persist({ style: { fill: color } })}
            />
          </DeckField>
          <DeckField id="td-input-part-stroke" label={boxLabels.stroke}>
            <TvRibbonColorPicker
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

      {isText ? (
        <>
          <DeckField id="td-input-part-color" label="Cor do texto">
            <TvRibbonColorPicker
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
