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
  fill = false,
  kpiParts,
  kpiOptions,
  interaction = null,
}: DelpiKpiCardProps) {
  const titleHostRef = useRef<HTMLParagraphElement>(null);
  const valueHostRef = useRef<HTMLElement>(null);
  const hintHostRef = useRef<HTMLParagraphElement>(null);
  const iconHostRef = useRef<HTMLDivElement>(null);
  const cardHostRef = useRef<HTMLElement>(null);

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

  const titleContent = parts.title?.content?.trim() || label;
  const hintContent = parts.hint?.content?.trim() || hint;
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
  const cardState = getKpiPartState(parts, { kind: "card" }) ?? parts.card;
  const titleFramed = Boolean(resolveKpiPartFrame(titleState));
  const valueFramed = Boolean(resolveKpiPartFrame(valueState));
  const hintFramed = Boolean(resolveKpiPartFrame(hintState));
  const iconFramed = Boolean(resolveKpiPartFrame(iconState));
  const cardFramed = Boolean(resolveKpiPartFrame(cardState));
  const titleLayoutStyle = resolveKpiPartLayoutStyle(titleState, { partKind: "title" });
  const valueLayoutStyle = resolveKpiPartLayoutStyle(valueState, { partKind: "value" });
  const hintLayoutStyle = resolveKpiPartLayoutStyle(hintState, { partKind: "hint" });
  const cardLayoutStyle = resolveKpiPartLayoutStyle(cardState, { partKind: "card" });

  const valueAutoFit = kpiPartUsesAutoFitFont("value", parts.value?.style);
  const valueFontSizePx = resolveKpiPartFontSize("value", parts.value?.style);

  const titleTextStyle: CSSProperties = {
    ...resolveKpiPartTypographyStyle(
      {
        ...parts.title?.style,
        fontSize: resolveKpiPartFontSize("title", parts.title?.style),
        color: resolvedTitleColor,
      },
      { flexPart: false },
    ),
    ...titleLayoutStyle,
  };
  const valueTextStyle: CSSProperties = {
    ...resolveKpiPartTypographyStyle(
      {
        ...parts.value?.style,
        // Auto-fit: FitText define o tamanho; não fixar fontSize no host.
        ...(valueAutoFit ? { fontSize: undefined } : { fontSize: valueFontSizePx }),
        ...(valueColorForStyle ? { color: valueColorForStyle } : { color: undefined }),
      },
      { flexPart: true },
    ),
    ...valueLayoutStyle,
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

  const cardPtr = bindKpiPartPointer({ kind: "card" }, interaction);
  const titlePtr = bindKpiPartPointer({ kind: "title" }, interaction);
  const valuePtr = bindKpiPartPointer({ kind: "value" }, interaction);
  const hintPtr = bindKpiPartPointer({ kind: "hint" }, interaction);
  const iconPtr = bindKpiPartPointer({ kind: "icon" }, interaction);

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
  const cardShowChrome =
    cardPtr.selected &&
    kpiPartAllowsResize({ kind: "card" }) &&
    Boolean(interaction?.onPartResizePointerDown);

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
                  fixedPx={valueAutoFit ? null : valueFontSizePx}
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
                iconFramed ? "delpi-kpi-icon--framed" : "",
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
