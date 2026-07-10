export type TextLinkFieldMode = "text" | "link";

const URL_LIKE_PATTERN = /^(https?:\/\/|mailto:|tel:|www\.)/i;

export function isLikelyExternalUrl(value: string): boolean {
  const trimmed = value.trim();
  if (!trimmed) return false;
  return URL_LIKE_PATTERN.test(trimmed) || /^[^\s]+\.[^\s]{2,}/.test(trimmed);
}

export function normalizeHrefInput(value: string): string {
  const trimmed = value.trim();
  if (!trimmed) return "";
  if (/^www\./i.test(trimmed)) return `https://${trimmed}`;
  return trimmed;
}

/** Modo inicial ao selecionar o bloco (Canva/PPT: link ativo quando há endereço). */
export function resolveDefaultTextLinkMode(
  hasHref: boolean,
  content: string,
): TextLinkFieldMode {
  if (hasHref) return "link";
  if (isLikelyExternalUrl(content)) return "link";
  return "text";
}

export function textLinkFieldPlaceholder(
  mode: TextLinkFieldMode,
  blockType: "heading" | "text",
  hasRichTextRuns: boolean,
): string {
  if (mode === "link") return "https://…";
  if (hasRichTextRuns) return "Duplo-clique no palco para editar formatação";
  return blockType === "heading" ? "Título" : "Texto";
}
