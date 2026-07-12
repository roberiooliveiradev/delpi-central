import type { CSSProperties, ReactNode } from "react";

import { MetricKpiCard, metricKpiCardBemClasses, type MetricKpiCardTone } from "./MetricKpiCard";

export type { MetricKpiCardTone as DelpiKpiCardTone };

export type DelpiKpiColorRuleOp = "gt" | "gte" | "lt" | "lte" | "eq" | "between";

export type DelpiKpiColorRule = {
  op: DelpiKpiColorRuleOp;
  value: number;
  valueTo?: number;
  tone?: MetricKpiCardTone;
  valueColor?: string;
  backgroundColor?: string;
};

export type DelpiKpiResolvedPresentation = {
  tone: MetricKpiCardTone;
  valueColor?: string;
  backgroundColor?: string;
  matchedRuleIndex: number | null;
};

/**
 * Resolve tone/cores a partir do valor numérico e regras (primeira que casa vence).
 * Componente canônico — dashboards e TV reutilizam sem duplicar a lógica.
 */
export function resolveDelpiKpiTone(
  numericValue: number | null | undefined,
  rules: DelpiKpiColorRule[] | undefined,
  fallbackTone: MetricKpiCardTone = "default",
): DelpiKpiResolvedPresentation {
  if (numericValue == null || !Number.isFinite(numericValue) || !rules?.length) {
    return { tone: fallbackTone, matchedRuleIndex: null };
  }

  for (let index = 0; index < rules.length; index += 1) {
    const rule = rules[index];
    if (!rule || !matchesRule(numericValue, rule)) continue;
    return {
      tone: rule.tone ?? fallbackTone,
      valueColor: rule.valueColor,
      backgroundColor: rule.backgroundColor,
      matchedRuleIndex: index,
    };
  }

  return { tone: fallbackTone, matchedRuleIndex: null };
}

function matchesRule(value: number, rule: DelpiKpiColorRule): boolean {
  switch (rule.op) {
    case "gt":
      return value > rule.value;
    case "gte":
      return value >= rule.value;
    case "lt":
      return value < rule.value;
    case "lte":
      return value <= rule.value;
    case "eq":
      return value === rule.value;
    case "between": {
      const high = rule.valueTo ?? rule.value;
      const low = Math.min(rule.value, high);
      const top = Math.max(rule.value, high);
      return value >= low && value <= top;
    }
    default:
      return false;
  }
}

export function parseKpiNumericValue(value: unknown): number | null {
  if (typeof value === "number" && Number.isFinite(value)) return value;
  if (typeof value === "string") {
    const trimmed = value.trim();
    const pct = trimmed.replace("%", "").trim();
    const br = Number(pct.replace(/\./g, "").replace(",", "."));
    if (Number.isFinite(br) && /[.,]/.test(pct)) return br;
    const plain = Number(pct.replace(/[^\d.-]/g, ""));
    return Number.isFinite(plain) ? plain : null;
  }
  return null;
}

const DELPI_KPI_CLASS_NAMES = metricKpiCardBemClasses("delpi");

export type DelpiKpiCardProps = {
  label: string;
  value: string;
  hint?: string;
  titleHint?: string;
  icon?: ReactNode;
  tone?: MetricKpiCardTone;
  /** Cor explícita do valor (sobrescreve tone CSS quando setada). */
  valueColor?: string;
  backgroundColor?: string;
  className?: string;
};

/** Card KPI canônico Delpi — label, valor, ícone opcional e tone condicional. */
export function DelpiKpiCard({
  label,
  value,
  hint,
  titleHint,
  icon,
  tone = "default",
  valueColor,
  backgroundColor,
  className,
}: DelpiKpiCardProps) {
  const shellStyle: CSSProperties = {
    ...(backgroundColor ? { backgroundColor } : {}),
    ...(valueColor ? ({ ["--delpi-kpi-value-color" as string]: valueColor } as CSSProperties) : {}),
  };

  return (
    <div
      className="delpi-kpi-card-shell"
      data-custom-value={valueColor ? "true" : undefined}
      style={Object.keys(shellStyle).length ? shellStyle : undefined}
    >
      <MetricKpiCard
        label={label}
        value={value}
        hint={hint}
        titleHint={titleHint}
        icon={icon}
        tone={tone}
        classNames={DELPI_KPI_CLASS_NAMES}
        className={className}
      />
    </div>
  );
}
