import type {
  ChatDataAnswer,
  ChatDataCoverageNotice,
  ChatDepthState,
  ChatPaginationState,
  ChatPresentationDecision,
  ChatStoryPresentation,
  ChatToolCall,
} from "../../../data/api/chatTypes";

import { isNativeSingleViewSelection } from "../message/assistantContentLayout";

export type ViewFormat = "text" | "chart" | "table" | "tree" | "kpi" | "dashboard";

export function getDataCoverageNoticeFromToolCall(
  toolCall?: ChatToolCall,
): ChatDataCoverageNotice | null {
  if (!toolCall) {
    return null;
  }

  const metadata = (toolCall.metadata as Record<string, unknown>) || {};

  if (
    metadata.sqlSchemaPrefetch === true ||
    metadata.suppressClientPresentation === true
  ) {
    return null;
  }

  const path = String(metadata.path || "").toLowerCase();

  if (
    path.includes("/system/tables") &&
    (path.includes("/columns") || path.includes("/schema") || path.includes("/relations"))
  ) {
    return null;
  }

  const notice = metadata.dataCoverageNotice;

  if (
    notice &&
    typeof notice === "object" &&
    typeof (notice as ChatDataCoverageNotice).message === "string" &&
    (notice as ChatDataCoverageNotice).message.trim()
  ) {
    return notice as ChatDataCoverageNotice;
  }

  return null;
}

export function getDataCoverageNoticeFromToolCalls(
  toolCalls?: ChatToolCall[],
): ChatDataCoverageNotice | null {
  if (!Array.isArray(toolCalls)) {
    return null;
  }

  for (const toolCall of toolCalls) {
    const notice = getDataCoverageNoticeFromToolCall(toolCall);

    if (notice) {
      return notice;
    }
  }

  return null;
}

const CHART_DECISION_TOKENS = new Set([
  "chart",
  "line_chart",
  "area_chart",
  "bar_chart",
  "horizontal_bar",
  "donut",
  "grouped_bar",
  "stacked_bar",
  "combo_chart",
  "histogram",
  "heatmap",
  "gauge",
  "scatter",
]);

export function getPresentationDecisionFromToolCalls(
  toolCalls?: ChatToolCall[],
): ChatPresentationDecision | null {
  if (!Array.isArray(toolCalls)) {
    return null;
  }

  for (const toolCall of toolCalls) {
    const decision = (toolCall.metadata as Record<string, unknown>)?.presentationDecision;

    if (
      decision &&
      typeof decision === "object" &&
      (typeof (decision as ChatPresentationDecision).selected === "string" ||
        typeof (decision as ChatPresentationDecision).layoutMode === "string")
    ) {
      return decision as ChatPresentationDecision;
    }
  }

  return null;
}

export function getPresentationInsightFromToolCalls(
  toolCalls?: ChatToolCall[],
): string {
  const decision = getPresentationDecisionFromToolCalls(toolCalls);
  const insight = String(decision?.insight ?? "").trim();

  if (insight) {
    return insight;
  }

  const reason = String(decision?.reason ?? "").trim();
  const nativeSingle = isNativeSingleViewSelection(toolCalls);

  if (nativeSingle.active && nativeSingle.kind === "text") {
    return "";
  }

  return reason;
}

function isStoryPresentation(value: unknown): value is ChatStoryPresentation {
  return (
    typeof value === "object" &&
    value !== null &&
    (value as ChatStoryPresentation).type === "story" &&
    Array.isArray((value as ChatStoryPresentation).blocks)
  );
}

export function getPresentationModeFromToolCalls(
  toolCalls?: ChatToolCall[],
): string | null {
  if (!Array.isArray(toolCalls)) {
    return null;
  }

  for (const toolCall of toolCalls) {
    const metadata = toolCall.metadata as Record<string, unknown> | undefined;
    const decision = metadata?.presentationDecision;

    if (decision && typeof decision === "object") {
      const mode = String((decision as ChatPresentationDecision).presentationMode || "").trim();

      if (mode) {
        return mode;
      }
    }

    const plan = metadata?.stackPresentationPlan;

    if (plan && typeof plan === "object") {
      const mode = String((plan as Record<string, unknown>).presentationMode || "").trim();

      if (mode) {
        return mode;
      }
    }
  }

  return null;
}

