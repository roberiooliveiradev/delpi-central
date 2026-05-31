/** Posicionamento do card do tour sem cobrir o alvo em destaque. */

export type SpotlightRect = {
  top: number;
  left: number;
  width: number;
  height: number;
};

export type TourTooltipPlacement = "above" | "below" | "beside-end" | "beside-start" | "center";

export type TourTooltipLayout = {
  top: number;
  left: number;
  width: number;
  placement: TourTooltipPlacement;
};

const DEFAULT_ESTIMATED_HEIGHT = 210;
const DEFAULT_MAX_WIDTH = 352;
const GAP = 12;
const VIEWPORT_MARGIN = 12;
const BOTTOM_DOCK_RATIO = 0.42;
const TOP_REGION_RATIO = 0.32;

export function clamp(value: number, min: number, max: number): number {
  return Math.min(Math.max(value, min), max);
}

function tooltipBox(
  top: number,
  left: number,
  width: number,
  height: number,
): { top: number; left: number; width: number; height: number; right: number; bottom: number } {
  return {
    top,
    left,
    width,
    height,
    right: left + width,
    bottom: top + height,
  };
}

export function tourTooltipOverlapsSpotlight(
  layout: Pick<TourTooltipLayout, "top" | "left" | "width">,
  spotlight: SpotlightRect,
  tooltipHeight: number,
  gap = GAP,
): boolean {
  const tooltip = tooltipBox(layout.top, layout.left, layout.width, tooltipHeight);

  return !(
    tooltip.right + gap <= spotlight.left ||
    tooltip.left - gap >= spotlight.left + spotlight.width ||
    tooltip.bottom + gap <= spotlight.top ||
    tooltip.top - gap >= spotlight.top + spotlight.height
  );
}

type Candidate = TourTooltipLayout & { score: number };

function buildCandidates(
  spotlight: SpotlightRect,
  viewportWidth: number,
  viewportHeight: number,
  tooltipHeight: number,
  maxWidth: number,
): Candidate[] {
  const candidates: Candidate[] = [];
  const targetCenterX = spotlight.left + spotlight.width / 2;
  const targetTop = spotlight.top;
  const targetBottom = spotlight.top + spotlight.height;
  const targetInBottomDock = targetBottom >= viewportHeight * (1 - BOTTOM_DOCK_RATIO);
  const targetInTopRegion = targetTop <= viewportHeight * TOP_REGION_RATIO;

  const spaceAbove = targetTop - VIEWPORT_MARGIN;
  const spaceBelow = viewportHeight - targetBottom - VIEWPORT_MARGIN;
  const spaceLeft = spotlight.left - VIEWPORT_MARGIN;
  const spaceRight =
    viewportWidth - (spotlight.left + spotlight.width) - VIEWPORT_MARGIN;

  const centeredLeft = (width: number) =>
    clamp(
      targetCenterX - width / 2,
      VIEWPORT_MARGIN,
      viewportWidth - width - VIEWPORT_MARGIN,
    );

  if (spaceAbove >= tooltipHeight + GAP) {
    candidates.push({
      top: targetTop - tooltipHeight - GAP,
      left: centeredLeft(maxWidth),
      width: maxWidth,
      placement: "above",
      score: spaceAbove + (targetInBottomDock ? 2_000 : 400),
    });
  }

  if (spaceBelow >= tooltipHeight + GAP) {
    candidates.push({
      top: targetBottom + GAP,
      left: centeredLeft(maxWidth),
      width: maxWidth,
      placement: "below",
      score: spaceBelow + (targetInTopRegion ? 1_200 : 200),
    });
  }

  if (spaceRight >= maxWidth + GAP) {
    const width = Math.min(maxWidth, spaceRight - GAP);
    const top = clamp(
      targetTop,
      VIEWPORT_MARGIN,
      viewportHeight - tooltipHeight - VIEWPORT_MARGIN,
    );

    candidates.push({
      top,
      left: spotlight.left + spotlight.width + GAP,
      width,
      placement: "beside-end",
      score: spaceRight + (targetInBottomDock ? 50 : 300),
    });
  }

  if (spaceLeft >= maxWidth + GAP) {
    const width = Math.min(maxWidth, spaceLeft - GAP);
    const top = clamp(
      targetTop,
      VIEWPORT_MARGIN,
      viewportHeight - tooltipHeight - VIEWPORT_MARGIN,
    );

    candidates.push({
      top,
      left: spotlight.left - width - GAP,
      width,
      placement: "beside-start",
      score: spaceLeft + 250,
    });
  }

  const fallbackWidth = Math.min(maxWidth, viewportWidth - VIEWPORT_MARGIN * 2);
  const fallbackTop = clamp(
    targetInBottomDock
      ? targetTop - tooltipHeight - GAP
      : targetBottom + GAP,
    VIEWPORT_MARGIN,
    viewportHeight - tooltipHeight - VIEWPORT_MARGIN,
  );

  candidates.push({
    top: fallbackTop,
    left: centeredLeft(fallbackWidth),
    width: fallbackWidth,
    placement: "center",
    score: targetInBottomDock ? 100 : 0,
  });

  return candidates.sort((left, right) => right.score - left.score);
}

export function computeTourTooltipLayout(
  spotlight: SpotlightRect,
  viewportWidth: number,
  viewportHeight: number,
  options: {
    estimatedHeight?: number;
    maxWidth?: number;
    narrowViewportMaxWidth?: number;
  } = {},
): TourTooltipLayout {
  const tooltipHeight = options.estimatedHeight ?? DEFAULT_ESTIMATED_HEIGHT;
  const isNarrow = viewportWidth < 768;
  const maxWidth = Math.min(
    isNarrow
      ? (options.narrowViewportMaxWidth ?? viewportWidth - VIEWPORT_MARGIN * 2)
      : (options.maxWidth ?? DEFAULT_MAX_WIDTH),
    viewportWidth - VIEWPORT_MARGIN * 2,
  );

  const candidates = buildCandidates(
    spotlight,
    viewportWidth,
    viewportHeight,
    tooltipHeight,
    maxWidth,
  );

  for (const candidate of candidates) {
    if (!tourTooltipOverlapsSpotlight(candidate, spotlight, tooltipHeight)) {
      const { score: _score, ...layout } = candidate;
      return layout;
    }
  }

  const best = candidates[0];
  const { score: _score, ...layout } = best;

  if (tourTooltipOverlapsSpotlight(layout, spotlight, tooltipHeight)) {
    return {
      top: clamp(
        spotlight.top - tooltipHeight - GAP,
        VIEWPORT_MARGIN,
        viewportHeight - tooltipHeight - VIEWPORT_MARGIN,
      ),
      left: clamp(
        spotlight.left + spotlight.width / 2 - maxWidth / 2,
        VIEWPORT_MARGIN,
        viewportWidth - maxWidth - VIEWPORT_MARGIN,
      ),
      width: maxWidth,
      placement: "above",
    };
  }

  return layout;
}
