import { useRef, useState } from "react";
import {
  AnchoredPanelPortal,
  FormSelectControl,
  LucideIconGridPanel,
  NativeTextControl,
  type DelpiKpiCardTone,
  type DelpiKpiColorRuleOp,
} from "@delpi/plugin-ui/index";
import {
  COMUNICADO_ICON_OPTIONS,
  mergeComunicadoKpiOptions,
  type ComunicadoKpiOptions,
  type ComunicadoKpiViewBlock,
} from "@delpi/tv-dashboard-presentation";

import { TV_DASHBOARD_HELP_TOOLTIPS } from "../content/helpTooltips";
import { useComunicadoEditor } from "./comunicadoEditorContext";
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

export function KpiViewOptionsInspector({ pane = false }: Props) {
  const { selected, updateSelected } = useComunicadoEditor();
  const iconAnchorRef = useRef<HTMLDivElement>(null);
  const iconPanelRef = useRef<HTMLDivElement>(null);
  const [iconMenuOpen, setIconMenuOpen] = useState(false);

  if (!selected || selected.type !== "kpi_view") return null;

  const block = selected as ComunicadoKpiViewBlock;
  const options = mergeComunicadoKpiOptions(block.kpiOptions);

  function patchOptions(patch: Partial<ComunicadoKpiOptions>) {
    updateSelected({
      kpiOptions: mergeComunicadoKpiOptions({ ...options, ...patch }),
    } as Partial<typeof selected>);
  }

  const rules = options.colorRules ?? [];

  return (
    <>
      <DeckPropertySection pane={pane} title="Card KPI" hint={TV_DASHBOARD_HELP_TOOLTIPS.data.kpiCard} defaultOpen>
        <DeckField id="td-kpi-title" label="Título">
          <NativeTextControl
            id="td-kpi-title"
            value={options.title ?? ""}
            placeholder="Usar label da fonte"
            onChange={(value) => patchOptions({ title: value.trim() || undefined })}
          />
        </DeckField>
        <DeckField id="td-kpi-subtitle" label="Subtítulo">
          <NativeTextControl
            id="td-kpi-subtitle"
            value={options.subtitle ?? ""}
            onChange={(value) => patchOptions({ subtitle: value.trim() || undefined })}
          />
        </DeckField>
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
        <div className="td-deck-inspector__row">
          <label className="td-check">
            <input
              type="checkbox"
              checked={options.showIcon !== false}
              onChange={(event) => patchOptions({ showIcon: event.target.checked })}
            />
            Exibir ícone
          </label>
        </div>
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
  );
}
