import type {
  ChatToolCall,
} from "../../data/api/chatTypes";

import { resolveAssistantContentLayout } from "./message/assistantContentLayout";
import { isHierarchyDuplicateTable } from "./presentation/pipeline/presentationStructureDedup";
import { normalizeChartPresentation } from "./presentation/pipeline/chartPresentationNormalize";
import {
  getPresentationPairFromToolCalls,
  getTablePresentationFromPair,
  getTreePresentationFromPair,
  hasRichPresentation,
  isTablePresentation,
  type PresentationPair,
} from "./presentation/presentationPairResolver";

import {
  stripChartMarkdownFallbackFromMarkdown,
  stripCompositionCodeFenceFromMarkdown,
  stripMarkdownGfmTablesFromCommentary,
  stripRedundantGuideTableFromMarkdown,
  stripRedundantHierarchyListFromMarkdown,
  stripRedundantInspectionDumpFromMarkdown,
  stripRedundantInspectionFromMarkdown,
  stripRedundantProfileTableFromMarkdown,
  stripRedundantStructureFromMarkdown,
  getTextMarkdownFromToolCalls,
  stripLeadingMarkdownTitle,
  stripCoverageNoticeFromMarkdown,
  hasDisplayableRichText,
  tablePresentationToMarkdown,
} from "./presentation/presentationMarkdownNormalization";

import {
  getAvailableFormatsFromToolCalls,
  getPathFromToolCalls,
  getPreferredFormatFromToolCalls,
  getPresentationDecisionFromToolCalls,
  getPresentationRenderHintsFromToolCalls,
  getTextPresentationTitleFromToolCalls,
  hasRenderPlanContract,
  isExplicitTextSessionMode,
  mapPresentationDecisionToViewFormat,
  type ViewFormat,
} from "./presentation/presentationMetadataReaders";

export type { ViewFormat, PresentationRenderHints, PresentationRenderPlan } from "./presentation/presentationMetadataReaders";
export {
  getAvailableFormatsFromToolCalls,
  getDataAnswerFromToolCalls,
  getDataCoverageNoticeFromToolCall,
  getDataCoverageNoticeFromToolCalls,
  getDepthStateFromToolCall,
  getDepthStateFromToolCalls,
  getPaginationStateFromToolCall,
  getPaginationStateFromToolCalls,
  getPathFromToolCalls,
  getPreferredFormatFromToolCalls,
  getPresentationDecisionFromToolCalls,
  getPresentationInsightFromToolCalls,
  getPresentationMessageFromToolCalls,
  getPresentationModeFromToolCalls,
  getPresentationPurposeFromToolCalls,
  getPresentationReadingLayersFromToolCalls,
  getPresentationRecommendationsFromToolCalls,
  getPresentationRenderHintsFromToolCalls,
  getPresentationScoresFromToolCalls,
  getRenderPlanAllowedVisualKinds,
  getRenderPlanFromToolCalls,
  getStoryPresentationFromToolCalls,
  getTextPresentationTitleFromToolCalls,
  hasExplicitPresentationFormatChoice,
  hasRenderPlanContract,
  isExplicitTextSessionMode,
  isRenderPlanVisualKindAllowed,
  mapPresentationDecisionToViewFormat,
  renderPlanHasOnlyProseSegments,
  getProseDeliveryModeFromToolCalls,
  getTemplateProseArchiveFromToolCalls,
  resolveRenderableHumanizedLines,
  resolveRenderableTemplateMarkdown,
} from "./presentation/presentationMetadataReaders";

export type { ChatProseDeliveryMode, ChatTemplateProseArchive } from "../../data/api/chatTypes";


export {
  getTextMarkdownFromToolCalls,
  hasDisplayableRichText,
  stripChartMarkdownFallbackFromMarkdown,
  stripCompositionCodeFenceFromMarkdown,
  stripCoverageNoticeFromMarkdown,
  stripLeadingMarkdownTitle,
  stripMarkdownGfmTablesFromCommentary,
  stripRedundantGuideTableFromMarkdown,
  stripRedundantHierarchyListFromMarkdown,
  stripRedundantInspectionDumpFromMarkdown,
  stripRedundantInspectionFromMarkdown,
  stripRedundantProfileTableFromMarkdown,
  stripRedundantStructureFromMarkdown,
  tablePresentationToMarkdown,
} from "./presentation/presentationMarkdownNormalization";



export type { PresentationPair } from "./presentation/presentationPairResolver";
export {
  getChartPresentationFromPair,
  getPresentationPairFromToolCalls,
  getTablePresentationFromPair,
  getTreePresentationFromPair,
  hasRichPresentation,
  isTablePresentation,
} from "./presentation/presentationPairResolver";


function getTableMarkdownBody(toolCalls?: ChatToolCall[]): string {
  const pair = getPresentationPairFromToolCalls(toolCalls);
  const table = getTablePresentationFromPair(pair);

  if (!table) {
    return "";
  }

  return tablePresentationToMarkdown(table, { includeTitle: false });
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


/** Remove dumps técnicos de inspeção (legado) quando há painel estruturado. */

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

/** Texto markdown já preparado na API (renderHints ou renderPlan P6). */
export function isApiPreparedMarkdown(toolCalls?: ChatToolCall[]): boolean {
  const hints = getPresentationRenderHintsFromToolCalls(toolCalls);
  const mode = String(hints?.textRenderMode || "").trim().toLowerCase();

  if (mode === "compact" || mode === "full") {
    return true;
  }

  return hasRenderPlanContract(toolCalls);
}

/** Legacy: só compacta markdown no cliente quando a API não enviou `renderHints.textRenderMode`. */
export function shouldApplyClientMarkdownCompaction(toolCalls?: ChatToolCall[]): boolean {
  if (isApiPreparedMarkdown(toolCalls)) {
    return false;
  }

  return hasRichStackPresentation(toolCalls) && !isExplicitTextSessionMode(toolCalls);
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

  if (!isApiPreparedMarkdown(toolCalls)) {
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

  const externalCalls = toolCalls.filter(
    (toolCall) => toolCall.name === "execute_external_action",
  );

  if (
    externalCalls.length > 0 &&
    externalCalls.every((toolCall) => toolCall.metadata?.ok === false)
  ) {
    return false;
  }

  if (shouldShowRichPresentation(content, toolCalls)) {
    return false;
  }

  return !hasToolCallTextPresentation(toolCalls);
}
