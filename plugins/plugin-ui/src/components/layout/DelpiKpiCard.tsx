import type { CSSProperties, ReactNode } from "react";
import { useLayoutEffect, useRef } from "react";

import { HelpTooltip } from "../help/HelpTooltip";
import {
  hasIllegibleTextContrast,
  isAutomaticTextColor,
  resolveAutomaticTextColor,
} from "../shape/colorUtils";
import { DECK_KPI_DEFAULTS } from "../../theme/deckColorCatalog";
import { FitText } from "./FitText";
import { KpiPartResizeHandles } from "./KpiPartResizeHandles";
import { metricKpiCardBemClasses, type MetricKpiCardTone } from "./MetricKpiCard";
import {
  KPI_ICON_DEFAULT_RADIUS_PX,
  KPI_PART_DATA_ATTR,
  bindKpiPartPointer,
  clampKpiPartFrame,
  getKpiPartState,
  isKpiPartVisible,
  kpiPartAllowsResize,
  kpiPartCornerAdjustCssPosition,
  mergeKpiPartsWithOptions,
  resolveKpiIconBoxStyle,
  resolveKpiPartFontSize,
  resolveKpiPartFrame,
  resolveKpiPartFrameRoot,
  resolveKpiPartLayoutStyle,
  resolveKpiPartTypographyStyle,
  kpiPartHasBoxPaint,
  type KpiCardFlatOptions,
  type KpiCardInteraction,
  type KpiPartRef,
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
  serializeKpiPartRef,
  upsertKpiPartState,
  applyKpiPartStyleToSiblingParts,
  isKpiTextPartKind,
  KPI_TEXT_PART_KINDS,
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

function useMaterializeKpiPartFrame(
  partRef: KpiPartRef,
  hostRef: { current: HTMLElement | null },
  showResize: boolean,
  framed: boolean,
  onPartFrameChange: KpiCardInteraction["onPartFrameChange"],
) {
  useLayoutEffect(() => {
    if (!showResize || framed || !onPartFrameChange) return;
    const host = hostRef.current;
    if (!host) return;
    const root = resolveKpiPartFrameRoot(host, partRef);
    if (!root) return;
    const rect = root.getBoundingClientRect();
    const el = host.getBoundingClientRect();
    if (rect.width < 1 || rect.height < 1) return;
    onPartFrameChange(
      partRef,
      clampKpiPartFrame({
        x: ((el.left - rect.left) / rect.width) * 100,
        y: ((el.top - rect.top) / rect.height) * 100,
        w: Math.max(8, (el.width / rect.width) * 100),
        h: Math.max(4, (el.height / rect.height) * 100),
      }),
    );
  }, [framed, hostRef, onPartFrameChange, partRef, showResize]);
}

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
  const titleLayoutStyle = resolveKpiPartLayoutStyle(titleState);
  const valueLayoutStyle = resolveKpiPartLayoutStyle(valueState);
  const hintLayoutStyle = resolveKpiPartLayoutStyle(hintState);
  const cardLayoutStyle = resolveKpiPartLayoutStyle(cardState);

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
        fontSize: resolveKpiPartFontSize("value", parts.value?.style),
        color: resolvedValueColor,
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
  const cardCornerRadius = parts.card?.style?.borderRadius ?? cardRadius ?? 12;

  useMaterializeKpiPartFrame(
    { kind: "title" },
    titleHostRef,
    titleShowResize,
    titleFramed,
    interaction?.onPartFrameChange,
  );
  useMaterializeKpiPartFrame(
    { kind: "value" },
    valueHostRef,
    valueShowResize,
    valueFramed,
    interaction?.onPartFrameChange,
  );
  useMaterializeKpiPartFrame(
    { kind: "hint" },
    hintHostRef,
    hintShowResize,
    hintFramed,
    interaction?.onPartFrameChange,
  );
  useMaterializeKpiPartFrame(
    { kind: "icon" },
    iconHostRef,
    iconShowResize,
    iconFramed,
    interaction?.onPartFrameChange,
  );
  useMaterializeKpiPartFrame(
    { kind: "card" },
    cardHostRef,
    cardShowChrome,
    cardFramed,
    interaction?.onPartFrameChange,
  );

  const shellStyle: CSSProperties = {
    position: "relative",
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
    ...(parts.card?.style?.opacity != null
      ? ({
          ["--delpi-kpi-card-opacity" as string]: String(parts.card.style.opacity),
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

  const valueFontSizePx = resolveKpiPartFontSize("value", parts.value?.style);

  return (
    <div
      className="delpi-kpi-card-shell"
      data-custom-value={resolvedValueColor ? "true" : undefined}
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
                <FitText fixedPx={valueFontSizePx}>{value}</FitText>
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
              style={resolveKpiIconBoxStyle(iconState)}
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
