/**
 * Assistência ao modo fonte HTML (padrão Monaco/CKEditor Enhanced, sem lib pesada):
 * - sugestão de tags allowlisted ao digitar `<`
 * - sugestão de propriedades/valores CSS dentro de `style="…"`
 * - fechamento automático ao digitar `>` com cursor entre abertura e fechamento
 */

/** Tags aceitas pelos sanitizers de ata (CIPA / CEC / Transformômetro). */
export const RICH_TEXT_HTML_SUGGEST_TAGS = [
  "a",
  "b",
  "blockquote",
  "br",
  "caption",
  "col",
  "colgroup",
  "del",
  "div",
  "em",
  "font",
  "h1",
  "h2",
  "h3",
  "h4",
  "h5",
  "h6",
  "i",
  "ins",
  "li",
  "mark",
  "ol",
  "p",
  "s",
  "span",
  "strike",
  "strong",
  "sub",
  "sup",
  "table",
  "tbody",
  "td",
  "tfoot",
  "th",
  "thead",
  "tr",
  "u",
  "ul",
] as const;

/** Propriedades CSS do allowlist dos sanitizers de ata. */
export const RICH_TEXT_CSS_SUGGEST_PROPERTIES = [
  "background",
  "background-color",
  "border",
  "border-collapse",
  "color",
  "font-family",
  "font-size",
  "font-style",
  "font-weight",
  "padding",
  "text-align",
  "text-decoration",
  "text-decoration-line",
  "vertical-align",
  "width",
] as const;

/** Valores comuns sugeridos por propriedade (subconjunto seguro do allowlist). */
export const RICH_TEXT_CSS_VALUE_HINTS: Record<string, readonly string[]> = {
  "text-align": ["left", "center", "right", "justify"],
  "font-weight": ["normal", "bold", "600", "700"],
  "font-style": ["normal", "italic"],
  "border-collapse": ["collapse", "separate"],
  "vertical-align": ["top", "middle", "bottom", "baseline"],
  color: ["#111111", "#089bdb", "#dc2626"],
  "background-color": ["#fef08a", "#e8f4fb", "transparent"],
  background: ["#fef08a", "#e8f4fb", "transparent"],
  "font-size": ["12px", "14px", "16px", "18px", "20px", "24px"],
  "font-family": ["Arial", "Inter", "Georgia"],
  "text-decoration": ["underline", "line-through", "none"],
  "text-decoration-line": ["underline", "line-through", "none"],
  width: ["100%", "50%", "auto"],
  padding: ["0", "4px", "8px", "10px"],
  border: ["1px solid #c5cdd6", "none"],
};

const VOID_TAGS = new Set(["br", "col"]);
const TAG_SET = new Set<string>(RICH_TEXT_HTML_SUGGEST_TAGS);
const CSS_PROP_SET = new Set<string>(RICH_TEXT_CSS_SUGGEST_PROPERTIES);

export type RichTextHtmlAssistEdit = {
  value: string;
  selectionStart: number;
  selectionEnd: number;
};

export type RichTextSourceSuggestionKind = "tag" | "css-prop" | "css-value";

export type RichTextSourceSuggestionSession = {
  kind: RichTextSourceSuggestionKind;
  /** Início do token a substituir. */
  start: number;
  prefix: string;
  items: string[];
  /** Para `css-value`: propriedade à esquerda dos `:`. */
  cssProperty?: string;
};

export type RichTextHtmlTagSuggestionContext = {
  start: number;
  prefix: string;
};

/** Detecta token de tag aberta incompleta à esquerda do cursor (`<p`, `<tab`…). */
export function findRichTextHtmlTagSuggestionContext(
  value: string,
  cursor: number,
): RichTextHtmlTagSuggestionContext | null {
  const before = value.slice(0, cursor);
  const match = before.match(/<([a-zA-Z][\w-]*)?$/);
  if (!match) return null;
  if (before.endsWith("</") || /<\/[a-zA-Z][\w-]*$/.test(before)) return null;
  return {
    start: cursor - match[0].length,
    prefix: (match[1] ?? "").toLowerCase(),
  };
}

export function listRichTextHtmlTagSuggestions(prefix: string, limit = 12): string[] {
  const needle = prefix.toLowerCase();
  return RICH_TEXT_HTML_SUGGEST_TAGS.filter((tag) => tag.startsWith(needle)).slice(0, limit);
}

export function listRichTextCssPropertySuggestions(prefix: string, limit = 12): string[] {
  const needle = prefix.toLowerCase();
  return RICH_TEXT_CSS_SUGGEST_PROPERTIES.filter((prop) => prop.startsWith(needle)).slice(
    0,
    limit,
  );
}

export function listRichTextCssValueSuggestions(
  property: string,
  prefix: string,
  limit = 12,
): string[] {
  const hints = RICH_TEXT_CSS_VALUE_HINTS[property.toLowerCase()] ?? [];
  const needle = prefix.toLowerCase();
  return hints.filter((value) => value.toLowerCase().startsWith(needle)).slice(0, limit);
}

type StyleAttrSlice = {
  /** Índice do primeiro caractere dentro das aspas do style. */
  contentStart: number;
  content: string;
};

