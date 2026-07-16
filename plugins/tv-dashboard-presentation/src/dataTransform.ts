/**
 * Transformações tipo Power Query sobre a tabela da fonte (antes da View/*Projection).
 * Persistir só `steps` — nunca rows.
 */

export type DataTransformCmp = "eq" | "neq" | "gt" | "lt" | "notNull";

export type DataTransformStep =
  | { op: "rename"; from: string; to: string }
  | { op: "select"; columns: string[] }
  | { op: "filter"; column: string; cmp: DataTransformCmp; value?: unknown }
  | { op: "addColumn"; name: string; expr: string };

export type DataTransform = {
  steps: DataTransformStep[];
};

export type DataTableSnapshot = {
  columns: string[];
  rows: Array<Record<string, unknown>>;
};

const IDENT = /^[A-Za-z_][A-Za-z0-9_]*$/;

export function normalizeDataTransform(raw: unknown): DataTransform | undefined {
  if (!raw || typeof raw !== "object") return undefined;
  const stepsRaw = (raw as DataTransform).steps;
  if (!Array.isArray(stepsRaw) || stepsRaw.length === 0) return undefined;
  const steps: DataTransformStep[] = [];
  for (const item of stepsRaw) {
    if (!item || typeof item !== "object") continue;
    const op = String((item as { op?: unknown }).op || "").trim();
    if (op === "rename") {
      const from = String((item as { from?: unknown }).from || "").trim();
      const to = String((item as { to?: unknown }).to || "").trim();
      if (from && to) steps.push({ op: "rename", from, to });
      continue;
    }
    if (op === "select") {
      const columns = Array.isArray((item as { columns?: unknown }).columns)
        ? (item as { columns: unknown[] }).columns
            .map((col) => String(col || "").trim())
            .filter(Boolean)
        : [];
      if (columns.length) steps.push({ op: "select", columns });
      continue;
    }
    if (op === "filter") {
      const column = String((item as { column?: unknown }).column || "").trim();
      const cmp = String((item as { cmp?: unknown }).cmp || "").trim() as DataTransformCmp;
      if (!column || !["eq", "neq", "gt", "lt", "notNull"].includes(cmp)) continue;
      steps.push({
        op: "filter",
        column,
        cmp,
        value: (item as { value?: unknown }).value,
      });
      continue;
    }
    if (op === "addColumn") {
      const name = String((item as { name?: unknown }).name || "").trim();
      const expr = String((item as { expr?: unknown }).expr || "").trim();
      if (name && expr) steps.push({ op: "addColumn", name, expr });
    }
  }
  return steps.length ? { steps } : undefined;
}

/** Extrai tabela tabular de payload API comum (lista ou envelope). */
export function coercePayloadToTable(data: unknown): DataTableSnapshot | null {
  if (Array.isArray(data)) {
    const rows = data.filter((row): row is Record<string, unknown> =>
      Boolean(row && typeof row === "object" && !Array.isArray(row)),
    );
    if (!rows.length) return { columns: [], rows: [] };
    const columns: string[] = [];
    const seen = new Set<string>();
    for (const row of rows) {
      for (const key of Object.keys(row)) {
        if (!seen.has(key)) {
          seen.add(key);
          columns.push(key);
        }
      }
    }
    return { columns, rows: rows.map((row) => ({ ...row })) };
  }
  if (data && typeof data === "object") {
    const record = data as Record<string, unknown>;
    for (const key of ["items", "rows", "data", "results", "values"]) {
      const inner = record[key];
      if (Array.isArray(inner)) {
        const nested = coercePayloadToTable(inner);
        if (nested) return nested;
      }
    }
  }
  return null;
}

function asNumber(value: unknown): number | null {
  if (typeof value === "number" && Number.isFinite(value)) return value;
  if (typeof value === "string" && value.trim()) {
    const parsed = Number(value.replace(",", "."));
    return Number.isFinite(parsed) ? parsed : null;
  }
  return null;
}

function compareFilter(
  cell: unknown,
  cmp: DataTransformCmp,
  value: unknown,
): boolean {
  if (cmp === "notNull") return cell != null && String(cell).trim() !== "";
  if (cmp === "eq") return String(cell ?? "") === String(value ?? "");
  if (cmp === "neq") return String(cell ?? "") !== String(value ?? "");
  const left = asNumber(cell);
  const right = asNumber(value);
  if (left == null || right == null) return false;
  if (cmp === "gt") return left > right;
  if (cmp === "lt") return left < right;
  return false;
}

/**
 * Avalia expressão aritmética segura: identificadores = colunas da linha,
 * operadores + - * / e parênteses. Sem eval livre.
 */
