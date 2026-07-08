import streamActivityContent from "./stream_activity_content.json";

export type StreamActivityProgress = {
  step?: number;
  total?: number;
  completePercent?: number;
  remainingPercent?: number;
};

export type StreamActivityFlowKind = "drawingWithPdf" | "drawingWithoutPdf" | "default";

const CONTENT = streamActivityContent;

export function streamActivityProgressRemainingTemplate(percent: number): string {
  return CONTENT.progressRemainingTemplate.replace("{percent}", String(percent));
}

export function streamActivityAnsweringRemainingPercent(): number {
  return CONTENT.pipelineTotals.answeringRemainingPercent;
}

export function streamActivityPipelineTotal(flow: StreamActivityFlowKind): number {
  return CONTENT.pipelineTotals[flow];
}

export function detectStreamActivityFlow(
  entries: Array<{ phase?: string; id?: string }>,
): StreamActivityFlowKind {
  const hasDrawing = entries.some(
    (entry) =>
      entry.phase === "drawing_analysis" ||
      String(entry.id || "").startsWith("drawing-analysis-"),
  );
  const hasPdfVision = entries.some((entry) => entry.phase === "document_vision");

  if (hasDrawing || hasPdfVision) {
    return hasPdfVision ? "drawingWithPdf" : "drawingWithoutPdf";
  }

  return "default";
}
