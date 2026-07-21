import {
  FormSelectControl,
  LucideIconField,
  NativeTextControl,
  type DelpiKpiCardTone,
} from "@delpi/plugin-ui/index";
import {
  KPI_ELEMENT_CATALOG,
  applyKpiElementVisibility,
  isKpiElementEnabled,
  isKpiElementOpenForPart,
  kpiElementPrimaryPartRef,
  mergeComunicadoKpiOptions,
  mergeKpiPartsWithOptions,
  partsToKpiOptions,
  type ComunicadoKpiOptions,
  type ComunicadoKpiViewBlock,
  type KpiElementId,
  type ComunicadoBlock,
} from "@delpi/tv-dashboard-presentation";

import { TV_DASHBOARD_HELP_TOOLTIPS } from "../content/helpTooltips";
import { useComunicadoEditor } from "./comunicadoEditorContext";
import { InspectorElementRow } from "./InspectorElementRow";
import { KpiColorRulesEditor } from "./KpiColorRulesEditor";
import { KpiPartInspector } from "./KpiPartInspector";
import { DeckField } from "./deck/DeckField";
import { DeckPropertySection } from "./deck/DeckPropertySection";

type Props = { pane?: boolean };

const TONE_OPTIONS: Array<{ value: DelpiKpiCardTone; label: string }> = [
  { value: "default", label: "Padrão" },
  { value: "positive", label: "Positivo" },
  { value: "negative", label: "Negativo" },
  { value: "warning", label: "Atenção" },
];

export function KpiViewOptionsInspector({ pane = false }: Props) {
  const { selected, updateSelected, selectKpiPart, selectedKpiPart } = useComunicadoEditor();

  if (!selected || selected.type !== "kpi_view") return null;

  const block = selected as ComunicadoKpiViewBlock;
  const options = mergeComunicadoKpiOptions({
    ...block.kpiOptions,
    ...partsToKpiOptions(block.kpiParts),
  });
  const hasPartSelection = Boolean(selectedKpiPart);
  const rules = options.colorRules ?? [];

  const persistOptions = (nextOptions: ComunicadoKpiOptions) => {
    updateSelected({
      kpiOptions: nextOptions,
      kpiParts: mergeKpiPartsWithOptions(block.kpiParts, nextOptions),
    } as Partial<ComunicadoBlock>);
  };

  const patchOptions = (patch: Partial<ComunicadoKpiOptions>) => {
    persistOptions(mergeComunicadoKpiOptions({ ...options, ...patch }));
  };

  const focusElement = (elementId: KpiElementId) => {
    selectKpiPart(block.id, kpiElementPrimaryPartRef(elementId));
  };

  const toggleElement = (elementId: KpiElementId, enabled: boolean) => {
    if ((elementId === "kpiValue" || elementId === "kpiCard") && !enabled) {
      focusElement(elementId);
      return;
    }
    const result = applyKpiElementVisibility(elementId, enabled, options, block.kpiParts);
    updateSelected({
      kpiOptions: mergeComunicadoKpiOptions(result.options),
      kpiParts: result.parts,
    } as Partial<ComunicadoBlock>);
    if (enabled) focusElement(elementId);
  };

  return (
    <>
      <KpiPartInspector pane={pane} block={block} />

      {!hasPartSelection ? (
        <>
          <p className="td-deck-inspector__hint td-deck-inspector__hint--stage">
            Duplo clique no palco para selecionar uma parte. Detalhes abrem ao selecionar a parte.
          </p>

          <DeckPropertySection
            pane={pane}
            title="Elementos do KPI"
            hint={TV_DASHBOARD_HELP_TOOLTIPS.data.kpiElements}
            defaultOpen
          >
            <div className="td-chart-elements" role="group" aria-label="Elementos do KPI">
              {KPI_ELEMENT_CATALOG.map((element) => {
                const enabled = isKpiElementEnabled(element.id, options, block.kpiParts);
                const focused = isKpiElementOpenForPart(element.id, selectedKpiPart);
                return (
                  <InspectorElementRow
                    key={element.id}
                    id={`td-kpi-element-${element.id}`}
                    label={element.label}
                    hint={element.description}
                    enabled={enabled}
                    focused={focused}
                    onToggle={(next) => toggleElement(element.id, next)}
                    onSelect={() => focusElement(element.id)}
                  />
                );
              })}
            </div>
          </DeckPropertySection>

          <DeckPropertySection
            pane={pane}
            title="Aparência"
            hint={TV_DASHBOARD_HELP_TOOLTIPS.data.kpiCard}
            defaultOpen
          >
            <DeckField id="td-kpi-unit" label="Unidade">
              <NativeTextControl
                id="td-kpi-unit"
                value={options.unit ?? ""}
                placeholder="%, R$, un…"
                onChange={(value) => patchOptions({ unit: value.trim() || undefined })}
              />
            </DeckField>
            <DeckField id="td-kpi-format" label="Formato do valor">
              <FormSelectControl
                id="td-kpi-format"
                ariaLabel="Formato do valor"
                value={options.valueFormat ?? "raw"}
                onChange={(value) =>
                  patchOptions({
                    valueFormat: value as ComunicadoKpiOptions["valueFormat"],
                  })
                }
                options={[
                  { value: "raw", label: "Como veio da fonte" },
                  { value: "number", label: "Número" },
                  { value: "percent", label: "Percentual" },
                  { value: "currency", label: "Moeda" },
                  { value: "compact", label: "Compacto" },
                ]}
              />
            </DeckField>
            <DeckField id="td-kpi-tone" label="Cor base (tone)">
              <FormSelectControl
                id="td-kpi-tone"
                ariaLabel="Cor base"
                value={options.tone ?? "default"}
                onChange={(value) => patchOptions({ tone: value as DelpiKpiCardTone })}
                options={TONE_OPTIONS}
              />
            </DeckField>
            {options.showIcon !== false ? (
              <DeckField id="td-kpi-icon" label="Ícone">
                <LucideIconField
                  value={options.iconName ?? "Gauge"}
                  defaultIcon="Gauge"
                  nameFormat="pascal"
                  curatedOnly={false}
                  labels={{ clear: "Usar ícone padrão", close: "Fechar" }}
                  onChange={(name) =>
                    patchOptions({ iconName: name?.trim() || "Gauge", showIcon: true })
                  }
                  ariaLabel="Selecionar ícone do KPI"
                />
              </DeckField>
            ) : null}
          </DeckPropertySection>

          <DeckPropertySection
            pane={pane}
            title="Cores condicionais"
            hint={TV_DASHBOARD_HELP_TOOLTIPS.data.kpiColorRules}
            defaultOpen={rules.length > 0}
          >
            <KpiColorRulesEditor
              idPrefix="td-kpi-global-rules"
              rules={rules}
              onChange={(colorRules) => patchOptions({ colorRules })}
            />
          </DeckPropertySection>
        </>
      ) : null}
    </>
  );
}
