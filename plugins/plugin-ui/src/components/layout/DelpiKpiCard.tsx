import type { CSSProperties, ReactNode } from "react";
import { useRef } from "react";

import { HelpTooltip } from "../help/HelpTooltip";
import {
  isAutomaticTextColor,
  resolveAutomaticTextColor,
  resolveComplexBlockForeground,
} from "../shape/colorUtils";
import { DECK_KPI_DEFAULTS } from "../../theme/deckColorCatalog";
import { FitText } from "./FitText";
import { KpiPartResizeHandles } from "./KpiPartResizeHandles";
import { metricKpiCardBemClasses, type MetricKpiCardTone } from "./MetricKpiCard";
import {
  KPI_ICON_DEFAULT_RADIUS_PX,
  KPI_PART_DATA_ATTR,
  bindKpiPartPointer,
  getKpiPartState,
  isKpiPartVisible,
  kpiPartAllowsResize,
  kpiPartCornerAdjustCssPosition,
  mergeKpiPartsWithOptions,
  resolveKpiIconBoxStyle,
  resolveKpiPartFontSize,
  resolveKpiPartFrame,
  resolveKpiPartLayoutStyle,
  resolveKpiPartTypographyStyle,
  kpiPartHasBoxPaint,
  kpiPartUsesAutoFitFont,
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
  return resolveComplexBlockForeground(explicit, cardBg, {
    role: role === "value" ? "emphasis" : "muted",
    mutedColor: auto === "#000000" ? DECK_KPI_DEFAULTS.labelColor : "#94a3b8",
  });
}

export type { MetricKpiCardTone as DelpiKpiCardTone };
export type {
  KpiCardFlatOptions,
  KpiCardInteraction,
  KpiFramePartKind,
  KpiPartFrame,
  KpiPartRef,
  KpiPartResizeHandle,
  KpiPartsMap,
  KpiPartState,
  KpiPartStyle,
  KpiTextPartKind,
} from "./kpiCardParts";
export {
  KPI_ICON_DEFAULT_FRAME,
  KPI_ICON_DEFAULT_RADIUS_PX,
  KPI_ICON_DEFAULT_SIZE_PX,
  KPI_PART_DEFAULT_FRAMES,
  KPI_PART_FONT_SIZE_DEFAULTS,
  KPI_PART_DATA_ATTR,
  KPI_PART_RESIZE_HANDLES,
  bindKpiPartPointer,
  clampKpiPartFrame,
  defaultKpiPartFrame,
  deleteKpiPart,
  findKpiPartFromTarget,
  getKpiPartState,
  isKpiPartRefEqual,
  isKpiPartSelected,
  isKpiPartVisible,
  kpiOptionsToParts,
  kpiPartAllowsDelete,
  kpiPartAllowsEdit,
  kpiPartAllowsFrame,
  kpiPartAllowsMove,
  kpiPartAllowsResize,
  kpiPartCapabilities,
  kpiPartBoxChromeLabels,
  kpiPartHasBoxPaint,
  kpiPartSupportsTypography,
  kpiPartCornerAdjFromLocalX,
  kpiPartCornerAdjustCssPosition,
  resolveKpiShapeChromePartRef,
  mergeKpiPartsWithOptions,
  normalizeKpiPartsForLoad,
  parseKpiPartRef,
  partsToKpiOptions,
  resizeKpiPartFrame,
  borderRadiusPxToKpiCornerAdj,
  kpiCornerAdjToBorderRadiusPx,
  resolveKpiIconBoxStyle,
  resolveKpiIconFrame,
  resolveKpiPartFontSize,
  resolveKpiPartFrame,
  resolveKpiPartFrameRoot,
  resolveKpiPartLayoutStyle,
  resolveKpiPartTypographyStyle,
  kpiPartUsesAutoFitFont,
  serializeKpiPartRef,
  upsertKpiPartState,
  applyKpiPartStyleToSiblingParts,
  clearKpiPartsFreeLayoutFrames,
  materializeMissingKpiPartFramesFromRoot,
  seedKpiPartsFreeLayoutFrames,
  isKpiTextPartKind,
  KPI_TEXT_PART_KINDS,
  KPI_FREE_LAYOUT_PART_KINDS,
} from "./kpiCardParts";
export {
  KPI_ELEMENT_CATALOG,
  KPI_LAYOUT_PRESET_FRAMES,
  applyKpiAddElementChoice,
  applyKpiAddElementChoiceWithParts,
  applyKpiElementVisibility,
  applyKpiLayoutPreset,
  isKpiAddElementChoiceActive,
  isKpiElementEnabled,
  isKpiElementOpenForPart,
  kpiElementIdForAddChoice,
  kpiElementIdForPartRef,
  kpiElementPrimaryPartRef,
  setKpiElementEnabled,
  type KpiAddElementChoiceId,
  type KpiElementDefinition,
  type KpiElementId,
} from "./kpiElementCatalog";
export {
  kpiPartStyleWithAutoFont,
  kpiPartStyleWithFixedFontSize,
  mergeKpiPartStyle,
  type KpiPartTypographyMode,
} from "./kpiCardParts";

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
  if (typeof value !== "string") return null;

  const pct = value.trim().replace("%", "").trim();
  if (!pct) return null;

  const hasComma = pct.includes(",");
  const hasDot = pct.includes(".");

  // 1.234,56 (BR) ou 1,234.56 (US) — o separador decimal é o último.
  if (hasComma && hasDot) {
    const lastComma = pct.lastIndexOf(",");
    const lastDot = pct.lastIndexOf(".");
    if (lastComma > lastDot) {
      const br = Number(pct.replace(/\./g, "").replace(",", "."));
      return Number.isFinite(br) ? br : null;
    }
    const us = Number(pct.replace(/,/g, ""));
    return Number.isFinite(us) ? us : null;
  }

  // Só vírgula: 86,2 / 1234,56
  if (hasComma) {
    const br = Number(pct.replace(/\./g, "").replace(",", "."));
    return Number.isFinite(br) ? br : null;
  }

  // Só ponto: 78.91 (decimal) vs 1.234 (milhar BR).
  if (hasDot) {
    if (/^\d{1,3}(\.\d{3})+$/.test(pct)) {
      const thousands = Number(pct.replace(/\./g, ""));
      return Number.isFinite(thousands) ? thousands : null;
    }
    const decimal = Number(pct);
    return Number.isFinite(decimal) ? decimal : null;
  }

  const plain = Number(pct.replace(/[^\d.-]/g, ""));
  return Number.isFinite(plain) ? plain : null;
}

