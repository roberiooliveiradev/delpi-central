import type {
  ChatDataAnswer,
  ChatDataCoverageNotice,
  ChatDepthState,
  ChatPaginationState,
  ChatPresentation,
  ChatPresentationDecision,
  ChatStoryPresentation,
  ChatToolCall,
} from "../../data/api/chatTypes";

import { isNativeSingleViewSelection, resolveAssistantContentLayout } from "./assistantContentLayout";
import { isHierarchyDuplicateTable } from "./presentationStructureDedup";
import { normalizeChartPresentation } from "./chartPresentationNormalize";

export type PresentationPair = {
  primary: ChatPresentation | null;
  table: ChatPresentation | null;
  tree: ChatPresentation | null;
};

export type ViewFormat = "text" | "chart" | "table" | "tree" | "kpi" | "dashboard";

function isTablePresentation(
  value: unknown,
): value is Extract<ChatPresentation, { type: "table" }> {
  return (
    typeof value === "object" &&
    value !== null &&
    (value as { type?: string }).type === "table"
  );
}

function isTreePresentation(
  value: unknown,
): value is Extract<ChatPresentation, { type: "tree" }> {
  return (
    typeof value === "object" &&
    value !== null &&
    (value as { type?: string }).type === "tree"
  );
}

function tableColumnsMatch(
  left: Extract<ChatPresentation, { type: "table" }>["columns"],
  right: Extract<ChatPresentation, { type: "table" }>["columns"],
): boolean {
  if (left.length !== right.length) {
    return false;
  }

  return left.every((column, index) => column.key === right[index]?.key);
}

function inferProductCodeFromTable(
  table: Extract<ChatPresentation, { type: "table" }>,
): string {
  const firstRow = table.rows[0];

  if (!firstRow) {
    return "";
  }

  for (const key of ["product_code", "code", "productCode", "produto"]) {
    const value = firstRow[key];

    if (value !== undefined && value !== null && String(value).trim()) {
      return String(value).trim();
    }
  }

  return "";
}

function mergeTablePresentations(
  tables: Extract<ChatPresentation, { type: "table" }>[],
): Extract<ChatPresentation, { type: "table" }> | null {
  if (tables.length === 0) {
    return null;
  }

  if (tables.length === 1) {
    return tables[0];
  }

  const [first, ...rest] = tables;

  if (!rest.every((table) => tableColumnsMatch(first.columns, table.columns))) {
    return first;
  }

  const productCodes = tables
    .map((table) => inferProductCodeFromTable(table))
    .filter(Boolean);

  const title =
    productCodes.length > 1
      ? "Estoque por filial/armazém"
      : first.title;

  return {
    ...first,
    title,
    rows: tables.flatMap((table) => table.rows),
  };
}

function prefixChartSeriesName(
  entry: Record<string, unknown>,
  productCode: string,
): Record<string, unknown> {
  if (!productCode) {
    return entry;
  }

  const name = String(entry.name ?? "").trim();

  if (!name) {
    return entry;
  }

  if (name.startsWith(`${productCode} ·`) || name.startsWith(`${productCode} `)) {
    return entry;
  }

  return {
    ...entry,
    name: `${productCode} · ${name}`,
  };
}

function mergeChartPresentations(
  charts: Extract<ChatPresentation, { type: "chart" }>[],
  tables: Extract<ChatPresentation, { type: "table" }>[],
): Extract<ChatPresentation, { type: "chart" }> | null {
  if (charts.length === 0) {
    return null;
  }

  if (charts.length === 1) {
    return charts[0];
  }

  const [first, ...rest] = charts;

  if (
    rest.some(
      (chart) =>
        chart.chartType !== first.chartType ||
        JSON.stringify(chart.config ?? {}) !== JSON.stringify(first.config ?? {}),
    )
  ) {
    return first;
  }

  const mergedData = charts.flatMap((chart, index) => {
    const productCode = inferProductCodeFromTable(tables[index] ?? { type: "table", title: "", columns: [], rows: [] });

    return (chart.data ?? []).map((entry) =>
      prefixChartSeriesName(entry as Record<string, unknown>, productCode),
    );
  });

  const productCodes = tables
    .map((table) => inferProductCodeFromTable(table))
    .filter(Boolean);

  return {
    ...first,
    title:
      productCodes.length > 1
        ? "Estoque por filial/armazém"
        : first.title,
    data: mergedData,
  };
}

function collectExternalActionPresentations(toolCalls: ChatToolCall[]): {
  charts: Extract<ChatPresentation, { type: "chart" }>[];
  tables: Extract<ChatPresentation, { type: "table" }>[];
  trees: Extract<ChatPresentation, { type: "tree" }>[];
} {
  const charts: Extract<ChatPresentation, { type: "chart" }>[] = [];
  const tables: Extract<ChatPresentation, { type: "table" }>[] = [];
  const trees: Extract<ChatPresentation, { type: "tree" }>[] = [];

  for (const toolCall of toolCalls) {
    if (toolCall.name && toolCall.name !== "execute_external_action") {
      continue;
    }

    const metadata = (toolCall.metadata ?? {}) as Record<string, unknown>;
    const presentation = metadata.presentation;
    const tablePresentation = metadata.tablePresentation;
    const treePresentation = metadata.treePresentation;
    const chartPresentation = metadata.chartPresentation;

    const normalizedChart =
      normalizeChartPresentation(presentation) ?? normalizeChartPresentation(chartPresentation);

    if (normalizedChart) {
      charts.push(normalizedChart);
    }

    if (isTreePresentation(presentation)) {
      trees.push(presentation);
    } else if (isTreePresentation(treePresentation)) {
      trees.push(treePresentation);
    }

    if (isTablePresentation(tablePresentation)) {
      tables.push(tablePresentation);
    } else if (isTablePresentation(presentation)) {
      tables.push(presentation);
    }
  }

  return { charts, tables, trees };
}