export type PresentationRenderHints = {
  textRenderMode?: "compact" | "full";
  tailVisualPolicy?: "allowlist" | "legacy";
  suppressedKinds?: string[];
};

export type PresentationRenderPlan = {
  version?: number;
  layoutMode?: string;
  segments?: Array<{
    kind: string;
    slot?: string;
    source?: string;
  }>;
};

export function getPresentationRenderHintsFromToolCalls(
  toolCalls?: ChatToolCall[],
): PresentationRenderHints | null {
  if (!Array.isArray(toolCalls)) {
    return null;
  }

  for (const toolCall of toolCalls) {
    const metadata = toolCall.metadata as Record<string, unknown> | undefined;

    if (!metadata) {
      continue;
    }

    const rootHints = metadata.renderHints;

    if (rootHints && typeof rootHints === "object") {
      return rootHints as PresentationRenderHints;
    }

    const plan = metadata.stackPresentationPlan;

    if (!plan || typeof plan !== "object") {
      continue;
    }

    const hints = (plan as Record<string, unknown>).renderHints;

    if (hints && typeof hints === "object") {
      return hints as PresentationRenderHints;
    }
  }

  return null;
}

export function getRenderPlanFromToolCalls(
  toolCalls?: ChatToolCall[],
): PresentationRenderPlan | null {
  if (!Array.isArray(toolCalls)) {
    return null;
  }

  for (const toolCall of toolCalls) {
    const metadata = toolCall.metadata as Record<string, unknown> | undefined;
    const renderPlan = metadata?.renderPlan;

    if (renderPlan && typeof renderPlan === "object") {
      return renderPlan as PresentationRenderPlan;
    }
  }

  return null;
}

const PROSE_RENDER_PLAN_KINDS = new Set(["markdown", "decision"]);

/** P6: API envia só prosa no renderPlan — MFE não deve montar visuais latentes do metadata. */
export function renderPlanHasOnlyProseSegments(
  renderPlan: PresentationRenderPlan | null | undefined,
): boolean {
  if (!renderPlan || renderPlan.version !== 1 || !Array.isArray(renderPlan.segments)) {
    return false;
  }

  if (!renderPlan.segments.length) {
    return false;
  }

  return renderPlan.segments.every((segment) =>
    PROSE_RENDER_PLAN_KINDS.has(String(segment?.kind || "").trim().toLowerCase()),
  );
}

const RENDER_PLAN_VISUAL_KINDS = new Set(["table", "chart", "tree", "kpi", "dashboard"]);

/** Kinds visuais permitidos pelo renderPlan v1; `null` = payload legado sem contrato. */
export function getRenderPlanAllowedVisualKinds(
  toolCalls?: ChatToolCall[],
): Set<string> | null {
  const renderPlan = getRenderPlanFromToolCalls(toolCalls);

  if (!hasRenderPlanContract(toolCalls) || !Array.isArray(renderPlan?.segments)) {
    return null;
  }

  const allowed = new Set<string>();

  for (const segment of renderPlan.segments) {
    const kind = String(segment?.kind || "").trim().toLowerCase();

    if (RENDER_PLAN_VISUAL_KINDS.has(kind)) {
      allowed.add(kind);
    }
  }

  return allowed;
}

export function isRenderPlanVisualKindAllowed(
  kind: string,
  toolCalls?: ChatToolCall[],
): boolean {
  const allowed = getRenderPlanAllowedVisualKinds(toolCalls);

  if (!allowed) {
    return true;
  }

  return allowed.has(String(kind || "").trim().toLowerCase());
}

/** Playbook 13 P6 — contrato mínimo para executor render-only (sem fallback blueprint). */
export function hasRenderPlanContract(toolCalls?: ChatToolCall[]): boolean {
  const renderPlan = getRenderPlanFromToolCalls(toolCalls);

  return Boolean(
    renderPlan &&
      renderPlan.version === 1 &&
      Array.isArray(renderPlan.segments) &&
      renderPlan.segments.length > 0,
  );
}

