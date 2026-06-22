import type { DrawingAnalysisExportPayload } from "./drawingAnalysisExport";

type DrawingCheckItem = {
  section?: string;
  item?: string;
  status?: string;
  recommendation?: string;
};

export type DrawingChecklistConsistency = {
  ok: boolean;
  displayItemCount: number;
  exportChecklistRows: number;
  issues: string[];
};

/** Valida paridade entre `drawingAnalysis.items` e tabelas do export (render-only no MFE). */
export function validateDrawingChecklistConsistency(
  exportPayload: DrawingAnalysisExportPayload,
  drawingAnalysis?: Record<string, unknown>,
): DrawingChecklistConsistency {
  const items = (drawingAnalysis?.items as DrawingCheckItem[] | undefined) ?? [];
  const displayItemCount = items.length;
  const checklistTable = exportPayload.tables?.find((table) => table.key === "checklist");
  const exportChecklistRows = checklistTable?.rows?.length ?? 0;
  const issues: string[] = [];

  if (exportPayload.checklistConsistency?.ok === false) {
    const apiIssues = exportPayload.checklistConsistency.issues;

    if (Array.isArray(apiIssues)) {
      issues.push(...apiIssues.map((issue) => String(issue)));
    }
  }

  if (checklistTable && exportChecklistRows !== displayItemCount) {
    issues.push(
      `export_checklist_rows:${exportChecklistRows}!=drawing_items:${displayItemCount}`,
    );
  }

  return {
    ok: issues.length === 0,
    displayItemCount,
    exportChecklistRows,
    issues,
  };
}
