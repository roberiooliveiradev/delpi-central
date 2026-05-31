import type { ChatMessageMetadata } from "../../data/api/chatTypes";

export function downloadDrawingAnalysisExport(
  exportPayload: NonNullable<ChatMessageMetadata["drawingAnalysisExport"]>,
): void {
  const markdown = String(exportPayload.markdown || "").trim();

  if (!markdown) {
    return;
  }

  const blob = new Blob([markdown], {
    type: exportPayload.mimeType || "text/markdown;charset=utf-8",
  });
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = exportPayload.filename || "relatorio-desenho.md";
  anchor.click();
  URL.revokeObjectURL(url);
}