export function getStoryPresentationFromToolCalls(
  toolCalls?: ChatToolCall[],
): ChatStoryPresentation | null {
  if (!Array.isArray(toolCalls)) {
    return null;
  }

  for (const toolCall of toolCalls) {
    const story = (toolCall.metadata as Record<string, unknown> | undefined)?.storyPresentation;

    if (isStoryPresentation(story)) {
      return story;
    }
  }

  return null;
}

export function getDataAnswerFromToolCalls(
  toolCalls?: ChatToolCall[],
): ChatDataAnswer | null {
  if (!Array.isArray(toolCalls)) {
    return null;
  }

  for (const toolCall of toolCalls) {
    const dataAnswer = (toolCall.metadata as Record<string, unknown> | undefined)?.dataAnswer;

    if (dataAnswer && typeof dataAnswer === "object") {
      return dataAnswer as ChatDataAnswer;
    }
  }

  return null;
}

export function getPresentationPurposeFromToolCalls(
  toolCalls?: ChatToolCall[],
): string {
  const decision = getPresentationDecisionFromToolCalls(toolCalls);

  return String(decision?.purpose ?? "").trim();
}

export function getPresentationMessageFromToolCalls(
  toolCalls?: ChatToolCall[],
): string {
  const decision = getPresentationDecisionFromToolCalls(toolCalls);

  return String(decision?.message ?? "").trim();
}

export function getPresentationScoresFromToolCalls(
  toolCalls?: ChatToolCall[],
): Record<string, number> | null {
  const decision = getPresentationDecisionFromToolCalls(toolCalls);
  const scores = decision?.scores;

  if (!scores || typeof scores !== "object") {
    return null;
  }

  const normalized: Record<string, number> = {};

  for (const [key, value] of Object.entries(scores)) {
    if (typeof value === "number" && Number.isFinite(value)) {
      normalized[key] = value;
    }
  }

  return Object.keys(normalized).length ? normalized : null;
}

export function getPresentationReadingLayersFromToolCalls(
  toolCalls?: ChatToolCall[],
): ChatPresentationDecision["readingLayers"] {
  const decision = getPresentationDecisionFromToolCalls(toolCalls);
  const layers = decision?.readingLayers;

  if (!layers || typeof layers !== "object") {
    return null;
  }

  return layers;
}

export function getPresentationRecommendationsFromToolCalls(
  toolCalls?: ChatToolCall[],
): Array<{ label: string; reason?: string; query: string }> {
  const decision = getPresentationDecisionFromToolCalls(toolCalls);
  const dataAnswer = getDataAnswerFromToolCalls(toolCalls);
  const merged: Array<{ label: string; reason?: string; query: string; view?: string }> = [];
  const seen = new Set<string>();

  const pushRecommendation = (item: {
    label?: string | null;
    reason?: string | null;
    query?: string | null;
    view?: string | null;
  }) => {
    const label = String(item.label ?? "").trim();
    const query = String(item.query ?? label).trim();

    if (!label || !query || seen.has(query)) {
      return;
    }

    seen.add(query);
    merged.push({
      label,
      query,
      reason: item.reason ? String(item.reason).trim() : undefined,
      view: item.view ? String(item.view).trim() : undefined,
    });
  };

  for (const item of dataAnswer?.recommendations ?? []) {
    if (item && typeof item === "object") {
      pushRecommendation(item);
    }
  }

  for (const item of decision?.recommendations ?? []) {
    if (item && typeof item === "object") {
      pushRecommendation(item);
    }
  }

  if (!merged.length) {
    return [];
  }

  const selected = String(decision?.selected ?? "").trim().toLowerCase();

  return merged
    .map((item) => ({
      label: String(item.label ?? "").trim(),
      reason: item.reason ? String(item.reason).trim() : undefined,
      query: String(item.query ?? "").trim(),
      view: String(item.view ?? "").trim().toLowerCase(),
    }))
    .filter((item) => {
      if (!item.label || !item.query) {
        return false;
      }

      if (!selected) {
        return true;
      }

      if (item.view === selected) {
        return false;
      }

      if (
        selected === "chart" &&
        (item.view.includes("chart") || item.view === "line_chart" || item.view === "bar_chart")
      ) {
        return false;
      }

      return true;
    })
    .map(({ label, reason, query }) => ({ label, reason, query }));
}

