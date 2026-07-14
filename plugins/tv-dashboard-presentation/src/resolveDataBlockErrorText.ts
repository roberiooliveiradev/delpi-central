/**
 * Texto de erro para blocos de dados no palco/editor.
 * Prefere `error` (já com status da API); usa `detail` se o error for genérico/legado.
 */

const GENERIC_UNAVAILABLE =
  /dados indispon[ií]veis|fonte de dados indispon[ií]vel|indicador indispon[ií]vel/i;

export type DataResolvedErrorFields = {
  error?: string | null;
  detail?: string | null;
  statusCode?: number | null;
};

export function resolveDataBlockErrorText(
  resolved?: DataResolvedErrorFields | null,
): string | null {
  const error = typeof resolved?.error === "string" ? resolved.error.trim() : "";
  const detail = typeof resolved?.detail === "string" ? resolved.detail.trim() : "";

  if (error && detail && error !== detail && GENERIC_UNAVAILABLE.test(error)) {
    return `${error} ${detail}`;
  }
  if (error) return error;
  if (detail) return detail;
  return null;
}