export function evaluateSafeArithmeticExpr(
  expr: string,
  row: Record<string, unknown>,
): number | null {
  const trimmed = expr.trim();
  if (!trimmed) return null;
  const columns = Object.keys(row).sort((a, b) => b.length - a.length);
  let i = 0;
  const peek = () => trimmed[i] ?? "";
  const consume = () => {
    const ch = trimmed[i] ?? "";
    i += 1;
    return ch;
  };
  const skipWs = () => {
    while (/\s/.test(peek())) i += 1;
  };

  const parseIdentifierOrNumber = (): number => {
    skipWs();
    if (peek() === "(") {
      consume();
      const value = parseExpr();
      skipWs();
      if (peek() !== ")") throw new Error("paren");
      consume();
      return value;
    }
    if (peek() === "-") {
      consume();
      return -parseIdentifierOrNumber();
    }
    if (/\d/.test(peek()) || peek() === ".") {
      let raw = "";
      while (/[\d.]/.test(peek())) raw += consume();
      const num = Number(raw);
      if (!Number.isFinite(num)) throw new Error("number");
      return num;
    }
    let ident = "";
    while (/[A-Za-z0-9_]/.test(peek())) ident += consume();
    if (!ident || !IDENT.test(ident)) throw new Error("ident");
    if (!columns.includes(ident) && !(ident in row)) throw new Error("col");
    const num = asNumber(row[ident]);
    if (num == null) throw new Error("nan");
    return num;
  };

  const parseTerm = (): number => {
    let left = parseIdentifierOrNumber();
    for (;;) {
      skipWs();
      const op = peek();
      if (op !== "*" && op !== "/") break;
      consume();
      const right = parseIdentifierOrNumber();
      left = op === "*" ? left * right : right === 0 ? NaN : left / right;
      if (!Number.isFinite(left)) throw new Error("arith");
    }
    return left;
  };

  const parseExpr = (): number => {
    let left = parseTerm();
    for (;;) {
      skipWs();
      const op = peek();
      if (op !== "+" && op !== "-") break;
      consume();
      const right = parseTerm();
      left = op === "+" ? left + right : left - right;
      if (!Number.isFinite(left)) throw new Error("arith");
    }
    return left;
  };

  try {
    const value = parseExpr();
    skipWs();
    if (i !== trimmed.length) return null;
    return Number.isFinite(value) ? value : null;
  } catch {
    return null;
  }
}

export function applyDataTransformSteps(
  table: DataTableSnapshot,
  steps: DataTransformStep[] | undefined | null,
): DataTableSnapshot {
  if (!steps?.length) {
    return { columns: [...table.columns], rows: table.rows.map((row) => ({ ...row })) };
  }
  let columns = [...table.columns];
  let rows = table.rows.map((row) => ({ ...row }));

  for (const step of steps) {
    if (step.op === "rename") {
      columns = columns.map((col) => (col === step.from ? step.to : col));
      rows = rows.map((row) => {
        if (!(step.from in row)) return row;
        const next = { ...row };
        next[step.to] = next[step.from];
        delete next[step.from];
        return next;
      });
      continue;
    }
    if (step.op === "select") {
      const keep = step.columns.filter((col) => columns.includes(col) || rows.some((row) => col in row));
      columns = keep.length ? keep : columns;
      rows = rows.map((row) => {
        const next: Record<string, unknown> = {};
        for (const col of columns) next[col] = row[col];
        return next;
      });
      continue;
    }
    if (step.op === "filter") {
      rows = rows.filter((row) => compareFilter(row[step.column], step.cmp, step.value));
      continue;
    }
    if (step.op === "addColumn") {
      const name = step.name.trim();
      if (!name) continue;
      if (!columns.includes(name)) columns = [...columns, name];
      rows = rows.map((row) => ({
        ...row,
        [name]: evaluateSafeArithmeticExpr(step.expr, row),
      }));
    }
  }

  return { columns, rows };
}

/** Aplica steps ao payload cru; devolve lista de rows (formato tabular simples). */
export function applyDataTransformToPayload(
  data: unknown,
  transform: DataTransform | undefined | null,
): { data: unknown; applied: boolean; table: DataTableSnapshot | null } {
  const steps = transform?.steps;
  if (!steps?.length) {
    return { data, applied: false, table: coercePayloadToTable(data) };
  }
  const table = coercePayloadToTable(data);
  if (!table) {
    return { data, applied: false, table: null };
  }
  const next = applyDataTransformSteps(table, steps);
  return { data: next.rows, applied: true, table: next };
}
