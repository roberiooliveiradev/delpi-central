export type DataCellKind = "value" | "null" | "empty" | "missing" | "error";

export type DataCellError = {
  code?: string;
  message: string;
};

export type DataCellSemantics = {
  kind: DataCellKind;
  value: unknown;
  displayText: string;
  copyText: string;
  ariaLabel: string;
  title?: string;
  error?: DataCellError;
};

export type ResolveDataCellOptions = {
  present?: boolean;
  nullLabel?: string;
  emptyLabel?: string;
  missingLabel?: string;
  errorLabel?: string;
};

const DEFAULT_LABELS = {
  null: "null",
  empty: "vazio",
  missing: "ausente",
  error: "error",
} as const;

function structuredError(value: unknown): DataCellError | null {
  if (!value || typeof value !== "object" || Array.isArray(value)) return null;
  const candidate = (value as { error?: unknown }).error;
  if (!candidate || typeof candidate !== "object" || Array.isArray(candidate)) return null;
  const payload = candidate as Record<string, unknown>;
  const message = String(payload.message ?? payload.detail ?? payload.code ?? "Erro na célula");
  const code = payload.code == null ? undefined : String(payload.code);
  return { message, ...(code ? { code } : {}) };
}

function scalarText(value: unknown): string {
  if (typeof value === "string") return value;
  if (typeof value === "number" || typeof value === "bigint" || typeof value === "boolean") {
    return String(value);
  }
  if (value instanceof Date) return value.toISOString();
  try {
    return JSON.stringify(value);
  } catch {
    return String(value);
  }
}

export function resolveDataCellSemantics(
  value: unknown,
  options: ResolveDataCellOptions = {},
): DataCellSemantics {
  const labels = {
    null: options.nullLabel ?? DEFAULT_LABELS.null,
    empty: options.emptyLabel ?? DEFAULT_LABELS.empty,
    missing: options.missingLabel ?? DEFAULT_LABELS.missing,
    error: options.errorLabel ?? DEFAULT_LABELS.error,
  };

  if (options.present === false) {
    return {
      kind: "missing",
      value,
      displayText: labels.missing,
      copyText: labels.missing,
      ariaLabel: "Campo ausente",
    };
  }
  if (value == null) {
    return {
      kind: "null",
      value,
      displayText: labels.null,
      copyText: labels.null,
      ariaLabel: "Valor nulo",
    };
  }
  const error = structuredError(value);
  if (error) {
    return {
      kind: "error",
      value,
      displayText: labels.error,
      copyText: `#ERROR${error.code ? `:${error.code}` : ""}`,
      ariaLabel: `Erro: ${error.message}`,
      title: error.message,
      error,
    };
  }
  if (typeof value === "string" && value.length === 0) {
    return {
      kind: "empty",
      value,
      displayText: labels.empty,
      copyText: "",
      ariaLabel: "Texto vazio",
    };
  }
  const text = scalarText(value);
  return {
    kind: "value",
    value,
    displayText: text,
    copyText: text,
    ariaLabel: text,
  };
}
