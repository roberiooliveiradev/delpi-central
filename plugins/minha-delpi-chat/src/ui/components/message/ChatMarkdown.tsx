import { useLayoutEffect, useRef, useState, type TableHTMLAttributes } from "react";
import type { Components } from "react-markdown";
import ReactMarkdown from "react-markdown";
import { Code2, Table2 } from "lucide-react";
import remarkGfm from "remark-gfm";

import {
  applySoftLineBreaks,
  prepareMarkdownContent,
  tableElementToGfmMarkdown,
} from "./chatMarkdown";
import { ChatPresentationCopyButton } from "../ChatPresentationCopyButton";
import { ChatMermaidBlock } from "./ChatMermaidBlock";

import "./ChatMarkdown.css";

type ChatMarkdownProps = {
  content: string;
  compact?: boolean;
  /** Preserva quebras de linha simples como hard breaks (ex.: mensagem do usuário). */
  softBreaks?: boolean;
};

type ChatCodeBlockProps = {
  language: string;
  code: string;
};

function ChatCodeBlock({ language, code }: ChatCodeBlockProps) {
  const label = (language || "text").toUpperCase();

  return (
    <div className="mdc-chat-code-block">
      <div className="mdc-chat-code-block__header">
        <span className="mdc-chat-code-block__lang">
          <Code2 size={15} aria-hidden="true" />
          {label}
        </span>
        <ChatPresentationCopyButton
          getText={() => code}
          copyAriaLabel="Copiar código"
          copiedAriaLabel="Código copiado"
        />
      </div>
      <pre className="mdc-chat-code-block__pre">
        <code className={`mdc-chat-code-block__code language-${language}`}>{code}</code>
      </pre>
    </div>
  );
}

function resolvePrecedingTableTitle(block: HTMLElement | null): string {
  const previous = block?.previousElementSibling;

  if (!(previous instanceof HTMLElement)) {
    return "TABELA";
  }

  const tag = previous.tagName.toUpperCase();

  if (!/^H[1-6]$/.test(tag)) {
    return "TABELA";
  }

  const title = previous.textContent?.replace(/\s+/g, " ").trim();

  if (!title) {
    return "TABELA";
  }

  previous.classList.add("mdc-chat-markdown__absorbed-heading");
  previous.setAttribute("aria-hidden", "true");

  return title.length > 72 ? `${title.slice(0, 69)}…` : title;
}

function ChatMarkdownTable({
  children,
  ...props
}: TableHTMLAttributes<HTMLTableElement>) {
  const blockRef = useRef<HTMLDivElement>(null);
  const tableRef = useRef<HTMLTableElement>(null);
  const [blockLabel, setBlockLabel] = useState("TABELA");

  useLayoutEffect(() => {
    setBlockLabel(resolvePrecedingTableTitle(blockRef.current));
  }, [children]);

  return (
    <div ref={blockRef} className="mdc-chat-code-block mdc-chat-code-block--table">
      <div className="mdc-chat-code-block__header">
        <span className="mdc-chat-code-block__lang">
          <Table2 size={15} aria-hidden="true" />
          {blockLabel}
        </span>
        <ChatPresentationCopyButton
          getText={() => {
            const table = tableRef.current;

            if (!table) {
              return "";
            }

            const markdown = tableElementToGfmMarkdown(table).trim();
            const title = blockLabel !== "TABELA" ? blockLabel : "";

            return title ? `### ${title}\n\n${markdown}` : markdown;
          }}
          copyAriaLabel="Copiar tabela"
          copiedAriaLabel="Tabela copiada"
        />
      </div>
      <div className="mdc-chat-markdown__table-wrap" tabIndex={0}>
        <table ref={tableRef} {...props}>
          {children}
        </table>
      </div>
    </div>
  );
}

const markdownComponents: Components = {
  p({ children }) {
    return <p>{children}</p>;
  },
  strong({ children }) {
    return <strong>{children}</strong>;
  },
  em({ children }) {
    return <em>{children}</em>;
  },
  pre({ children }) {
    return <>{children}</>;
  },
  a({ href, children, ...props }) {
    const label = String(children ?? "").trim();
    const isExternal = typeof href === "string" && /^https?:\/\//i.test(href);
    const isCitation = isExternal && label.length > 0 && label.length <= 40;

    if (isCitation) {
      return (
        <a
          className="mdc-chat-citation-badge"
          href={href}
          rel="noopener noreferrer"
          target="_blank"
          {...props}
        >
          {children}
        </a>
      );
    }

    return (
      <a href={href} rel={isExternal ? "noopener noreferrer" : undefined} target={isExternal ? "_blank" : undefined} {...props}>
        {children}
      </a>
    );
  },
  table({ children, ...props }) {
    return <ChatMarkdownTable {...props}>{children}</ChatMarkdownTable>;
  },
  code({ className, children, ...props }) {
    const match = /language-([\w-]+)/i.exec(className ?? "");
    const code = String(children).replace(/\n$/, "");

    if (match || code.includes("\n")) {
      const language = (match?.[1] || "text").toLowerCase();

      if (language === "mermaid") {
        return <ChatMermaidBlock code={code} />;
      }

      return <ChatCodeBlock language={language} code={code} />;
    }

    return (
      <code className="mdc-chat-markdown-inline-code" {...props}>
        {children}
      </code>
    );
  },
};

export function ChatMarkdown({ content, compact, softBreaks }: ChatMarkdownProps) {
  const prepared = prepareMarkdownContent(content);
  const normalized = softBreaks ? applySoftLineBreaks(prepared) : prepared;

  if (!normalized.trim()) {
    return null;
  }

  return (
    <div
      className={
        compact ? "mdc-chat-markdown mdc-chat-markdown--compact" : "mdc-chat-markdown"
      }
    >
      <ReactMarkdown remarkPlugins={[remarkGfm]} components={markdownComponents}>
        {normalized}
      </ReactMarkdown>
    </div>
  );
}
