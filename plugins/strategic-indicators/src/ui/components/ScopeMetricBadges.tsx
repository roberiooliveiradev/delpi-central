import { useMemo, useState } from "react";
import {
  formatIndicatorValue,
  hasBranchScopeValues,
  MISSING_VALUE_LABEL,
  type IndicatorDisplayContext,
  type IndicatorValueFormat,
} from "../shared/indicatorValueFormatter";
import { formatOperationalUnitCode } from "../shared/operationalUnitLabels";
import "./ScopeMetricBadges.css";

type ScopeMetricBadgesProps = {
  values?: Record<string, number | null> | null;
  format?: IndicatorValueFormat;
  displayContext?: IndicatorDisplayContext;
  maxVisible?: number;
  emptyLabel?: string;
  /** inline = chips em linha; compact = pilha vertical (tabelas e cards estreitos) */
  layout?: "inline" | "compact";
};

function listBranchKeys(values: Record<string, number | null>): string[] {
  return Object.keys(values)
    .filter((key) => key.trim() !== "" && key !== "consolidated")
    .sort();
}

function filterByActiveBranch(
  values: Record<string, number | null>,
  activeBranch?: string,
): Record<string, number | null> {
  const branch = (activeBranch ?? "").trim();
  if (!branch || !(branch in values)) return values;
  return { [branch]: values[branch] };
}

export function ScopeMetricBadges({
  values,
  format = {},
  displayContext,
  maxVisible = 4,
  emptyLabel = MISSING_VALUE_LABEL,
  layout = "inline",
}: ScopeMetricBadgesProps) {
  const activeBranch = displayContext?.activeBranch;

  const normalizedFormat = useMemo<IndicatorValueFormat>(() => {
    const unit = String((format as any).valueUnit ?? "").trim().toLowerCase();
    const prefix = String((format as any).valuePrefix ?? "").trim();
    const suffix = String((format as any).valueSuffix ?? "").trim();

    // Fallbacks: alguns endpoints usam `value_unit` mas não mandam prefixo/sufixo.
    if (unit === "currency" && !prefix) {
      return { ...format, valuePrefix: "R$" };
    }
    if (unit === "percent" && !suffix) {
      return { ...format, valueSuffix: "%" };
    }
    return format;
  }, [format]);

  const normalizedValues = useMemo(() => {
    const base = values ?? {};
    if (!Object.keys(base).length) return null;
    return filterByActiveBranch(base, activeBranch);
  }, [values, activeBranch]);

  const branchKeys = useMemo(() => {
    if (!normalizedValues) return [];
    return listBranchKeys(normalizedValues);
  }, [normalizedValues]);

  const [expanded, setExpanded] = useState(false);

  if (!normalizedValues || !Object.keys(normalizedValues).length) {
    return <span className="si-scope-badges__empty">{emptyLabel}</span>;
  }

  if (!hasBranchScopeValues(normalizedValues)) {
    const consolidated = normalizedValues.consolidated ?? null;
    return (
      <span className="si-scope-badges__single">
        {formatIndicatorValue(consolidated, normalizedFormat)}
      </span>
    );
  }

  const visibleKeys = expanded ? branchKeys : branchKeys.slice(0, maxVisible);
  const hiddenCount = Math.max(0, branchKeys.length - visibleKeys.length);

  const rootClassName =
    layout === "compact"
      ? "si-scope-badges si-scope-badges--compact"
      : "si-scope-badges";

  return (
    <span className={rootClassName}>
      {visibleKeys.map((key) => (
        <span
          key={key}
          className={`si-scope-badge si-scope-badge--branch-${key}`}
          title={formatOperationalUnitCode(key, key)}
        >
          <span className="si-scope-badge__key">
            {formatOperationalUnitCode(key, key)}
          </span>
          <span className="si-scope-badge__value">
            {formatIndicatorValue(normalizedValues[key], normalizedFormat)}
          </span>
        </span>
      ))}

      {hiddenCount > 0 ? (
        <button
          type="button"
          className="si-scope-badge si-scope-badge--more"
          onClick={() => setExpanded(true)}
          title={branchKeys.slice(maxVisible).join(", ")}
        >
          +{hiddenCount}
        </button>
      ) : null}

      {expanded && branchKeys.length > maxVisible ? (
        <button
          type="button"
          className="si-scope-badges__collapse"
          onClick={() => setExpanded(false)}
        >
          recolher
        </button>
      ) : null}
    </span>
  );
}

