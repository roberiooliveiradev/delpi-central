export type FieldLabels = Record<string, string>;
export type FieldFormats = Record<string, string>;

/**
 * Fallback mínimo quando a API não enviou fieldLabels.
 * Não inventa tradução semântica — apenas separa tokens da key técnica.
 * A fonte canônica de labels PT-BR é a API (FieldLabelBundle).
 */
function humanizeFieldKeyFallback(key: string): string {
  const normalized = String(key || "").trim();
  if (!normalized) {
    return "";
  }

  if (normalized.includes("_")) {
    return normalized
      .split("_")
      .filter(Boolean)
      .map((part) => part.charAt(0).toUpperCase() + part.slice(1).toLowerCase())
      .join(" ");
  }

  // camelCase → spaced words without inventing meaning
  const spaced = normalized.replace(/([a-z0-9])([A-Z])/g, "$1 $2");
  return spaced.charAt(0).toUpperCase() + spaced.slice(1);
}

export function resolveFieldLabel(
  key: string,
  fieldLabels?: FieldLabels | null,
): string {
  const normalizedKey = String(key || "").trim();

  if (!normalizedKey) {
    return "";
  }

  const configured = fieldLabels?.[normalizedKey];

  if (typeof configured === "string" && configured.trim()) {
    return configured.trim();
  }

  return humanizeFieldKeyFallback(normalizedKey);
}

export function resolveFieldFormat(
  key: string,
  fieldFormats?: FieldFormats | null,
): string | undefined {
  const normalizedKey = String(key || "").trim();

  if (!normalizedKey) {
    return undefined;
  }

  const configured = fieldFormats?.[normalizedKey];

  return typeof configured === "string" && configured.trim()
    ? configured.trim()
    : undefined;
}

export function formatChartAxisValue(
  value: unknown,
  key: string,
  fieldFormats?: FieldFormats | null,
): string {
  if (value == null) {
    return "";
  }

  const text = String(value).trim();
  const fieldFormat = resolveFieldFormat(key, fieldFormats);

  if (fieldFormat === "date") {
    // Já no padrão BR (ex.: rotas LMP).
    if (/^\d{2}\/\d{2}\/\d{4}$/.test(text)) {
      return text;
    }

    if (/^\d{8}$/.test(text)) {
      return `${text.slice(6, 8)}/${text.slice(4, 6)}/${text.slice(0, 4)}`;
    }

    if (/^\d{4}-\d{2}-\d{2}/.test(text)) {
      const parts = text.slice(0, 10).split("-");

      if (parts.length === 3) {
        return `${parts[2]}/${parts[1]}/${parts[0]}`;
      }
    }
  }

  if (fieldFormat === "percentage" && Number.isFinite(Number(text))) {
    return `${Number(text).toLocaleString("pt-BR", { maximumFractionDigits: 1 })}%`;
  }

  if (fieldFormat === "currency" && Number.isFinite(Number(text))) {
    return Number(text).toLocaleString("pt-BR", {
      style: "currency",
      currency: "BRL",
    });
  }

  if (
    (fieldFormat === "quantity" || fieldFormat === "integer" || fieldFormat === "decimal") &&
    Number.isFinite(Number(text))
  ) {
    return Number(text).toLocaleString("pt-BR", {
      maximumFractionDigits: fieldFormat === "integer" ? 0 : 2,
    });
  }

  return text;
}

export function buildFieldLabelsFromTableColumns(
  columns: Array<{ key: string; label: string; dataType?: string }>,
): { fieldLabels: FieldLabels; fieldFormats: FieldFormats } {
  const fieldLabels: FieldLabels = {};
  const fieldFormats: FieldFormats = {};

  for (const column of columns) {
    const key = String(column.key || "").trim();

    if (!key) {
      continue;
    }

    if (column.label?.trim()) {
      fieldLabels[key] = column.label.trim();
    }

    if (column.dataType?.trim()) {
      fieldFormats[key] = column.dataType.trim();
    }
  }

  return { fieldLabels, fieldFormats };
}
