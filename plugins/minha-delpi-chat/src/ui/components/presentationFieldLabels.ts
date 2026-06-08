export type FieldLabels = Record<string, string>;
export type FieldFormats = Record<string, string>;

function humanizeFieldKeyFallback(key: string): string {
  return key
    .replace(/_/g, " ")
    .replace(/\b\w/g, (char) => char.toUpperCase())
    .trim();
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