/** Localiza o conteúdo de `style="…"` / `style='…'` que contém o cursor. */
export function findRichTextStyleAttrSlice(
  value: string,
  cursor: number,
): StyleAttrSlice | null {
  const before = value.slice(0, cursor);
  const match = before.match(/\sstyle\s*=\s*(["'])([^"']*)$/i);
  if (!match) return null;
  const quote = match[1];
  const content = match[2] ?? "";
  // Ainda dentro das aspas: o fechamento não pode ter aparecido após o início do valor.
  const openAt = before.length - content.length;
  if (value[cursor] === quote) {
    /* cursor logo antes do fechamento — ainda dentro */
  }
  return { contentStart: openAt, content };
}

/**
 * Resolve sugestões no cursor: CSS dentro de `style="…"`, senão tags após `<`.
 * Prioridade alinhada ao CKEditor Enhanced (contexto-aware).
 */
export function resolveRichTextSourceSuggestions(
  value: string,
  cursor: number,
): RichTextSourceSuggestionSession | null {
  const style = findRichTextStyleAttrSlice(value, cursor);
  if (style) {
    const local = style.content;
    // valor após `prop:`
    const valueMatch = local.match(/(?:^|;)\s*([a-zA-Z][\w-]*)\s*:\s*([^;]*)$/);
    if (valueMatch) {
      const property = valueMatch[1].toLowerCase();
      const valuePrefix = valueMatch[2] ?? "";
      if (CSS_PROP_SET.has(property)) {
        const items = listRichTextCssValueSuggestions(property, valuePrefix.trimStart());
        if (items.length > 0) {
          const trimmed = valuePrefix.trimStart();
          const lead = valuePrefix.length - trimmed.length;
          return {
            kind: "css-value",
            start: style.contentStart + local.length - valuePrefix.length + lead,
            prefix: trimmed,
            items: [...items],
            cssProperty: property,
          };
        }
      }
    }

    // propriedade no início ou após `;`
    const propMatch = local.match(/(?:^|;)\s*([a-zA-Z][\w-]*)?$/);
    if (propMatch) {
      const prefix = (propMatch[1] ?? "").toLowerCase();
      const items = listRichTextCssPropertySuggestions(prefix);
      if (items.length === 0) return null;
      const token = propMatch[0];
      const namePart = propMatch[1] ?? "";
      const start = style.contentStart + local.length - namePart.length;
      // Evita confundir com valor a meio (já coberto acima quando há `:`)
      if (token.includes(":")) return null;
      return {
        kind: "css-prop",
        start,
        prefix,
        items: [...items],
      };
    }
    return null;
  }

  const tagCtx = findRichTextHtmlTagSuggestionContext(value, cursor);
  if (!tagCtx) return null;
  const items = listRichTextHtmlTagSuggestions(tagCtx.prefix);
  if (items.length === 0) return null;
  return {
    kind: "tag",
    start: tagCtx.start,
    prefix: tagCtx.prefix,
    items: [...items],
  };
}

/** Completa `<par` → `<p` (só o nome; o `>` dispara o auto-close). */
export function applyRichTextHtmlTagSuggestion(
  value: string,
  cursor: number,
  tag: string,
): RichTextHtmlAssistEdit | null {
  const ctx = findRichTextHtmlTagSuggestionContext(value, cursor);
  if (!ctx) return null;
  const safeTag = tag.toLowerCase();
  if (!TAG_SET.has(safeTag)) return null;
  const next = `${value.slice(0, ctx.start)}<${safeTag}${value.slice(cursor)}`;
  const caret = ctx.start + 1 + safeTag.length;
  return { value: next, selectionStart: caret, selectionEnd: caret };
}

/** Aplica item da sessão (tag / propriedade CSS / valor CSS) com cursor posicionado. */
export function applyRichTextSourceSuggestion(
  value: string,
  cursor: number,
  session: RichTextSourceSuggestionSession,
  item: string,
): RichTextHtmlAssistEdit | null {
  if (session.kind === "tag") {
    return applyRichTextHtmlTagSuggestion(value, cursor, item);
  }

  if (session.kind === "css-prop") {
    const safe = item.toLowerCase();
    if (!CSS_PROP_SET.has(safe)) return null;
    const insertion = `${safe}: `;
    const next = `${value.slice(0, session.start)}${insertion}${value.slice(cursor)}`;
    const caret = session.start + insertion.length;
    return { value: next, selectionStart: caret, selectionEnd: caret };
  }

  if (session.kind === "css-value") {
    const next = `${value.slice(0, session.start)}${item}${value.slice(cursor)}`;
    const caret = session.start + item.length;
    return { value: next, selectionStart: caret, selectionEnd: caret };
  }

  return null;
}

/**
 * Ao digitar `>` após `<tag`, insere `</tag>` e deixa o cursor no meio
 * (comportamento `autoClosingTags` do Monaco / Enhanced Source do CKEditor).
 */
export function applyRichTextHtmlAutoClose(
  value: string,
  cursor: number,
): RichTextHtmlAssistEdit | null {
  if (cursor < 1 || value[cursor - 1] !== ">") return null;

  const before = value.slice(0, cursor);
  const open = before.match(/<([a-zA-Z][\w-]*)>$/);
  if (!open) return null;

  const tag = open[1].toLowerCase();
  if (VOID_TAGS.has(tag)) return null;
  const after = value.slice(cursor);
  if (after.startsWith(`</${tag}>`)) return null;

  const closing = `</${tag}>`;
  const next = `${value.slice(0, cursor)}${closing}${value.slice(cursor)}`;
  return {
    value: next,
    selectionStart: cursor,
    selectionEnd: cursor,
  };
}

/** Conta aspas não escapadas de forma simples (evita auto-close dentro de atributo). */
export function richTextHtmlQuotesBalancedBefore(value: string, cursor: number): boolean {
  const before = value.slice(0, cursor);
  let doubleQuotes = 0;
  let singleQuotes = 0;
  for (let i = 0; i < before.length; i += 1) {
    const ch = before[i];
    if (ch === '"' && before[i - 1] !== "\\") doubleQuotes += 1;
    if (ch === "'" && before[i - 1] !== "\\") singleQuotes += 1;
  }
  return doubleQuotes % 2 === 0 && singleQuotes % 2 === 0;
}
