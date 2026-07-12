import type { CSSProperties, ReactNode } from "react";

import { HelpTooltip } from "../help/HelpTooltip";
import {
  hasIllegibleTextContrast,
  isAutomaticTextColor,
  resolveAutomaticTextColor,
  resolvePaintTextColor,
} from "../shape/colorUtils";
import { DECK_KPI_DEFAULTS } from "../../theme/deckColorCatalog";
import { FitText } from "./FitText";
import { metricKpiCardBemClasses, type MetricKpiCardTone } from "./MetricKpiCard";
import {
  KPI_PART_DATA_ATTR,
  bindKpiPartPointer,
  getKpiPartState,
  isKpiPartVisible,
  mergeKpiPartsWithOptions,
  resolveKpiIconBoxStyle,
  resolveKpiIconFrame,
  type KpiCardFlatOptions,
  type KpiCardInteraction,
  type KpiPartsMap,
} from "./kpiCardParts";

function resolveKpiPartForeground(
  explicit: string | undefined,
  cardBg: string,
  role: "label" | "value",
): string {
  const auto = resolveAutomaticTextColor(cardBg);
  const muted = auto === "#000000" ? DECK_KPI_DEFAULTS.labelColor : "#94a3b8";
  if (isAutomaticTextColor(explicit) || hasIllegibleTextContrast(explicit, cardBg)) {
    return role === "value" ? auto : muted;
  }
  return explicit!;
}

export type { MetricKpiCardTone as DelpiKpiCardTone };
export type {
  KpiCardFlatOptions,
  KpiCardInteraction,
  KpiPartFrame,
  KpiPartRef,
  KpiPartsMap,
  KpiPartState,
  KpiPartStyle,
} from "./kpiCardParts";
export {
  KPI_ICON_DEFAULT_FRAME,
  KPI_ICON_DEFAULT_RADIUS_PX,
  KPI_ICON_DEFAULT_SIZE_PX,
  KPI_PART_DATA_ATTR,
  bindKpiPartPointer,
  clampKpiPartFrame,
  deleteKpiPart,
  findKpiPartFromTarget,
  getKpiPartState,
  isKpiPartRefEqual,
  isKpiPartVisible,
  kpiOptionsToParts,
  kpiPartAllowsDelete,
  kpiPartAllowsEdit,
  kpiPartCapabilities,
  mergeKpiPartsWithOptions,
  normalizeKpiPartsForLoad,
  parseKpiPartRef,
  partsToKpiOptions,
  resolveKpiIconBoxStyle,
  resolveKpiIconFrame,
  serializeKpiPartRef,
  upsertKpiPartState,
} from "./kpiCardParts";
export {
  KPI_ELEMENT_CATALOG,
  applyKpiElementVisibility,
  isKpiElementEnabled,
  isKpiElementOpenForPart,
  kpiElementIdForPartRef,
  kpiElementPrimaryPartRef,
  setKpiElementEnabled,
  type KpiElementDefinition,
  type KpiElementId,
} from "./kpiElementCatalog";

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
  valueColor?: string;
  backgroundColor?: string;
  className?: string;
  /** Mapa de partes (primitivos) — padrão chartParts. */
  kpiParts?: KpiPartsMap | null;
  /** Options flat para merge com parts. */
  kpiOptions?: KpiCardFlatOptions | null;
  /** Hit-test / seleção no editor. */
  interaction?: KpiCardInteraction | null;
};

