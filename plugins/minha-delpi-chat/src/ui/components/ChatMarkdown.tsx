import { useState } from "react";
import type { Components } from "react-markdown";
import ReactMarkdown from "react-markdown";
import { Check, Code2, Copy } from "lucide-react";
import remarkGfm from "remark-gfm";

import { applySoftLineBreaks, prepareMarkdownContent } from "./chatMarkdown";

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
  const [copied, setCopied] = useState(false);
  const label = (language || "text").toUpperCase();

  async function handleCopy() {
    try {
      await navigator.clipboard.writeText(code);
      setCopied(true);
      window.setTimeout(() => setCopied(false), 1800);
    } catch {
      /* clipboard indisponível */
    }
  }

  return (
    <div className="mdc-chat-code-block">
      <div className="mdc-chat-code-block__header">
        <span className="mdc-chat-code-block__lang">
          <Code2 size={15} aria-hidden="true" />
          {label}
        </span>
        <button
          type="button"
          className="mdc-chat-code-block__copy"
          onClick={() => void handleCopy()}
          aria-label={copied ? "Código copiado" : "Copiar código"}
        >
          {copied ? <Check size={15} aria-hidden="true" /> : <Copy size={15} aria-hidden="true" />}
          <span>{copied ? "Copiado" : "Copiar"}</span>
        </button>
      </div>
      <pre className="mdc-chat-code-block__pre">
        <code className={`mdc-chat-code-block__code language-${language}`}>{code}</code>
      </pre>
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
  code({ className, children, ...props }) {
    const match = /language-([\w-]+)/i.exec(className ?? "");
    const code = String(children).replace(/\n$/, "");

    if (match) {
      return <ChatCodeBlock language={match[1]} code={code} />;
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
