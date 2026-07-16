/** Detecta conteúdo HTML vazio (só tags vazias ou &nbsp;). */
export function isHtmlEmpty(html: string | null | undefined): boolean {
  const raw = (html || "")
    .replace(/<br\s*\/?>/gi, "")
    .replace(/<p>\s*<\/p>/gi, "")
    .replace(/<[^>]+>/g, "")
    .replace(/&nbsp;/gi, " ")
    .trim();
  return raw.length === 0;
}

export function formatDateBr(isoDate: string): string {
  const match = /^(\d{4})-(\d{2})-(\d{2})/.exec(isoDate);
  if (!match) return isoDate;
  return `${match[3]}/${match[2]}/${match[1]}`;
}

export function formatDateTimeBr(isoDateTime: string): string {
  const match = /^(\d{4})-(\d{2})-(\d{2})[T ](\d{2}):(\d{2})/.exec(isoDateTime);
  if (!match) return formatDateBr(isoDateTime);
  return `${match[3]}/${match[2]}/${match[1]} ${match[4]}:${match[5]}`;
}
