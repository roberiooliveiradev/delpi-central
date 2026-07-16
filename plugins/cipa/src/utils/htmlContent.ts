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
