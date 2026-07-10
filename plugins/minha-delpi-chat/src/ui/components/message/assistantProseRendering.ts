import type { ChatMessageMetadata, ChatToolCall } from "../../../data/api/chatTypes";

import { hasMarkdownSyntax, stripPresentationSectionMarkers } from "./chatMarkdown";
import { isNativeSingleViewSelection } from "./assistantContentLayout";
import {
  getPresentationTitle,
  getRenderPlanFromToolCalls,
  getTextMarkdownFromToolCalls,
  isShortPresentationCaption,
  stripLeadingMarkdownTitle,
} from "../chatPresentation";
import { isLlmProseDecoupledFromToolCalls } from "../presentation/presentationMarkdownNormalization";

/**
 * Regras centralizadas de prosa do assistente (chat base).
 * Ponto de entrada único — não duplicar lógica em ChatMessageList, hooks ou segmentos.
 *
 * 1. Título de apresentação ≠ corpo da mensagem — prosa simples não gera heading.
 * 2. Corpo com markdown sempre passa por ChatMarkdown (nunca texto cru / reveal).
 * 3. stripLeadingMarkdownTitleSafely só remove linha quando o título é real e distinto do corpo.
 * 4. Streaming: detectar markdown cedo (`**` parcial) e desligar reveal caractere-a-caractere.
 */

/** Título de painel rico (gráfico/tabela); vazio em prosa simples. */
export function resolveAssistantPresentationTitle(
  content: string,
  toolCalls: ChatToolCall[] = [],
): string {
  return getPresentationTitle(content, toolCalls);
}

export type AssistantStreamingProseState = {
  /** Conteúdo enviado ao ChatMarkdown / ChatAssistantContent durante o stream. */
  markdownContent: string;
  /** Reveal incremental permitido (somente prosa sem markdown). */
  enableCharReveal: boolean;
  /** Legenda curta de apresentação rica deve usar ChatMarkdown, não <h3> cru. */
  captionUsesMarkdown: boolean;
};

/** Título legítimo: uma linha curta, sem markdown nem blocos de código. */
export function shouldRenderPresentationHeading(
  title: string | null | undefined,
): boolean {
  const value = String(title || "").trim();

  if (!value) {
    return false;
  }

  if (value.includes("```") || /\n/.test(value) || hasMarkdownSyntax(value)) {
    return false;
  }

  return value.length <= 120;
}

/**
 * Markdown principal exibido no histórico e nos segmentos do assistente.
 * Fonte única para buildAssistantContentSegments e derivados.
 */
export function isDrawingAnalysisTurn(
  metadata?: ChatMessageMetadata | null,
): boolean {
  return Boolean(
    metadata?.drawingAnalysisMode &&
      String(metadata?.drawingAnalysisExport?.markdown || "").trim(),
  );
}

/** Corpo principal do assistente em turnos de análise de desenho (relatório DELPI). */
export function resolveAssistantDisplayContent(
  content: string,
  toolCalls: ChatToolCall[] = [],
  metadata?: ChatMessageMetadata | null,
): string {
  const reportMarkdown = String(
    metadata?.drawingAnalysisExport?.markdown || "",
  ).trim();

  if (isDrawingAnalysisTurn(metadata) && reportMarkdown) {
    return reportMarkdown;
  }

  const raw = String(content || "").trim();

  if (isNativeSingleViewSelection(toolCalls).active) {
    const { kind } = isNativeSingleViewSelection(toolCalls);

    if (kind === "text") {
      return stripPresentationSectionMarkers(
        raw || getTextMarkdownFromToolCalls(toolCalls),
      );
    }

    if (raw) {
      return stripPresentationSectionMarkers(raw);
    }

    return "";
  }

  return stripPresentationSectionMarkers(
    raw || getTextMarkdownFromToolCalls(toolCalls),
  );
}

/**
 * Em turno de relatório de desenho, a árvore/tabelas do analyser ficam só nos exports —
 * o corpo da mensagem é o markdown do relatório.
 */
export function toolCallsForDrawingAnalysisDisplay(
  toolCalls: ChatToolCall[] = [],
  metadata?: ChatMessageMetadata | null,
): ChatToolCall[] {
  if (!isDrawingAnalysisTurn(metadata)) {
    return toolCalls;
  }

  return toolCalls.map((call) => {
    const path = String(call.metadata?.path || "").toLowerCase();

    if (!path.includes("/analyser")) {
      return call;
    }

    const meta = call.metadata;

    if (!meta) {
      return call;
    }

    const {
      presentation: _presentation,
      textPresentation: _textPresentation,
      tablePresentation: _tablePresentation,
      tablePresentations: _tablePresentations,
      chartPresentation: _chartPresentation,
      treePresentation: _treePresentation,
      kpiPresentation: _kpiPresentation,
      dashboardPresentation: _dashboardPresentation,
      inspectionTablePresentation: _inspectionTablePresentation,
      profileTablePresentation: _profileTablePresentation,
      humanizedSummary: _humanizedSummary,
      templateProseArchive: _templateProseArchive,
      stackPresentationPlan: _stackPresentationPlan,
      presentationDecision: _presentationDecision,
      dataCoverageNotice: _dataCoverageNotice,
      pagination: _pagination,
      renderPlan: _renderPlan,
      dataCommentary: _dataCommentary,
      dataAnswer: _dataAnswer,
      ...rest
    } = meta;

    return {
      ...call,
      metadata: {
        ...rest,
        suppressClientPresentation: true,
      },
    };
  });
}

