/**
 * Contrato de fórmulas da Query (barra fx) — serialize/parse tipado.
 * Runtime de avaliação fica no backend; este módulo só interpreta o texto da barra.
 */

import type { DataTransformCmp, DataTransformStep } from "./dataTransform";
import { dataTransformStepFormula } from "./dataTransform";

export type FormulaParseOk = { ok: true; step: DataTransformStep };
export type FormulaParseErr = { ok: false; error: string };
export type FormulaParseResult = FormulaParseOk | FormulaParseErr;

const ADD_COLUMN_FULL =
  /^=\s*AddColumn\s*\(\s*Fonte\s*,\s*([A-Za-z_][A-Za-z0-9_]*)\s*,\s*(.+)\s*\)\s*$/i;
const RENAME_FULL =
  /^=\s*RenameColumns\s*\(\s*Fonte\s*,\s*([A-Za-z_][A-Za-z0-9_]*)\s*→\s*([A-Za-z_][A-Za-z0-9_]*)\s*\)\s*$/i;
const SELECT_FULL =
  /^=\s*SelectColumns\s*\(\s*Fonte\s*,\s*\[([^\]]*)\]\s*\)\s*$/i;
const FILTER_NOT_NULL =
  /^=\s*FilterRows\s*\(\s*Fonte\s*,\s*([A-Za-z_][A-Za-z0-9_]*)\s+is\s+not\s+null\s*\)\s*$/i;
const FILTER_CMP =
  /^=\s*FilterRows\s*\(\s*Fonte\s*,\s*\[([A-Za-z_][A-Za-z0-9_]*)\]\s+(eq|neq|gt|lt|contains|startsWith)\s+(.+)\s*\)\s*$/i;
const SORT_FULL =
  /^=\s*Sort\s*\(\s*Fonte\s*,\s*([A-Za-z_][A-Za-z0-9_]*)\s*,\s*(asc|desc)\s*\)\s*$/i;
const REPLACE_FULL =
  /^=\s*ReplaceValue\s*\(\s*Fonte\s*,\s*([A-Za-z_][A-Za-z0-9_]*)\s*,\s*(.+?)\s*→\s*(.+)\s*\)\s*$/i;

const EDITABLE_OPS = new Set([
  "addColumn",
  "rename",
  "select",
  "filter",
  "sort",
  "replace",
]);

/** Fórmula canônica da etapa (ou Fonte). */
export function formatStepFormula(step: DataTransformStep | null | undefined): string {
  if (!step) return "= Fonte (rota api-delpi)";
  return dataTransformStepFormula(step);
}

export function canEditFormula(step: DataTransformStep | null | undefined): boolean {
  if (!step) return false;
  return EDITABLE_OPS.has(step.op);
}

/** Draft de nova coluna via barra fx (antes de existir etapa). */
export function canEditNewColumnFormula(draftMode: boolean): boolean {
  return draftMode;
}

function stripOuterQuotes(raw: string): string {
  const trimmed = raw.trim();
  if (
    (trimmed.startsWith('"') && trimmed.endsWith('"')) ||
    (trimmed.startsWith("'") && trimmed.endsWith("'"))
  ) {
    try {
      return JSON.parse(trimmed.startsWith("'") ? `"${trimmed.slice(1, -1)}"` : trimmed) as string;
    } catch {
      return trimmed.slice(1, -1);
    }
  }
  try {
    return JSON.parse(trimmed) as string;
  } catch {
    return trimmed;
  }
}

