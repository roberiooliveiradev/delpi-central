import { describe, expect, it } from "vitest";
import { validateDrawingChecklistConsistency } from "./drawingAnalysisConsistency";
import type { DrawingAnalysisExportPayload } from "./drawingAnalysisExport";

describe("drawingAnalysisConsistency", () => {
  it("ok quando export e items concordam", () => {
    const payload: DrawingAnalysisExportPayload = {
      filename: "relatorio.md",
      mimeType: "text/markdown",
      markdown: "# Rel",
      tables: [
        {
          key: "checklist",
          title: "Checklist",
          columns: [
            { key: "section", label: "Seção" },
            { key: "item", label: "Item" },
            { key: "status", label: "Status" },
            { key: "observation", label: "Observação" },
          ],
          rows: [{ section: "BOM", item: "X", status: "OK", observation: "—" }],
        },
      ],
      checklistConsistency: { ok: true, displayItemCount: 1, issues: [] },
    };

    const result = validateDrawingChecklistConsistency(payload, {
      items: [{ section: "BOM", item: "X", status: "ok" }],
    });

    expect(result.ok).toBe(true);
  });

  it("falha quando checklist do export diverge dos items", () => {
    const payload: DrawingAnalysisExportPayload = {
      filename: "relatorio.md",
      mimeType: "text/markdown",
      markdown: "# Rel",
      tables: [
        {
          key: "checklist",
          title: "Checklist",
          columns: [
            { key: "section", label: "Seção" },
            { key: "item", label: "Item" },
            { key: "status", label: "Status" },
            { key: "observation", label: "Observação" },
          ],
          rows: [],
        },
      ],
    };

    const result = validateDrawingChecklistConsistency(payload, {
      items: [{ section: "BOM", item: "X", status: "ok" }],
    });

    expect(result.ok).toBe(false);
    expect(result.issues.length).toBeGreaterThan(0);
  });
});
