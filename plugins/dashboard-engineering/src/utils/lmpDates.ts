/** Converte input YYYY-MM-DD para YYYYMMDD exigido pela API de LMPs. */
export function inputDateToLmpApi(value?: string): string | undefined {
  if (!value) return undefined;
  const normalized = value.trim();
  if (/^\d{8}$/.test(normalized)) return normalized;
  if (/^\d{4}-\d{2}-\d{2}$/.test(normalized)) {
    return normalized.replaceAll("-", "");
  }
  return normalized;
}

export function formatLmpDisplayDate(value?: string | null): string {
  if (!value || value.length !== 8) return "—";
  const year = value.slice(0, 4);
  const month = value.slice(4, 6);
  const day = value.slice(6, 8);
  return `${day}/${month}/${year}`;
}

export function formatListingKind(kind?: string | null): string {
  if (kind === "AMOSTRA") return "Amostra";
  if (kind === "OUTRO") return "Outro";
  if (kind === "LMP") return "LMP";
  return kind ?? "—";
}