const DELPI_KPI_CLASS_NAMES = metricKpiCardBemClasses("delpi");

export type DelpiKpiComparisonTone = "positive" | "negative" | "neutral";

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
  /** Preenche o host (TV / presentation) — classes `--fill` no shell e card. */
  fill?: boolean;
  /** Mapa de partes (primitivos) — padrão chartParts. */
  kpiParts?: KpiPartsMap | null;
  /** Options flat para merge com parts. */
  kpiOptions?: KpiCardFlatOptions | null;
  /** Hit-test / seleção no editor. */
  interaction?: KpiCardInteraction | null;
  /** Texto do delta (ex.: «▲ +3,2% vs meta»). */
  comparisonText?: string;
  comparisonTone?: DelpiKpiComparisonTone;
  /** Progresso 0–100 até a meta. */
  progressPct?: number | null;
  /** Pontos da sparkline (ordem temporal). */
  sparklinePoints?: number[] | null;
};

/**
 * Card KPI canônico Delpi composto por primitivos (`card`/`title`/`value`/`hint`/`icon`)
 * com `data-kpi-part` — mesmo padrão de ConfigurableSeriesChart.
 */
function KpiSparklineSvg({ points }: { points: number[] }) {
  if (points.length < 2) return null;
  const min = Math.min(...points);
  const max = Math.max(...points);
  const span = max - min || 1;
  const w = 100;
  const h = 36;
  const d = points
    .map((point, index) => {
      const x = (index / (points.length - 1)) * w;
      const y = h - ((point - min) / span) * (h - 4) - 2;
      return `${index === 0 ? "M" : "L"}${x.toFixed(2)},${y.toFixed(2)}`;
    })
    .join(" ");
  return (
    <svg className="delpi-kpi-sparkline__svg" viewBox={`0 0 ${w} ${h}`} preserveAspectRatio="none" aria-hidden>
      <path d={d} fill="none" stroke="currentColor" strokeWidth="2" strokeLinejoin="round" strokeLinecap="round" />
    </svg>
  );
}

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
  fill = false,
  kpiParts,
  kpiOptions,
  interaction = null,
  comparisonText,
  comparisonTone = "neutral",
  progressPct = null,
  sparklinePoints = null,
}: DelpiKpiCardProps) {
  const titleHostRef = useRef<HTMLParagraphElement>(null);
  const valueHostRef = useRef<HTMLElement>(null);
  const hintHostRef = useRef<HTMLParagraphElement>(null);
  const iconHostRef = useRef<HTMLDivElement>(null);
  const cardHostRef = useRef<HTMLElement>(null);
  const comparisonHostRef = useRef<HTMLParagraphElement>(null);
  const progressHostRef = useRef<HTMLDivElement>(null);
  const sparklineHostRef = useRef<HTMLDivElement>(null);

  // Options/parts mandam; `icon` só entra como fallback quando a visibilidade
  // ainda não foi declarada (evita reaparecer ícone oculto no modo apresentação).
  const iconVisibilityDeclared =
    kpiOptions?.showIcon != null || kpiParts?.icon?.visible != null;
  const parts = mergeKpiPartsWithOptions(kpiParts, {
    title: label,
    subtitle: hint,
    valueColor,
    backgroundColor,
    ...(kpiOptions ?? {}),
    ...(iconVisibilityDeclared ? {} : { showIcon: Boolean(icon) }),
  });

  const showTitle = isKpiPartVisible(parts, { kind: "title" }, true);
  const showValue = isKpiPartVisible(parts, { kind: "value" }, true);
  const showHint = isKpiPartVisible(parts, { kind: "hint" }, Boolean(hint?.trim()));
  const showIcon = isKpiPartVisible(parts, { kind: "icon" }, Boolean(icon));
  const comparisonFallback = Boolean(comparisonText?.trim());
  const showComparison = isKpiPartVisible(
    parts,
    { kind: "comparison" },
    comparisonFallback || kpiOptions?.showComparison === true,
  );
  const showProgress = isKpiPartVisible(
    parts,
    { kind: "progress" },
    kpiOptions?.showProgress === true && progressPct != null,
  );
  const sparkPoints = (sparklinePoints ?? []).filter((n) => Number.isFinite(n));
  const showSparkline = isKpiPartVisible(
    parts,
    { kind: "sparkline" },
    kpiOptions?.showSparkline === true && sparkPoints.length >= 2,
  );

  const titleContent = parts.title?.content?.trim() || label;
  const hintContent = parts.hint?.content?.trim() || hint;
  const comparisonContent = parts.comparison?.content?.trim() || comparisonText?.trim() || "";
  const cardBg = parts.card?.style?.fill ?? backgroundColor ?? DECK_KPI_DEFAULTS.backgroundColor;
  const autoFg = resolveAutomaticTextColor(cardBg);
  const resolvedTitleColor = resolveKpiPartForeground(parts.title?.style?.color, cardBg, "label");
  // Cor explícita do usuário/regra — `AUTOMATIC_TEXT_COLOR` do seed não conta (libera tom CSS).
  const rawValueColor = (parts.value?.style?.color ?? valueColor)?.trim() || undefined;
  const hasCustomValueColor = Boolean(rawValueColor) && !isAutomaticTextColor(rawValueColor);
  const resolvedValueColor = resolveKpiPartForeground(
    hasCustomValueColor ? rawValueColor : undefined,
    cardBg,
    "value",
  );
  const valueColorForStyle =
    hasCustomValueColor || tone === "default" ? resolvedValueColor : undefined;
  const resolvedHintColor = resolveKpiPartForeground(parts.hint?.style?.color, cardBg, "label");
  const resolvedBg = parts.card?.style?.fill ?? backgroundColor;
  const cardStroke = parts.card?.style?.stroke;
  const cardStrokeWidth = parts.card?.style?.strokeWidth;
  const cardRadius = parts.card?.style?.borderRadius;

  const titleState = getKpiPartState(parts, { kind: "title" }) ?? parts.title;
  const valueState = getKpiPartState(parts, { kind: "value" }) ?? parts.value;
  const hintState = getKpiPartState(parts, { kind: "hint" }) ?? parts.hint;
  const iconState = getKpiPartState(parts, { kind: "icon" }) ?? parts.icon;
  const comparisonState = getKpiPartState(parts, { kind: "comparison" }) ?? parts.comparison;
  const progressState = getKpiPartState(parts, { kind: "progress" }) ?? parts.progress;
  const sparklineState = getKpiPartState(parts, { kind: "sparkline" }) ?? parts.sparkline;
  const cardState = getKpiPartState(parts, { kind: "card" }) ?? parts.card;
  const titleFramed = Boolean(resolveKpiPartFrame(titleState));
  const valueFramed = Boolean(resolveKpiPartFrame(valueState));
  const hintFramed = Boolean(resolveKpiPartFrame(hintState));
  const iconFramed = Boolean(resolveKpiPartFrame(iconState));
  const comparisonFramed = Boolean(resolveKpiPartFrame(comparisonState));
  const progressFramed = Boolean(resolveKpiPartFrame(progressState));
  const sparklineFramed = Boolean(resolveKpiPartFrame(sparklineState));
  const titleLayoutStyle = resolveKpiPartLayoutStyle(titleState, { partKind: "title" });
  const valueLayoutStyle = resolveKpiPartLayoutStyle(valueState, { partKind: "value" });
  const hintLayoutStyle = resolveKpiPartLayoutStyle(hintState, { partKind: "hint" });
  const comparisonLayoutStyle = resolveKpiPartLayoutStyle(comparisonState, { partKind: "comparison" });
  const progressLayoutStyle = resolveKpiPartLayoutStyle(progressState, { partKind: "progress" });
  const sparklineLayoutStyle = resolveKpiPartLayoutStyle(sparklineState, { partKind: "sparkline" });
  const cardLayoutStyle = resolveKpiPartLayoutStyle(cardState, { partKind: "card" });

  const valueAutoFit = kpiPartUsesAutoFitFont("value", parts.value?.style);
  const valueFontSizePx = resolveKpiPartFontSize("value", parts.value?.style);
  const titleAutoFit = kpiPartUsesAutoFitFont("title", parts.title?.style);
  const titleFontSizePx = resolveKpiPartFontSize("title", parts.title?.style);
  // Paridade título: FitText só com frame (layout livre). Sem frame = px escalado no resize do bloco.
  const valueUsesFitText = valueAutoFit && valueFramed;
  const titleUsesFitText = titleAutoFit && titleFramed;

  const titleTextStyle: CSSProperties = {
    ...resolveKpiPartTypographyStyle(
      {
        ...parts.title?.style,
        // Sem frame: px no host (escala no resize do bloco). Com frame + auto-fit: FitText.
        ...(titleUsesFitText ? { fontSize: undefined } : { fontSize: titleFontSizePx }),
        color: resolvedTitleColor,
      },
      { flexPart: false, fillHost: titleFramed },
    ),
    ...titleLayoutStyle,
  };
  const valueTextStyle: CSSProperties = {
    ...resolveKpiPartTypographyStyle(
      {
        ...parts.value?.style,
        ...(valueUsesFitText ? { fontSize: undefined } : { fontSize: valueFontSizePx }),
        ...(valueColorForStyle ? { color: valueColorForStyle } : { color: undefined }),
      },
      { flexPart: valueFramed, fillHost: valueFramed },
    ),
    ...valueLayoutStyle,
    // Layout livre + FitText: host precisa esticar na caixa % (vence fit-content pintado).
    ...(valueUsesFitText
      ? {
          flex: "1 1 auto",
          alignSelf: "stretch",
          width: "100%",
          minWidth: 0,
          minHeight: 0,
        }
      : null),
  };
  const hintTextStyle: CSSProperties = {
    ...resolveKpiPartTypographyStyle(
      {
        ...parts.hint?.style,
        fontSize: resolveKpiPartFontSize("hint", parts.hint?.style),
        color: resolvedHintColor,
      },
      { flexPart: false },
    ),
    ...hintLayoutStyle,
  };
  const comparisonTextStyle: CSSProperties = {
    ...resolveKpiPartTypographyStyle(
      {
        ...parts.comparison?.style,
        fontSize: resolveKpiPartFontSize("comparison", parts.comparison?.style),
        color: parts.comparison?.style?.color ?? resolvedHintColor,
      },
      { flexPart: false, fillHost: comparisonFramed },
    ),
    ...comparisonLayoutStyle,
  };

  const cardPtr = bindKpiPartPointer({ kind: "card" }, interaction);
  const titlePtr = bindKpiPartPointer({ kind: "title" }, interaction);
  const valuePtr = bindKpiPartPointer({ kind: "value" }, interaction);
  const hintPtr = bindKpiPartPointer({ kind: "hint" }, interaction);
  const iconPtr = bindKpiPartPointer({ kind: "icon" }, interaction);
  const comparisonPtr = bindKpiPartPointer({ kind: "comparison" }, interaction);
  const progressPtr = bindKpiPartPointer({ kind: "progress" }, interaction);
  const sparklinePtr = bindKpiPartPointer({ kind: "sparkline" }, interaction);

  const titleShowResize =
    titlePtr.selected && !titlePtr.editing && kpiPartAllowsResize({ kind: "title" }) &&
    Boolean(interaction?.onPartResizePointerDown);
  const valueShowResize =
    valuePtr.selected && !valuePtr.editing && kpiPartAllowsResize({ kind: "value" }) &&
    Boolean(interaction?.onPartResizePointerDown);
  const hintShowResize =
    hintPtr.selected && !hintPtr.editing && kpiPartAllowsResize({ kind: "hint" }) &&
    Boolean(interaction?.onPartResizePointerDown);
  const iconShowResize =
    iconPtr.selected && !iconPtr.editing && kpiPartAllowsResize({ kind: "icon" }) &&
    Boolean(interaction?.onPartResizePointerDown);
  const comparisonShowResize =
    comparisonPtr.selected &&
    !comparisonPtr.editing &&
    kpiPartAllowsResize({ kind: "comparison" }) &&
    Boolean(interaction?.onPartResizePointerDown);
  const progressShowResize =
    progressPtr.selected &&
    !progressPtr.editing &&
    kpiPartAllowsResize({ kind: "progress" }) &&
    Boolean(interaction?.onPartResizePointerDown);
  const sparklineShowResize =
    sparklinePtr.selected &&
    !sparklinePtr.editing &&
    kpiPartAllowsResize({ kind: "sparkline" }) &&
    Boolean(interaction?.onPartResizePointerDown);
  const cardShowChrome = false; /* moldura = chrome do wrap (pai); evita handles duplicados */
  const clampedProgress =
    progressPct != null && Number.isFinite(progressPct)
      ? Math.max(0, Math.min(100, progressPct))
      : null;

  const partCornerStyle = (host: HTMLElement | null, radiusPx: number) => {
    const shortSide = Math.min(
      Math.max(1, host?.clientWidth ?? 64),
      Math.max(1, host?.clientHeight ?? 64),
    );
    return kpiPartCornerAdjustCssPosition(radiusPx, shortSide);
  };

  const titleCornerRadius = parts.title?.style?.borderRadius ?? 0;
  const valueCornerRadius = parts.value?.style?.borderRadius ?? 0;
  const hintCornerRadius = parts.hint?.style?.borderRadius ?? 0;
  const iconCornerRadius = parts.icon?.style?.borderRadius ?? KPI_ICON_DEFAULT_RADIUS_PX;
  const cardCornerRadius =
    parts.card?.style?.borderRadius ?? cardRadius ?? DECK_KPI_DEFAULTS.borderRadius;
  const cardShadow = parts.card?.style?.boxShadow ?? DECK_KPI_DEFAULTS.boxShadow;

  const shellStyle: CSSProperties = {
    position: "relative",
    ["--delpi-kpi-fg" as string]: autoFg,
    ["--delpi-kpi-label-color" as string]: resolvedTitleColor,
    ["--delpi-kpi-hint-color" as string]: resolvedHintColor,
    ...(valueColorForStyle
      ? ({ ["--delpi-kpi-value-fg" as string]: valueColorForStyle } as CSSProperties)
      : {}),
    ["--delpi-kpi-card-bg" as string]: resolvedBg ?? DECK_KPI_DEFAULTS.backgroundColor,
    ["--delpi-kpi-card-radius" as string]: `${cardCornerRadius}px`,
    ["--delpi-kpi-card-shadow" as string]: cardShadow,
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
        : {
            ["--delpi-kpi-card-border-width" as string]: `${DECK_KPI_DEFAULTS.borderWidth}px`,
            ["--delpi-kpi-card-border-color" as string]: DECK_KPI_DEFAULTS.borderColor,
          }),
    ...(parts.card?.style?.opacity != null
      ? ({
          ["--delpi-kpi-card-opacity" as string]: String(parts.card.style.opacity),
        } as CSSProperties)
      : {}),
    ...(hasCustomValueColor
      ? ({ ["--delpi-kpi-value-color" as string]: resolvedValueColor } as CSSProperties)
      : {}),
  };

  const articleClass = [
    DELPI_KPI_CLASS_NAMES.articleTone(tone),
    className,
    fill ? "delpi-kpi-card--fill" : "",
    cardPtr.selected ? "delpi-kpi-card--part-selected" : "",
    !showTitle && !showHint ? "delpi-kpi-card--value-dominant" : "",
  ]
    .filter(Boolean)
    .join(" ");

  return (
    <div
      className={["delpi-kpi-card-shell", fill ? "delpi-kpi-card-shell--fill" : ""]
        .filter(Boolean)
        .join(" ")}
      data-custom-value={hasCustomValueColor ? "true" : undefined}
      style={Object.keys(shellStyle).length ? shellStyle : undefined}
    >
      <article
        ref={cardHostRef}
        className={articleClass}
        style={cardLayoutStyle}
        {...{ [KPI_PART_DATA_ATTR]: cardPtr[KPI_PART_DATA_ATTR], "aria-selected": cardPtr["aria-selected"] }}
        onPointerDown={cardPtr.onPointerDown}
        onDoubleClick={cardPtr.onDoubleClick}
      >
        <div className={DELPI_KPI_CLASS_NAMES.header}>
          <div className="delpi-kpi-card__body">
            {showTitle ? (
              <p
                ref={titleHostRef}
                className={[
                  DELPI_KPI_CLASS_NAMES.label,
                  titleFramed ? "delpi-kpi-part--framed" : "",
                  !titleFramed && kpiPartHasBoxPaint(titleState?.style) ? "delpi-kpi-part--boxed" : "",
                  titleShowResize ? "delpi-kpi-part--resizable" : "",
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
                ) : titleUsesFitText ? (
                  <>
                    <FitText
                      fixedPx={null}
                      minPx={12}
                      maxPx={120}
                      className="delpi-kpi-card__title-fit"
                    >
                      {titleContent}
                    </FitText>
                    {titleHint && DELPI_KPI_CLASS_NAMES.labelHelp ? (
                      <HelpTooltip
                        content={titleHint}
                        ariaLabel={`Ajuda: ${titleContent}`}
                        className={DELPI_KPI_CLASS_NAMES.labelHelp}
                      />
                    ) : null}
                  </>
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
                <KpiPartResizeHandles
                  visible={titleShowResize}
                  onResizePointerDown={(handle, event) =>
                    interaction?.onPartResizePointerDown?.({ kind: "title" }, event, handle)
                  }
                  showCornerAdjust={Boolean(interaction?.onPartCornerAdjustPointerDown)}
                  cornerAdjustStyle={partCornerStyle(titleHostRef.current, titleCornerRadius)}
                  onCornerAdjustPointerDown={(event) =>
                    interaction?.onPartCornerAdjustPointerDown?.({ kind: "title" }, event)
                  }
                />
              </p>
            ) : null}
            {showValue ? (
              <strong
                ref={valueHostRef}
                className={[
                  DELPI_KPI_CLASS_NAMES.value,
                  valueFramed ? "delpi-kpi-part--framed" : "",
                  !valueFramed && kpiPartHasBoxPaint(valueState?.style) ? "delpi-kpi-part--boxed" : "",
                  valueShowResize ? "delpi-kpi-part--resizable" : "",
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
                <FitText
                  fixedPx={valueUsesFitText ? null : valueFontSizePx}
                  minPx={16}
                  maxPx={320}
                >
                  {value}
                </FitText>
                <KpiPartResizeHandles
                  visible={valueShowResize}
                  onResizePointerDown={(handle, event) =>
                    interaction?.onPartResizePointerDown?.({ kind: "value" }, event, handle)
                  }
                  showCornerAdjust={Boolean(interaction?.onPartCornerAdjustPointerDown)}
                  cornerAdjustStyle={partCornerStyle(valueHostRef.current, valueCornerRadius)}
                  onCornerAdjustPointerDown={(event) =>
                    interaction?.onPartCornerAdjustPointerDown?.({ kind: "value" }, event)
                  }
                />
              </strong>
            ) : null}
            {showComparison && comparisonContent ? (
              <p
                ref={comparisonHostRef}
                className={[
                  "delpi-kpi-card__comparison",
                  `delpi-kpi-card__comparison--${comparisonTone}`,
                  comparisonFramed ? "delpi-kpi-part--framed" : "",
                  comparisonShowResize ? "delpi-kpi-part--resizable" : "",
                  comparisonPtr.selected ? "delpi-kpi-part--selected" : "",
                ]
                  .filter(Boolean)
                  .join(" ")}
                style={comparisonTextStyle}
                {...{
                  [KPI_PART_DATA_ATTR]: comparisonPtr[KPI_PART_DATA_ATTR],
                  "aria-selected": comparisonPtr["aria-selected"],
                }}
                onPointerDown={comparisonPtr.onPointerDown}
                onDoubleClick={comparisonPtr.onDoubleClick}
              >
                {comparisonContent}
                <KpiPartResizeHandles
                  visible={comparisonShowResize}
                  onResizePointerDown={(handle, event) =>
                    interaction?.onPartResizePointerDown?.({ kind: "comparison" }, event, handle)
                  }
                />
              </p>
            ) : null}
            {showSparkline && sparkPoints.length >= 2 ? (
              <div
                ref={sparklineHostRef}
                className={[
                  "delpi-kpi-sparkline",
                  sparklineFramed ? "delpi-kpi-part--framed" : "",
                  sparklineShowResize ? "delpi-kpi-part--resizable" : "",
                  sparklinePtr.selected ? "delpi-kpi-part--selected" : "",
                ]
                  .filter(Boolean)
                  .join(" ")}
                style={sparklineLayoutStyle}
                {...{
                  [KPI_PART_DATA_ATTR]: sparklinePtr[KPI_PART_DATA_ATTR],
                  "aria-selected": sparklinePtr["aria-selected"],
                }}
                onPointerDown={sparklinePtr.onPointerDown}
                onDoubleClick={sparklinePtr.onDoubleClick}
              >
                <KpiSparklineSvg points={sparkPoints} />
                <KpiPartResizeHandles
                  visible={sparklineShowResize}
                  onResizePointerDown={(handle, event) =>
                    interaction?.onPartResizePointerDown?.({ kind: "sparkline" }, event, handle)
                  }
                />
              </div>
            ) : null}
            {showProgress && clampedProgress != null ? (
              <div
                ref={progressHostRef}
                className={[
                  "delpi-kpi-progress",
                  progressFramed ? "delpi-kpi-part--framed" : "",
                  progressShowResize ? "delpi-kpi-part--resizable" : "",
                  progressPtr.selected ? "delpi-kpi-part--selected" : "",
                ]
                  .filter(Boolean)
                  .join(" ")}
                style={progressLayoutStyle}
                role="progressbar"
                aria-valuenow={Math.round(clampedProgress)}
                aria-valuemin={0}
                aria-valuemax={100}
                {...{
                  [KPI_PART_DATA_ATTR]: progressPtr[KPI_PART_DATA_ATTR],
                  "aria-selected": progressPtr["aria-selected"],
                }}
                onPointerDown={progressPtr.onPointerDown}
                onDoubleClick={progressPtr.onDoubleClick}
              >
                <div className="delpi-kpi-progress__track">
                  <div
                    className="delpi-kpi-progress__fill"
                    style={{ width: `${clampedProgress}%` }}
                  />
                </div>
                <KpiPartResizeHandles
                  visible={progressShowResize}
                  onResizePointerDown={(handle, event) =>
                    interaction?.onPartResizePointerDown?.({ kind: "progress" }, event, handle)
                  }
                />
              </div>
            ) : null}
            {showHint && hintContent && DELPI_KPI_CLASS_NAMES.hint ? (
              <p
                ref={hintHostRef}
                className={[
                  DELPI_KPI_CLASS_NAMES.hint,
                  hintFramed ? "delpi-kpi-part--framed" : "",
                  !hintFramed && kpiPartHasBoxPaint(hintState?.style) ? "delpi-kpi-part--boxed" : "",
                  hintShowResize ? "delpi-kpi-part--resizable" : "",
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
                <KpiPartResizeHandles
                  visible={hintShowResize}
                  onResizePointerDown={(handle, event) =>
                    interaction?.onPartResizePointerDown?.({ kind: "hint" }, event, handle)
                  }
                  showCornerAdjust={Boolean(interaction?.onPartCornerAdjustPointerDown)}
                  cornerAdjustStyle={partCornerStyle(hintHostRef.current, hintCornerRadius)}
                  onCornerAdjustPointerDown={(event) =>
                    interaction?.onPartCornerAdjustPointerDown?.({ kind: "hint" }, event)
                  }
                />
              </p>
            ) : null}
          </div>
          {showIcon && icon && DELPI_KPI_CLASS_NAMES.icon ? (
            <div
              ref={iconHostRef}
              className={[
                DELPI_KPI_CLASS_NAMES.icon,
                iconFramed ? "delpi-kpi-icon--framed delpi-kpi-part--framed" : "",
                iconShowResize ? "delpi-kpi-part--resizable" : "",
                iconPtr.selected ? "delpi-kpi-part--selected" : "",
              ]
                .filter(Boolean)
                .join(" ")}
              style={resolveKpiIconBoxStyle(iconState, cardBg)}
              aria-hidden="true"
              {...{
                [KPI_PART_DATA_ATTR]: iconPtr[KPI_PART_DATA_ATTR],
                "aria-selected": iconPtr["aria-selected"],
              }}
              onPointerDown={iconPtr.onPointerDown}
              onDoubleClick={iconPtr.onDoubleClick}
            >
              {icon}
              <KpiPartResizeHandles
                visible={iconShowResize}
                onResizePointerDown={(handle, event) =>
                  interaction?.onPartResizePointerDown?.({ kind: "icon" }, event, handle)
                }
                showCornerAdjust={Boolean(interaction?.onPartCornerAdjustPointerDown)}
                cornerAdjustStyle={partCornerStyle(iconHostRef.current, iconCornerRadius)}
                onCornerAdjustPointerDown={(event) =>
                  interaction?.onPartCornerAdjustPointerDown?.({ kind: "icon" }, event)
                }
              />
            </div>
          ) : null}
        </div>
        <KpiPartResizeHandles
          visible={cardShowChrome}
          onResizePointerDown={(handle, event) =>
            interaction?.onPartResizePointerDown?.({ kind: "card" }, event, handle)
          }
          showCornerAdjust={Boolean(interaction?.onPartCornerAdjustPointerDown)}
          cornerAdjustStyle={partCornerStyle(cardHostRef.current, cardCornerRadius)}
          onCornerAdjustPointerDown={(event) =>
            interaction?.onPartCornerAdjustPointerDown?.({ kind: "card" }, event)
          }
        />
      </article>
    </div>
  );
}