export function mapPresentationDecisionToViewFormat(
  selected: string | null | undefined,
): ViewFormat | null {
  const token = String(selected ?? "").trim().toLowerCase();

  if (!token) {
    return null;
  }

  if (token === "table") {
    return "table";
  }

  if (token === "tree") {
    return "tree";
  }

  if (token === "text" || token === "canvas" || token === "checklist") {
    return "text";
  }

  if (CHART_DECISION_TOKENS.has(token) || token.includes("chart") || token.includes("bar")) {
    return "chart";
  }

  if (token === "kpi") {
    return "kpi";
  }

  if (token === "dashboard") {
    return "dashboard";
  }

  return null;
}

function mapViewTokenToLegacyFormat(token: string): string | null {
  const normalized = token.trim().toLowerCase();

  if (normalized === "table" || normalized === "tree" || normalized === "text") {
    return normalized;
  }

  if (
    CHART_DECISION_TOKENS.has(normalized) ||
    normalized.includes("chart") ||
    normalized.includes("bar") ||
    normalized === "donut" ||
    normalized === "heatmap" ||
    normalized === "gauge"
  ) {
    return "chart";
  }

  if (normalized === "kpi" || normalized === "dashboard") {
    return normalized;
  }

  return null;
}

export function getAvailableFormatsFromToolCalls(
  toolCalls?: ChatToolCall[],
): string[] {
  if (!Array.isArray(toolCalls)) {
    return [];
  }

  for (const toolCall of toolCalls) {
    const decision = (toolCall.metadata as Record<string, unknown>)?.presentationDecision;

    if (decision && typeof decision === "object") {
      const views = (decision as ChatPresentationDecision).availableViews;

      if (Array.isArray(views) && views.length > 0) {
        const mapped = views
          .map((view) => mapViewTokenToLegacyFormat(String(view)))
          .filter((format): format is string => Boolean(format));

        if (mapped.length > 0) {
          return [...new Set(mapped)];
        }
      }
    }

    const formats = (toolCall.metadata as Record<string, unknown>)?.availableFormats;

    if (Array.isArray(formats)) {
      return formats.map((format) => String(format));
    }
  }

  return [];
}

export function isExplicitTextSessionMode(toolCalls?: ChatToolCall[]): boolean {
  if (!Array.isArray(toolCalls)) {
    return false;
  }

  for (const toolCall of toolCalls) {
    const metadata = toolCall.metadata as Record<string, unknown> | undefined;

    if (!metadata) {
      continue;
    }

    const explicit = String(metadata.explicitSessionFormat || "").trim().toLowerCase();

    if (explicit === "text" || explicit === "topics") {
      return true;
    }
  }

  return false;
}

export function hasExplicitPresentationFormatChoice(
  toolCalls?: ChatToolCall[],
): boolean {
  if (!Array.isArray(toolCalls)) {
    return false;
  }

  for (const toolCall of toolCalls) {
    const metadata = toolCall.metadata as Record<string, unknown> | undefined;

    if (!metadata) {
      continue;
    }

    const explicit = String(metadata.explicitSessionFormat || "").trim();

    if (explicit) {
      return true;
    }

    const preferred = String(metadata.preferredFormat || "").trim().toLowerCase();
    const decision = metadata.presentationDecision as ChatPresentationDecision | undefined;
    const selected = mapPresentationDecisionToViewFormat(decision?.selected);

    if (
      preferred &&
      selected &&
      preferred === selected &&
      preferred !== "text"
    ) {
      return true;
    }

    const reason = String(decision?.reason || "").trim().toLowerCase();

    if (reason === "formato solicitado pelo usuário") {
      return true;
    }
  }

  return false;
}

export function getPreferredFormatFromToolCalls(
  toolCalls?: ChatToolCall[],
): ViewFormat | null {
  if (!Array.isArray(toolCalls)) {
    return null;
  }

  for (const toolCall of toolCalls) {
    const preferred = (toolCall.metadata as Record<string, unknown>)?.preferredFormat;

    if (preferred === "text" || preferred === "chart" || preferred === "table" || preferred === "tree") {
      return preferred;
    }
  }

  return null;
}