function parseColumnList(inner: string): string[] {
  return inner
    .split(",")
    .map((part) => part.trim())
    .filter(Boolean)
    .map((part) => part.replace(/^["']|["']$/g, ""));
}

/**
 * Parse da barra fx para addColumn.
 * Aceita `= AddColumn(Fonte, nome, expr)` ou só `expr` quando a etapa já é addColumn
 * (mantém o nome atual).
 */
export function parseAddColumnFormula(
  text: string,
  options?: { existingName?: string },
): FormulaParseResult {
  const trimmed = text.trim();
  if (!trimmed) {
    return { ok: false, error: "Informe a expressão da coluna." };
  }
  const full = ADD_COLUMN_FULL.exec(trimmed);
  if (full) {
    const name = full[1]!.trim();
    const expr = full[2]!.trim();
    if (!name || !expr) {
      return { ok: false, error: "AddColumn exige nome e expressão." };
    }
    return { ok: true, step: { op: "addColumn", name, expr } };
  }
  if (trimmed.startsWith("=") && /AddColumn/i.test(trimmed)) {
    return {
      ok: false,
      error: "Use = AddColumn(Fonte, nome, expr) ou só a expressão.",
    };
  }
  const existingName = options?.existingName?.trim();
  if (existingName) {
    const expr = trimmed.startsWith("=") ? trimmed.replace(/^=\s*/, "") : trimmed;
    if (!expr) {
      return { ok: false, error: "Informe a expressão da coluna." };
    }
    return { ok: true, step: { op: "addColumn", name: existingName, expr } };
  }
  return {
    ok: false,
    error: "Para nova coluna use = AddColumn(Fonte, nome, expr).",
  };
}

export function parseRenameFormula(text: string): FormulaParseResult {
  const match = RENAME_FULL.exec(text.trim());
  if (!match) {
    return {
      ok: false,
      error: "Use = RenameColumns(Fonte, de → para).",
    };
  }
  return {
    ok: true,
    step: { op: "rename", from: match[1]!, to: match[2]! },
  };
}

export function parseSelectFormula(text: string): FormulaParseResult {
  const match = SELECT_FULL.exec(text.trim());
  if (!match) {
    return {
      ok: false,
      error: "Use = SelectColumns(Fonte, [col1, col2]).",
    };
  }
  const columns = parseColumnList(match[1] ?? "");
  if (!columns.length) {
    return { ok: false, error: "Informe ao menos uma coluna." };
  }
  return { ok: true, step: { op: "select", columns } };
}

export function parseFilterFormula(text: string): FormulaParseResult {
  const trimmed = text.trim();
  const notNull = FILTER_NOT_NULL.exec(trimmed);
  if (notNull) {
    return {
      ok: true,
      step: { op: "filter", column: notNull[1]!, cmp: "notNull" },
    };
  }
  const cmpMatch = FILTER_CMP.exec(trimmed);
  if (!cmpMatch) {
    return {
      ok: false,
      error: "Use = FilterRows(Fonte, [col] eq \"valor\") ou … is not null.",
    };
  }
  const cmp = cmpMatch[2] as DataTransformCmp;
  return {
    ok: true,
    step: {
      op: "filter",
      column: cmpMatch[1]!,
      cmp,
      value: stripOuterQuotes(cmpMatch[3] ?? ""),
    },
  };
}

export function parseSortFormula(text: string): FormulaParseResult {
  const match = SORT_FULL.exec(text.trim());
  if (!match) {
    return { ok: false, error: "Use = Sort(Fonte, coluna, asc|desc)." };
  }
  return {
    ok: true,
    step: {
      op: "sort",
      column: match[1]!,
      direction: match[2] === "desc" ? "desc" : "asc",
    },
  };
}

export function parseReplaceFormula(text: string): FormulaParseResult {
  const match = REPLACE_FULL.exec(text.trim());
  if (!match) {
    return {
      ok: false,
      error: 'Use = ReplaceValue(Fonte, coluna, "a" → "b").',
    };
  }
  return {
    ok: true,
    step: {
      op: "replace",
      column: match[1]!,
      find: stripOuterQuotes(match[2] ?? ""),
      replaceWith: stripOuterQuotes(match[3] ?? ""),
    },
  };
}

/**
 * Interpreta o texto da barra conforme a etapa atual (ou draft de nova coluna).
 */
export function parseFormulaBarText(
  text: string,
  context: {
    step: DataTransformStep | null;
    newColumnDraft?: boolean;
  },
): FormulaParseResult {
  const trimmed = text.trim();
  if (context.newColumnDraft) {
    return parseAddColumnFormula(trimmed);
  }
  const step = context.step;
  if (!step || !canEditFormula(step)) {
    return { ok: false, error: "Esta etapa não é editável pela barra fx." };
  }
  if (step.op === "addColumn") {
    return parseAddColumnFormula(trimmed, { existingName: step.name });
  }
  if (step.op === "rename") return parseRenameFormula(trimmed);
  if (step.op === "select") return parseSelectFormula(trimmed);
  if (step.op === "filter") return parseFilterFormula(trimmed);
  if (step.op === "sort") return parseSortFormula(trimmed);
  if (step.op === "replace") return parseReplaceFormula(trimmed);
  return { ok: false, error: "Etapa não suportada na barra fx." };
}

/** Valor exibido no input: para addColumn, a expressão; senão a fórmula completa. */
export function formulaBarDisplayValue(
  step: DataTransformStep | null,
  options?: { newColumnDraft?: boolean; draftText?: string },
): string {
  if (options?.newColumnDraft) {
    return options.draftText ?? "= AddColumn(Fonte, nova_coluna, )";
  }
  if (!step) return formatStepFormula(null);
  if (step.op === "addColumn") return step.expr;
  return formatStepFormula(step);
}
