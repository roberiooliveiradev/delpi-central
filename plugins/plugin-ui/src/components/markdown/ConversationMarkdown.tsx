import { Fragment, type ReactNode } from "react";
import { marked } from "marked";

/**
 * Safe, presentation-only Markdown for a conversational surface.
 *
 * Disabled by default. The host must only enable it after an explicit,
 * backend-admitted presentation.v2 markdown_safe contract has been verified.
 * A model/tool/source string cannot turn the renderer on by itself.
 *
 * Unlike the document/editor Markdown pipeline, this component never uses
 * HTML strings, dangerouslySetInnerHTML, DOMParser, remote images or Mermaid.
 */
export type ConversationAuthorizedLink = {
  href: string;
  kind: "internal" | "external";
};

export type ConversationMarkdownProps = {
  text: string;
  enabled?: boolean;
  className?: string;
  /** Destinations already disclosed by an authorized owner contract.
   * A href occurring in Markdown alone is NEVER sufficient. */
  authorizedLinks?: readonly ConversationAuthorizedLink[];
};

type MarkdownToken = {
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

const MAX_SOURCE_LENGTH = 16_384;
const MAX_NODES = 256;
const MAX_DEPTH = 8;
const MAX_LINKS = 16;
const FORBIDDEN_QUERY_KEY = /^(?:token|access_token|refresh_token|id_token|auth|authorization|key|api_key|secret)$/i;

function safeDestination(href: string, links: readonly ConversationAuthorizedLink[]): "internal" | "external" | null {
  if (!href || href.trim() !== href || /[\\\u0000-\u001f\u007f]/.test(href)) return null;
  const published = links.find((entry) => entry.href === href);
  if (!published) return null;
  try {
    if (published.kind === "internal") {
      if (!href.startsWith("/") || href.startsWith("//") || href.includes("\\")) return null;
      const url = new URL(href, "https://portal.invalid");
      if (url.origin !== "https://portal.invalid") return null;
      for (const name of url.searchParams.keys()) if (FORBIDDEN_QUERY_KEY.test(name)) return null;
      return "internal";
    }
    if (published.kind !== "external") return null;
    const url = new URL(href);
    if (url.protocol !== "https:" || !url.hostname || url.username || url.password) return null;
    for (const name of url.searchParams.keys()) if (FORBIDDEN_QUERY_KEY.test(name)) return null;
    return "external";
  } catch {
    return null;
  }
}

function tokenize(source: string): MarkdownToken[] | null {
  if (source.length > MAX_SOURCE_LENGTH) return null;
  try {
    const tokens = marked.lexer(source, { gfm: true }) as unknown as MarkdownToken[];
    let count = 0;
    let links = 0;
    function inspect(nodes: MarkdownToken[], depth: number): boolean {
      if (depth > MAX_DEPTH) return false;
      for (const node of nodes) {
        if (++count > MAX_NODES) return false;
        if (node.type === "link" && ++links > MAX_LINKS) return false;
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

function inline(nodes: MarkdownToken[] | undefined, links: readonly ConversationAuthorizedLink[], depth = 0): ReactNode {
  if (!nodes || depth > MAX_DEPTH) return null;
  return nodes.map((token, index) => {
    const key = index;
    const body = token.tokens?.length
      ? inline(token.tokens, links, depth + 1)
      : (token.text ?? token.raw ?? "");
    switch (token.type) {
      case "text":
      case "escape":
        return <Fragment key={key}>{body}</Fragment>;
      case "strong":
        return <strong key={key}>{body}</strong>;
      case "em":
        return <em key={key}>{body}</em>;
      case "del":
        return <del key={key}>{body}</del>;
      case "codespan":
        return <code key={key}>{token.text ?? ""}</code>;
      case "br":
        return <Fragment key={key}>{"\n"}</Fragment>;
      case "link": {
        const kind = safeDestination(token.href ?? "", links);
        if (!kind) return <Fragment key={key}>{body}</Fragment>;
        return <a key={key} href={token.href} target={kind === "external" ? "_blank" : undefined} rel={kind === "external" ? "noopener noreferrer" : undefined}>{body}</a>;
      }
      case "image":
        return <Fragment key={key}>{token.text ?? ""}</Fragment>;
      case "html":
        return <Fragment key={key}>{token.raw ?? token.text ?? ""}</Fragment>;
      default:
        // Unsupported extension tokens are never interpreted as markup.
        return <Fragment key={key}>{token.raw ?? token.text ?? ""}</Fragment>;
    }
  });
}

function blocks(nodes: MarkdownToken[], links: readonly ConversationAuthorizedLink[], depth = 0): ReactNode {
  if (depth > MAX_DEPTH) return null;
  return nodes.map((token, index) => {
    const key = index;
    switch (token.type) {
      case "paragraph":
      case "text":
        return <p key={key}>{token.tokens?.length ? inline(token.tokens, links) : (token.text ?? "")}</p>;
      case "heading": {
        const label = token.tokens?.length ? inline(token.tokens, links) : (token.text ?? "");
        return token.depth === 1 || token.depth === 2
          ? <h4 key={key}>{label}</h4>
          : token.depth === 3 ? <h5 key={key}>{label}</h5> : <h6 key={key}>{label}</h6>;
      }
      case "list": {
        const children = (token.items ?? []).map((item, itemIndex) => (
          <li key={itemIndex}>{item.tokens?.length ? blocks(item.tokens, links, depth + 1) : (item.text ?? "")}</li>
        ));
        return token.ordered
          ? <ol key={key} start={token.start || 1}>{children}</ol>
          : <ul key={key}>{children}</ul>;
      }
      case "blockquote":
        return <blockquote key={key}>{blocks(token.tokens ?? [], links, depth + 1)}</blockquote>;
      case "code":
        return <pre key={key}><code>{token.text ?? ""}</code></pre>;
      case "hr":
        return <hr key={key} />;
      case "space":
        return null;
      case "html":
        return <p key={key}>{token.raw ?? token.text ?? ""}</p>;
      case "image":
        return <p key={key}>{token.text ?? ""}</p>;
      default:
        return <p key={key}>{token.raw ?? token.text ?? ""}</p>;
    }
  });
}

/** The copy action currently stays on the legacy plain content. The same
 * tokens can later feed a deterministic copy projection once v2 is admitted. */
export function ConversationMarkdown({
  text,
  enabled = false,
  className,
  authorizedLinks = [],
}: ConversationMarkdownProps) {
  // Keep the exact v1 DOM node and literal text when integration is off.
  if (!enabled) return <p className={className}>{text}</p>;
  const tokens = tokenize(text);
  if (!tokens) return <p className={className}>{text}</p>;
  return (
    <div className={["delpi-ui-conversation-markdown", className].filter(Boolean).join(" ")}>
      {blocks(tokens, authorizedLinks)}
    </div>
  );
}
