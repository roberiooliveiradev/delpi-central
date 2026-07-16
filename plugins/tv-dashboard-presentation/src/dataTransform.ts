/**
 * Transformações tipo Power Query sobre a tabela da fonte (antes da View/*Projection).
 * Persistir só `steps` — nunca rows.
 *
 * Canônico em runtime: Python `tv_data_transform_service` (enrichment / preview-block).
 * Este módulo TS é espelho para testes de paridade — a UI do editor NÃO deve aplicar steps
 * no browser; use `previewTransformTableOnServer` / `resolved.table` do backend.
 */

export type DataTransformCmp = "eq" | "neq" | "gt" | "lt" | "notNull" | "contains" | "startsWith";

export type DataTransformAgg = "sum" | "avg" | "min" | "max" | "count" | "first";

export type DataTransformStep =
  | { op: "rename"; from: string; to: string }
  | { op: "select"; columns: string[] }
  | { op: "filter"; column: string; cmp: DataTransformCmp; value?: unknown }
  | { op: "addColumn"; name: string; expr: string }
  | { op: "replace"; column: string; find: string; replaceWith: string }
  | { op: "sort"; column: string; direction: "asc" | "desc" }
  | { op: "keepRows"; count: number; from: "top" | "bottom" }
  | { op: "removeRows"; count: number; from: "top" | "bottom" }
  | { op: "changeType"; column: string; to: "number" | "string" }
  | { op: "fillDown"; column: string }
  | { op: "firstRowAsHeader" }
  | {
      op: "groupBy";
      keys: string[];
      aggregations: Array<{ column: string; fn: DataTransformAgg; as: string }>;
    }
  | {
      op: "pivot";
      column: string;
      valueColumn: string;
      aggregation?: DataTransformAgg;
    }
  | {
      op: "unpivot";
      columns: string[];
      nameColumn?: string;
      valueColumn?: string;
    }
  | {
      op: "merge";
      sourceId: string;
      leftKey: string;
      rightKey: string;
      columns?: string[];
      join?: "left";
    };

export type DataTransform = {
  steps: DataTransformStep[];
};

export type DataTableSnapshot = {
  columns: string[];
  rows: Array<Record<string, unknown>>;
};

export type DataTransformContext = {
  /** Outras consultas do slide (id → tabela) — merge. */
  siblingTables?: Record<string, DataTableSnapshot>;
};

const IDENT = /^[A-Za-z_][A-Za-z0-9_]*$/;
const FILTER_CMPS = new Set([
  "eq",
  "neq",
  "gt",
  "lt",
  "notNull",
  "contains",
  "startsWith",
]);
const AGGS = new Set(["sum", "avg", "min", "max", "count", "first"]);

