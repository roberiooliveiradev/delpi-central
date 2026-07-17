import type { MColumnSchemaDto } from "@delpi/tv-dashboard-presentation";

import type {
  DataQueryCompileResult,
  DataQueryPreview,
} from "../domain/dataQueryTypes";

export function adaptCompileResult(value: unknown): DataQueryCompileResult {
  const raw = (value && typeof value === "object" ? value : {}) as Record<string, unknown>;
  const completion = (raw.completionContext && typeof raw.completionContext === "object"
    ? raw.completionContext
    : {}) as Record<string, unknown>;
  return {
    profile: String(raw.profile || "m-delpi-v1"),
    canonicalScript: typeof raw.canonicalScript === "string" ? raw.canonicalScript : null,
    scriptHash: String(raw.scriptHash || ""),
    outputStepName: typeof raw.outputStepName === "string" ? raw.outputStepName : null,
    steps: Array.isArray(raw.steps)
      ? raw.steps.map((item) => {
          const step = item as Record<string, unknown>;
          return {
            name: String(step.name || ""),
            operation: String(step.operation || ""),
            label: String(step.label || step.name || ""),
            formula: String(step.formula || ""),
          };
        })
      : [],
    diagnostics: Array.isArray(raw.diagnostics)
      ? (raw.diagnostics as DataQueryCompileResult["diagnostics"])
      : [],
    referencedQueries: Array.isArray(raw.referencedQueries)
      ? raw.referencedQueries.map(String)
      : [],
    completionContext: {
      steps: Array.isArray(completion.steps) ? completion.steps.map(String) : [],
      columns: Array.isArray(completion.columns) ? completion.columns.map(String) : [],
      queries: Array.isArray(completion.queries) ? completion.queries.map(String) : [],
      items: Array.isArray(completion.items)
        ? completion.items.map((item) => {
            const suggestion = item as Record<string, unknown>;
            return {
              label: String(suggestion.label || ""),
              insertText: String(suggestion.insertText || suggestion.label || ""),
              kind: String(suggestion.kind || "step") as "step" | "column" | "query",
            };
          })
        : [],
    },
    syntaxTokens: Array.isArray(raw.syntaxTokens)
      ? raw.syntaxTokens.flatMap((item) => {
          const token = item as Record<string, unknown>;
          const startOffset = Number(token.startOffset);
          const endOffset = Number(token.endOffset);
          const kind = String(token.kind) as DataQueryCompileResult["syntaxTokens"][number]["kind"];
          return Number.isFinite(startOffset) && Number.isFinite(endOffset)
            ? [{ kind, startOffset, endOffset }]
            : [];
        })
      : [],
  };
}

export function adaptPreviewResult(value: unknown): DataQueryPreview {
  const raw = (value && typeof value === "object" ? value : {}) as Record<string, unknown>;
  const preview = (raw.preview && typeof raw.preview === "object"
    ? raw.preview
    : {}) as Record<string, unknown>;
  const query = (raw.query && typeof raw.query === "object"
    ? raw.query
    : {}) as Record<string, unknown>;
  const block = (raw.block && typeof raw.block === "object"
    ? raw.block
    : {}) as Record<string, unknown>;
  const resolved = (block.resolved && typeof block.resolved === "object"
    ? block.resolved
    : {}) as Record<string, unknown>;
  const table = (resolved.table && typeof resolved.table === "object"
    ? resolved.table
    : {}) as Record<string, unknown>;
  const rawColumns = (preview.columns ?? table.columns) as unknown;
  const columns: MColumnSchemaDto[] = Array.isArray(rawColumns)
    ? rawColumns.map((item) => {
        const column = item as Record<string, unknown>;
        return {
          key: String(column.key || ""),
          label: String(column.label || column.key || ""),
          type: (String(column.type || "any") as MColumnSchemaDto["type"]),
          nullable: column.nullable !== false,
          typeSource: (String(column.typeSource || "unknown") as MColumnSchemaDto["typeSource"]),
        };
      })
    : [];
  const rawRows = preview.rows ?? table.rows;
  const rows = Array.isArray(rawRows)
    ? rawRows.map((row) => ({ ...(row as Record<string, unknown>) }))
    : [];
  return {
    columns,
    rows,
    returnedRows: Number(preview.returnedRows ?? rows.length),
    availableRows: Number(preview.availableRows ?? rows.length),
    truncated: Boolean(preview.truncated),
    isSample: Boolean(preview.isSample ?? preview.truncated),
    selectedStepName:
      typeof query.selectedStepName === "string" ? query.selectedStepName : null,
    diagnostics: Array.isArray(query.diagnostics)
      ? (query.diagnostics as DataQueryPreview["diagnostics"])
      : [],
  };
}
