/**
 * Texto de erro para blocos de dados no palco/editor.
 * Prefere `error` (já com status da API); usa `detail` se o error for genérico/legado.
 */

const GENERIC_UNAVAILABLE =
  /dados indispon[ií]veis|fonte de dados indispon[ií]vel|indicador indispon[ií]vel/i;

export type DataResolvedErrorFields = {
  error?: unknown;
  detail?: unknown;
  statusCode?: number | null;
};

function asTrimmedText(value: unknown): string {
  if (typeof value === "string") return value.trim();
  if (value == null) return "";
  if (typeof value === "number" || typeof value === "boolean") return String(value);
  if (typeof value === "object" && "message" in value) {
    const message = (value as { message: unknown }).message;
    if (typeof message === "string" && message.trim()) return message.trim();
  }
  return "";
}

export function resolveDataBlockErrorText(
  resolved?: DataResolvedErrorFields | null,
): string | null {
  const error = asTrimmedText(resolved?.error);
  const detail = asTrimmedText(resolved?.detail);

  if (error && detail && error !== detail && GENERIC_UNAVAILABLE.test(error)) {
    return `${error} ${detail}`;
  }
  if (error) return error;
  if (detail) return detail;
  return null;
}
