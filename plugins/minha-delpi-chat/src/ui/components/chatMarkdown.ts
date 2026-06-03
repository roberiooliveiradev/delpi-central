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
    /\*\*[^*]+\*\*/.test(text) ||
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
  return String(content || "")
    .replace(/\\(\*|_|`)/g, "$1")
    .replace(/\r\n/g, "\n");
}
