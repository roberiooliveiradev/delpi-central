import {
  KPI_ELEMENT_CATALOG,
  applyKpiElementVisibility,
  isKpiElementEnabled,
  kpiElementPrimaryPartRef,
  mergeComunicadoKpiOptions,
  mergeKpiPartsWithOptions,
  partsToKpiOptions,
  type ComunicadoBlock,
  type ComunicadoKpiOptions,
  type ComunicadoKpiViewBlock,
  type KpiElementId,
} from "@delpi/tv-dashboard-presentation";

import { ComplexSelectionFloatToolbar } from "./ComplexSelectionFloatToolbar";
import { FloatChecklist, FloatChecklistItem } from "./FloatChecklist";
import { useComunicadoEditor } from "./comunicadoEditorContext";

type Props = {
  block: ComunicadoKpiViewBlock;
};

const TONE_OPTIONS: Array<{ value: NonNullable<ComunicadoKpiOptions["tone"]>; label: string }> = [
  { value: "default", label: "Tom padrão" },
  { value: "positive", label: "Tom positivo" },
  { value: "negative", label: "Tom negativo" },
  { value: "warning", label: "Tom atenção" },
];

/**
 * Float do KPI — + elementos (parts), pincel aparência, funil dados/métricas.
 */
export function KpiSelectionFloatToolbar({ block }: Props) {
  const { updateSelected, openDataPanel, selectKpiPart, setSelectionPanelTab } =
    useComunicadoEditor();

  const options = mergeComunicadoKpiOptions({
    ...block.kpiOptions,
    ...partsToKpiOptions(block.kpiParts),
  });

  const persistOptions = (nextOptions: ComunicadoKpiOptions) => {
    updateSelected({
      kpiOptions: nextOptions,
      kpiParts: mergeKpiPartsWithOptions(block.kpiParts, nextOptions),
    } as Partial<ComunicadoBlock>);
  };

  const patchOptions = (patch: Partial<ComunicadoKpiOptions>) => {
    persistOptions(mergeComunicadoKpiOptions({ ...options, ...patch }));
  };

  const toggleElement = (elementId: KpiElementId, enabled: boolean) => {
    if ((elementId === "kpiValue" || elementId === "kpiCard") && !enabled) {
      selectKpiPart(block.id, kpiElementPrimaryPartRef(elementId));
      return;
    }
    const result = applyKpiElementVisibility(elementId, enabled, options, block.kpiParts);
    updateSelected({
      kpiOptions: mergeComunicadoKpiOptions(result.options),
      kpiParts: result.parts,
    } as Partial<ComunicadoBlock>);
    if (enabled) selectKpiPart(block.id, kpiElementPrimaryPartRef(elementId));
  };

  const openDataFocus = (anchorId?: string) => {
    openDataPanel();
    setSelectionPanelTab("data");
    if (anchorId) {
      requestAnimationFrame(() => {
        document.getElementById(anchorId)?.scrollIntoView({ block: "nearest" });
      });
    }
  };

  const formatLabel =
    options.valueFormat === "percent"
      ? "Percentual"
      : options.valueFormat === "number"
        ? "Número"
        : options.valueFormat === "compact"
          ? "Compacto"
          : "Como veio";

  return (
    <ComplexSelectionFloatToolbar
      blockId={block.id}
      frame={block.frame}
      labels={{
        elements: "Elementos do KPI",
        style: "Aparência do KPI",
        data: "Dados do KPI",
      }}
      renderElements={() => (
        <FloatChecklist aria-label="Elementos do KPI">
          {KPI_ELEMENT_CATALOG.map((element) => {
            const enabled = isKpiElementEnabled(element.id, options, block.kpiParts);
            return (
              <FloatChecklistItem
                key={element.id}
                label={element.label}
                active={enabled}
                onClick={() => toggleElement(element.id, !enabled)}
              />
            );
          })}
        </FloatChecklist>
      )}
      renderStyle={(close) => (
        <FloatChecklist aria-label="Aparência do KPI">
          {TONE_OPTIONS.map((tone) => (
            <FloatChecklistItem
              key={tone.value}
              label={tone.label}
              active={(options.tone ?? "default") === tone.value}
              onClick={() => {
                patchOptions({ tone: tone.value });
                close();
              }}
            />
          ))}
          <FloatChecklistItem
            label={`Formato: ${formatLabel}`}
            onClick={() => {
              patchOptions({
                valueFormat:
                  options.valueFormat === "percent"
                    ? "number"
                    : options.valueFormat === "number"
                      ? "compact"
                      : options.valueFormat === "compact"
                        ? "raw"
                        : "percent",
              });
            }}
          />
        </FloatChecklist>
      )}
      renderData={(close) => (
        <>
          <button
            type="button"
            className="td-deck-ribbon__cascade-item"
            onClick={() => {
              openDataFocus("td-view-data-source");
              close();
            }}
          >
            Selecionar fonte…
          </button>
          <button
            type="button"
            className="td-deck-ribbon__cascade-item"
            onClick={() => {
              openDataFocus("td-view-kpi-metrics");
              close();
            }}
          >
            Métricas e cálculo…
          </button>
        </>
      )}
    />
  );
}