function asAgg(raw: unknown): DataTransformAgg | null {
  const value = String(raw || "").trim();
  return AGGS.has(value) ? (value as DataTransformAgg) : null;
}

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
      if (!column || !FILTER_CMPS.has(cmp)) continue;
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
      continue;
    }
    if (op === "replace") {
      const column = String((item as { column?: unknown }).column || "").trim();
      const find = String((item as { find?: unknown }).find ?? "");
      const replaceWith = String(
        (item as { replaceWith?: unknown }).replaceWith ??
          (item as { replace?: unknown }).replace ??
          "",
      );
      if (column) steps.push({ op: "replace", column, find, replaceWith });
      continue;
    }
    if (op === "sort") {
      const column = String((item as { column?: unknown }).column || "").trim();
      const direction =
        String((item as { direction?: unknown }).direction || "asc").trim() === "desc"
          ? "desc"
          : "asc";
      if (column) steps.push({ op: "sort", column, direction });
      continue;
    }
    if (op === "keepRows" || op === "removeRows") {
      const count = Math.max(0, Math.floor(Number((item as { count?: unknown }).count) || 0));
      const from =
        String((item as { from?: unknown }).from || "top").trim() === "bottom" ? "bottom" : "top";
      if (count > 0) steps.push({ op, count, from });
      continue;
    }
    if (op === "changeType") {
      const column = String((item as { column?: unknown }).column || "").trim();
      const to =
        String((item as { to?: unknown }).to || "").trim() === "number" ? "number" : "string";
      if (column) steps.push({ op: "changeType", column, to });
      continue;
    }
    if (op === "fillDown") {
      const column = String((item as { column?: unknown }).column || "").trim();
      if (column) steps.push({ op: "fillDown", column });
      continue;
    }
    if (op === "firstRowAsHeader") {
      steps.push({ op: "firstRowAsHeader" });
      continue;
    }
    if (op === "groupBy") {
      const keys = Array.isArray((item as { keys?: unknown }).keys)
        ? (item as { keys: unknown[] }).keys.map((k) => String(k || "").trim()).filter(Boolean)
        : [];
      const aggregationsRaw = Array.isArray((item as { aggregations?: unknown }).aggregations)
        ? (item as { aggregations: unknown[] }).aggregations
        : [];
      const aggregations: Array<{ column: string; fn: DataTransformAgg; as: string }> = [];
      for (const agg of aggregationsRaw) {
        if (!agg || typeof agg !== "object") continue;
        const column = String((agg as { column?: unknown }).column || "").trim();
        const fn = asAgg((agg as { fn?: unknown }).fn);
        const asName = String((agg as { as?: unknown }).as || "").trim() || `${column}_${fn}`;
        if (column && fn) aggregations.push({ column, fn, as: asName });
      }
      if (keys.length && aggregations.length) {
        steps.push({ op: "groupBy", keys, aggregations });
      }
      continue;
    }
    if (op === "pivot") {
      const column = String((item as { column?: unknown }).column || "").trim();
      const valueColumn = String((item as { valueColumn?: unknown }).valueColumn || "").trim();
      const aggregation = asAgg((item as { aggregation?: unknown }).aggregation) ?? "sum";
      if (column && valueColumn) {
        steps.push({ op: "pivot", column, valueColumn, aggregation });
      }
      continue;
    }
    if (op === "unpivot") {
      const columns = Array.isArray((item as { columns?: unknown }).columns)
        ? (item as { columns: unknown[] }).columns
            .map((col) => String(col || "").trim())
            .filter(Boolean)
        : [];
      if (!columns.length) continue;
      steps.push({
        op: "unpivot",
        columns,
        nameColumn:
          String((item as { nameColumn?: unknown }).nameColumn || "").trim() || "atributo",
        valueColumn:
          String((item as { valueColumn?: unknown }).valueColumn || "").trim() || "valor",
      });
      continue;
    }
    if (op === "merge") {
      const sourceId = String((item as { sourceId?: unknown }).sourceId || "").trim();
      const leftKey = String((item as { leftKey?: unknown }).leftKey || "").trim();
      const rightKey = String((item as { rightKey?: unknown }).rightKey || "").trim();
      const columns = Array.isArray((item as { columns?: unknown }).columns)
        ? (item as { columns: unknown[] }).columns
            .map((col) => String(col || "").trim())
            .filter(Boolean)
        : undefined;
      if (sourceId && leftKey && rightKey) {
        steps.push({
          op: "merge",
          sourceId,
          leftKey,
          rightKey,
          ...(columns?.length ? { columns } : {}),
          join: "left",
        });
      }
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

function compareFilter(cell: unknown, cmp: DataTransformCmp, value: unknown): boolean {
  if (cmp === "notNull") return cell != null && String(cell).trim() !== "";
  const left = String(cell ?? "");
  const right = String(value ?? "");
  if (cmp === "eq") return left === right;
  if (cmp === "neq") return left !== right;
  if (cmp === "contains") return left.includes(right);
  if (cmp === "startsWith") return left.startsWith(right);
  const ln = asNumber(cell);
  const rn = asNumber(value);
  if (ln == null || rn == null) return false;
  if (cmp === "gt") return ln > rn;
  if (cmp === "lt") return ln < rn;
  return false;
}

function aggregateColumn(
  values: unknown[],
  fn: DataTransformAgg,
): unknown {
  if (fn === "count") return values.length;
  if (fn === "first") return values[0] ?? null;
  const nums = values.map(asNumber).filter((n): n is number => n != null);
  if (!nums.length) return null;
  if (fn === "sum") return nums.reduce((a, b) => a + b, 0);
  if (fn === "avg") return nums.reduce((a, b) => a + b, 0) / nums.length;
  if (fn === "min") return Math.min(...nums);
  if (fn === "max") return Math.max(...nums);
  return null;
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

function safeHeader(value: unknown, index: number): string {
  const raw = String(value ?? "").trim() || `coluna_${index + 1}`;
  return raw.replace(/[^\w]+/g, "_").replace(/^(\d)/, "_$1");
}

export function applyDataTransformSteps(
  table: DataTableSnapshot,
  steps: DataTransformStep[] | undefined | null,
  context?: DataTransformContext,
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
      const keep = step.columns.filter(
        (col) => columns.includes(col) || rows.some((row) => col in row),
      );
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
      continue;
    }
    if (step.op === "replace") {
      rows = rows.map((row) => ({
        ...row,
        [step.column]: String(row[step.column] ?? "").split(step.find).join(step.replaceWith),
      }));
      continue;
    }
    if (step.op === "sort") {
      const dir = step.direction === "desc" ? -1 : 1;
      rows = [...rows].sort((a, b) => {
        const av = a[step.column];
        const bv = b[step.column];
        const an = asNumber(av);
        const bn = asNumber(bv);
        if (an != null && bn != null) return (an - bn) * dir;
        return String(av ?? "").localeCompare(String(bv ?? ""), "pt-BR") * dir;
      });
      continue;
    }
    if (step.op === "keepRows") {
      rows =
        step.from === "bottom"
          ? rows.slice(Math.max(0, rows.length - step.count))
          : rows.slice(0, step.count);
      continue;
    }
    if (step.op === "removeRows") {
      rows =
        step.from === "bottom"
          ? rows.slice(0, Math.max(0, rows.length - step.count))
          : rows.slice(step.count);
      continue;
    }
    if (step.op === "changeType") {
      rows = rows.map((row) => {
        const raw = row[step.column];
        if (step.to === "number") {
          return { ...row, [step.column]: asNumber(raw) };
        }
        return { ...row, [step.column]: raw == null ? "" : String(raw) };
      });
      continue;
    }
    if (step.op === "fillDown") {
      let last: unknown = null;
      rows = rows.map((row) => {
        const cell = row[step.column];
        if (cell != null && String(cell).trim() !== "") {
          last = cell;
          return row;
        }
        return { ...row, [step.column]: last };
      });
      continue;
    }
    if (step.op === "firstRowAsHeader") {
      if (!rows.length) continue;
      const headerRow = rows[0]!;
      const nextColumns = columns.map((col, index) => safeHeader(headerRow[col], index));
      rows = rows.slice(1).map((row) => {
        const next: Record<string, unknown> = {};
        columns.forEach((col, index) => {
          next[nextColumns[index]!] = row[col];
        });
        return next;
      });
      columns = nextColumns;
      continue;
    }
    if (step.op === "groupBy") {
      const groups = new Map<string, Record<string, unknown>[]>();
      for (const row of rows) {
        const key = step.keys.map((k) => String(row[k] ?? "")).join("\u0001");
        const list = groups.get(key) ?? [];
        list.push(row);
        groups.set(key, list);
      }
      const nextRows: Array<Record<string, unknown>> = [];
      for (const groupRows of groups.values()) {
        const next: Record<string, unknown> = {};
        for (const key of step.keys) next[key] = groupRows[0]?.[key];
        for (const agg of step.aggregations) {
          next[agg.as] = aggregateColumn(
            groupRows.map((row) => row[agg.column]),
            agg.fn,
          );
        }
        nextRows.push(next);
      }
      columns = [...step.keys, ...step.aggregations.map((agg) => agg.as)];
      rows = nextRows;
      continue;
    }
    if (step.op === "pivot") {
      const stay = columns.filter((col) => col !== step.column && col !== step.valueColumn);
      const pivotValues = [
        ...new Set(rows.map((row) => String(row[step.column] ?? "")).filter(Boolean)),
      ];
      const groups = new Map<string, Record<string, unknown>[]>();
      for (const row of rows) {
        const key = stay.map((k) => String(row[k] ?? "")).join("\u0001");
        const list = groups.get(key) ?? [];
        list.push(row);
        groups.set(key, list);
      }
      const nextColumns = [...stay, ...pivotValues.map((v) => safeHeader(v, 0))];
      const nextRows: Array<Record<string, unknown>> = [];
      for (const groupRows of groups.values()) {
        const next: Record<string, unknown> = {};
        for (const key of stay) next[key] = groupRows[0]?.[key];
        for (const pivot of pivotValues) {
          const matched = groupRows.filter((row) => String(row[step.column] ?? "") === pivot);
          next[safeHeader(pivot, 0)] = aggregateColumn(
            matched.map((row) => row[step.valueColumn]),
            step.aggregation ?? "sum",
          );
        }
        nextRows.push(next);
      }
      columns = nextColumns;
      rows = nextRows;
      continue;
    }
    if (step.op === "unpivot") {
      const stay = columns.filter((col) => !step.columns.includes(col));
      const nameCol = step.nameColumn || "atributo";
      const valueCol = step.valueColumn || "valor";
      const nextRows: Array<Record<string, unknown>> = [];
      for (const row of rows) {
        for (const col of step.columns) {
          const next: Record<string, unknown> = {};
          for (const key of stay) next[key] = row[key];
          next[nameCol] = col;
          next[valueCol] = row[col];
          nextRows.push(next);
        }
      }
      columns = [...stay, nameCol, valueCol];
      rows = nextRows;
      continue;
    }
    if (step.op === "merge") {
      const other = context?.siblingTables?.[step.sourceId];
      if (!other) continue;
      const rightIndex = new Map<string, Record<string, unknown>>();
      for (const row of other.rows) {
        rightIndex.set(String(row[step.rightKey] ?? ""), row);
      }
      const takeCols =
        step.columns?.length
          ? step.columns
          : other.columns.filter((col) => col !== step.rightKey);
      for (const col of takeCols) {
        if (!columns.includes(col)) columns = [...columns, col];
      }
      rows = rows.map((row) => {
        const match = rightIndex.get(String(row[step.leftKey] ?? ""));
        if (!match) return row;
        const next = { ...row };
        for (const col of takeCols) next[col] = match[col];
        return next;
      });
    }
  }

  return { columns, rows };
}