function getPresentationFromToolCalls(
  toolCalls?: ChatToolCall[],
): ChatPresentation | null {
  if (!Array.isArray(toolCalls)) {
    return null;
  }

  const { charts, tables, trees } = collectExternalActionPresentations(toolCalls);

  if (trees.length > 0) {
    return trees[0];
  }

  const mergedChart = mergeChartPresentations(charts, tables);

  if (mergedChart) {
    return mergedChart;
  }

  if (trees.length === 1) {
    return trees[0];
  }

  if (trees.length > 1) {
    return trees[0];
  }

  for (const toolCall of toolCalls) {
    const presentation = toolCall.metadata?.presentation;

    if (
      presentation &&
      typeof presentation === "object" &&
      "type" in presentation
    ) {
      const presentationType = (presentation as ChatPresentation).type;

      if (presentationType !== "markdown") {
        return presentation as ChatPresentation;
      }
    }
  }

  return null;
}

function getTablePresentationFromToolCalls(
  toolCalls?: ChatToolCall[],
): ChatPresentation | null {
  if (!Array.isArray(toolCalls)) {
    return null;
  }

  const { tables } = collectExternalActionPresentations(toolCalls);
  const mergedTable = mergeTablePresentations(tables);

  if (mergedTable) {
    return mergedTable;
  }

  for (const toolCall of toolCalls) {
    const tablePresentation = (toolCall.metadata as Record<string, unknown>)?.tablePresentation;

    if (isTablePresentation(tablePresentation)) {
      return tablePresentation;
    }
  }

  return null;
}

function getTreePresentationFromToolCalls(
  toolCalls?: ChatToolCall[],
): ChatPresentation | null {
  if (!Array.isArray(toolCalls)) {
    return null;
  }

  const { trees } = collectExternalActionPresentations(toolCalls);

  if (trees.length === 1) {
    return trees[0];
  }

  if (trees.length > 1) {
    return trees[0];
  }

  for (const toolCall of toolCalls) {
    const treePresentation = (toolCall.metadata as Record<string, unknown>)?.treePresentation;

    if (isTreePresentation(treePresentation)) {
      return treePresentation;
    }
  }

  return null;
}

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
      typeof (decision as ChatPresentationDecision).selected === "string"
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

  if (isNativeSingleViewSelection(toolCalls).active) {
    return "";
  }

  return String(decision?.reason ?? "").trim();
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