/**
 * Card KPI canônico Delpi composto por primitivos (`card`/`title`/`value`/`hint`/`icon`)
 * com `data-kpi-part` — mesmo padrão de ConfigurableSeriesChart.
 */
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
  kpiParts,
  kpiOptions,
  interaction = null,
}: DelpiKpiCardProps) {
  const parts = mergeKpiPartsWithOptions(kpiParts, {
    title: label,
    subtitle: hint,
    showIcon: Boolean(icon),
    valueColor,
    backgroundColor,
    ...(kpiOptions ?? {}),
  });

  const showTitle = isKpiPartVisible(parts, { kind: "title" }, true);
  const showValue = isKpiPartVisible(parts, { kind: "value" }, true);
  const showHint = isKpiPartVisible(parts, { kind: "hint" }, Boolean(hint?.trim()));
  const showIcon = isKpiPartVisible(parts, { kind: "icon" }, Boolean(icon));

  const titleContent = parts.title?.content?.trim() || label;
  const hintContent = parts.hint?.content?.trim() || hint;
  const cardBg = parts.card?.style?.fill ?? backgroundColor ?? DECK_KPI_DEFAULTS.backgroundColor;
  const autoFg = resolveAutomaticTextColor(cardBg);
  const resolvedTitleColor = resolveKpiPartForeground(parts.title?.style?.color, cardBg, "label");
  const resolvedValueColor = resolveKpiPartForeground(
    parts.value?.style?.color ?? valueColor,
    cardBg,
    "value",
  );
  const resolvedHintColor = resolveKpiPartForeground(parts.hint?.style?.color, cardBg, "label");
  const resolvedBg = parts.card?.style?.fill ?? backgroundColor;
  const cardStroke = parts.card?.style?.stroke;
  const cardStrokeWidth = parts.card?.style?.strokeWidth;
  const cardRadius = parts.card?.style?.borderRadius;

  const titleTextStyle: CSSProperties | undefined = (() => {
    const s = parts.title?.style;
    return {
      fontFamily: s?.fontFamily,
      fontSize: s?.fontSize != null ? `${s.fontSize}px` : undefined,
      fontWeight: s?.fontWeight,
      fontStyle: s?.fontStyle,
      color: resolvedTitleColor,
      textDecoration: s?.textDecoration,
    };
  })();
  const valueTextStyle: CSSProperties | undefined = (() => {
    const s = parts.value?.style;
    return {
      fontFamily: s?.fontFamily,
      fontSize: s?.fontSize != null ? `${s.fontSize}px` : undefined,
      fontWeight: s?.fontWeight,
      fontStyle: s?.fontStyle,
      color: resolvedValueColor,
      textDecoration: s?.textDecoration,
    };
  })();
  const hintTextStyle: CSSProperties | undefined = (() => {
    const s = parts.hint?.style;
    return {
      fontFamily: s?.fontFamily,
      fontSize: s?.fontSize != null ? `${s.fontSize}px` : undefined,
      fontWeight: s?.fontWeight,
      fontStyle: s?.fontStyle,
      color: resolvedHintColor,
      textDecoration: s?.textDecoration,
    };
  })();

  const cardPtr = bindKpiPartPointer({ kind: "card" }, interaction);
  const titlePtr = bindKpiPartPointer({ kind: "title" }, interaction);
  const valuePtr = bindKpiPartPointer({ kind: "value" }, interaction);
  const hintPtr = bindKpiPartPointer({ kind: "hint" }, interaction);
  const iconPtr = bindKpiPartPointer({ kind: "icon" }, interaction);

  const shellStyle: CSSProperties = {
    ["--delpi-kpi-fg" as string]: autoFg,
    ["--delpi-kpi-label-color" as string]: resolvedTitleColor,
    ["--delpi-kpi-hint-color" as string]: resolvedHintColor,
    ["--delpi-kpi-value-fg" as string]: resolvedValueColor,
    ["--delpi-kpi-card-bg" as string]: resolvedBg ?? DECK_KPI_DEFAULTS.backgroundColor,
    ...(cardStroke && cardStrokeWidth != null && cardStrokeWidth > 0
      ? ({
          ["--delpi-kpi-card-border-width" as string]: `${cardStrokeWidth}px`,
          ["--delpi-kpi-card-border-color" as string]: cardStroke,
        } as CSSProperties)
      : cardStrokeWidth === 0
        ? ({
            ["--delpi-kpi-card-border-width" as string]: "0px",
            ["--delpi-kpi-card-border-color" as string]: "transparent",
          } as CSSProperties)
        : {}),
    ...(cardRadius != null
      ? ({
          ["--delpi-kpi-card-radius" as string]: `${cardRadius}px`,
        } as CSSProperties)
      : {}),
    ["--delpi-kpi-value-color" as string]: resolvedValueColor,
  };

  const articleClass = [
    DELPI_KPI_CLASS_NAMES.articleTone(tone),
    className,
    cardPtr.selected ? "delpi-kpi-card--part-selected" : "",
    !showTitle && !showHint ? "delpi-kpi-card--value-dominant" : "",
  ]
    .filter(Boolean)
    .join(" ");

  const valueFontSizePx = parts.value?.style?.fontSize;

  /* Uma única árvore de render: tipografia de kpiParts vale com ou sem interaction
   * (TV / deselect no editor). Handlers só existem quando interaction está setada. */
  return (
    <div
      className="delpi-kpi-card-shell"
      data-custom-value={resolvedValueColor ? "true" : undefined}
      style={Object.keys(shellStyle).length ? shellStyle : undefined}
    >
      <article
        className={articleClass}
        {...{ [KPI_PART_DATA_ATTR]: cardPtr[KPI_PART_DATA_ATTR], "aria-selected": cardPtr["aria-selected"] }}
        onPointerDown={cardPtr.onPointerDown}
        onDoubleClick={cardPtr.onDoubleClick}
      >
        <div className={DELPI_KPI_CLASS_NAMES.header}>
          <div className="delpi-kpi-card__body">
            {showTitle ? (
              <p
                className={[
                  DELPI_KPI_CLASS_NAMES.label,
                  titlePtr.selected ? "delpi-kpi-part--selected" : "",
                ]
                  .filter(Boolean)
                  .join(" ")}
                style={titleTextStyle}
                {...{
                  [KPI_PART_DATA_ATTR]: titlePtr[KPI_PART_DATA_ATTR],
                  "aria-selected": titlePtr["aria-selected"],
                }}
                onPointerDown={titlePtr.onPointerDown}
                onDoubleClick={titlePtr.onDoubleClick}
              >
                {titlePtr.editing ? (
                  <input
                    className="delpi-kpi-card__edit"
                    defaultValue={titleContent}
                    autoFocus
                    onBlur={(event) => interaction?.onPartContentCommit?.({ kind: "title" }, event.target.value)}
                    onKeyDown={(event) => {
                      if (event.key === "Enter") {
                        event.preventDefault();
                        (event.target as HTMLInputElement).blur();
                      }
                      if (event.key === "Escape") {
                        event.preventDefault();
                        interaction?.onPartEditCancel?.();
                      }
                    }}
                  />
                ) : (
                  <>
                    {titleContent}
                    {titleHint && DELPI_KPI_CLASS_NAMES.labelHelp ? (
                      <HelpTooltip
                        content={titleHint}
                        ariaLabel={`Ajuda: ${titleContent}`}
                        className={DELPI_KPI_CLASS_NAMES.labelHelp}
                      />
                    ) : null}
                  </>
                )}
              </p>
            ) : null}
            {showValue ? (
              <strong
                className={[
                  DELPI_KPI_CLASS_NAMES.value,
                  valuePtr.selected ? "delpi-kpi-part--selected" : "",
                ]
                  .filter(Boolean)
                  .join(" ")}
                style={valueTextStyle}
                {...{
                  [KPI_PART_DATA_ATTR]: valuePtr[KPI_PART_DATA_ATTR],
                  "aria-selected": valuePtr["aria-selected"],
                }}
                onPointerDown={valuePtr.onPointerDown}
                onDoubleClick={valuePtr.onDoubleClick}
              >
                <FitText fixedPx={valueFontSizePx}>{value}</FitText>
              </strong>
            ) : null}
            {showHint && hintContent && DELPI_KPI_CLASS_NAMES.hint ? (
              <p
                className={[
                  DELPI_KPI_CLASS_NAMES.hint,
                  hintPtr.selected ? "delpi-kpi-part--selected" : "",
                ]
                  .filter(Boolean)
                  .join(" ")}
                style={hintTextStyle}
                {...{
                  [KPI_PART_DATA_ATTR]: hintPtr[KPI_PART_DATA_ATTR],
                  "aria-selected": hintPtr["aria-selected"],
                }}
                onPointerDown={hintPtr.onPointerDown}
                onDoubleClick={hintPtr.onDoubleClick}
              >
                {hintPtr.editing ? (
                  <input
                    className="delpi-kpi-card__edit"
                    defaultValue={hintContent}
                    autoFocus
                    onBlur={(event) => interaction?.onPartContentCommit?.({ kind: "hint" }, event.target.value)}
                    onKeyDown={(event) => {
                      if (event.key === "Enter") {
                        event.preventDefault();
                        (event.target as HTMLInputElement).blur();
                      }
                      if (event.key === "Escape") {
                        event.preventDefault();
                        interaction?.onPartEditCancel?.();
                      }
                    }}
                  />
                ) : (
                  hintContent
                )}
              </p>
            ) : null}
          </div>
          {showIcon && icon && DELPI_KPI_CLASS_NAMES.icon ? (
            <div
              className={[
                DELPI_KPI_CLASS_NAMES.icon,
                resolveKpiIconFrame(parts.icon) ? "delpi-kpi-icon--framed" : "",
                iconPtr.selected ? "delpi-kpi-part--selected" : "",
              ]
                .filter(Boolean)
                .join(" ")}
              style={resolveKpiIconBoxStyle(getKpiPartState(parts, { kind: "icon" }) ?? parts.icon)}
              aria-hidden="true"
              {...{
                [KPI_PART_DATA_ATTR]: iconPtr[KPI_PART_DATA_ATTR],
                "aria-selected": iconPtr["aria-selected"],
              }}
              onPointerDown={iconPtr.onPointerDown}
              onDoubleClick={iconPtr.onDoubleClick}
            >
              {icon}
            </div>
          ) : null}
        </div>
      </article>
    </div>
  );
}