/** Aplica steps ao payload cru; devolve lista de rows (formato tabular simples). */
export function applyDataTransformToPayload(
  data: unknown,
  transform: DataTransform | undefined | null,
  context?: DataTransformContext,
): { data: unknown; applied: boolean; table: DataTableSnapshot | null } {
  const steps = transform?.steps;
  if (!steps?.length) {
    return { data, applied: false, table: coercePayloadToTable(data) };
  }
  const table = coercePayloadToTable(data);
  if (!table) {
    return { data, applied: false, table: null };
  }
  const next = applyDataTransformSteps(table, steps, context);
  return { data: next.rows, applied: true, table: next };
}

/** Rótulo PT curto para lista de etapas. */
export function dataTransformStepLabel(step: DataTransformStep): string {
  switch (step.op) {
    case "rename":
      return `Renomear ${step.from} → ${step.to}`;
    case "select":
      return `Colunas: ${step.columns.join(", ")}`;
    case "filter":
      return `Filtrar ${step.column} ${step.cmp}${
        step.cmp === "notNull" ? "" : ` ${String(step.value ?? "")}`
      }`;
    case "addColumn":
      return `Coluna ${step.name} = ${step.expr}`;
    case "replace":
      return `Substituir em ${step.column}`;
    case "sort":
      return `Ordenar ${step.column} (${step.direction})`;
    case "keepRows":
      return `Manter ${step.count} linhas (${step.from})`;
    case "removeRows":
      return `Remover ${step.count} linhas (${step.from})`;
    case "changeType":
      return `Tipo ${step.column} → ${step.to}`;
    case "fillDown":
      return `Preencher abaixo ${step.column}`;
    case "firstRowAsHeader":
      return "Usar 1ª linha como cabeçalho";
    case "groupBy":
      return `Agrupar por ${step.keys.join(", ")}`;
    case "pivot":
      return `Pivot ${step.column}`;
    case "unpivot":
      return `Unpivot ${step.columns.join(", ")}`;
    case "merge":
      return `Mesclar ← ${step.sourceId}`;
    default:
      return "Etapa";
  }
}

