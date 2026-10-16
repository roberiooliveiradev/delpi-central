import { Fragment, type ReactNode } from "react";

import {
  safeConversationLinkDestination,
  tokenizeConversationMarkdown,
  type ConversationAuthorizedLink,
  type MarkdownToken,
} from "./conversationMarkdownModel";

export type { ConversationAuthorizedLink } from "./conversationMarkdownModel";
export { conversationMarkdownToPlainText } from "./conversationMarkdownModel";

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
export type ConversationMarkdownProps = {
  text: string;
  /** Explicit host admission — never inferred from text shape. */
  enabled?: boolean;
  className?: string;
  /** Destinations already disclosed by an authorized owner contract.
   * A href occurring in Markdown alone is NEVER sufficient. */
  authorizedLinks?: readonly ConversationAuthorizedLink[];
};

function inline(
  nodes: MarkdownToken[] | undefined,
  links: readonly ConversationAuthorizedLink[],
  depth = 0,
): ReactNode {
  if (!nodes || depth > 8) return null;
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
        return <br key={key} />;
      case "link": {
        const kind = safeConversationLinkDestination(token.href ?? "", links);
        if (!kind) return <Fragment key={key}>{body}</Fragment>;
        return (
          <a
            key={key}
            href={token.href}
            target={kind === "external" ? "_blank" : undefined}
            rel={kind === "external" ? "noopener noreferrer" : undefined}
          >
            {body}
          </a>
        );
      }
      case "image":
        return <Fragment key={key}>{token.text ?? ""}</Fragment>;
      case "html":
        return <Fragment key={key}>{token.raw ?? token.text ?? ""}</Fragment>;
      default:
        return <Fragment key={key}>{token.raw ?? token.text ?? ""}</Fragment>;
    }
  });
}

function blocks(
  nodes: MarkdownToken[],
  links: readonly ConversationAuthorizedLink[],
  depth = 0,
): ReactNode {
  if (depth > 8) return null;
  return nodes.map((token, index) => {
    const key = index;
    switch (token.type) {
      case "paragraph":
      case "text":
        return (
          <p key={key}>
            {token.tokens?.length
              ? inline(token.tokens, links)
              : (token.text ?? "")}
          </p>
        );
      case "heading": {
        const label = token.tokens?.length
          ? inline(token.tokens, links)
          : (token.text ?? "");
        if (token.depth === 1 || token.depth === 2) {
          return <h4 key={key}>{label}</h4>;
        }
        if (token.depth === 3) return <h5 key={key}>{label}</h5>;
        return <h6 key={key}>{label}</h6>;
      }
      case "list": {
        const children = (token.items ?? []).map((item, itemIndex) => (
          <li key={itemIndex}>
            {item.tokens?.length
              ? blocks(item.tokens, links, depth + 1)
              : (item.text ?? "")}
          </li>
        ));
        return token.ordered ? (
          <ol key={key} start={token.start || 1}>
            {children}
          </ol>
        ) : (
          <ul key={key}>{children}</ul>
        );
      }
      case "blockquote":
        return (
          <blockquote key={key}>
            {blocks(token.tokens ?? [], links, depth + 1)}
          </blockquote>
        );
      case "code":
        return (
          <pre key={key}>
            <code>{token.text ?? ""}</code>
          </pre>
        );
      case "hr":
        return <hr key={key} />;
      case "space":
        return null;
      case "table":
        // GFM tables are not admitted — preserve factual text inertly.
        return <p key={key}>{token.raw ?? token.text ?? ""}</p>;
      case "html":
        return <p key={key}>{token.raw ?? token.text ?? ""}</p>;
      case "image":
        return <p key={key}>{token.text ?? ""}</p>;
      default:
        return <p key={key}>{token.raw ?? token.text ?? ""}</p>;
    }
  });
}

export function ConversationMarkdown({
  text,
  enabled = false,
  className,
  authorizedLinks = [],
}: ConversationMarkdownProps) {
  // Keep the exact v1 DOM node and literal text when integration is off.
  if (!enabled) {
    return <p className={className}>{text}</p>;
  }
  const tokens = tokenizeConversationMarkdown(text);
  if (!tokens) {
    return <p className={className}>{text}</p>;
  }
  return (
    <div
      className={["delpi-ui-conversation-markdown", className]
        .filter(Boolean)
        .join(" ")}
      data-delpi-ui="conversation-markdown"
    >
      {blocks(tokens, authorizedLinks)}
    </div>
  );
}