export function resolveAssistantRenderableMarkdown(
  content: string,
  toolCalls: ChatToolCall[] = [],
): string {
  const renderPlan = getRenderPlanFromToolCalls(toolCalls);
  const usesAssistantMessageLead =
    isLlmProseDecoupledFromToolCalls(toolCalls) &&
    Boolean(
      renderPlan?.segments?.some(
        (segment) =>
          String(segment.kind || "").trim().toLowerCase() === "markdown" &&
          String(segment.slot || "").trim().toLowerCase() === "lead" &&
          String(segment.source || "").trim().toLowerCase() === "assistantmessage",
      ),
    );

  if (usesAssistantMessageLead) {
    const raw = String(content || "").trim();
    const presentationTitle = resolveAssistantPresentationTitle(content, toolCalls);

    return stripLeadingMarkdownTitleSafely(
      stripPresentationSectionMarkers(raw),
      presentationTitle,
    );
  }

  const nativeSingle = isNativeSingleViewSelection(toolCalls);

  if (nativeSingle.active && nativeSingle.kind === "text") {
    const fromMetadata = getTextMarkdownFromToolCalls(toolCalls);
    const presentationTitle = resolveAssistantPresentationTitle(content, toolCalls);
    const raw = String(content || "").trim();

    if (fromMetadata) {
      return stripLeadingMarkdownTitleSafely(
        stripPresentationSectionMarkers(fromMetadata),
        presentationTitle,
      );
    }

    if (raw && isShortPresentationCaption(raw, toolCalls)) {
      return stripPresentationSectionMarkers(
        stripLeadingMarkdownTitleSafely(raw, presentationTitle),
      );
    }

    return stripPresentationSectionMarkers(raw);
  }

  if (nativeSingle.active) {
    const raw = String(content || "").trim();
    const presentationTitle = resolveAssistantPresentationTitle(content, toolCalls);

    if (raw && isShortPresentationCaption(raw, toolCalls)) {
      return stripPresentationSectionMarkers(
        stripLeadingMarkdownTitleSafely(raw, presentationTitle),
      );
    }

    if (presentationTitle) {
      const titled = presentationTitle.startsWith("#")
        ? presentationTitle
        : `### ${presentationTitle}`;

      return titled;
    }

    return stripPresentationSectionMarkers(raw);
  }

  const fromMetadata = getTextMarkdownFromToolCalls(toolCalls);
  const presentationTitle = resolveAssistantPresentationTitle(content, toolCalls);
  const raw = String(content || "").trim();
  const source = stripPresentationSectionMarkers(fromMetadata || raw);

  return stripLeadingMarkdownTitleSafely(source, presentationTitle);
}

/**
 * Não remove o corpo inteiro quando o “título” coincide com a mensagem completa.
 */
export function stripLeadingMarkdownTitleSafely(
  markdown: string,
  title: string,
): string {
  const normalized = String(markdown || "").trim();
  const normalizedTitle = String(title || "").trim();

  if (!normalized) {
    return "";
  }

  if (!normalizedTitle || normalizedTitle === normalized) {
    return normalized;
  }

  const stripped = stripLeadingMarkdownTitle(normalized, normalizedTitle);

  return stripped || normalized;
}

/** Respostas com markdown nunca usam reveal caractere-a-caractere nem playback incremental. */
export function shouldBypassIncrementalTextReveal(
  content: string | null | undefined,
): boolean {
  return hasMarkdownSyntax(content);
}

export function resolveAssistantStreamingProseState(options: {
  answer: string;
  revealedAnswer: string;
  suppressRichPresentation: boolean;
  isGenerating: boolean;
  isPlayback: boolean;
}): AssistantStreamingProseState {
  const answer = String(options.answer || "");
  const hasMarkdown = hasMarkdownSyntax(answer);

  if (hasMarkdown) {
    return {
      markdownContent: answer,
      enableCharReveal: false,
      captionUsesMarkdown: true,
    };
  }

  const enableCharReveal =
    options.isGenerating &&
    !options.suppressRichPresentation &&
    !options.isPlayback;

  return {
    markdownContent: enableCharReveal ? options.revealedAnswer : answer,
    enableCharReveal,
    captionUsesMarkdown: false,
  };
}
