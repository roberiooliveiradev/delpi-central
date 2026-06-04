import type { ChatPresentation } from "../../data/api/chatTypes";

import type { AssistantContentSegment } from "./assistantContentTypes";

const STRUCTURE_TABLE_TITLE_MARKERS = ["componentes da estrutura"];
const PARENTS_TABLE_TITLE_MARKERS = ["produtos pai", "onde é usado"];

export function isStructureComponentsTable(
  presentation: ChatPresentation | null | undefined,
): boolean {
  if (!presentation || presentation.type !== "table") {
    return false;
  }

  const title = String(presentation.title || "").trim().toLowerCase();

  if (STRUCTURE_TABLE_TITLE_MARKERS.some((marker) => title.includes(marker))) {
    return true;
  }

  const keys = new Set(
    (presentation.columns || []).map((column) => String(column.key || "").trim().toLowerCase()),
  );

  return keys.has("parent_code") && keys.has("component_code");
}

export function isParentsUsageTable(
  presentation: ChatPresentation | null | undefined,
): boolean {
  if (!presentation || presentation.type !== "table") {
    return false;
  }

  const title = String(presentation.title || "").trim().toLowerCase();

  return PARENTS_TABLE_TITLE_MARKERS.some((marker) => title.includes(marker));
}

export function isHierarchyDuplicateTable(
  presentation: ChatPresentation | null | undefined,
): boolean {
  return isStructureComponentsTable(presentation) || isParentsUsageTable(presentation);
}

export function toolCallsHaveTree(toolCalls: { metadata?: Record<string, unknown> }[]): boolean {
  for (const toolCall of toolCalls) {
    const metadata = toolCall.metadata;

    if (!metadata) {
      continue;
    }

    for (const key of ["treePresentation", "presentation"]) {
      const presentation = metadata[key];

      if (
        presentation &&
        typeof presentation === "object" &&
        (presentation as ChatPresentation).type === "tree"
      ) {
        return true;
      }
    }
  }

  return false;
}

export function shouldSkipTableSegment(
  presentation: Extract<ChatPresentation, { type: "table" }>,
  toolCalls: { metadata?: Record<string, unknown> }[],
): boolean {
  return toolCallsHaveTree(toolCalls) && isHierarchyDuplicateTable(presentation);
}

export function filterSegmentsWithoutHierarchyTableDuplicates(
  segments: AssistantContentSegment[],
  toolCalls: { metadata?: Record<string, unknown> }[],
): AssistantContentSegment[] {
  if (!toolCallsHaveTree(toolCalls)) {
    return segments;
  }

  return segments.filter((segment) => {
    if (segment.kind !== "table") {
      return true;
    }

    return !isHierarchyDuplicateTable(segment.presentation);
  });
}
