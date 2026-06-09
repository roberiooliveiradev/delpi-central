/** Marcadores internos do stack humanizado (API) — não devem aparecer na UI. */
const PRESENTATION_SECTION_MARKER_RE =
  /<!--\s*\/?section:[a-z_]+\s*-->\s*/gi;

/**
 * Remove comentários `<!-- section:* -->` injetados pelo pipeline de apresentação.
 */
export function stripPresentationSectionMarkers(
  content: string | null | undefined,
): string {
  return String(content || "")
    .replace(PRESENTATION_SECTION_MARKER_RE, "")
    .replace(/\n{3,}/g, "\n\n")
    .trim();
}

/**
 * Detecta sintaxe markdown na resposta para evitar reveal caractere-a-caractere
 * (que exibe `**` literal até o fechamento do destaque).
 */
export function hasMarkdownSyntax(content: string | null | undefined): boolean {
  const text = String(content || "").trim();

  if (!text) {
    return false;
  }

  return (
    /\*\*/.test(text) ||
    /(?:^|\n)#{1,6}\s/.test(text) ||
    /```/.test(text) ||
    /(?:^|\n)\s*[-*]\s+\S/.test(text) ||
    /(?<![\w*])\*[^*\s][^*]*\*(?![\w*])/.test(text) ||
    /__[^_]+__/.test(text) ||
    /\[[^\]]+\]\([^)]+\)/.test(text)
  );
}

/** Normaliza escapes comuns vindos do LLM antes do parse markdown. */
export function prepareMarkdownContent(content: string): string {
  return stripPresentationSectionMarkers(
    String(content || "")
      .replace(/\\(\*|_|`)/g, "$1")
      .replace(/\r\n/g, "\n"),
  );
}

/**
 * Converte quebras de linha simples em hard breaks (estilo chat), preservando
 * parágrafos (\n\n) e blocos de código cercados (```), para que mensagens
 * multilinha mantenham as quebras como o usuário digitou.
 */
export function applySoftLineBreaks(content: string): string {
  const parts = String(content || "").split(/(```[\s\S]*?```)/g);

  return parts
    .map((part, index) => {
      // Índices ímpares são blocos de código cercados — não tocar.
      if (index % 2 === 1) {
        return part;
      }

      return part.replace(/([^\n ])\n(?!\n)/g, "$1  \n");
    })
    .join("");
}
