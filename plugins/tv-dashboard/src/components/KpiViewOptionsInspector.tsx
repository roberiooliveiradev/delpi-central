import { useRef, useState } from "react";
import {
  AnchoredPanelPortal,
  FormSelectControl,
  LucideIconGridPanel,
  NativeCheckboxControl,
  NativeTextControl,
  type DelpiKpiCardTone,
  type DelpiKpiColorRuleOp,
} from "@delpi/plugin-ui/index";
import {
  COMUNICADO_ICON_OPTIONS,
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
} from "@delpi/tv-dashboard-presentation";

import { TV_DASHBOARD_HELP_TOOLTIPS } from "../content/helpTooltips";
import { useComunicadoEditor } from "./comunicadoEditorContext";
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

const OP_OPTIONS: Array<{ value: DelpiKpiColorRuleOp; label: string }> = [
  { value: "gte", label: "≥" },
  { value: "gt", label: ">" },
  { value: "lte", label: "≤" },
  { value: "lt", label: "<" },
  { value: "eq", label: "=" },
  { value: "between", label: "entre" },
];

function KpiElementRow({
  elementId,
  enabled,
  focused,
  onToggle,
  onSelect,
  label,
  hint,
}: {
  elementId: KpiElementId;
  enabled: boolean;
  focused: boolean;
  onToggle: (next: boolean) => void;
  onSelect: () => void;
  label: string;
  hint?: string;
}) {
  return (
    <div
      className={["td-chart-element", "td-chart-element--row", focused ? "td-chart-element--focused" : null]
        .filter(Boolean)
        .join(" ")}
    >
      <div className="td-chart-element__summary">
        <span className="td-chart-element__toggle" onClick={(event) => event.stopPropagation()}>
          <NativeCheckboxControl
            checked={enabled}
            aria-label={`Exibir ${label}`}
            onChange={onToggle}
          />
        </span>
        <button
          type="button"
          className="td-chart-element__label-btn"
          id={`td-kpi-element-${elementId}`}
          title={hint}
          onClick={(event) => {
            event.preventDefault();
            onSelect();
          }}
        >
          {label}
        </button>
      </div>
    </div>
  );
}

export function KpiViewOptionsInspector({ pane = false }: Props) {
  const { selected, updateSelected, selectKpiPart, selectedKpiPart } = useComunicadoEditor();
  const iconAnchorRef = useRef<HTMLDivElement>(null);
  const iconPanelRef = useRef<HTMLDivElement>(null);
  const [iconMenuOpen, setIconMenuOpen] = useState(false);

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
    } as Partial<typeof selected>);
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
    } as Partial<typeof selected>);
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
                  <KpiElementRow
                    key={element.id}
                    elementId={element.id}
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
              <div ref={iconAnchorRef} className="td-composer__dropdown">
                <DeckField id="td-kpi-icon" label="Ícone">
                  <button
                    type="button"
                    className="td-btn td-btn--sm td-btn--ghost"
                    onClick={() => setIconMenuOpen((open) => !open)}
                  >
                    {options.iconName ?? "Gauge"}
                  </button>
                </DeckField>
                {iconMenuOpen ? (
                  <AnchoredPanelPortal
                    open={iconMenuOpen}
                    anchorRef={iconAnchorRef}
                    panelRef={iconPanelRef}
                    variant="bare"
                    className="td-icon-library-portal"
                    role="menu"
                    aria-label="Ícone do KPI"
                  >
                    <LucideIconGridPanel
                      title="Ícone do KPI"
                      items={COMUNICADO_ICON_OPTIONS.map((item) => ({
                        name: item.name,
                        label: item.label,
                      }))}
                      onSelect={(name) => {
                        patchOptions({ iconName: name });
                        setIconMenuOpen(false);
                      }}
                    />
                  </AnchoredPanelPortal>
                ) : null}
              </div>
            ) : null}
          </DeckPropertySection>

          <DeckPropertySection
            pane={pane}
            title="Cores condicionais"
            hint={TV_DASHBOARD_HELP_TOOLTIPS.data.kpiColorRules}
            defaultOpen={rules.length > 0}
          >
            <p className="td-deck-inspector__hint">Primeira regra que casar com o valor define a cor.</p>
            {rules.map((rule, index) => (
              <div key={`kpi-rule-${index}`} className="td-kpi-rule">
                <DeckField id={`td-kpi-rule-op-${index}`} label="Se valor">
                  <FormSelectControl
                    id={`td-kpi-rule-op-${index}`}
                    ariaLabel="Operador"
                    value={rule.op}
                    onChange={(value) => {
                      const next = [...rules];
                      next[index] = { ...rule, op: value as DelpiKpiColorRuleOp };
                      patchOptions({ colorRules: next });
                    }}
                    options={OP_OPTIONS}
                  />
                </DeckField>
                <DeckField id={`td-kpi-rule-value-${index}`} label="Limiar">
                  <NativeTextControl
                    id={`td-kpi-rule-value-${index}`}
                    type="number"
                    value={String(rule.value)}
                    onChange={(raw) => {
                      const next = [...rules];
                      next[index] = { ...rule, value: Number(raw) || 0 };
                      patchOptions({ colorRules: next });
                    }}
                  />
                </DeckField>
                {rule.op === "between" ? (
                  <DeckField id={`td-kpi-rule-value-to-${index}`} label="Até">
                    <NativeTextControl
                      id={`td-kpi-rule-value-to-${index}`}
                      type="number"
                      value={rule.valueTo ?? ""}
                      onChange={(raw) => {
                        const next = [...rules];
                        next[index] = { ...rule, valueTo: raw.trim() ? Number(raw) : undefined };
                        patchOptions({ colorRules: next });
                      }}
                    />
                  </DeckField>
                ) : null}
                <DeckField id={`td-kpi-rule-tone-${index}`} label="Tom">
                  <FormSelectControl
                    id={`td-kpi-rule-tone-${index}`}
                    ariaLabel="Tom da regra"
                    value={rule.tone ?? "default"}
                    onChange={(value) => {
                      const next = [...rules];
                      next[index] = { ...rule, tone: value as DelpiKpiCardTone };
                      patchOptions({ colorRules: next });
                    }}
                    options={TONE_OPTIONS}
                  />
                </DeckField>
                <button
                  type="button"
                  className="td-btn td-btn--sm td-btn--ghost"
                  onClick={() => patchOptions({ colorRules: rules.filter((_, i) => i !== index) })}
                >
                  Remover regra
                </button>
              </div>
            ))}
            <button
              type="button"
              className="td-btn td-btn--sm td-btn--ghost"
              onClick={() =>
                patchOptions({
                  colorRules: [...rules, { op: "gte", value: 90, tone: "positive" }],
                })
              }
            >
              Adicionar regra
            </button>
          </DeckPropertySection>
        </>
      ) : null}
    </>
  );
}
