/**
 * Inspector de opções de KPI: comparação, meta (literal/campo), título/subtítulo
 * dinâmicos e cores condicionais. Bindings tipados — resolução no enrich BE.
 */
import {
  FormSelectControl,
  NativeTextControl,
  type DelpiKpiCardTone,
  type DelpiKpiColorRule,
} from "@delpi/plugin-ui/index";
import type { ComunicadoKpiOptions } from "@delpi/tv-dashboard-presentation";

import { TV_DASHBOARD_HELP_TOOLTIPS } from "../content/helpTooltips";
import { useKpiBoundFieldOptions } from "../hooks/useKpiBoundFieldOptions";
import { useComunicadoEditor } from "./comunicadoEditorContext";
import { DeckField } from "./deck/DeckField";
import { DeckPropertySection } from "./deck/DeckPropertySection";
import { KpiColorRulesEditor } from "./KpiColorRulesEditor";
import { KpiDynamicFieldSelect } from "./KpiDynamicFieldSelect";

type Props = {
  pane?: boolean;
};

type MetaMode = "none" | "literal" | "field";

function resolveMetaMode(options: ComunicadoKpiOptions): MetaMode {
  if (options.targetField?.trim()) return "field";
  if (typeof options.target === "number" && Number.isFinite(options.target)) return "literal";
  return "none";
}

export function KpiViewOptionsInspector({ pane = false }: Props) {
  const { selected, updateSelected } = useComunicadoEditor();
  const fieldOptions = useKpiBoundFieldOptions(selected?.id);

  if (!selected || selected.type !== "kpi_view") return null;

  const options = selected.kpiOptions ?? {};
  const colorRules: DelpiKpiColorRule[] = options.colorRules ?? [];
  const metaMode = resolveMetaMode(options);

  const patch = (partial: Partial<ComunicadoKpiOptions>) => {
    updateSelected({
      kpiOptions: {
        ...options,
        ...partial,
      },
    });
  };

  const setMetaMode = (mode: MetaMode) => {
    if (mode === "none") {
      patch({
        target: undefined,
        targetField: undefined,
        targetAggregation: undefined,
        comparisonMode: "none",
      });
      return;
    }
    if (mode === "field") {
      const field = options.targetField?.trim() || fieldOptions[0]?.field;
      patch({
        targetField: field,
        targetAggregation: options.targetAggregation ?? "first",
        target: undefined,
        comparisonMode: "target",
      });
      return;
    }
    patch({
      targetField: undefined,
      targetAggregation: undefined,
      target: typeof options.target === "number" ? options.target : 0,
      comparisonMode: "target",
    });
  };

  return (
    <DeckPropertySection
      title="KPI"
      hint={TV_DASHBOARD_HELP_TOOLTIPS.ribbon.kpiDynamicMeta}
      pane={pane}
    >
      <DeckField id="kpi-comparison-mode" label="Modo de comparação">
        <FormSelectControl
          id="kpi-comparison-mode"
          ariaLabel="Modo de comparação"
          value={options.comparisonMode ?? "none"}
          onChange={(value) =>
            patch({
              comparisonMode: value as ComunicadoKpiOptions["comparisonMode"],
            })
          }
          options={[
            { value: "none", label: "Nenhuma" },
            { value: "target", label: "Versus meta" },
            { value: "previous", label: "Versus período anterior" },
          ]}
        />
      </DeckField>

      <DeckField id="kpi-meta-mode" label="Fonte da meta">
        <FormSelectControl
          id="kpi-meta-mode"
          ariaLabel="Fonte da meta"
          value={metaMode}
          onChange={(value) => setMetaMode(value as MetaMode)}
          options={[
            { value: "none", label: "Sem meta" },
            { value: "literal", label: "Valor fixo" },
            ...(fieldOptions.length > 0
              ? [{ value: "field", label: "Campo do DataModel" }]
              : []),
          ]}
        />
      </DeckField>

      {metaMode === "literal" ? (
        <DeckField id="kpi-target" label="Meta (número)">
          <NativeTextControl
            id="kpi-target"
            type="number"
            value={options.target ?? ""}
            onChange={(raw) => {
              const trimmed = raw.trim();
              patch({
                target: trimmed === "" ? undefined : Number(trimmed),
                comparisonMode: trimmed === "" ? "none" : "target",
              });
            }}
          />
        </DeckField>
      ) : null}

      {metaMode === "field" ? (
        <KpiDynamicFieldSelect
          id="kpi-target-field"
          label="Campo da meta"
          value={options.targetField}
          fieldOptions={fieldOptions}
          noneLabel="Selecione o campo"
          onChange={(field) =>
            patch({
              targetField: field,
              targetAggregation: "first",
              target: undefined,
              comparisonMode: field ? "target" : "none",
            })
          }
        />
      ) : null}

      <DeckField id="kpi-show-target" label="Exibir valor da meta">
        <FormSelectControl
          id="kpi-show-target"
          ariaLabel="Exibir valor da meta"
          value={options.showTarget === true ? "on" : "off"}
          onChange={(value) => patch({ showTarget: value === "on" })}
          options={[
            { value: "off", label: "Oculta (binding preservado)" },
            { value: "on", label: "Exibir número formatado" },
          ]}
        />
      </DeckField>

      <DeckField id="kpi-higher-is-better" label="Direção">
        <FormSelectControl
          id="kpi-higher-is-better"
          ariaLabel="Direção do indicador"
          value={options.higherIsBetter === false ? "lower" : "higher"}
          onChange={(value) => patch({ higherIsBetter: value !== "lower" })}
          options={[
            { value: "higher", label: "Maior é melhor" },
            { value: "lower", label: "Menor é melhor" },
          ]}
        />
      </DeckField>

      <DeckField id="kpi-title" label="Título (literal)">
        <NativeTextControl
          id="kpi-title"
          value={options.title ?? ""}
          onChange={(value) => patch({ title: value || undefined })}
        />
      </DeckField>
      <KpiDynamicFieldSelect
        id="kpi-title-field"
        label="Título dinâmico (campo)"
        value={options.titleField}
        fieldOptions={fieldOptions}
        onChange={(field) => patch({ titleField: field })}
      />

      <DeckField id="kpi-subtitle" label="Subtítulo (literal)">
        <NativeTextControl
          id="kpi-subtitle"
          value={options.subtitle ?? ""}
          onChange={(value) => patch({ subtitle: value || undefined })}
        />
      </DeckField>
      <KpiDynamicFieldSelect
        id="kpi-subtitle-field"
        label="Subtítulo dinâmico (campo)"
        value={options.subtitleField}
        fieldOptions={fieldOptions}
        onChange={(field) => patch({ subtitleField: field })}
      />

      <DeckField id="kpi-tone" label="Tom padrão">
        <FormSelectControl
          id="kpi-tone"
          ariaLabel="Tom padrão do KPI"
          value={options.tone ?? "default"}
          onChange={(value) => patch({ tone: value as DelpiKpiCardTone })}
          options={[
            { value: "default", label: "Padrão" },
            { value: "positive", label: "Positivo" },
            { value: "negative", label: "Negativo" },
            { value: "warning", label: "Atenção" },
          ]}
        />
      </DeckField>

      <DeckField id="kpi-color-rules" label="Cores condicionais">
        <KpiColorRulesEditor
          idPrefix="kpi"
          rules={colorRules}
          fieldOptions={fieldOptions}
          onChange={(next) => patch({ colorRules: next })}
        />
      </DeckField>
    </DeckPropertySection>
  );
}
