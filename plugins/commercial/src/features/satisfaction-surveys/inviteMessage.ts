/**
 * Mensagem padrão da campanha — campos dinâmicos, prévias e cópia.
 *
 * Os dois únicos campos dinâmicos são definidos em código e espelham a API
 * (`INVITE_PLACEHOLDERS`). A substituição autoritativa (nome TOTVS + link
 * exclusivo) acontece no backend em `.../recipients/{id}/invite`; aqui só há
 * prévia com dados fictícios identificados e conversão segura para HTML.
 *
 * SEGURANÇA: `RichTextEditor mode="preview"` injeta `value` via
 * `dangerouslySetInnerHTML` sem sanitizar. Todo HTML que chega nele DEVE sair de
 * `buildInviteHtml`, que escapa todo caractere especial e só linkifica http(s).
 */
export const INVITE_COMPANY_TOKEN = "{nome_empresa}";
export const INVITE_LINK_TOKEN = "{link_pesquisa}";
export const INVITE_PLACEHOLDERS = [INVITE_COMPANY_TOKEN, INVITE_LINK_TOKEN] as const;

/** Valores fictícios, claramente identificados, usados só na prévia de configuração. */
export const INVITE_SAMPLE_COMPANY = "Empresa Exemplo (fictícia)";
export const INVITE_SAMPLE_LINK = "https://exemplo.invalid/link-ficticio-da-pesquisa";

export function replaceInvitePlaceholders(
  template: string,
  values: { company: string; link: string },
): string {
  return template.split(INVITE_COMPANY_TOKEN).join(values.company).split(INVITE_LINK_TOKEN).join(values.link);
}

export function missingInvitePlaceholders(body: string): string[] {
  return INVITE_PLACEHOLDERS.filter((token) => !body.includes(token));
}

export function escapeHtml(value: string): string {
  return value
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");
}

const URL_CANDIDATE_RE = /https?:\/\/[^\s<>"']+/gi;
const TRAILING_PUNCTUATION_RE = /[.,;:!?)\]]+$/;

/** Aceita só http(s) absoluto e bem formado. */
export function isSafeHttpUrl(value: string): boolean {
  try {
    const url = new URL(value);
    return url.protocol === "http:" || url.protocol === "https:";
  } catch {
    return false;
  }
}

function linkifyEscapedLine(rawLine: string, linkify: boolean): string {
  if (!linkify) return escapeHtml(rawLine);
  let result = "";
  let cursor = 0;
  for (const match of rawLine.matchAll(URL_CANDIDATE_RE)) {
    const index = match.index ?? 0;
    const candidate = match[0];
    const trailing = TRAILING_PUNCTUATION_RE.exec(candidate)?.[0] ?? "";
    const url = trailing ? candidate.slice(0, candidate.length - trailing.length) : candidate;
    result += escapeHtml(rawLine.slice(cursor, index));
    if (isSafeHttpUrl(url)) {
      const safe = escapeHtml(url);
      result += `<a href="${safe}" target="_blank" rel="noopener noreferrer">${safe}</a>`;
    } else {
      result += escapeHtml(url);
    }
    result += escapeHtml(trailing);
    cursor = index + candidate.length;
  }
  return result + escapeHtml(rawLine.slice(cursor));
}

/**
 * Texto simples → HTML seguro (parágrafos por linha em branco, `<br>` por quebra simples).
 * Nunca interpreta HTML digitado pelo usuário.
 */
export function buildInviteHtml(text: string, options: { linkify?: boolean } = {}): string {
  const linkify = options.linkify ?? true;
  const normalized = text.replace(/\r\n?/g, "\n").trim();
  if (!normalized) return "<p></p>";
  return normalized
    .split(/\n{2,}/)
    .map((paragraph) => {
      const lines = paragraph.split("\n").map((line) => linkifyEscapedLine(line, linkify));
      return `<p>${lines.join("<br>")}</p>`;
    })
    .join("");
}

/** Texto simples do modo Mensageiro (quebras preservadas, link legível). */
export function buildMessengerText(text: string): string {
  return text.replace(/\r\n?/g, "\n").trim();
}

/** Insere `token` na seleção atual de um texto; devolve novo texto e posição do cursor. */
export function insertTokenAtSelection(
  text: string,
  token: string,
  selectionStart: number | null | undefined,
  selectionEnd: number | null | undefined,
): { text: string; cursor: number } {
  const start = clamp(selectionStart ?? text.length, text.length);
  const end = clamp(selectionEnd ?? start, text.length);
  const from = Math.min(start, end);
  const to = Math.max(start, end);
  return { text: text.slice(0, from) + token + text.slice(to), cursor: from + token.length };
}

function clamp(value: number, max: number): number {
  return Math.max(0, Math.min(value, max));
}
