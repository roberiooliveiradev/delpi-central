import type { ChatPresentation } from "../../data/api/chatTypes";

import type { AssistantContentSegment } from "./message/assistantContentTypes";

export function tablePresentationSignature(
  presentation: Extract<ChatPresentation, { type: "table" }>,
): string {
  const title = String(presentation.title || "").trim().toLowerCase();
  const columnKeys = (presentation.columns || [])
    .map((column) => String(column.key || "").trim().toLowerCase())
    .join("|");
  const rowCount = (presentation.rows || []).length;
  const firstRow = presentation.rows?.[0];

  if (!firstRow || typeof firstRow !== "object") {
    return `${title}::${columnKeys}::${rowCount}`;
  }

  const preview = Object.entries(firstRow as Record<string, unknown>)
    .slice(0, 4)
    .map(([key, value]) => `${key}=${String(value ?? "").trim()}`)
    .join(",");

  return `${title}::${columnKeys}::${rowCount}::${preview}`;
}

export function isSameTablePresentation(
  left: Extract<ChatPresentation, { type: "table" }>,
  right: Extract<ChatPresentation, { type: "table" }>,
): boolean {
  return tablePresentationSignature(left) === tablePresentationSignature(right);
}

export function dedupeTablePresentations(
  tables: Extract<ChatPresentation, { type: "table" }>[],
): Extract<ChatPresentation, { type: "table" }>[] {
  const seen = new Set<string>();
  const result: Extract<ChatPresentation, { type: "table" }>[] = [];

  for (const table of tables) {
    const signature = tablePresentationSignature(table);

    if (seen.has(signature)) {
      continue;
    }

    seen.add(signature);
    result.push(table);
  }

  return result;
}

export function dedupeTableSegments(
  segments: AssistantContentSegment[],
): AssistantContentSegment[] {
  const seen = new Set<string>();
  const result: AssistantContentSegment[] = [];

  for (const segment of segments) {
    if (segment.kind !== "table") {
      result.push(segment);
      continue;
    }

    const signature = tablePresentationSignature(segment.presentation);

    if (seen.has(signature)) {
      continue;
    }

    seen.add(signature);
    result.push(segment);
  }

  return result;
}
