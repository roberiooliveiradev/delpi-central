import type { ChatPresentation, ChatToolCall } from "../../data/api/chatTypes";
import type { AssistantContentSegment } from "./assistantContentTypes";
import { buildInterleavedStackSegments } from "./assistantContentInterleave";
import { orderVisualSegments, resolveStackLayoutOrderFromToolCalls } from "./assistantContentLayout";
import { buildMultiRouteStackSegments } from "./presentationMultiRoute";
import { dedupeTablePresentations } from "./presentationTableDedup";
import { appendVisualSegment } from "./segmentDedupe";
import { parseMarkdownAndCodeSegments } from "./sqlMarkdownNormalizer";
import { resolveStackCommentaryBody, tablePresentationToMarkdown } from "./chatPresentation";

export function buildStackedSegments(
  content: string,
  toolCalls: ChatToolCall[],
  visuals: AssistantContentSegment[],
): AssistantContentSegment[] {
  const commentary = resolveStackCommentaryBody(content, toolCalls);
  const layoutOrder = resolveStackLayoutOrderFromToolCalls(toolCalls);
  const visualOrder = layoutOrder.filter((slot) => slot !== "text");
  const orderedVisuals = orderVisualSegments(visuals, visualOrder);

  const multiRoute = buildMultiRouteStackSegments(
    commentary,
    toolCalls,
    appendVisualSegment,
  );

  if (multiRoute?.length) {
    return multiRoute;
  }

  return buildInterleavedStackSegments(
    commentary,
    orderedVisuals,
    parseMarkdownAndCodeSegments,
    appendVisualSegment,
    toolCalls,
  );
}

export function appendEmbeddedTablesForExplicitText(
  markdown: string,
  toolCalls: ChatToolCall[],
): string {
  const body = String(markdown || "").trim();

  if (!body || body.includes("|")) {
    return body;
  }

  const sections: string[] = [body];
  const seen = new Set<string>();

  for (const toolCall of toolCalls) {
    if (toolCall.name && toolCall.name !== "execute_external_action") {
      continue;
    }

    const metadata = (toolCall.metadata ?? {}) as Record<string, unknown>;
    const candidates: Extract<ChatPresentation, { type: "table" }>[] = [];

    const pushTable = (value: unknown) => {
      if (
        value &&
        typeof value === "object" &&
        (value as ChatPresentation).type === "table"
      ) {
        candidates.push(value as Extract<ChatPresentation, { type: "table" }>);
      }
    };

    pushTable(metadata.presentation);
    pushTable(metadata.profileTablePresentation);
    pushTable(metadata.tablePresentation);
    pushTable(metadata.inspectionTablePresentation);

    const bundled = metadata.tablePresentations;

    if (Array.isArray(bundled)) {
      for (const item of bundled) {
        pushTable(item);
      }
    }

    for (const table of dedupeTablePresentations(candidates)) {
      const section = tablePresentationToMarkdown(table).trim();

      if (!section || seen.has(section)) {
        continue;
      }

      seen.add(section);
      sections.push(section);
    }
  }

  return sections.join("\n\n").trim();
}
