import { NativeTextControl } from "@delpi/plugin-ui/index";
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

  const persistPart = (patch: {
    content?: string;
    style?: { fill?: string; color?: string };
    visible?: boolean;
  }) => {
    const nextParts = upsertKpiPartState(block.kpiParts, selectedKpiPart, patch);
    const nextOptions = mergeComunicadoKpiOptions({
      ...options,
      ...partsToKpiOptions(nextParts),
    });
    if (selectedKpiPart.kind === "title" && patch.content !== undefined) {
      nextOptions.title = patch.content.trim() || undefined;
    }
    if (selectedKpiPart.kind === "hint" && patch.content !== undefined) {
      nextOptions.subtitle = patch.content.trim() || undefined;
    }
    if (selectedKpiPart.kind === "card" && patch.style?.fill) {
      nextOptions.backgroundColor = patch.style.fill;
    }
    if (selectedKpiPart.kind === "value" && patch.style?.color) {
      nextOptions.valueColor = patch.style.color;
    }
    updateSelected({
      kpiOptions: nextOptions,
      kpiParts: mergeKpiPartsWithOptions(nextParts, nextOptions),
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
      defaultOpen
    >
      <div className="td-deck-inspector__row">
        <button
          type="button"
          className="td-btn td-btn--sm td-btn--ghost"
          onClick={() => clearKpiPartSelection()}
        >
          Voltar aos elementos
        </button>
        {selectedKpiPart.kind === "title" || selectedKpiPart.kind === "hint" ? (
          <button
            type="button"
            className="td-btn td-btn--sm td-btn--ghost"
            onClick={() => beginEditKpiPart(block.id, selectedKpiPart)}
          >
            Editar no palco
          </button>
        ) : null}
        {canDelete ? (
          <button type="button" className="td-btn td-btn--sm td-btn--ghost" onClick={removePart}>
            Ocultar parte
          </button>
        ) : null}
      </div>

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
            onChange={(value) => persistPart({ content: value, visible: true })}
          />
        </DeckField>
      ) : null}

      {selectedKpiPart.kind === "card" ? (
        <DeckField id="td-kpi-part-card-fill" label="Fundo do card">
          <TvRibbonColorPicker
            inline
            label="Fundo"
            value={partState?.style?.fill ?? options.backgroundColor ?? "#ffffff"}
            onChange={(color) => persistPart({ style: { fill: color } })}
          />
        </DeckField>
      ) : null}

      {selectedKpiPart.kind === "value" ? (
        <DeckField id="td-kpi-part-value-color" label="Cor do valor">
          <TvRibbonColorPicker
            inline
            label="Cor do valor"
            value={partState?.style?.color ?? options.valueColor ?? "#111827"}
            onChange={(color) => persistPart({ style: { color } })}
          />
        </DeckField>
      ) : null}

      {selectedKpiPart.kind === "icon" ? (
        <p className="td-deck-inspector__hint">
          Escolha o ícone e o tom nas seções gerais ao voltar aos elementos, ou oculte esta parte.
        </p>
      ) : null}
    </DeckPropertySection>
  );
}
