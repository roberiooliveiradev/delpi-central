export type ColumnType =
  | "text"
  | "number"
  | "currency"
  | "date"
  | "percent"
  | "quantity"
  | "days"
  | undefined;

const CURRENCY_KEYS =
  /preco|price|custo|cost|total|revenue|faturamento|receita|saldo|vlr|vl_/i;
const PERCENT_KEYS = /pct|percent|taxa|rate|margem|margin|otd|giro|eficiencia/i;
const DATE_KEYS =
  /data|date|emissao|criacao|atualizacao|inicio|fim|vencimento|dt_|created|updated/i;
const QTY_KEYS =
  /qtd|quantidade|qty|quantity|disponivel|reservado|estoque|volume|documento/i;
const DAYS_KEYS = /_days|pmr|lead_time|dias_uteis/i;

function normalizeLabel(value: string): string {
  return value
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .toLowerCase();
}

export function inferColumnTypeFromCampoLabel(campo: string): ColumnType {
  const normalized = normalizeLabel(campo);

  if (
    /documento|quantidade|registro|produto distinto|localizacao|itens/.test(
      normalized,
    ) &&
    !/valor|preco|custo|faturado|receita/.test(normalized)
  ) {
    return "quantity";
  }

  if (/valor|preco|custo|faturado|receita|saldo/.test(normalized)) {
    return "currency";
  }

  if (/emissao|revisao|vencimento|data/.test(normalized)) {
    return "date";
  }

  if (/percent|taxa|margem|otd|giro/.test(normalized)) {
    return "percent";
  }

  return undefined;
}

export function inferColumnType(
  key: string,
  dataType?: ColumnType,
  row?: Record<string, unknown>,
): ColumnType {
  const rowTypeKey = `${key}Type`;

  if (row && typeof row[rowTypeKey] === "string") {
    return row[rowTypeKey] as ColumnType;
  }

  if (dataType) {
    return dataType;
  }

  if (key === "valor" && row && typeof row.campo === "string") {
    const fromCampo = inferColumnTypeFromCampoLabel(String(row.campo));

    if (fromCampo) {
      return fromCampo;
    }

    return undefined;
  }

  if (key === "valor") {
    return undefined;
  }

  if (CURRENCY_KEYS.test(key)) return "currency";
  if (PERCENT_KEYS.test(key)) return "percent";
  if (DATE_KEYS.test(key)) return "date";
  if (DAYS_KEYS.test(key)) return "days";
  if (QTY_KEYS.test(key)) return "quantity";

  return undefined;
}

export function getAlignClass(
  key: string,
  value: unknown,
  dataType?: ColumnType,
  row?: Record<string, unknown>,
): string {
  const t = inferColumnType(key, dataType, row);

  if (
    typeof value === "number" ||
    t === "currency" ||
    t === "quantity" ||
    t === "percent" ||
    t === "number"
  ) {
    return "mdc-rich-table__td--right";
  }

  return "";
}

export function formatCellValue(
  value: unknown,
  columnKey?: string,
  dataType?: ColumnType,
  row?: Record<string, unknown>,
): string {
  if (value == null) return "—";
  if (typeof value === "boolean") return value ? "Sim" : "Não";

  if (Array.isArray(value)) {
    return value
      .map((item) => formatNestedCellObject(item))
      .filter((item) => item.length > 0)
      .join(", ");
  }

  if (typeof value === "object") {
    return formatNestedCellObject(value);
  }

  const key = columnKey || "";
  const colType = inferColumnType(key, dataType, row);

  if (typeof value === "number") {
    if (colType === "currency") {
      return value.toLocaleString("pt-BR", {
        style: "currency",
        currency: "BRL",
      });
    }

    if (colType === "percent") {
      return `${value.toLocaleString("pt-BR", {
        minimumFractionDigits: 1,
        maximumFractionDigits: 2,
      })}%`;
    }

    if (colType === "quantity") {
      return value.toLocaleString("pt-BR", {
        minimumFractionDigits: 0,
        maximumFractionDigits: 0,
      });
    }

    if (colType === "days") {
      if (Number.isInteger(value)) {
        return `${value.toLocaleString("pt-BR")} dias`;
      }

      return `${value.toLocaleString("pt-BR", {
        minimumFractionDigits: 1,
        maximumFractionDigits: 2,
      })} dias`;
    }

    if (Number.isInteger(value)) return value.toLocaleString("pt-BR");

    return value.toLocaleString("pt-BR", {
      minimumFractionDigits: 2,
      maximumFractionDigits: 4,
    });
  }

  const str = String(value);

  if (colType === "date" && /^\d{8}$/.test(str)) {
    return `${str.slice(6, 8)}/${str.slice(4, 6)}/${str.slice(0, 4)}`;
  }

  if (colType === "date" || /^\d{4}-\d{2}-\d{2}/.test(str)) {
    const d = new Date(str);

    if (!isNaN(d.getTime())) {
      if (str.includes("T") || str.length > 10) {
        return d.toLocaleString("pt-BR", {
          dateStyle: "short",
          timeStyle: "short",
        });
      }

      return d.toLocaleDateString("pt-BR");
    }
  }

  return str;
}

function formatNestedCellObject(value: unknown): string {
  if (value == null) {
    return "";
  }

  if (typeof value !== "object") {
    return String(value);
  }

  const obj = value as Record<string, unknown>;
  const code = String(obj.code || "").trim();
  const description = String(obj.description || "").trim();
  const label = String(obj.label || "").trim();

  if (code && description) {
    return `${code} — ${description}`;
  }

  if (code) {
    return code;
  }

  if (description) {
    return description;
  }

  if (label) {
    return label;
  }

  try {
    return JSON.stringify(value);
  } catch {
    return "—";
  }
}
