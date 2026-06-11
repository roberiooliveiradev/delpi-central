import type { ChatPresentation } from "../../data/api/chatTypes";

import {
  parentsTableTitleMarkers,
  structureTableTitleMarkers,
} from "../../content/presentationVocabulary";

import type { AssistantContentSegment } from "./assistantContentTypes";

function metadataStructureDedupApplied(
  toolCalls: { metadata?: Record<string, unknown> }[],
): boolean {
  return toolCalls.some((toolCall) => toolCall.metadata?.structureDedupApplied === true);
}

export function isStructureComponentsTable(
  presentation: ChatPresentation | null | undefined,
): boolean {
  if (!presentation || presentation.type !== "table") {
    return false;
  }

  const title = String(presentation.title || "").trim().toLowerCase();

  if (structureTableTitleMarkers().some((marker) => title.includes(marker))) {
    return true;
  }

  const keys = new Set(
    (presentation.columns || []).map((column) => String(column.key || "").trim().toLowerCase()),
  );

  if (keys.has("parent_code") && keys.has("component_code")) {
    return true;
  }

  if (keys.has("level") && keys.has("component_code")) {
    return true;
  }

  if (
    keys.has("level") &&
    keys.has("product_code") &&
    (keys.has("exclusive_raw_material_label") ||
      keys.has("exclusive_raw_material") ||
      keys.has("component_type"))
  ) {
    return true;
  }

  return false;
}

export function isParentsUsageTable(
  presentation: ChatPresentation | null | undefined,
): boolean {
  if (!presentation || presentation.type !== "table") {
    return false;
  }

  const title = String(presentation.title || "").trim().toLowerCase();

  return parentsTableTitleMarkers().some((marker) => title.includes(marker));
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

/** @deprecated Playbook 13 P6 — dedup estrutural na API via `structureDedupApplied` + prune. */
export function shouldSkipTableSegment(
  presentation: Extract<ChatPresentation, { type: "table" }>,
  toolCalls: { metadata?: Record<string, unknown> }[],
): boolean {
  if (metadataStructureDedupApplied(toolCalls)) {
    return false;
  }

  return toolCallsHaveTree(toolCalls) && isHierarchyDuplicateTable(presentation);
}

export function filterSegmentsWithoutHierarchyTableDuplicates(
  segments: AssistantContentSegment[],
  toolCalls: { metadata?: Record<string, unknown> }[],
): AssistantContentSegment[] {
  if (metadataStructureDedupApplied(toolCalls) || !toolCallsHaveTree(toolCalls)) {
    return segments;
  }

  return segments.filter((segment) => {
    if (segment.kind !== "table") {
      return true;
    }

    return !isHierarchyDuplicateTable(segment.presentation);
  });
}
