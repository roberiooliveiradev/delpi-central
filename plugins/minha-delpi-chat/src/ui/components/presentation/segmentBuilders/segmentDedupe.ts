import type { AssistantContentSegment } from "../../message/assistantContentTypes";
import { isSameTablePresentation } from "../../presentationTableDedup";

export function normalizeProseChunk(value: string): string {
  return value
    .replace(/```[\w]*/gi, "")
    .replace(/`+/g, "")
    .replace(/\s+/g, " ")
    .trim()
    .toLowerCase();
}

export function proseChunksSimilar(left: string, right: string): boolean {
  const leftKey = normalizeProseChunk(left);
  const rightKey = normalizeProseChunk(right);

  if (!leftKey || !rightKey) {
    return false;
  }

  if (leftKey.length < 24 || rightKey.length < 24) {
    return leftKey === rightKey;
  }

  if (leftKey.includes(rightKey) || rightKey.includes(leftKey)) {
    return true;
  }

  const sample = (value: string) => value.slice(0, 500);
  const leftSample = sample(leftKey);
  const rightSample = sample(rightKey);
  let matches = 0;
  const limit = Math.min(leftSample.length, rightSample.length);

  for (let index = 0; index < limit; index += 1) {
    if (leftSample[index] === rightSample[index]) {
      matches += 1;
    }
  }

  return limit > 0 && matches / limit >= 0.82;
}

export function sameAssistantSegment(
  left: AssistantContentSegment,
  right: AssistantContentSegment,
): boolean {
  if (left.kind !== right.kind) {
    return false;
  }

  if (left.kind === "markdown") {
    return right.kind === "markdown" && left.markdown === right.markdown;
  }

  if (left.kind === "code") {
    return right.kind === "code" && left.language === right.language && left.code === right.code;
  }

  if (left.kind === "table" && right.kind === "table") {
    return isSameTablePresentation(left.presentation, right.presentation);
  }

  if (left.kind === "stackSection" && right.kind === "stackSection") {
    return left.section.id === right.section.id;
  }

  if (left.kind === "decision" && right.kind === "decision") {
    return left.presentation.title === right.presentation.title;
  }

  if (
    left.kind === "chart" ||
    left.kind === "tree" ||
    left.kind === "kpi" ||
    left.kind === "dashboard"
  ) {
    return (
      (right.kind === "chart" ||
        right.kind === "tree" ||
        right.kind === "kpi" ||
        right.kind === "dashboard") &&
      left.presentation === right.presentation
    );
  }

  return false;
}

export function appendVisualSegment(
  segments: AssistantContentSegment[],
  segment: AssistantContentSegment,
): void {
  const exists = segments.some((item) => sameAssistantSegment(item, segment));

  if (!exists) {
    segments.push(segment);
  }
}