export function dataTransformStepFormula(step: DataTransformStep): string {
  switch (step.op) {
    case "rename":
      return `= RenameColumns(Fonte, ${step.from} → ${step.to})`;
    case "select":
      return `= SelectColumns(Fonte, [${step.columns.join(", ")}])`;
    case "filter":
      return step.cmp === "notNull"
        ? `= FilterRows(Fonte, ${step.column} is not null)`
        : `= FilterRows(Fonte, [${step.column}] ${step.cmp} ${JSON.stringify(step.value ?? "")})`;
    case "addColumn":
      return `= AddColumn(Fonte, ${step.name}, ${step.expr})`;
    case "replace":
      return `= ReplaceValue(Fonte, ${step.column}, ${JSON.stringify(step.find)} → ${JSON.stringify(step.replaceWith)})`;
    case "sort":
      return `= Sort(Fonte, ${step.column}, ${step.direction})`;
    case "keepRows":
      return `= KeepRows(Fonte, ${step.count}, ${step.from})`;
    case "removeRows":
      return `= RemoveRows(Fonte, ${step.count}, ${step.from})`;
    case "changeType":
      return `= ChangeType(Fonte, ${step.column}, ${step.to})`;
    case "fillDown":
      return `= FillDown(Fonte, ${step.column})`;
    case "firstRowAsHeader":
      return "= PromoteHeaders(Fonte)";
    case "groupBy":
      return `= GroupBy(Fonte, [${step.keys.join(", ")}])`;
    case "pivot":
      return `= Pivot(Fonte, ${step.column}, ${step.valueColumn})`;
    case "unpivot":
      return `= Unpivot(Fonte, [${step.columns.join(", ")}])`;
    case "merge":
      return `= Merge(Fonte, ${step.sourceId}, ${step.leftKey}=${step.rightKey})`;
    default:
      return "= Fonte";
  }
}