export function getTextPresentationTitleFromToolCalls(
  toolCalls?: ChatToolCall[],
): string {
  if (!Array.isArray(toolCalls)) {
    return "";
  }

  for (const toolCall of toolCalls) {
    const textPresentation = (toolCall.metadata as Record<string, unknown>)?.textPresentation;

    if (
      textPresentation &&
      typeof textPresentation === "object" &&
      typeof (textPresentation as { title?: string }).title === "string"
    ) {
      const title = (textPresentation as { title?: string }).title?.trim();

      if (title) {
        return title;
      }
    }
  }

  return "";
}
function readPaginationDetail(details: Record<string, unknown>): Record<string, unknown> | null {
  for (const key of ["pagination", "structurePagination", "stockPagination"]) {
    const candidate = details[key];

    if (candidate && typeof candidate === "object") {
      return candidate as Record<string, unknown>;
    }
  }

  return null;
}

function paginationStateFromNotice(
  notice: ChatDataCoverageNotice | null,
): ChatPaginationState | null {
  if (!notice) {
    return null;
  }

  const details =
    notice.details && typeof notice.details === "object"
      ? notice.details
      : null;
  const pagination = details ? readPaginationDetail(details) : null;

  const page = Number(pagination?.page ?? notice.page);
  const pageSize = Number(pagination?.pageSize ?? notice.pageSize);
  const totalPages = Number(pagination?.totalPages ?? notice.totalPages);
  const total = Number(pagination?.total ?? notice.total);

  if (!Number.isFinite(page) || page < 1 || !Number.isFinite(pageSize) || pageSize < 1) {
    return null;
  }

  const resolvedTotalPages =
    Number.isFinite(totalPages) && totalPages > 0
      ? totalPages
      : Number.isFinite(total) && total > 0
        ? Math.max(1, Math.ceil(total / pageSize))
        : undefined;

  return {
    page,
    pageSize,
    totalPages: resolvedTotalPages,
    total: Number.isFinite(total) && total >= 0 ? total : undefined,
    hasPrevious: page > 1,
    hasNext: resolvedTotalPages ? page < resolvedTotalPages : true,
  };
}

function depthStateFromNotice(notice: ChatDataCoverageNotice | null): ChatDepthState | null {
  if (!notice) {
    return null;
  }

  const details =
    notice.details && typeof notice.details === "object"
      ? notice.details
      : null;
  const depth =
    details?.depth && typeof details.depth === "object"
      ? (details.depth as Record<string, unknown>)
      : null;
  const maxDepth = Number(depth?.maxDepth ?? notice.maxDepth);

  if (!Number.isFinite(maxDepth) || maxDepth < 1 || maxDepth >= 99) {
    return null;
  }

  return {
    maxDepth,
    canIncrease: maxDepth < 99,
  };
}

export function getPaginationStateFromToolCall(
  toolCall?: ChatToolCall,
): ChatPaginationState | null {
  return paginationStateFromNotice(getDataCoverageNoticeFromToolCall(toolCall));
}

export function getDepthStateFromToolCall(toolCall?: ChatToolCall): ChatDepthState | null {
  return depthStateFromNotice(getDataCoverageNoticeFromToolCall(toolCall));
}

export function getPaginationStateFromToolCalls(
  toolCalls?: ChatToolCall[],
): ChatPaginationState | null {
  return paginationStateFromNotice(getDataCoverageNoticeFromToolCalls(toolCalls));
}

export function getDepthStateFromToolCalls(
  toolCalls?: ChatToolCall[],
): ChatDepthState | null {
  return depthStateFromNotice(getDataCoverageNoticeFromToolCalls(toolCalls));
}

export function getPathFromToolCalls(toolCalls?: ChatToolCall[]): string {
  if (!Array.isArray(toolCalls)) {
    return "";
  }

  for (const toolCall of toolCalls) {
    const path = (toolCall.metadata as Record<string, unknown>)?.path;

    if (typeof path === "string" && path.trim()) {
      return path.trim();
    }
  }

  return "";
}
