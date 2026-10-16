import { marked } from "marked";

/**
 * Token model + deterministic plain-text projection for ConversationMarkdown.
 * Parse-only over marked.lexer — never emits HTML strings.
 */

export type ConversationAuthorizedLink = {
  href: string;
  kind: "internal" | "external";
};

export type MarkdownToken = {
  type: string;
  raw?: string;
  text?: string;
  href?: string;
  tokens?: MarkdownToken[];
  items?: MarkdownToken[];
  ordered?: boolean;
  start?: number;
  depth?: number;
};

export const CONVERSATION_MARKDOWN_MAX_SOURCE_LENGTH = 16_384;
export const CONVERSATION_MARKDOWN_MAX_NODES = 256;
export const CONVERSATION_MARKDOWN_MAX_DEPTH = 8;
export const CONVERSATION_MARKDOWN_MAX_LINKS = 16;

const FORBIDDEN_QUERY_KEY =
  /^(?:token|access_token|refresh_token|id_token|auth|authorization|key|api_key|secret)$/i;

export function safeConversationLinkDestination(
  href: string,
  links: readonly ConversationAuthorizedLink[],
): "internal" | "external" | null {
  if (!href || href.trim() !== href || /[\\\u0000-\u001f\u007f]/.test(href)) {
    return null;
  }
  const published = links.find((entry) => entry.href === href);
  if (!published) return null;
  try {
    if (published.kind === "internal") {
      if (!href.startsWith("/") || href.startsWith("//") || href.includes("\\")) {
        return null;
      }
      const url = new URL(href, "https://portal.invalid");
      if (url.origin !== "https://portal.invalid") return null;
      for (const name of url.searchParams.keys()) {
        if (FORBIDDEN_QUERY_KEY.test(name)) return null;
      }
      return "internal";
    }
    if (published.kind !== "external") return null;
    const url = new URL(href);
    if (url.protocol !== "https:" || !url.hostname || url.username || url.password) {
      return null;
    }
    for (const name of url.searchParams.keys()) {
      if (FORBIDDEN_QUERY_KEY.test(name)) return null;
    }
    return "external";
  } catch {
    return null;
  }
}

export function tokenizeConversationMarkdown(
  source: string,
): MarkdownToken[] | null {
  if (source.length > CONVERSATION_MARKDOWN_MAX_SOURCE_LENGTH) return null;
  try {
    const tokens = marked.lexer(source, { gfm: true }) as unknown as MarkdownToken[];
    let count = 0;
    let links = 0;
    function inspect(nodes: MarkdownToken[], depth: number): boolean {
      if (depth > CONVERSATION_MARKDOWN_MAX_DEPTH) return false;
      for (const node of nodes) {
        if (++count > CONVERSATION_MARKDOWN_MAX_NODES) return false;
        if (node.type === "link" && ++links > CONVERSATION_MARKDOWN_MAX_LINKS) {
          return false;
        }
        if (node.tokens && !inspect(node.tokens, depth + 1)) return false;
        if (node.items && !inspect(node.items, depth + 1)) return false;
      }
      return true;
    }
    return inspect(tokens, 0) ? tokens : null;
  } catch {
    return null;
  }
}

function inlinePlain(
  nodes: MarkdownToken[] | undefined,
  links: readonly ConversationAuthorizedLink[],
  depth: number,
): string {
  if (!nodes || depth > CONVERSATION_MARKDOWN_MAX_DEPTH) return "";
  return nodes
    .map((token) => {
      switch (token.type) {
        case "text":
        case "escape":
          return token.text ?? token.raw ?? "";
        case "strong":
        case "em":
        case "del":
          return inlinePlain(token.tokens, links, depth + 1);
        case "codespan":
          return token.text ?? "";
        case "br":
          return "\n";
        case "link": {
          const label = token.tokens?.length
            ? inlinePlain(token.tokens, links, depth + 1)
            : (token.text ?? "");
          const kind = safeConversationLinkDestination(token.href ?? "", links);
          if (kind && token.href) return `${label} (${token.href})`;
          return label;
        }
        case "image":
          return token.text ?? "";
        case "html":
          return token.raw ?? token.text ?? "";
        default:
          return token.tokens?.length
            ? inlinePlain(token.tokens, links, depth + 1)
            : (token.raw ?? token.text ?? "");
      }
    })
    .join("");
}

function blockPlain(
  nodes: MarkdownToken[],
  links: readonly ConversationAuthorizedLink[],
  depth: number,
): string {
  if (depth > CONVERSATION_MARKDOWN_MAX_DEPTH) return "";
  const parts: string[] = [];
  for (const token of nodes) {
    switch (token.type) {
      case "space":
        break;
      case "paragraph":
      case "text":
        parts.push(
          token.tokens?.length
            ? inlinePlain(token.tokens, links, depth + 1)
            : (token.text ?? ""),
        );
        break;
      case "heading":
        parts.push(
          token.tokens?.length
            ? inlinePlain(token.tokens, links, depth + 1)
            : (token.text ?? ""),
        );
        break;
      case "list": {
        const start = token.start && token.start > 0 ? token.start : 1;
        (token.items ?? []).forEach((item, index) => {
          const marker = token.ordered ? `${start + index}. ` : "- ";
          const body = item.tokens?.length
            ? blockPlain(item.tokens, links, depth + 1).replace(/\n+/g, "\n")
            : (item.text ?? "");
          parts.push(`${marker}${body.trim()}`);
        });
        break;
      }
      case "blockquote": {
        const inner = blockPlain(token.tokens ?? [], links, depth + 1);
        parts.push(
          inner
            .split("\n")
            .map((line) => (line ? `> ${line}` : ">"))
            .join("\n"),
        );
        break;
      }
      case "code":
        parts.push(token.text ?? "");
        break;
      case "hr":
        parts.push("---");
        break;
      case "html":
      case "table":
      case "image":
      default:
        parts.push(token.raw ?? token.text ?? "");
        break;
    }
  }
  return parts.filter((part) => part.length > 0).join("\n\n");
}

/**
 * Deterministic clipboard projection from the same token tree used to render.
 * Returns null when the source exceeds safe bounds (caller keeps legacy plain).
 */
export function conversationMarkdownToPlainText(
  source: string,
  authorizedLinks: readonly ConversationAuthorizedLink[] = [],
): string | null {
  const tokens = tokenizeConversationMarkdown(source);
  if (!tokens) return null;
  return blockPlain(tokens, authorizedLinks, 0);
}
