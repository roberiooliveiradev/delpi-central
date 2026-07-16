import {
  FormSelectControl,
  NativeTextControl,
  type DelpiKpiCardTone,
  type DelpiKpiColorRule,
  type DelpiKpiColorRuleOp,
} from "@delpi/plugin-ui/index";

import { DeckField } from "./deck/DeckField";

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

type Props = {
  idPrefix: string;
  rules: DelpiKpiColorRule[];
  onChange: (next: DelpiKpiColorRule[] | undefined) => void;
  compact?: boolean;
};

/** Editor completo de regras condicionais de KPI (op, limiar, between, tom). */
export function KpiColorRulesEditor({ idPrefix, rules, onChange, compact = false }: Props) {
  const patch = (next: DelpiKpiColorRule[]) => {
    onChange(next.length > 0 ? next : undefined);
  };

  return (
    <div className={compact ? "td-kpi-rules td-kpi-rules--compact" : "td-kpi-rules"}>
      <p className="td-deck-inspector__hint">Primeira regra que casar com o valor define a cor.</p>
      {rules.map((rule, index) => (
        <div key={`${idPrefix}-rule-${index}`} className="td-kpi-rule">
          <DeckField id={`${idPrefix}-op-${index}`} label="Se valor">
            <FormSelectControl
              id={`${idPrefix}-op-${index}`}
              className={compact ? "delpi-ui-select--compact" : undefined}
              ariaLabel="Operador"
              value={rule.op}
              onChange={(value) => {
                const next = [...rules];
                next[index] = { ...rule, op: value as DelpiKpiColorRuleOp };
                patch(next);
              }}
              options={OP_OPTIONS}
            />
          </DeckField>
          <DeckField id={`${idPrefix}-value-${index}`} label="Limiar">
            <NativeTextControl
              id={`${idPrefix}-value-${index}`}
              className={compact ? "delpi-ui-native-control--compact" : undefined}
              type="number"
              value={String(rule.value)}
              onChange={(raw) => {
                const next = [...rules];
                next[index] = { ...rule, value: Number(raw) || 0 };
                patch(next);
              }}
            />
          </DeckField>
          {rule.op === "between" ? (
            <DeckField id={`${idPrefix}-value-to-${index}`} label="Até">
              <NativeTextControl
                id={`${idPrefix}-value-to-${index}`}
                className={compact ? "delpi-ui-native-control--compact" : undefined}
                type="number"
                value={rule.valueTo ?? ""}
                onChange={(raw) => {
                  const next = [...rules];
                  next[index] = { ...rule, valueTo: raw.trim() ? Number(raw) : undefined };
                  patch(next);
                }}
              />
            </DeckField>
          ) : null}
          <DeckField id={`${idPrefix}-tone-${index}`} label="Tom">
            <FormSelectControl
              id={`${idPrefix}-tone-${index}`}
              className={compact ? "delpi-ui-select--compact" : undefined}
              ariaLabel="Tom da regra"
              value={rule.tone ?? "default"}
              onChange={(value) => {
                const next = [...rules];
                next[index] = { ...rule, tone: value as DelpiKpiCardTone };
                patch(next);
              }}
              options={TONE_OPTIONS}
            />
          </DeckField>
          <button
            type="button"
            className="td-btn td-btn--sm td-btn--ghost"
            onClick={() => patch(rules.filter((_, i) => i !== index))}
          >
            Remover regra
          </button>
        </div>
      ))}
      <button
        type="button"
        className="td-btn td-btn--sm td-btn--ghost"
        onClick={() => patch([...rules, { op: "gte", value: 90, tone: "positive" }])}
      >
        Adicionar regra
      </button>
    </div>
  );
}