export function isSummaryThenEvidenceMode(toolCalls?: ChatToolCall[]): boolean {
  return getPresentationModeFromToolCalls(toolCalls) === "summary_then_evidence";
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
    const plan = metadata?.stackPresentationPlan;

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

/** Legacy: só compacta markdown no cliente quando a API não enviou `renderHints.textRenderMode`. */
export function shouldApplyClientMarkdownCompaction(toolCalls?: ChatToolCall[]): boolean {
  const hints = getPresentationRenderHintsFromToolCalls(toolCalls);

  if (hints?.textRenderMode === "compact" || hints?.textRenderMode === "full") {
    return false;
  }

  return hasRichStackPresentation(toolCalls) && !isExplicitTextSessionMode(toolCalls);
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

export function getTextMarkdownFromToolCalls(toolCalls?: ChatToolCall[]): string {
  if (!Array.isArray(toolCalls)) {
    return "";
  }

  const sections: string[] = [];

  for (const toolCall of toolCalls) {
    const textPresentation = (toolCall.metadata as Record<string, unknown>)?.textPresentation;

    if (
      textPresentation &&
      typeof textPresentation === "object" &&
      (textPresentation as { type?: string }).type === "markdown"
    ) {
      const markdown = (textPresentation as { markdown?: string }).markdown;

      if (typeof markdown === "string" && markdown.trim()) {
        sections.push(markdown.trim());
      }
    }
  }

  if (sections.length > 1) {
    return sections.join("\n\n");
  }

  if (sections.length === 1) {
    return sections[0];
  }

  for (const toolCall of toolCalls) {
    const textPresentation = (toolCall.metadata as Record<string, unknown>)?.textPresentation;

    if (
      textPresentation &&
      typeof textPresentation === "object" &&
      (textPresentation as { type?: string }).type === "markdown"
    ) {
      const markdown = (textPresentation as { markdown?: string }).markdown;

      if (typeof markdown === "string" && markdown.trim()) {
        return markdown.trim();
      }
    }

    const presentation = toolCall.metadata?.presentation;

    if (
      presentation &&
      typeof presentation === "object" &&
      (presentation as { type?: string }).type === "markdown"
    ) {
      const markdown = (presentation as { markdown?: string }).markdown;

      if (typeof markdown === "string" && markdown.trim()) {
        return markdown.trim();
      }
    }
  }

  return "";
}

function escapeMarkdownCell(value: unknown): string {
  return String(value ?? "")
    .replace(/\|/g, "\\|")
    .replace(/\n/g, " ");
}

export function getTablePresentationFromPair(
  pair: PresentationPair,
): Extract<ChatPresentation, { type: "table" }> | null {
  if (pair.table?.type === "table") {
    return pair.table;
  }

  if (pair.primary?.type === "table") {
    return pair.primary;
  }

  return null;
}

export function getTreePresentationFromPair(
  pair: PresentationPair,
): Extract<ChatPresentation, { type: "tree" }> | null {
  if (pair.tree?.type === "tree") {
    return pair.tree;
  }

  if (pair.primary?.type === "tree") {
    return pair.primary;
  }

  return null;
}

export function getChartPresentationFromPair(
  pair: PresentationPair,
  toolCalls?: ChatToolCall[],
): Extract<ChatPresentation, { type: "chart" }> | null {
  if (pair.primary?.type === "chart") {
    return pair.primary;
  }

  if (!Array.isArray(toolCalls)) {
    return null;
  }

  const { charts, tables } = collectExternalActionPresentations(toolCalls);

  return mergeChartPresentations(charts, tables);
}

function inferPresentationTitleFromToolPath(path: string): string | null {
  const lowered = path.toLowerCase();

  if (lowered.includes("eficiencia-fabril") || lowered.includes("eficiencia_fabril")) {
    return "Eficiência fabril";
  }

  if (lowered.includes("/lmp")) {
    return "Lista de LMPs";
  }

  return null;
}

const STALE_LMP_TITLE = "Lista de LMPs";

export function getPresentationTitle(
  messageContent: string | null | undefined,
  toolCalls?: ChatToolCall[],
): string {
  const pathTitle = inferPresentationTitleFromToolPath(getPathFromToolCalls(toolCalls ?? []));
  const textTitle = getTextPresentationTitleFromToolCalls(toolCalls);

  if (textTitle && (!pathTitle || textTitle !== STALE_LMP_TITLE)) {
    return textTitle;
  }

  const pair = getPresentationPairFromToolCalls(toolCalls);

  if (pair.primary?.type === "chart" && pair.primary.title) {
    const chartTitle = pair.primary.title;

    if (pathTitle && chartTitle === STALE_LMP_TITLE) {
      return pathTitle;
    }

    return chartTitle;
  }

  const tree = getTreePresentationFromPair(pair);

  if (tree?.title) {
    return tree.title;
  }

  const table = getTablePresentationFromPair(pair);

  if (table?.title) {
    if (pathTitle && table.title === STALE_LMP_TITLE) {
      return pathTitle;
    }

    return table.title;
  }

  if (pathTitle) {
    return pathTitle;
  }

  const trimmed = String(messageContent || "").trim();

  if (!trimmed) {
    return "Resultado";
  }

  // Prosa simples (sem apresentação rica): não usar o corpo inteiro como título.
  if (!hasRichPresentation(pair) && !getTextMarkdownFromToolCalls(toolCalls)) {
    return "";
  }

  return trimmed;
}

export function tablePresentationToMarkdown(
  presentation: Extract<ChatPresentation, { type: "table" }>,
  options?: { includeTitle?: boolean },
): string {
  const { title, columns, rows } = presentation;
  const includeTitle = options?.includeTitle !== false;

  if (!columns.length) {
    return includeTitle && title ? `### ${title}` : "";
  }

  const header = columns.map((column) => column.label).join(" | ");
  const separator = columns.map(() => "---").join(" | ");
  const body = rows.map((row) =>
    columns.map((column) => escapeMarkdownCell(row[column.key])).join(" | "),
  );

  const tableLines = [
    `| ${header} |`,
    `| ${separator} |`,
    ...body.map((line) => `| ${line} |`),
  ];

  if (includeTitle && title) {
    return [`### ${title}`, "", ...tableLines].join("\n");
  }

  return tableLines.join("\n");
}

function getTableMarkdownBody(toolCalls?: ChatToolCall[]): string {
  const pair = getPresentationPairFromToolCalls(toolCalls);
  const table = getTablePresentationFromPair(pair);

  if (!table) {
    return "";
  }

  return tablePresentationToMarkdown(table, { includeTitle: false });
}

export function stripLeadingMarkdownTitle(markdown: string, title: string): string {
  const normalizedTitle = title.trim();

  if (!normalizedTitle) {
    return markdown.trim();
  }

  const lines = markdown.split("\n");
  const firstNonEmpty = lines.findIndex((line) => line.trim());

  if (firstNonEmpty === -1) {
    return "";
  }

  const heading = lines[firstNonEmpty].trim();

  if (
    heading === `### ${normalizedTitle}` ||
    heading === `## ${normalizedTitle}` ||
    heading === `# ${normalizedTitle}` ||
    heading === normalizedTitle
  ) {
    return lines
      .slice(firstNonEmpty + 1)
      .join("\n")
      .trim();
  }

  return markdown.trim();
}

export function isShortPresentationCaption(
  content: string | null | undefined,
  toolCalls?: ChatToolCall[],
): boolean {
  const trimmed = String(content || "").trim();

  if (!trimmed) {
    return false;
  }

  if (trimmed.includes("|") && trimmed.includes("-")) {
    return false;
  }

  if (trimmed.length > 220 || trimmed.split("\n").length > 5) {
    return false;
  }

  const title = getPresentationTitle(trimmed, toolCalls);

  return trimmed === title || trimmed === `### ${title}`;
}

export function hasDisplayableRichText(text: string | null | undefined): boolean {
  return String(text || "").trim().length > 0;
}

/** Remove dumps técnicos de inspeção (legado) quando há painel estruturado. */
export function stripRedundantInspectionDumpFromMarkdown(markdown: string): string {
  const lines = markdown.split("\n");
  const result: string[] = [];

  for (const line of lines) {
    const trimmed = line.trim();

    if (
      trimmed.startsWith("- Product=")
      || trimmed.includes("Qp6=[")
      || trimmed.includes("Qp7=[")
      || trimmed.includes("QP6_PRODUT")
    ) {
      continue;
    }

    result.push(line);
  }

  return result.join("\n").replace(/\n{3,}/g, "\n\n").trim();
}

/** Remove tabela Campo/Valor duplicada quando `tablePresentation` já exibe o cadastro. */
export function stripRedundantProfileTableFromMarkdown(markdown: string): string {
  const lines = markdown.split("\n");
  const result: string[] = [];
  let skipping = false;

  for (const line of lines) {
    const trimmed = line.trim();

    if (
      !skipping &&
      /^\|\s*(Campo|campo)\s*\|/i.test(trimmed) &&
      /\bValor\b/i.test(trimmed)
    ) {
      skipping = true;
      continue;
    }

    if (skipping) {
      if (trimmed.startsWith("|")) {
        continue;
      }

      skipping = false;
    }

    result.push(line);
  }

  return result.join("\n").replace(/\n{3,}/g, "\n\n").trim();
}

/** Remove tabela markdown do roteiro quando `tablePresentation` já exibe o componente nativo. */
export function stripRedundantGuideTableFromMarkdown(markdown: string): string {
  const lines = markdown.split("\n");
  const result: string[] = [];
  let skipping = false;

  for (const line of lines) {
    const trimmed = line.trim();

    if (!skipping && /^\*\*Roteiro de produção\*\*$/i.test(trimmed)) {
      skipping = true;
      continue;
    }

    if (skipping) {
      if (
        trimmed.startsWith("|") ||
        trimmed === "" ||
        /^Inspeção:/i.test(trimmed)
      ) {
        if (/^Inspeção:/i.test(trimmed)) {
          skipping = false;
          result.push(line);
        }

        continue;
      }

      skipping = false;
    }

    result.push(line);
  }

  return result.join("\n").replace(/\n{3,}/g, "\n\n").trim();
}

/** Remove blocos markdown de inspeção quando há tabela nativa no metadata. */
export function stripRedundantInspectionFromMarkdown(markdown: string): string {
  const lines = markdown.split("\n");
  const result: string[] = [];
  let skipping = false;

  for (const line of lines) {
    const trimmed = line.trim();

    if (!skipping && /^\*\*Plano de inspeção\*\*$/i.test(trimmed)) {
      skipping = true;
      continue;
    }

    if (skipping) {
      if (
        trimmed.startsWith("|") ||
        trimmed === "" ||
        /^\*(Ensaios|Componentes referenciados)/i.test(trimmed) ||
        /^\*\*Destaques\*\*$/i.test(trimmed) ||
        /^\*\*Pontos de atenção/i.test(trimmed)
      ) {
        if (
          /^\*\*Destaques\*\*$/i.test(trimmed) ||
          /^\*\*Pontos de atenção/i.test(trimmed)
        ) {
          skipping = false;
          result.push(line);
        }

        continue;
      }

      skipping = false;
    }

    result.push(line);
  }

  return result.join("\n").replace(/\n{3,}/g, "\n\n").trim();
}

export function stripRedundantStructureFromMarkdown(markdown: string): string {
  const lines = markdown.split("\n");
  const result: string[] = [];
  let skipping = false;

  for (const line of lines) {
    const trimmed = line.trim();

    if (
      !skipping &&
      (trimmed.startsWith("**Estrutura do produto") ||
        trimmed === "**Produto pai**" ||
        trimmed === "**Componentes nível 1**" ||
        trimmed === "**Estrutura detalhada**")
    ) {
      skipping = true;
      continue;
    }

    if (skipping) {
      if (trimmed.startsWith("**Insights**")) {
        skipping = false;
        result.push(line);
      }

      continue;
    }

    result.push(line);
  }

  return result.join("\n").replace(/\n{3,}/g, "\n\n").trim();
}

export function stripRedundantHierarchyListFromMarkdown(markdown: string): string {
  const lines = markdown.split("\n");
  const result: string[] = [];

  for (const line of lines) {
    const trimmed = line.trim();

    if (
      trimmed.startsWith("**") &&
      trimmed.includes("—") &&
      (trimmed.includes("| Qtd:") || trimmed.includes("Qtd:"))
    ) {
      continue;
    }

    if (/^Total encontrado:/i.test(trimmed)) {
      continue;
    }

    result.push(line);
  }

  return result.join("\n").replace(/\n{3,}/g, "\n\n").trim();
}

function countComplementaryVisuals(metadata: Record<string, unknown>): {
  tables: number;
  trees: number;
  charts: number;
} {
  let tables = 0;
  const bundled = metadata.tablePresentations;

  if (Array.isArray(bundled)) {
    tables += bundled.filter(
      (item) => (item as { type?: string } | undefined)?.type === "table",
    ).length;
  }

  for (const key of [
    "tablePresentation",
    "profileTablePresentation",
    "inspectionTablePresentation",
  ]) {
    if ((metadata[key] as { type?: string } | undefined)?.type === "table") {
      tables += 1;
    }
  }

  if ((metadata.presentation as { type?: string } | undefined)?.type === "table") {
    tables += 1;
  }

  const trees =
    Number((metadata.treePresentation as { type?: string } | undefined)?.type === "tree") +
    Number((metadata.presentation as { type?: string } | undefined)?.type === "tree");
  const charts =
    Number((metadata.chartPresentation as { type?: string } | undefined)?.type === "chart") +
    Number((metadata.presentation as { type?: string } | undefined)?.type === "chart");

  return { tables, trees, charts };
}

function stripMarkdownGfmTablesFromCommentary(markdown: string): string {
  const lines = markdown.split("\n");
  const result: string[] = [];
  let skipping = false;

  for (const line of lines) {
    const trimmed = line.trim();

    if (!skipping && trimmed.startsWith("|") && trimmed.includes("|")) {
      skipping = true;
      continue;
    }

    if (skipping) {
      if (trimmed.startsWith("|") || trimmed === "") {
        continue;
      }

      skipping = false;
    }

    result.push(line);
  }

  return result.join("\n").replace(/\n{3,}/g, "\n\n").trim();
}

/** Apresentação rica empilhada (qualquer rota com texto + visuais nativos). */
export function hasRichStackPresentation(toolCalls?: ChatToolCall[]): boolean {
  if (!Array.isArray(toolCalls)) {
    return false;
  }

  for (const toolCall of toolCalls) {
    if (toolCall.name && toolCall.name !== "execute_external_action") {
      continue;
    }

    const metadata = (toolCall.metadata ?? {}) as Record<string, unknown>;

    if (!metadata.ok) {
      continue;
    }

    const decision = metadata.presentationDecision as
      | { layoutMode?: string; availableViews?: string[] }
      | undefined;

    if (decision?.layoutMode === "stack") {
      return true;
    }

    const { tables, trees, charts } = countComplementaryVisuals(metadata);
    const kinds = Number(tables > 0) + Number(trees > 0) + Number(charts > 0);

    if (kinds >= 2 || tables >= 2) {
      return true;
    }
  }

  return false;
}

function hasTreePresentation(toolCalls?: ChatToolCall[]): boolean {
  if (!Array.isArray(toolCalls)) {
    return false;
  }

  return toolCalls.some((toolCall) => {
    const metadata = (toolCall.metadata ?? {}) as Record<string, unknown>;
    const tree = metadata.treePresentation;
    const presentation = metadata.presentation;

    return (
      (tree && typeof tree === "object" && (tree as { type?: string }).type === "tree") ||
      (presentation &&
        typeof presentation === "object" &&
        (presentation as { type?: string }).type === "tree")
    );
  });
}

function hasChartPresentation(toolCalls?: ChatToolCall[]): boolean {
  if (!Array.isArray(toolCalls)) {
    return false;
  }

  return toolCalls.some((toolCall) => {
    const metadata = (toolCall.metadata ?? {}) as Record<string, unknown>;
    const chart = normalizeChartPresentation(metadata.chartPresentation);
    const presentation = normalizeChartPresentation(metadata.presentation);

    return Boolean(chart || presentation);
  });
}

export function stripCompositionCodeFenceFromMarkdown(markdown: string): string {
  const withSection = markdown.replace(
    /(?:^|\n)\s*\*\*Composição\*\*\s*\n+```[\w-]*\s*\n[\s\S]*?\n```/gi,
    "",
  );

  return withSection.replace(/(?:^|\n)\s*```text\s*\n[\s\S]*?\n```/gi, "").trim();
}

export function stripChartMarkdownFallbackFromMarkdown(markdown: string): string {
  return markdown
    .replace(
      /(?:^|\n)\s*\*\*[^*]+\*\*\s*\n+_Dados do gráfico[\s\S]*?(?=\n\*\*[^*]+\*\*|\n#{1,3} |\n<!-- section:|\Z)/gi,
      "",
    )
    .replace(/\n{3,}/g, "\n\n")
    .trim();
}

/** Remove narrativa duplicada quando componentes nativos já exibem os dados. */
export function stripRichUiRedundantProseFromMarkdown(
  markdown: string,
  toolCalls?: ChatToolCall[],
): string {
  let body = String(markdown || "").trim();

  if (!body || !hasRichStackPresentation(toolCalls)) {
    return body;
  }

  body = body
    .replace(
      /O produto \*\*[^*]+\*\*[^.\n]*\.\s*A estrutura de nível \d+ inclui:[\s\S]*?(?:Fontes cruzadas nesta consulta:[^\n]+\n?)?/gi,
      "",
    )
    .replace(/Fontes cruzadas nesta consulta:[^\n]+\n?/gi, "")
    .replace(
      /A \*\*(?:estrutura|composição|hierarquia|dados)\*\*[^\n]*(?:árvore|tabela|gráfico|visualizações)[^\n]*\n?/gi,
      "",
    )
    .replace(/Use a \*\*(?:árvore|tabela)\*\*[^\n]+\n?/gi, "");

  const pair = getPresentationPairFromToolCalls(toolCalls);

  if (getTablePresentationFromPair(pair) || hasGuideTablePresentation(toolCalls)) {
    body = stripMarkdownGfmTablesFromCommentary(body);
    body = stripRedundantProfileTableFromMarkdown(body);
    body = stripRedundantGuideTableFromMarkdown(body);
  }

  if (getTreePresentationFromPair(pair) || hasTreePresentation(toolCalls)) {
    body = stripRedundantStructureFromMarkdown(body);
    body = stripRedundantHierarchyListFromMarkdown(body);
    body = stripCompositionCodeFenceFromMarkdown(body);
  }

  if (hasChartPresentation(toolCalls)) {
    body = stripChartMarkdownFallbackFromMarkdown(body);
  }

  if (hasInspectionTablePresentation(toolCalls)) {
    body = stripRedundantInspectionFromMarkdown(body);
    body = stripRedundantInspectionDumpFromMarkdown(body);
  }

  const lines = body.split("\n");
  const filtered: string[] = [];

  for (const line of lines) {
    const trimmed = line.trim();

    if (/^Produto \*\*[^*]+\*\*:/i.test(trimmed)) {
      continue;
    }

    if (
      /^(Tipo |Status ativo:|Indicador de bloqueio:|Referência de cliente:|Último preço|Última revisão:|Inspeção:|Armazém padrão:)/i.test(
        trimmed,
      )
    ) {
      continue;
    }

    filtered.push(line);
  }

  return filtered.join("\n").replace(/\n{3,}/g, "\n\n").trim();
}

export function stripCoverageNoticeFromMarkdown(markdown: string): string {
  const trimmed = String(markdown || "").trim();

  if (!trimmed) {
    return "";
  }

  const coverageBlockPattern =
    /(?:^|\n\n)> \*\*Cobertura dos dados:\*\*[^\n]*(?:\n> [^\n]*)*/gu;

  return trimmed.replace(coverageBlockPattern, "").replace(/\n{3,}/g, "\n\n").trim();
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

export function isStructureLikeToolCalls(toolCalls?: ChatToolCall[]): boolean {
  const path = getPathFromToolCalls(toolCalls).toLowerCase();

  return (
    path.includes("/structure") ||
    path.includes("/parents") ||
    path.includes("/analyser")
  );
}

export function hasTreePresentationAvailable(
  toolCalls?: ChatToolCall[],
  pair?: PresentationPair,
): boolean {
  const resolvedPair = pair ?? getPresentationPairFromToolCalls(toolCalls);

  return Boolean(getTreePresentationFromPair(resolvedPair));
}

export type RichFormatToggleOptions = {
  showText: boolean;
  showTree: boolean;
  showTable: boolean;
  showChart: boolean;
};

/** Texto + árvore + tabela; oculta gráfico quando há árvore hierárquica. */
export function resolveRichFormatToggles(options: {
  hasText: boolean;
  hasChart: boolean;
  hasTable: boolean;
  hasTree: boolean;
  isCommentaryVisual: boolean;
}): RichFormatToggleOptions {
  const { hasText, hasChart, hasTable, hasTree, isCommentaryVisual } = options;
  const hierarchyWithTree = hasTree;

  return {
    showText: !isCommentaryVisual && hasText,
    showTree: hasTree,
    showTable: hasTable,
    showChart: hasChart && !hierarchyWithTree,
  };
}

export function countRichVisualFormats(toggles: RichFormatToggleOptions): number {
  return [toggles.showTree, toggles.showTable, toggles.showChart].filter(Boolean).length;
}

/** Modo visual inicial: árvore quando existir; texto só se não houver árvore. */
export function resolveDefaultRichViewMode(
  toolCalls: ChatToolCall[] | undefined,
  options: {
    hasText: boolean;
    hasChart: boolean;
    hasTable: boolean;
    hasTree: boolean;
    commentaryVisual?: boolean;
  },
): ViewFormat {
  const { hasText, hasChart, hasTable, hasTree, commentaryVisual = false } = options;
  const preferred = getPreferredFormatFromToolCalls(toolCalls);
  const decision = getPresentationDecisionFromToolCalls(toolCalls);
  const decisionView = mapPresentationDecisionToViewFormat(decision?.selected);

  if (decisionView === "tree" && hasTree) {
    return "tree";
  }

  if (decisionView === "chart" && hasChart) {
    return "chart";
  }

  if (decisionView === "table" && hasTable) {
    return "table";
  }

  if (!commentaryVisual && decisionView === "text" && hasText && !hasTree) {
    return "text";
  }

  if (!commentaryVisual && preferred === "text" && hasText && !hasTree) {
    return "text";
  }

  if (hasTree && (!decisionView || decisionView === "tree")) {
    return "tree";
  }

  if (preferred === "chart" && hasChart) {
    return "chart";
  }

  if (preferred === "table" && hasTable) {
    return "table";
  }

  if (hasChart) {
    return "chart";
  }

  if (hasTable) {
    return "table";
  }

  if (!commentaryVisual && hasText) {
    return "text";
  }

  return "tree";
}

export function hasInspectionTablePresentation(toolCalls?: ChatToolCall[]): boolean {
  if (!Array.isArray(toolCalls)) {
    return false;
  }

  for (const toolCall of toolCalls) {
    if (toolCall.name && toolCall.name !== "execute_external_action") {
      continue;
    }

    const metadata = (toolCall.metadata ?? {}) as Record<string, unknown>;
    const candidates = [
      metadata.inspectionTablePresentation,
      ...(Array.isArray(metadata.tablePresentations) ? metadata.tablePresentations : []),
    ];

    for (const candidate of candidates) {
      if (!isTablePresentation(candidate)) {
        continue;
      }

      const title = String(candidate.title || "").toLowerCase();

      if (title.includes("inspeção") || title.includes("inspecao")) {
        return true;
      }

      const keys = new Set(
        (candidate.columns ?? []).map((column) => String(column.key || "").toLowerCase()),
      );

      if (keys.has("section") && keys.has("test")) {
        return true;
      }
    }
  }

  return false;
}

export function hasGuideTablePresentation(toolCalls?: ChatToolCall[]): boolean {
  if (!Array.isArray(toolCalls)) {
    return false;
  }

  for (const toolCall of toolCalls) {
    if (toolCall.name && toolCall.name !== "execute_external_action") {
      continue;
    }

    const metadata = (toolCall.metadata ?? {}) as Record<string, unknown>;
    const candidates = [metadata.tablePresentation, metadata.presentation].filter(Boolean);

    for (const candidate of candidates) {
      if (!isTablePresentation(candidate)) {
        continue;
      }

      const title = String(candidate.title || "").toLowerCase();
      const keys = new Set(
        (candidate.columns ?? []).map((column) => String(column.key || "").toLowerCase()),
      );

      if (title.includes("roteiro")) {
        return true;
      }

      if (
        keys.has("product_code") &&
        keys.has("operation_description") &&
        keys.has("bom_level")
      ) {
        return true;
      }
    }
  }

  return false;
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

export type PresentationLayoutMode = "toggle" | "commentary-visual";

/** Legado: o chat usa `resolveAssistantContentLayout` (assistantContentLayout.ts). */
export function resolvePresentationLayoutMode(
  toolCalls?: ChatToolCall[],
  pair?: PresentationPair,
): PresentationLayoutMode {
  return resolveAssistantContentLayout("", toolCalls ?? [], pair) === "stack"
    ? "commentary-visual"
    : "toggle";
}

/** Empilha texto + visuais quando a API indica combinação (layoutMode stack). */
export function shouldStackPresentationBlocks(
  toolCalls?: ChatToolCall[],
  pair?: PresentationPair,
): boolean {
  return resolveAssistantContentLayout("", toolCalls ?? [], pair) === "stack";
}

/** Narrativa para intercalar seções (preserva **Destaques** / **Pontos de atenção**). */
export function resolveStackCommentaryBody(
  messageContent: string | null | undefined,
  toolCalls?: ChatToolCall[],
): string {
  const fromMetadata = getTextMarkdownFromToolCalls(toolCalls);
  const presentationTitle =
    getTextPresentationTitleFromToolCalls(toolCalls) ||
    getPresentationTitle(messageContent, toolCalls);

  let body = fromMetadata;

  if (!body) {
    body = stripLeadingMarkdownTitle(
      String(messageContent || "").trim(),
      presentationTitle,
    );
  } else {
    body = stripLeadingMarkdownTitle(body, presentationTitle);
  }

  body = stripCoverageNoticeFromMarkdown(body);

  if (shouldApplyClientMarkdownCompaction(toolCalls)) {
    body = stripRichUiRedundantProseFromMarkdown(body, toolCalls);
  }

  return body.trim();
}

export function resolveCommentaryTextBody(
  messageContent: string | null | undefined,
  toolCalls?: ChatToolCall[],
  pair?: PresentationPair,
): string {
  const resolvedPair = pair ?? getPresentationPairFromToolCalls(toolCalls);
  const fromMetadata = getTextMarkdownFromToolCalls(toolCalls);
  const presentationTitle =
    getTextPresentationTitleFromToolCalls(toolCalls) ||
    getPresentationTitle(messageContent, toolCalls);

  let body = fromMetadata;

  if (!body) {
    body = stripLeadingMarkdownTitle(
      String(messageContent || "").trim(),
      presentationTitle,
    );
  } else {
    body = stripLeadingMarkdownTitle(body, presentationTitle);
  }

  if (getTreePresentationFromPair(resolvedPair) || getTablePresentationFromPair(resolvedPair)) {
    body = stripRedundantProfileTableFromMarkdown(body);
    body = stripRedundantStructureFromMarkdown(body);
    body = stripRedundantHierarchyListFromMarkdown(body);
    body = stripRedundantInspectionDumpFromMarkdown(body);
  }

  if (hasGuideTablePresentation(toolCalls)) {
    body = stripRedundantGuideTableFromMarkdown(body);
  }

  if (hasInspectionTablePresentation(toolCalls)) {
    body = stripRedundantInspectionFromMarkdown(body);
  }

  if (shouldApplyClientMarkdownCompaction(toolCalls)) {
    body = stripRichUiRedundantProseFromMarkdown(body, toolCalls);
  }

  body = stripCoverageNoticeFromMarkdown(body);

  return body.trim();
}

/** Corpo markdown da aba Texto (tabela em GFM), sem repetir o título do cabeçalho. */
export function resolveRichTextBody(
  messageContent: string | null | undefined,
  toolCalls?: ChatToolCall[],
): string {
  const pair = getPresentationPairFromToolCalls(toolCalls);
  const fromMessage = String(messageContent || "").trim();
  const presentationTitle = getPresentationTitle(fromMessage, toolCalls);
  const hasTree = Boolean(getTreePresentationFromPair(pair));
  const hasHierarchyTable = Boolean(getTablePresentationFromPair(pair));
  const tableBody = getTableMarkdownBody(toolCalls);

  if (
    tableBody &&
    !hasTree &&
    !hasHierarchyTable &&
    (isShortPresentationCaption(fromMessage, toolCalls) || !fromMessage)
  ) {
    return tableBody;
  }

  const fromMetadata = getTextMarkdownFromToolCalls(toolCalls);

  if (fromMetadata) {
    return stripLeadingMarkdownTitle(fromMetadata, presentationTitle);
  }

  if (fromMessage) {
    return stripLeadingMarkdownTitle(fromMessage, presentationTitle);
  }

  if (!hasTree && !hasHierarchyTable) {
    return tableBody;
  }

  return "";
}

/** Texto do rascunho de e-mail (assunto + corpo), sem blocos de apresentação rica. */
export function buildEmailCopyText(messageContent: string | null | undefined): string {
  const raw = String(messageContent || "").trim();
  if (!raw) {
    return "";
  }

  const withoutRich = raw
    .replace(/^###\s+/gm, "")
    .replace(/\*\*Assunto[^*]*\*\*/gi, (match) => match.replace(/\*\*/g, ""))
    .replace(/\*\*/g, "")
    .trim();

  const subjectMatch = withoutRich.match(/^\s*assunto\s*:\s*(.+)$/im);
  if (subjectMatch) {
    return withoutRich;
  }

  const altSubject = withoutRich.match(/^\s*\*\*assunto\s+sugerido:\*\*\s*(.+)$/im);
  if (altSubject) {
    return withoutRich.replace(/^\s*\*\*assunto\s+sugerido:\*\*\s*/i, "Assunto: ");
  }

  return withoutRich;
}

/** Texto completo para copiar/compartilhar respostas com apresentação rica. */
export function buildAssistantCopyText(
  messageContent: string | null | undefined,
  toolCalls?: ChatToolCall[],
): string {
  const title = getPresentationTitle(messageContent, toolCalls);
  const body = resolveRichTextBody(messageContent, toolCalls);

  if (title && body) {
    return `${title}\n\n${body}`;
  }

  return body || title || String(messageContent || "").trim();
}

/** Compat: título + corpo (legado). Preferir getPresentationTitle + resolveRichTextBody. */
export function resolveRichTextContent(
  messageContent: string | null | undefined,
  toolCalls?: ChatToolCall[],
): string {
  const title = getPresentationTitle(messageContent, toolCalls);
  const body = resolveRichTextBody(messageContent, toolCalls);

  if (title && body) {
    return `### ${title}\n\n${body}`;
  }

  return body || title;
}

export function getPresentationPairFromToolCalls(
  toolCalls?: ChatToolCall[],
): PresentationPair {
  return {
    primary: getPresentationFromToolCalls(toolCalls),
    table: getTablePresentationFromToolCalls(toolCalls),
    tree: getTreePresentationFromToolCalls(toolCalls),
  };
}

const RICH_PRESENTATION_TYPES = new Set([
  "table",
  "chart",
  "kpi",
  "tree",
  "dashboard",
]);

export function hasRichPresentation(pair: PresentationPair): boolean {
  const primaryType = pair.primary?.type;

  if (primaryType && RICH_PRESENTATION_TYPES.has(primaryType)) {
    return true;
  }

  const tableType = pair.table?.type;
  const treeType = pair.tree?.type;

  return Boolean(
    (tableType && RICH_PRESENTATION_TYPES.has(tableType)) ||
      (treeType && RICH_PRESENTATION_TYPES.has(treeType)),
  );
}

export function hasMultiFormatPresentation(toolCalls?: ChatToolCall[]): boolean {
  const formats = getAvailableFormatsFromToolCalls(toolCalls);
  const unique = new Set(formats);

  if (unique.size >= 2) {
    return true;
  }

  const pair = getPresentationPairFromToolCalls(toolCalls);
  const flags = [
    Boolean(resolveRichTextContent("", toolCalls)),
    pair.primary?.type === "chart" || pair.table?.type === "table",
    pair.primary?.type === "table" || pair.table?.type === "table",
    pair.primary?.type === "tree" || pair.tree?.type === "tree",
  ];

  return flags.filter(Boolean).length >= 2;
}

/** Exibe tabela/gráfico/KPI ou painel multi-formato; evita repetir só markdown na aba Texto. */
export function shouldShowRichPresentation(
  content: string | null | undefined,
  toolCalls?: ChatToolCall[],
): boolean {
  if (!Array.isArray(toolCalls) || toolCalls.length === 0) {
    return false;
  }

  const pair = getPresentationPairFromToolCalls(toolCalls);

  if (hasRichPresentation(pair)) {
    return true;
  }

  if (hasMultiFormatPresentation(toolCalls)) {
    return true;
  }

  return shouldSuppressMarkdownForPresentation(content, pair, toolCalls);
}

export function shouldSuppressMarkdownForPresentation(
  content: string | null | undefined,
  pair: PresentationPair,
  toolCalls?: ChatToolCall[],
): boolean {
  const trimmed = String(content || "").trim();

  const tree = getTreePresentationFromPair(pair);
  const table = getTablePresentationFromPair(pair);

  if (tree && table?.title && isHierarchyDuplicateTable(table)) {
    const tableTitle = String(table.title).trim();

    if (
      trimmed === tableTitle ||
      trimmed === `### ${tableTitle}` ||
      trimmed.includes(tableTitle)
    ) {
      return true;
    }
  }

  if (hasMultiFormatPresentation(toolCalls)) {
    if (!trimmed) {
      return true;
    }

    if (isShortPresentationCaption(trimmed, toolCalls)) {
      return true;
    }
  }

  if (!hasRichPresentation(pair)) {
    return false;
  }

  if (shouldStackPresentationBlocks(toolCalls, pair)) {
    if (!trimmed) {
      return true;
    }

    if (isShortPresentationCaption(trimmed, toolCalls)) {
      return true;
    }

    const stackTitle = getPresentationTitle(content, toolCalls);
    const tableTitle = getTablePresentationFromPair(pair)?.title;
    const commentary = resolveCommentaryTextBody(content, toolCalls, pair);

    if (trimmed === stackTitle || trimmed === `### ${stackTitle}`) {
      return true;
    }

    if (tableTitle && (trimmed === tableTitle || trimmed === `### ${tableTitle}` || trimmed.includes(tableTitle))) {
      return true;
    }

    if (commentary && trimmed === commentary) {
      return true;
    }

    if (stripRedundantHierarchyListFromMarkdown(trimmed) !== trimmed) {
      return true;
    }
  }

  const panelBody = resolveRichTextBody(content, toolCalls);
  const panelTitle = getPresentationTitle(content, toolCalls);

  if (!hasDisplayableRichText(panelBody) && !panelTitle) {
    return false;
  }

  if (!trimmed) {
    return false;
  }

  if (isShortPresentationCaption(trimmed, toolCalls)) {
    return true;
  }

  if (trimmed === panelTitle) {
    return true;
  }

  if (trimmed.includes("|") && trimmed.includes("-")) {
    return true;
  }

  if (pair.primary?.type === "kpi") {
    return trimmed.length > 80;
  }

  return trimmed.length > 100;
}

function hasToolCallTextPresentation(toolCalls?: ChatToolCall[]): boolean {
  if (!Array.isArray(toolCalls)) {
    return false;
  }

  for (const toolCall of toolCalls) {
    const textPresentation = (toolCall.metadata as Record<string, unknown>)?.textPresentation;

    if (
      textPresentation &&
      typeof textPresentation === "object" &&
      typeof (textPresentation as { markdown?: string }).markdown === "string" &&
      (textPresentation as { markdown?: string }).markdown?.trim()
    ) {
      return true;
    }
  }

  return false;
}

/** Oculta JSON bruto da API quando já há apresentação rica ou texto humanizado. */
export function shouldShowActionResults(
  content: string | null | undefined,
  toolCalls?: ChatToolCall[],
): boolean {
  if (!Array.isArray(toolCalls) || toolCalls.length === 0) {
    return false;
  }

  if (shouldShowRichPresentation(content, toolCalls)) {
    return false;
  }

  return !hasToolCallTextPresentation(toolCalls);
}
